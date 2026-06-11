"""
update_controller.py
UI-Anbindung für Update-Prüfung und Installer-Download.
"""

import os
import threading
import traceback
import webbrowser
from typing import Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon

from src.services.config_service import config
from src.services.update_service import UpdateCheckResult, UpdateInfo, UpdateService
from src.services.update_downloader import download_release_asset
from src.services.update_installer import launch_update_installer
from src.utils.app_paths import user_data_dir
from src.version import GITHUB_REPO, __version__

RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"
_TRAY_MS = 12_000


class UpdateSignals(QObject):
    """Thread-sichere Signale für Update-Ergebnisse (Worker → UI-Thread)."""

    result_ready = pyqtSignal(object, bool)
    download_ready = pyqtSignal(object, object)

    def __init__(self, controller: "UpdateController", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.result_ready.connect(
            self._deliver_result,
            Qt.ConnectionType.QueuedConnection,
        )
        self.download_ready.connect(
            self._deliver_download,
            Qt.ConnectionType.QueuedConnection,
        )

    def _deliver_result(self, result: UpdateCheckResult, silent: bool) -> None:
        try:
            self._controller._on_result(result, silent)
        except Exception:
            self._controller._log(f"UI-Fehler bei Update-Ergebnis:\n{traceback.format_exc()}")
            self._controller._checking = False

    def _deliver_download(self, path: object, info: UpdateInfo) -> None:
        try:
            self._controller._on_download_done(path, info)
        except Exception:
            self._controller._log(f"UI-Fehler nach Download:\n{traceback.format_exc()}")


class UpdateController:
    """Steuert Update-Checks und Benutzer-Rückmeldung."""

    def __init__(self, app) -> None:
        self.app = app
        self.service = UpdateService()
        self._checking = False
        self._pending_info: Optional[UpdateInfo] = None
        qt_app = app.app if hasattr(app, "app") else None
        self._signals = UpdateSignals(self, parent=qt_app)

    def schedule_startup_check(self) -> None:
        if not config.get_bool("check_updates_on_startup", True):
            return
        QTimer.singleShot(12_000, lambda: self.check_now(silent=True))

    def check_now(self, silent: bool = False) -> None:
        if self._checking:
            return
        self._checking = True
        if not silent:
            self._notify(
                "Update-Prüfung",
                "Suche nach Updates…",
                toast_ms=4000,
                icon=QSystemTrayIcon.MessageIcon.Information,
            )
        self.service.check_async(
            lambda result, is_silent=silent: self._signals.result_ready.emit(result, is_silent)
        )

    def _on_result(self, result: UpdateCheckResult, silent: bool) -> None:
        self._checking = False

        if result.error:
            self._log(f"Fehler (v{__version__}): {result.error}")
            if not silent:
                self._notify(
                    "Update fehlgeschlagen",
                    f"{result.error}\nRelease-Seite wird geöffnet…",
                    toast_ms=8000,
                    icon=QSystemTrayIcon.MessageIcon.Warning,
                    error=True,
                )
                QTimer.singleShot(600, self._open_releases_fallback)
            return

        if result.info is None:
            if not silent:
                self._notify(
                    "SurepriseAi",
                    f"Bereits aktuell (v{__version__})",
                    toast_ms=5000,
                    icon=QSystemTrayIcon.MessageIcon.Information,
                )
            return

        info = result.info
        self._log(f"Update gefunden: v{info.version}")
        self._pending_info = info
        self._notify(
            "SurepriseAi Update",
            f"Version {info.version} verfügbar!\nDownload startet gleich…",
            toast_ms=10_000,
            icon=QSystemTrayIcon.MessageIcon.Information,
            update=True,
        )

        if info.download_url:
            QTimer.singleShot(2500, self._start_pending_download)
        elif info.page_url:
            webbrowser.open(info.page_url)

    def _start_pending_download(self) -> None:
        info = self._pending_info
        if not info or not info.download_url:
            return
        self._notify(
            "SurepriseAi Update",
            f"Lade v{info.version} herunter (~140 MB)…",
            toast_ms=10_000,
            icon=QSystemTrayIcon.MessageIcon.Information,
            update=True,
        )
        threading.Thread(
            target=self._download_worker,
            args=(info,),
            daemon=True,
        ).start()

    def _download_worker(self, info: UpdateInfo) -> None:
        try:
            name = info.download_url.rsplit("/", 1)[-1] if info.download_url else ""
            path = download_release_asset(info.download_url or "", name)
            self._log(f"Download: {path}")
            self._signals.download_ready.emit(path, info)
        except Exception:
            self._log(f"Download-Fehler:\n{traceback.format_exc()}")
            self._signals.download_ready.emit(None, info)

    def _on_download_done(self, path: Optional[object], info: UpdateInfo) -> None:
        self._pending_info = None
        if path and hasattr(path, "suffix") and path.suffix.lower() == ".exe":
            self._notify(
                "SurepriseAi Update",
                f"v{info.version} heruntergeladen.\nInstallation läuft automatisch…",
                toast_ms=10_000,
                icon=QSystemTrayIcon.MessageIcon.Information,
                update=True,
            )
            self._launch_installer(path)
        elif path:
            os.startfile(path.parent)
        elif info.page_url:
            webbrowser.open(info.page_url)
            self._notify(
                "Update",
                "Download fehlgeschlagen – Release-Seite geöffnet.",
                toast_ms=8000,
                icon=QSystemTrayIcon.MessageIcon.Warning,
                error=True,
            )
        else:
            self._notify(
                "Update",
                "Download fehlgeschlagen.",
                toast_ms=8000,
                icon=QSystemTrayIcon.MessageIcon.Critical,
                error=True,
            )
            QTimer.singleShot(600, self._open_releases_fallback)

    def _launch_installer(self, path) -> None:
        """Startet NSIS-Setup und beendet die App, damit Dateien freigegeben werden."""
        self._log(f"Starte Silent-Installer: {path}")
        try:
            launch_update_installer(path)
        except Exception:
            self._log(f"Installer-Start fehlgeschlagen:\n{traceback.format_exc()}")
            self._notify(
                "Update",
                "Installation konnte nicht gestartet werden.\n"
                "Bitte SurepriseAi-Setup.exe im Downloads-Ordner manuell ausführen.",
                toast_ms=10_000,
                icon=QSystemTrayIcon.MessageIcon.Warning,
                error=True,
            )
            return
        # App kurz danach beenden – Installer läuft bereits detached.
        QTimer.singleShot(600, self.app.controller.shutdown)

    def open_releases_page(self) -> None:
        self._open_releases_fallback()

    def _open_releases_fallback(self) -> None:
        webbrowser.open(RELEASES_PAGE)
        self._notify(
            "SurepriseAi",
            "Release-Seite im Browser geöffnet.",
            toast_ms=6000,
            icon=QSystemTrayIcon.MessageIcon.Information,
        )

    def _notify(
        self,
        title: str,
        body: str,
        toast_ms: int = 5000,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        *,
        error: bool = False,
        update: bool = False,
    ) -> None:
        """Tray-Ballon (Windows) + Toast – doppelte Absicherung."""
        try:
            self.app.tray.showMessage(title, body, icon, _TRAY_MS)
        except Exception:
            pass
        if update:
            self.app.toast.show_update(body)
        elif error:
            self.app.toast.show_error(body, duration_ms=toast_ms)
        else:
            self.app.toast.show_message(body, duration_ms=toast_ms)

    def _log(self, message: str) -> None:
        print(f"[Update] {message}")
        try:
            log_dir = user_data_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "update.log", "a", encoding="utf-8") as fh:
                fh.write(f"{message}\n")
        except OSError:
            pass

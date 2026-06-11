"""
update_controller.py
UI-Anbindung für Update-Prüfung und Installer-Download.
"""

import os
import threading
import webbrowser
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon

from src.services import update_logger
from src.services.config_service import config
from src.services.update_service import UpdateCheckResult, UpdateInfo, UpdateService
from src.services.update_downloader import download_release_asset
from src.services.update_installer import cleanup_desktop_update_artifacts, launch_update_installer
from src.services import update_state
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
            update_logger.write_exception("UI-Fehler bei Update-Ergebnis")
            self._controller._checking = False

    def _deliver_download(self, path: object, info: UpdateInfo) -> None:
        try:
            self._controller._on_download_done(path, info)
        except Exception:
            update_logger.write_exception("UI-Fehler nach Download")


class UpdateController:
    """Steuert Update-Checks und Benutzer-Rückmeldung."""

    def __init__(self, app) -> None:
        self.app = app
        self.service = UpdateService()
        self._checking = False
        self._pending_info: Optional[UpdateInfo] = None
        qt_app = app.app if hasattr(app, "app") else None
        self._signals = UpdateSignals(self, parent=qt_app)
        cleanup_desktop_update_artifacts()
        update_logger.write_session_header("UpdateController initialisiert")
        cleanup_desktop_update_artifacts()
        update_state.reconcile_pending()

    def schedule_startup_check(self) -> None:
        if not config.get_bool("check_updates_on_startup", True):
            update_logger.write("Startup-Check deaktiviert (check_updates_on_startup=false)")
            return
        allowed, msg = update_state.should_auto_update(manual=False)
        if msg:
            update_logger.write(msg)
        if not allowed:
            return
        update_logger.write("Startup-Check geplant in 12s")
        QTimer.singleShot(12_000, lambda: self.check_now(silent=True))

    def check_now(self, silent: bool = False) -> None:
        if self._checking:
            update_logger.write("check_now übersprungen: Prüfung läuft bereits")
            return
        allowed, msg = update_state.should_auto_update(manual=not silent)
        if not allowed:
            update_logger.write(f"check_now blockiert: {msg.replace(chr(10), ' | ')}")
            if not silent:
                self._notify(
                    "SurepriseAi Update",
                    msg,
                    toast_ms=10_000,
                    icon=QSystemTrayIcon.MessageIcon.Warning,
                )
            return
        self._checking = True
        update_logger.write_session_header(f"Update-Prüfung gestartet (silent={silent})")
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
            update_logger.write(f"Prüfung fehlgeschlagen (v{__version__}): {result.error}")
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
            update_logger.write(f"Bereits aktuell (v{__version__})")
            if not silent:
                self._notify(
                    "SurepriseAi",
                    f"Bereits aktuell (v{__version__})",
                    toast_ms=5000,
                    icon=QSystemTrayIcon.MessageIcon.Information,
                )
            return

        info = result.info
        if update_state.is_duplicate_attempt(info.version):
            update_logger.write(
                f"Update v{info.version} bereits pending – kein erneuter Download"
            )
            if not silent:
                self._notify(
                    "SurepriseAi Update",
                    f"Installation v{info.version} läuft bereits.\n"
                    "Bitte warten – Log: Desktop\\SurepriseAi-Update.log",
                    toast_ms=10_000,
                    icon=QSystemTrayIcon.MessageIcon.Information,
                )
            return

        update_logger.write(f"Update gefunden: v{info.version}")
        update_logger.write(f"  download_url={info.download_url}")
        update_logger.write(f"  page_url={info.page_url}")
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
            update_logger.write("Kein Download-Asset – öffne Release-Seite")
            webbrowser.open(info.page_url)

    def _start_pending_download(self) -> None:
        info = self._pending_info
        if not info or not info.download_url:
            update_logger.write("_start_pending_download: kein pending info/url")
            return
        update_logger.write(f"Download startet für v{info.version}")
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
            path = download_release_asset(
                info.download_url or "",
                name,
                target_version=info.version,
            )
            update_logger.write(f"Download-Worker fertig: {path!r}")
            self._signals.download_ready.emit(path, info)
        except Exception:
            update_logger.write_exception("Download-Worker")
            self._signals.download_ready.emit(None, info)

    def _on_download_done(self, path: Optional[object], info: UpdateInfo) -> None:
        self._pending_info = None
        update_logger.write(f"_on_download_done: path={path!r} type={type(path).__name__}")

        setup_path = Path(path) if path else None
        if setup_path:
            update_logger.write(
                f"  suffix={setup_path.suffix!r} "
                f"exists={setup_path.is_file()} "
                f"size={setup_path.stat().st_size if setup_path.is_file() else 'n/a'}"
            )

        if setup_path and setup_path.suffix.lower() == ".exe" and setup_path.is_file():
            update_logger.write("Zweig: .exe erkannt → starte Installer")
            self._notify(
                "SurepriseAi Update",
                f"v{info.version} heruntergeladen.\nInstallation läuft automatisch…",
                toast_ms=10_000,
                icon=QSystemTrayIcon.MessageIcon.Information,
                update=True,
            )
            self._launch_installer(setup_path, info.version)
        elif setup_path:
            update_logger.write(
                f"Zweig: Datei ohne .exe ({setup_path.suffix}) → öffne Downloads-Ordner"
            )
            os.startfile(setup_path.parent)
        elif info.page_url:
            update_logger.write("Zweig: Download fehlgeschlagen → Release-Seite")
            webbrowser.open(info.page_url)
            self._notify(
                "Update",
                "Download fehlgeschlagen – Release-Seite geöffnet.",
                toast_ms=8000,
                icon=QSystemTrayIcon.MessageIcon.Warning,
                error=True,
            )
        else:
            update_logger.write("Zweig: Download fehlgeschlagen (keine URL)")
            self._notify(
                "Update",
                "Download fehlgeschlagen.",
                toast_ms=8000,
                icon=QSystemTrayIcon.MessageIcon.Critical,
                error=True,
            )
            QTimer.singleShot(600, self._open_releases_fallback)

    def _launch_installer(self, path: Path, target_version: str) -> None:
        """Startet NSIS-Setup via PowerShell in %TEMP% (taskkill + /S + Neustart)."""
        update_logger.write_session_header(
            f"Installer-Start für {path} (Ziel v{target_version})"
        )
        update_state.mark_pending(target_version, str(path))
        try:
            launch_update_installer(path)
            update_logger.write("launch_update_installer: OK – PowerShell übernimmt taskkill + NSIS")
        except Exception:
            update_state.clear_pending()
            update_logger.write_exception("Installer-Start fehlgeschlagen")
            self._notify(
                "Update",
                "Installation konnte nicht gestartet werden.\n"
                f"Log: {update_logger.desktop_log_path()}",
                toast_ms=12_000,
                icon=QSystemTrayIcon.MessageIcon.Warning,
                error=True,
            )
            return
        self._notify(
            "SurepriseAi Update",
            f"v{target_version}: Installation startet…\nApp wird beendet und neu gestartet.",
            toast_ms=10_000,
            icon=QSystemTrayIcon.MessageIcon.Information,
            update=True,
        )

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
        update_logger.write(f"Notify [{title}]: {body.replace(chr(10), ' | ')}")
        try:
            self.app.tray.showMessage(title, body, icon, _TRAY_MS)
        except Exception as exc:
            update_logger.write(f"Tray showMessage fehlgeschlagen: {exc}")
        if update:
            self.app.toast.show_update(body)
        elif error:
            self.app.toast.show_error(body, duration_ms=toast_ms)
        else:
            self.app.toast.show_message(body, duration_ms=toast_ms)

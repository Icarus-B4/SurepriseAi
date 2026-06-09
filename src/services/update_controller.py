"""
update_controller.py
UI-Anbindung für Update-Prüfung und Installer-Download.
"""

import os
import subprocess
import threading
import webbrowser
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.services.config_service import config
from src.services.update_service import UpdateInfo, UpdateService
from src.services.update_downloader import download_release_asset
from src.version import __version__


class UpdateSignals(QObject):
    """Thread-sichere Signale für Update-Ergebnisse (Worker → UI-Thread)."""

    result_ready = pyqtSignal(object, bool)
    download_ready = pyqtSignal(object, object)  # Pfad | None, UpdateInfo


class UpdateController:
    """Steuert Update-Checks und Benutzer-Rückmeldung."""

    def __init__(self, app) -> None:
        self.app = app
        self.service = UpdateService()
        self._checking = False
        self._signals = UpdateSignals()
        self._signals.result_ready.connect(self._on_result)
        self._signals.download_ready.connect(self._on_download_done)

    def schedule_startup_check(self) -> None:
        """Prüft nach Start im Hintergrund auf Updates."""
        if not config.get_bool("check_updates_on_startup", True):
            return
        QTimer.singleShot(12_000, lambda: self.check_now(silent=True))

    def check_now(self, silent: bool = False) -> None:
        if self._checking:
            return
        self._checking = True
        if not silent:
            self.app.toast.show_message("Suche nach Updates…", duration_ms=1500)
        self.service.check_async(
            lambda info, is_silent=silent: self._signals.result_ready.emit(info, is_silent)
        )

    def _on_result(self, info: Optional[UpdateInfo], silent: bool) -> None:
        """Läuft garantiert im Qt-Hauptthread."""
        self._checking = False
        if info is None:
            if not silent:
                self.app.toast.show_message(
                    f"Bereits aktuell (v{__version__})",
                    duration_ms=2200,
                )
            return

        self.app.toast.show_success(f"Update v{info.version} verfügbar!")
        if info.download_url:
            self.app.toast.show_message("Lade Installer…", duration_ms=3000)
            threading.Thread(
                target=self._download_worker,
                args=(info,),
                daemon=True,
            ).start()
        elif info.page_url:
            webbrowser.open(info.page_url)

    def _download_worker(self, info: UpdateInfo) -> None:
        name = info.download_url.rsplit("/", 1)[-1] if info.download_url else ""
        path = download_release_asset(info.download_url or "", name)
        self._signals.download_ready.emit(path, info)

    def _on_download_done(self, path: Optional[object], info: UpdateInfo) -> None:
        """Download abgeschlossen – wieder im Hauptthread."""
        if path and hasattr(path, "suffix") and path.suffix.lower() == ".exe":
            self._launch_installer(path)
        elif path:
            os.startfile(path.parent)
        elif info.page_url:
            webbrowser.open(info.page_url)
            self.app.toast.show_error("Download fehlgeschlagen – Release-Seite geöffnet.")
        else:
            self.app.toast.show_error("Update-Download fehlgeschlagen.")

    def _launch_installer(self, path) -> None:
        """Startet Setup-EXE nach Download (App beenden)."""
        self.app.toast.show_message(
            "Installer wird gestartet – SurepriseAi beendet sich…",
            duration_ms=2500,
        )
        QTimer.singleShot(800, self.app.controller.shutdown)
        QTimer.singleShot(1200, lambda: subprocess.Popen([str(path)], shell=True))

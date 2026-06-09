"""
update_controller.py
UI-Anbindung für Update-Prüfung und Installer-Download.
"""

import os
import subprocess
import webbrowser
from typing import Optional

from PyQt6.QtCore import QTimer

from src.services.config_service import config
from src.services.update_service import UpdateInfo, UpdateService
from src.services.update_downloader import download_release_asset
from src.version import __version__


class UpdateController:
    """Steuert Update-Checks und Benutzer-Rückmeldung."""

    def __init__(self, app) -> None:
        self.app = app
        self.service = UpdateService()
        self._checking = False

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
        self.service.check_async(lambda info: self._on_result(info, silent))

    def _on_result(self, info: Optional[UpdateInfo], silent: bool) -> None:
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
            name = info.download_url.rsplit("/", 1)[-1]
            path = download_release_asset(info.download_url, name)
            if path and path.suffix.lower() == ".exe":
                self._launch_installer(path)
            elif path:
                os.startfile(path.parent)
        elif info.page_url:
            webbrowser.open(info.page_url)

    def _launch_installer(self, path) -> None:
        """Startet Setup-EXE nach Download (App beenden)."""
        self.app.toast.show_message(
            "Installer wird gestartet – SurepriseAi beendet sich…",
            duration_ms=2500,
        )
        QTimer.singleShot(800, self.app.controller.shutdown)
        QTimer.singleShot(1200, lambda: subprocess.Popen([str(path)], shell=True))

"""
app.py
Haupt-App-Controller für SurepriseAi (PyQt6 Version).
Schlanke Hauptorchestrierung, delegiert Event-Handling an AppController.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.ui.dynamic_island import DynamicIslandWindow
from src.ui.toast_notification import ToastNotification
from src.ui.island_states import IslandState, IslandStateMachine
from src.services.transcription_pipeline import TranscriptionPipeline
from src.services.hotkey_service import HotkeyService
from src.services.outside_click_service import OutsideClickService, OutsideClickBridge
from src.services.config_service import config
from src.services.app_controller import AppController
from src.ui.tray_icon import SurepriseTrayIcon
from src.ui.accent_theme import apply_accent_from_config


class PipelineSignals(QObject):
    """Thread-sichere Signalschnittstelle für Qt-UI."""
    ready = pyqtSignal(bool)
    state_changed = pyqtSignal(str)
    result_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)
    audio_level = pyqtSignal(float)
    partial_ready = pyqtSignal(str)  # Für Live-Transkription


class SurepriseApp:
    """
    Hauptanwendungsklasse für SurepriseAi.
    Orchestriert Initialisierung von UI, Hotkeys und Pipeline.
    """

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.signals = PipelineSignals()
        self.pipeline = TranscriptionPipeline()
        self.hotkey = HotkeyService()
        self.outside_click_bridge = OutsideClickBridge()
        self.outside_click = OutsideClickService(self.outside_click_bridge)
        self.state_machine = IslandStateMachine()

        # UI & Tray
        self.window = DynamicIslandWindow(self.state_machine)
        self.toast = ToastNotification()
        self.tray = SurepriseTrayIcon()

        # Controller für die Event-Verarbeitung instanziieren
        self.controller = AppController(self)
        self.controller.connect_all()
        self.mini_fab = None

    def start(self):
        """Startet Services und die Qt-Ereignisschleife."""
        apply_accent_from_config()

        self.pipeline.initialize_async(on_ready=self.signals.ready.emit)
        if config.hotkey_enabled:
            self.hotkey.start()

        self.outside_click_bridge.clicked.connect(self.controller.handle_outside_click)
        self.outside_click.start()

        self._sync_mini_fab_at_start()

        self.accent_timer = QTimer()
        self.accent_timer.timeout.connect(self.controller.check_accent_changed)
        self.accent_timer.start(45_000)

        self.window.show()
        self.tray.show()
        sys.exit(self.app.exec())

    def _sync_mini_fab_at_start(self):
        if config.get_bool("enable_mini_fab", False):
            from src.ui.mini_fab import MiniFab
            self.mini_fab = MiniFab()
            self.mini_fab.toggle_recording.connect(self.pipeline.toggle)
            self.mini_fab.show_with_fade()
        else:
            self.mini_fab = None

    def shutdown(self):
        """Delegiert das saubere Beenden an den AppController."""
        self.controller.shutdown()

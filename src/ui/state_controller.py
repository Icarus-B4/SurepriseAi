"""
state_controller.py
State-Transition-Controller für die Dynamic Island.
Übernimmt die visuelle Anpassung des Fensters und der Kapsel bei Zustandsänderungen
sowie das Steuern des Fokus-Verhaltens.
"""

from PyQt6.QtCore import Qt
from src.ui.island_states import IslandState
from src.ui.design_tokens import IslandSize
from src.services.config_service import config


class StateController:
    """Verwaltet Zustandsänderungen und Fokusverhalten der Dynamic Island."""

    def __init__(self, window):
        self.window = window

    def on_state_changed(self, prev_state: IslandState, new_state: IslandState):
        """Reagiert auf Zustandswechsel und passt die Window-Größe und den Modus an."""
        self.window._outside_overlay.hide_overlay()

        if prev_state == IslandState.EXPANDED and new_state != IslandState.EXPANDED:
            pass  # Größe wird unten per sync_carrier_to_pill gesetzt

        if new_state == IslandState.IDLE:
            self.window.pill.set_idle()
            self.window.pill.set_corner_radius(IslandSize.IDLE_HEIGHT // 2)
            self.window.animate_to(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
            self.set_focus_accepting(False)
            self.window.sync_carrier_to_pill(IslandSize.IDLE_WIDTH, IslandSize.IDLE_HEIGHT)
            if config.get_bool("enable_presence_bar", True):
                self.window._set_idle_revealed(False)
            else:
                self.window.presence_controller.reset_visit_state()
                self.window.presence_controller.check_hover()
        elif new_state == IslandState.RECORDING:
            self.window._exit_presence_mode()
            self.window.pill.start_recording()
            self.window.pill.set_corner_radius(IslandSize.RECORDING_HEIGHT // 2)
            self.window.animate_to(IslandSize.RECORDING_WIDTH, IslandSize.RECORDING_HEIGHT)
            self.set_focus_accepting(False)
            self.window.sync_carrier_to_pill(IslandSize.RECORDING_WIDTH, IslandSize.RECORDING_HEIGHT)
        elif new_state == IslandState.PROCESSING:
            self.window._exit_presence_mode()
            self.window.pill.expanded_widget.exit_live_mode()
            if prev_state == IslandState.RECORDING:
                self.window.pill.play_settle_pulse()
            self.window.pill.start_processing()
            self.window.pill.set_corner_radius(IslandSize.PROCESSING_HEIGHT // 2)
            self.window.animate_to(IslandSize.PROCESSING_WIDTH, IslandSize.PROCESSING_HEIGHT)
            self.set_focus_accepting(False)
            self.window.sync_carrier_to_pill(IslandSize.PROCESSING_WIDTH, IslandSize.PROCESSING_HEIGHT)
        elif new_state == IslandState.SUCCESS:
            self.window._exit_presence_mode()
            self.window.pill.stop_processing()
            self.window.pill.set_corner_radius(IslandSize.SUCCESS_HEIGHT // 2)
            self.window.animate_to(IslandSize.SUCCESS_WIDTH, IslandSize.SUCCESS_HEIGHT)
            self.set_focus_accepting(False)
            self.window.sync_carrier_to_pill(IslandSize.SUCCESS_WIDTH, IslandSize.SUCCESS_HEIGHT)
        elif new_state == IslandState.EXPANDED:
            self.window._exit_presence_mode()
            expanded = self.window.pill.expanded_widget
            if prev_state == IslandState.RECORDING:
                expanded.enter_live_mode()
            else:
                expanded.exit_live_mode()
            self.window.pill.stacked_widget.setCurrentIndex(4)
            self.window.pill.set_corner_radius(IslandSize.EXPANDED_RADIUS)
            self.window.animate_to(IslandSize.EXPANDED_WIDTH, self.window._expanded_height)
            self.window.sync_carrier_to_pill(IslandSize.EXPANDED_WIDTH, self.window._expanded_height)
            self.set_focus_accepting(True)
            self.window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.window._outside_overlay.show_below(self.window)
        elif new_state == IslandState.BASICS:
            self.window._exit_presence_mode()
            self.window.pill.set_basics()
            self.window.pill.set_corner_radius(IslandSize.BASICS_HEIGHT // 2)
            self.window.animate_to(
                IslandSize.BASICS_WIDTH, IslandSize.BASICS_HEIGHT
            )
            self.set_focus_accepting(False)
            self.window.sync_carrier_to_pill(
                IslandSize.BASICS_WIDTH, IslandSize.BASICS_HEIGHT
            )

    def set_focus_accepting(self, accept: bool):
        """Bestimmt, ob das Fenster Tastatureingaben/Fokus akzeptieren darf."""
        flags = self.window.windowFlags()
        has_focus_block = bool(flags & Qt.WindowType.WindowDoesNotAcceptFocus)

        if accept and has_focus_block:
            geom = self.window.geometry()
            self.window.setWindowFlags(flags & ~Qt.WindowType.WindowDoesNotAcceptFocus)
            self.window.setGeometry(geom)
            self.window.show()
        elif not accept and not has_focus_block:
            geom = self.window.geometry()
            self.window.setWindowFlags(flags | Qt.WindowType.WindowDoesNotAcceptFocus)
            self.window.setGeometry(geom)
            self.window.show()

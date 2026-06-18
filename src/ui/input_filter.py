"""
input_filter.py
Maus- und Eingabe-EventFilter für die Dynamic Island.
Abfängt Mausklicks, Doppelklicks und Scroll-Ereignisse auf dem Fenster.
"""

from PyQt6.QtCore import QObject, QEvent, Qt, QTimer
from src.ui.island_states import IslandState
from src.services.config_service import config


class InputFilter(QObject):
    """Event-Filter zur Kapselung der Mausinteraktionen auf dem Hauptfenster."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        
        # Klick-Timer für Einfachklicks
        self._pill_click_timer = QTimer(self)
        self._pill_click_timer.setSingleShot(True)
        self._pill_click_timer.timeout.connect(self._on_pill_single_click)

    def _handle_mouse_press(self, event):
        """Behandelt einfache Mausklicks."""
        point = event.position().toPoint()
        sm = self.window.state_machine

        if sm.is_expanded and event.button() == Qt.MouseButton.LeftButton:
            if not self.window._local_point_hits_chrome(point):
                if self.window.outside_dismiss_callback:
                    self.window.outside_dismiss_callback()
                event.accept()
                return

        if self.window.presence_bar.isVisible() and self.window.presence_bar.geometry().contains(point):
            if event.button() == Qt.MouseButton.LeftButton:
                self.window._set_idle_revealed(True)
                self._schedule_pill_single_click()
            event.accept()
            return

        if self.window.pill.isVisible() and self.window.pill.geometry().contains(point):
            if event.button() == Qt.MouseButton.RightButton:
                if sm.is_idle or sm.is_success or sm.is_recording:
                    sm.transition_by_name("expanded")
                event.accept()
            elif event.button() == Qt.MouseButton.LeftButton:
                self._schedule_pill_single_click()
                event.accept()

    def _schedule_pill_single_click(self):
        sm = self.window.state_machine
        if sm.is_idle or sm.is_success or sm.is_recording:
            self._pill_click_timer.start(280)

    def _on_pill_single_click(self):
        sm = self.window.state_machine
        if sm.is_idle or sm.is_success:
            sm.transition_by_name("expanded")
        elif sm.is_recording:
            sm.transition_by_name("expanded")

    def _handle_mouse_double_click(self, event):
        """Behandelt Maus-Doppelklicks."""
        if self.window.pill.isVisible() and self.window.pill.geometry().contains(event.position().toPoint()):
            if event.button() == Qt.MouseButton.LeftButton:
                self._pill_click_timer.stop()
                self.window._toggle_settings()
                event.accept()

    def _handle_wheel(self, event):
        """Mausrad: Presence-Bar ↔ Idle-Pill ↔ Basics (nur IDLE/BASICS)."""
        sm = self.window.state_machine
        if sm.current not in (IslandState.IDLE, IslandState.BASICS):
            event.ignore()
            return

        delta = event.angleDelta().y()
        if delta == 0:
            event.accept()
            return

        scroll_up = delta > 0
        presence_enabled = config.get_bool("enable_presence_bar", True)

        if sm.current == IslandState.BASICS:
            if not scroll_up:
                sm.transition_to(IslandState.IDLE)
                self.window._exit_presence_mode()
            event.accept()
            return

        # IDLE
        if not presence_enabled:
            if scroll_up:
                sm.transition_to(IslandState.BASICS)
            event.accept()
            return

        if self.window._idle_revealed:
            if scroll_up:
                sm.transition_to(IslandState.BASICS)
            else:
                self.window._set_idle_revealed(False)
        elif scroll_up:
            self.window._set_idle_revealed(True)

        event.accept()

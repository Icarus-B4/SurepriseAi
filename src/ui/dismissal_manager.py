"""
dismissal_manager.py
Dismissal- und Click-Outside-Manager für die Dynamic Island.
Ermittelt, ob ein Klick außerhalb des sichtbaren Fensterbereichs stattgefunden hat,
und kollabiert das Overlay gegebenenfalls.
"""

from PyQt6.QtCore import QObject, QRect, QPoint


class DismissalManager(QObject):
    """Verwaltet Klicks außerhalb der Dynamic Island und steuert das Kollabieren."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def is_dismissible_by_outside_click(self) -> bool:
        """Prüft, ob der aktuelle Zustand ein Schließen per Klick außerhalb erlaubt."""
        if self.window._presence_hidden_for_settings:
            return False
        sm = self.window.state_machine
        if sm.is_recording or sm.is_processing:
            return False
        if sm.is_expanded:
            return True
        if sm.is_idle or sm.is_basics or sm.is_success:
            return self.window.windowOpacity() > 0.01
        return False

    def visible_chrome_global_rect(self) -> QRect:
        """Liefert das umgebende Rechteck aller sichtbaren Elemente in globalen Koordinaten."""
        if self.window.windowOpacity() < 0.01:
            return QRect()

        local_rects = []
        if self.window.presence_bar.isVisible():
            local_rects.append(self.window.presence_bar.geometry())
        if self.window.pill.isVisible():
            local_rects.append(self.window.pill.geometry())

        if not local_rects:
            return QRect()

        united = local_rects[0]
        for rect in local_rects[1:]:
            united = united.united(rect)

        top_left = self.window.mapToGlobal(united.topLeft())
        return QRect(top_left, united.size())

    def should_dismiss_for_global_click(self, global_x: int, global_y: int) -> bool:
        """Prüft, ob ein globaler Klick außerhalb des sichtbaren Fensters stattfand."""
        if not self.is_dismissible_by_outside_click():
            return False
        if not self.window.isVisible() or self.window.windowOpacity() < 0.01:
            return False
        if not self.window.geometry().contains(global_x, global_y):
            return True
        local = self.window.mapFromGlobal(QPoint(global_x, global_y))
        return not self._local_point_hits_chrome(local)

    def _local_point_hits_chrome(self, point: QPoint) -> bool:
        """Prüft, ob der lokale Punkt eines der sichtbaren UI-Elemente trifft."""
        if self.window.presence_bar.isVisible() and self.window.presence_bar.geometry().contains(point):
            return True
        if self.window.pill.isVisible() and self.window.pill.geometry().contains(point):
            return True
        return False

    def collapse_from_outside_click(self) -> None:
        """Kollabiert das Fenster komplett bei Klicks außerhalb."""
        self.window._idle_revealed = False
        if hasattr(self.window, "presence_controller"):
            self.window.presence_controller.reset_visit_state()
        self.window._hide_idle_completely()

"""
presence_controller.py
Hover- und Presence-Manager für die Dynamic Island.
Presence-Bar ↔ Pill per Mausrad; Auto-Hide wenn die Maus ~2 cm entfernt ist.
"""

from PyQt6.QtCore import QObject, QTimer, QRect, QPoint
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication
from src.ui.design_tokens import IslandSize
from src.services.config_service import config


class PresenceController(QObject):
    """Steuert Sichtbarkeit von Presence-Bar und Idle-Pill per Mausnähe."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self._was_in_trigger_zone = False

        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self.check_hover)
        self.hover_timer.start(100)

    def _proximity_margin_px(self) -> int:
        """~2 cm Abstand in Bildschirm-Pixel (DPI-abhängig)."""
        screen = QApplication.primaryScreen()
        dpi = screen.logicalDotsPerInchX() if screen else 96.0
        return max(48, int(dpi * IslandSize.PRESENCE_PROXIMITY_CM / 2.54))

    def _cursor_near_chrome(self) -> bool:
        """True wenn der Cursor innerhalb ~2 cm um sichtbares Chrome liegt."""
        pos = QCursor.pos()
        margin = self._proximity_margin_px()

        if self.window.windowOpacity() > 0.01:
            chrome = self.window.dismissal_manager.visible_chrome_global_rect()
            if not chrome.isNull():
                return chrome.adjusted(-margin, -margin, margin, margin).contains(pos)

        geo = self.window.geometry()
        if geo.width() > 0 and geo.height() > 0:
            wake = QRect(
                geo.left() - margin,
                geo.top() - margin,
                geo.width() + margin * 2,
                geo.height() + margin * 2,
            )
            if wake.contains(pos):
                return True

        screen_rect = QApplication.primaryScreen().geometry()
        center_x = screen_rect.width() / 2
        half_w = IslandSize.PRESENCE_TRIGGER_HALF_W
        return (
            center_x - half_w <= pos.x() <= center_x + half_w
            and pos.y() <= IslandSize.PRESENCE_TRIGGER_MAX_Y + margin
        )

    def check_hover(self):
        """Blendet Presence-Bar/Pill ein oder aus – abhängig von der Mausnähe."""
        sm = self.window.state_machine

        if sm.is_basics:
            self.window._exit_presence_mode()
            return

        if not sm.is_idle:
            if self.window.windowOpacity() < 1.0:
                self.window._fade_to(1.0)
            if not self.window.pill.isVisible():
                self.window._exit_presence_mode()
            return

        if self.window._presence_hidden_for_settings:
            return

        if not config.get_bool("enable_presence_bar", True):
            pos = QCursor.pos()
            screen_rect = QApplication.primaryScreen().geometry()
            center_x = screen_rect.width() / 2
            half_w = IslandSize.PRESENCE_TRIGGER_HALF_W
            is_in_zone = (
                center_x - half_w <= pos.x() <= center_x + half_w
                and pos.y() <= IslandSize.PRESENCE_TRIGGER_MAX_Y
            )
            if self.window.geometry().contains(pos):
                is_in_zone = True
            self.window.is_hovered = is_in_zone
            if is_in_zone:
                if self.window.windowOpacity() < 0.01:
                    self.window._restore_idle_chrome()
                self.window._set_idle_revealed(True)
            else:
                self.window._hide_idle_completely()
            return

        near = self._cursor_near_chrome()
        self.window.is_hovered = near
        self._was_in_trigger_zone = near

        if near:
            if self.window.windowOpacity() < 0.01:
                self.window._restore_idle_chrome()
            elif self.window.windowOpacity() < 1.0:
                self.window._fade_to(1.0)
            elif self.window._idle_revealed and not self.window.pill.isVisible():
                self.window._exit_presence_mode()
            elif not self.window._idle_revealed and not self.window.presence_bar.isVisible():
                self.window._set_idle_revealed(False)
        else:
            if self.window.windowOpacity() > 0.01:
                self.window._hide_idle_completely()

    def reset_visit_state(self):
        self._was_in_trigger_zone = False

    def force_active_visit(self):
        """Nach Expanded-Dismiss: Presence-Bar oder Pill je nach Modus."""
        if config.get_bool("enable_presence_bar", True):
            if self._cursor_near_chrome():
                self.window._restore_idle_chrome()
            else:
                self.window._hide_idle_completely()
        else:
            if self._cursor_near_chrome():
                self.window._set_idle_revealed(True)
            else:
                self.window._hide_idle_completely()

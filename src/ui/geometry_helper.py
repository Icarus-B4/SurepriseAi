"""
geometry_helper.py
Geometrie- und Positionierungshelfer für die Dynamic Island.
Kapselt die Fenster-Zentrierung sowie die Größen-Animationen (animate_to).
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPropertyAnimation, Qt
from src.ui.design_tokens import AnimationTokens, Motion


class GeometryHelper:
    """Helferklasse zur Kapselung von Geometrieberechnungen und -animationen."""

    def __init__(self, window):
        self.window = window

    def setup_position(self, force: bool = False):
        """Zentriert das Fenster am oberen Bildschirmrand, es sei denn, der Nutzer hat es verschoben."""
        if self.window._user_moved and not force:
            return
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = int(geom.left() + (geom.width() - self.window.width()) / 2.0)
            y = int(geom.top() + 10)
            self.window.move(x, y)

    def animate_to(self, target_w: int, target_h: int):
        """Animiert die Breite und Höhe der Kapsel (Pill)."""
        self.anim_w = QPropertyAnimation(self.window, b"pill_width")
        self.anim_w.setDuration(AnimationTokens.NORMAL)
        self.anim_w.setStartValue(self.window.pill.width())
        self.anim_w.setEndValue(target_w)
        self.anim_w.setEasingCurve(Motion.spring())

        self.anim_h = QPropertyAnimation(self.window, b"pill_height")
        self.anim_h.setDuration(AnimationTokens.NORMAL)
        self.anim_h.setStartValue(self.window.pill.height())
        self.anim_h.setEndValue(target_h)
        self.anim_h.setEasingCurve(Motion.spring())

        def _on_anim_done():
            self.window.sync_carrier_to_pill(target_w, target_h)

        self.anim_h.finished.connect(_on_anim_done, Qt.ConnectionType.SingleShotConnection)
        self.anim_w.start()
        self.anim_h.start()

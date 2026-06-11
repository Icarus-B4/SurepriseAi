"""
island_shimmer_indicator.py
Kompakte Presence-Bar mit Shimmer-Animation – zeigt an, dass die Dynamic Island aktiv ist.
Sichtbarkeit und Auto-Hide steuert dynamic_island.py (Parent).
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import (
    QBrush,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QColor,
)

from src.ui.design_tokens import Colors, IslandSize


class IslandShimmerIndicator(QWidget):
    """Schmale Kapsel oben am Bildschirm mit wanderndem Lichtreflex."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(IslandSize.PRESENCE_WIDTH, IslandSize.PRESENCE_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._phase = 0.0
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        """Startet die Shimmer-Animation."""
        if self._active:
            return
        self._active = True
        self._timer.start(16)
        self.show()

    def stop(self) -> None:
        """Stoppt die Animation."""
        self._active = False
        self._timer.stop()

    def _tick(self) -> None:
        self._phase = (self._phase + 0.012) % 1.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2.0
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # Basis-Kapsel
        painter.fillPath(path, QBrush(QColor(13, 13, 15, 210)))
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        painter.drawPath(path)

        # Wandernder Shimmer (Indigo → Weiß → Indigo)
        band = w * 0.55
        center = -band + (w + band * 2) * self._phase
        grad = QLinearGradient(center - band, 0, center + band, 0)
        grad.setColorAt(0.0, QColor(99, 102, 241, 0))
        grad.setColorAt(0.35, QColor(99, 102, 241, 55))
        grad.setColorAt(0.5, QColor(245, 245, 247, 120))
        grad.setColorAt(0.65, QColor(129, 140, 248, 70))
        grad.setColorAt(1.0, QColor(99, 102, 241, 0))

        painter.setClipPath(path)
        painter.fillRect(QRectF(0, 0, w, h), QBrush(grad))

        # Dezenter Rand-Glow
        glow = QLinearGradient(0, 0, w, 0)
        glow.setColorAt(0.0, QColor(Colors.ACCENT_HEX))
        glow.setColorAt(0.5, QColor(Colors.ACCENT_BRIGHT_HEX))
        glow.setColorAt(1.0, QColor(Colors.ACCENT_HEX))
        painter.setPen(QPen(QBrush(glow), 1.2))
        painter.drawPath(path)

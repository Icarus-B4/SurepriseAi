"""
led_level_indicator.py
Vertikaler LED-Pegel-Indikator für die Aufnahme-Ansicht.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QBrush, QColor


class LedLevelIndicator(QWidget):
    """5-Segment LED-Balken (Grün → Rot) für den Mikrofonpegel."""

    _COLORS = ["#30D158", "#30D158", "#FFD60A", "#FF9F0A", "#FF453A"]
    _THRESHOLDS = [0.05, 0.20, 0.40, 0.65, 0.85]

    def __init__(self, parent=None, *, compact: bool = False):
        super().__init__(parent)
        self._compact = compact
        self.setFixedSize(14 if compact else 18, 36 if compact else 46)
        self._level = 0.0

    def set_level(self, level: float) -> None:
        self._level = max(0.0, min(1.0, level))
        self.update()

    def reset(self) -> None:
        self.set_level(0.0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._compact:
            led_w, led_h, spacing, base_y = 7, 3, 3, 30
            x = 3
        else:
            led_w, led_h, spacing, base_y = 10, 5, 4, 40
            x = 4

        for i in range(5):
            y = base_y - i * (led_h + spacing)
            color = QColor(self._COLORS[i])
            if self._level >= self._THRESHOLDS[i]:
                painter.setBrush(QBrush(color))
            else:
                dim = QColor(color)
                dim.setAlpha(55)
                painter.setBrush(QBrush(dim))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, led_w, led_h, 2, 2)

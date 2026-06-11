"""
toggle_switch.py
Kompakter Fluent-Toggle für Einstellungen (unabhängig von Windows-Akzent-QSS).
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor

from src.ui.design_tokens import Colors, AnimationTokens

# Feste Toggle-Farben – Einstellungen bleiben visuell konsistent (kein Windows-Gelb)
_TRACK_OFF = QColor("#3A3A42")
_TRACK_ON = QColor("#6366F1")
_THUMB = QColor("#FFFFFF")

_TRACK_W = 32
_TRACK_H = 18
_THUMB_D = 14
_THUMB_MARGIN = 2


class ToggleSwitch(QWidget):
    """Kleiner iOS/Fluent-Schalter mit Daumen-Animation."""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, *, checked: bool = False):
        super().__init__(parent)
        self._checked = checked
        self._thumb_pos = 1.0 if checked else 0.0
        self.setFixedSize(_TRACK_W, _TRACK_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"thumbPosition")
        self._anim.setDuration(AnimationTokens.FAST)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, *, animate: bool = True) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        target = 1.0 if checked else 0.0
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._thumb_pos)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._thumb_pos = target
            self.update()
        self.toggled.emit(checked)

    def getThumbPosition(self) -> float:
        return self._thumb_pos

    def setThumbPosition(self, pos: float) -> None:
        self._thumb_pos = pos
        self.update()

    thumbPosition = pyqtProperty(float, getThumbPosition, setThumbPosition)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            event.accept()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        radius = h / 2.0

        off = _TRACK_OFF.getRgbF()[:3]
        on = _TRACK_ON.getRgbF()[:3]
        t = self._thumb_pos
        track = QColor(
            int((off[0] + (on[0] - off[0]) * t) * 255),
            int((off[1] + (on[1] - off[1]) * t) * 255),
            int((off[2] + (on[2] - off[2]) * t) * 255),
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 0, self.width(), h, radius, radius)

        travel = self.width() - _THUMB_D - 2 * _THUMB_MARGIN
        thumb_x = _THUMB_MARGIN + travel * self._thumb_pos
        thumb_y = (h - _THUMB_D) / 2.0
        p.setBrush(_THUMB)
        p.drawEllipse(int(thumb_x), int(thumb_y), _THUMB_D, _THUMB_D)


class ToggleRow(QWidget):
    """Label links, kompakter Toggle rechts."""

    toggled = pyqtSignal(bool)

    def __init__(self, label: str, *, checked: bool = False, parent=None):
        super().__init__(parent)
        self._switch = ToggleSwitch(checked=checked)
        self._switch.toggled.connect(self.toggled.emit)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 5, 0, 5)
        row.setSpacing(12)

        lbl = QLabel(label)
        lbl.setObjectName("ToggleLabel")
        lbl.setWordWrap(True)

        row.addWidget(lbl, stretch=1)
        row.addWidget(self._switch, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def isChecked(self) -> bool:
        return self._switch.isChecked()

    def setChecked(self, checked: bool) -> None:
        self._switch.setChecked(checked, animate=False)

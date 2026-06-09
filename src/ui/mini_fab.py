"""
mini_fab.py
Optionaler schwebender Mikrofon-Button (FAB) neben der Dynamic Island.
"""

from PyQt6.QtWidgets import QWidget, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QGuiApplication

from src.ui.design_tokens import Colors, AnimationTokens


class MiniFab(QWidget):
    """Kleiner, immer im Vordergrund liegender Aufnahme-Button."""

    toggle_recording = pyqtSignal()

    SIZE = 52

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recording = False
        self._fade_anim: QPropertyAnimation | None = None
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.btn = QPushButton("🎙", self)
        self.btn.setFixedSize(self.SIZE, self.SIZE)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self.toggle_recording.emit)
        self._apply_style(False)

    def showEvent(self, event):
        super().showEvent(event)
        self._place_bottom_right()
        self.raise_()

    def _apply_style(self, recording: bool) -> None:
        bg = Colors.RECORDING_RED_HEX if recording else Colors.ACCENT_HEX
        hover = "#FF6961" if recording else Colors.ACCENT_BRIGHT_HEX
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: 2px solid rgba(255,255,255,0.18);
                border-radius: {self.SIZE // 2}px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)

    def _place_bottom_right(self) -> None:
        screen = QGuiApplication.screenAt(self.frameGeometry().center()) or QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        margin = 28
        self.move(geo.right() - self.SIZE - margin, geo.bottom() - self.SIZE - margin)

    def set_recording(self, active: bool) -> None:
        self._recording = active
        self.btn.setText("⏹" if active else "🎙")
        self._apply_style(active)

    def show_with_fade(self) -> None:
        self._place_bottom_right()
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(AnimationTokens.NORMAL)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()

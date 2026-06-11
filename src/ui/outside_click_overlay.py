"""
outside_click_overlay.py
Vollbild-Ebene unter der Expanded-Island – einmal anzeigen, kein raise()-Spam.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QRect


class OutsideClickOverlay(QWidget):
    """Fängt Klicks außerhalb der Island ab (nur im EXPANDED-Modus aktiv)."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._active_screen_geo: QRect | None = None

    def show_below(self, anchor: QWidget) -> None:
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.geometry()
        if not self.isVisible() or self._active_screen_geo != geo:
            self.setGeometry(geo)
            self._active_screen_geo = geo
            self.show()
        anchor.raise_()

    def hide_overlay(self) -> None:
        self.hide()
        self._active_screen_geo = None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

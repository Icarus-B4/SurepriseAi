"""
drag_handle.py
Kleiner Griff zum Verschieben des Dynamic-Island-Fensters per Drag-and-Drop.
"""

from typing import Optional

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPoint
from src.ui.design_tokens import Colors, FluentIcons


class DragHandleButton(QPushButton):
    """Griff-Button – ziehen verschiebt das übergeordnete Fenster."""

    def __init__(self, parent=None):
        super().__init__(FluentIcons.DRAG_GRIP, parent)
        self._drag_offset: Optional[QPoint] = None
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setToolTip("Verschieben")
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_SECONDARY_HEX};
                font-size: 12px;
                letter-spacing: -2px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_BRIGHT_HEX};
                background: rgba(99, 102, 241, 0.15);
                border-radius: 11px;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win:
                self._drag_offset = (
                    event.globalPosition().toPoint() - win.frameGeometry().topLeft()
                )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset and event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if win:
                win.move(event.globalPosition().toPoint() - self._drag_offset)
                if hasattr(win, "mark_user_positioned"):
                    win.mark_user_positioned()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

"""
ollama_status_badge.py
Kompaktes Ollama-Status-Badge – nur der Punkt ist farbig (🔴/🟡/🟢).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from src.ui.design_tokens import Typography

_STATUS_COPY = {
    "offline": ("🔴", "offline"),
    "pending": ("🟡", "Verbindung…"),
    "connected": ("🟢", "verbunden"),
}


class OllamaStatusBadge(QWidget):
    """Inline: Status · farbiger Punkt · Label (ohne Vollbreiten-Farbfläche)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        prefix = QLabel("Status", self)
        prefix.setObjectName("OllamaStatusPrefix")
        prefix.setFont(Typography.get_font(Typography.TINY, bold=True))

        self._dot = QFrame(self)
        self._dot.setObjectName("OllamaStatusDot")
        self._dot.setFixedSize(28, 28)
        dot_layout = QHBoxLayout(self._dot)
        dot_layout.setContentsMargins(0, 0, 0, 0)
        self._icon = QLabel("🟡", self._dot)
        self._icon.setObjectName("OllamaStatusIcon")
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot_layout.addWidget(self._icon)

        self._label = QLabel("wird geprüft…", self)
        self._label.setObjectName("OllamaStatusText")
        self._label.setFont(Typography.get_font(Typography.SMALL))

        layout.addWidget(prefix)
        layout.addWidget(self._dot)
        layout.addWidget(self._label)

        self.set_state("pending", "wird geprüft…")

    def set_state(self, state: str, detail: str | None = None) -> None:
        icon, default_text = _STATUS_COPY.get(state, _STATUS_COPY["pending"])
        self._icon.setText(icon)
        self._label.setText(detail or default_text)
        self._dot.setProperty("ollamaStatus", state)
        self._dot.style().unpolish(self._dot)
        self._dot.style().polish(self._dot)
        self._dot.update()

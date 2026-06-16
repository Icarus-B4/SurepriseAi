"""
ollama_status_badge.py
Futuristisches Status-Badge für Ollama (🔴/🟡/🟢).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

from src.ui.design_tokens import Typography

_STATUS_COPY = {
    "offline": ("🔴", "offline"),
    "pending": ("🟡", "Verbindung…"),
    "connected": ("🟢", "verbunden"),
}


class OllamaStatusBadge(QFrame):
    """Pill-Badge: Status · Emoji · Label mit Zustandsfarbe via QSS-Property."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("OllamaStatusBadge")
        self.setProperty("ollamaStatus", "pending")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 14, 8)
        layout.setSpacing(8)

        prefix = QLabel("STATUS", self)
        prefix.setObjectName("OllamaStatusPrefix")
        prefix.setFont(Typography.get_font(Typography.TINY, bold=True))

        self._icon = QLabel("🟡", self)
        self._icon.setObjectName("OllamaStatusIcon")

        self._label = QLabel("wird geprüft…", self)
        self._label.setObjectName("OllamaStatusText")
        self._label.setFont(Typography.get_font(Typography.SMALL, bold=True))

        layout.addWidget(prefix)
        layout.addWidget(self._icon)
        layout.addWidget(self._label)
        layout.addStretch()

        self.set_state("pending", "wird geprüft…")

    def set_state(self, state: str, detail: str | None = None) -> None:
        icon, default_text = _STATUS_COPY.get(state, _STATUS_COPY["pending"])
        self._icon.setText(icon)
        self._label.setText(detail or default_text)
        self.setProperty("ollamaStatus", state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

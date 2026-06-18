"""
typewriter_label.py
Animiertes Label mit Typewriter-Effekt und blinkendem Cursor.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer


class TypewriterLabel(QLabel):
    """Schreibt Text Zeichen für Zeichen – optional mit Cursor."""

    def __init__(
        self,
        text: str = "",
        parent=None,
        ms_per_char: int = 52,
        show_cursor: bool = True,
    ):
        super().__init__(parent)
        self._full_text = text
        self._visible_len = 0
        self._show_cursor = show_cursor
        self._cursor_on = True
        self._paused = False

        self._type_timer = QTimer(self)
        self._type_timer.timeout.connect(self._type_next)
        self._type_timer.setInterval(ms_per_char)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink_cursor)
        self._blink_timer.setInterval(480)

        if text:
            self.restart()

    def restart(self) -> None:
        """Startet die Schreib-Animation von vorn."""
        self._paused = False
        self._visible_len = 0
        self._cursor_on = True
        self._type_timer.start()
        self._blink_timer.start()
        self._render()

    def pause(self) -> None:
        """Pausiert Typewriter (z. B. für temporäre Statusmeldung)."""
        self._paused = True
        self._type_timer.stop()

    def resume(self) -> None:
        """Setzt Typewriter nach Pause fort."""
        if self._visible_len >= len(self._full_text):
            self._render()
            return
        self._paused = False
        self._type_timer.start()
        self._blink_timer.start()

    def set_brand_text(self, text: str, *, restart: bool = True) -> None:
        """Setzt den Zieltext (Standard: SurepriseAI)."""
        self._full_text = text
        if restart:
            self.restart()

    def _type_next(self) -> None:
        if self._paused:
            return
        if self._visible_len < len(self._full_text):
            self._visible_len += 1
            self._render()
            return
        self._type_timer.stop()

    def _blink_cursor(self) -> None:
        if self._paused or self._visible_len < len(self._full_text):
            return
        self._cursor_on = not self._cursor_on
        self._render()

    def _render(self) -> None:
        shown = self._full_text[: self._visible_len]
        if (
            self._show_cursor
            and not self._paused
            and self._visible_len >= len(self._full_text)
            and self._cursor_on
        ):
            shown += "│"
        self.setText(shown)

"""
polish_animator.py
Eloquent-ähnliche Diff-Animation im Expanded-Textfeld (PyQt6).
"""

from __future__ import annotations

from typing import Callable, List, Optional

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QTextEdit

from src.utils.diff_helper import Frame, generate_diff_frames


class PolishAnimator(QObject):
    """Spielt Rohtext → Diff → polierter Text als gestaffelte Animation ab."""

    INTRO_MS = 520
    FRAME_MS = 240
    FINAL_HOLD_MS = 1000

    def __init__(self, text_edit: QTextEdit, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._edit = text_edit
        self._frames: List[Frame] = []
        self._index = 0
        self._on_finished: Optional[Callable[[], None]] = None
        self._on_progress: Optional[Callable[[int, int, str], None]] = None
        self._intro_timer = QTimer(self)
        self._intro_timer.setSingleShot(True)
        self._intro_timer.timeout.connect(self._start_frames)
        self._frame_timer = QTimer(self)
        self._frame_timer.timeout.connect(self._next_frame)

    def is_running(self) -> bool:
        return self._intro_timer.isActive() or self._frame_timer.isActive()

    def cancel(self) -> None:
        self._intro_timer.stop()
        self._frame_timer.stop()
        self._frames.clear()
        self._on_finished = None

    def play(
        self,
        raw: str,
        polished: str,
        on_finished: Optional[Callable[[], None]] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> None:
        self.cancel()
        self._on_finished = on_finished
        self._on_progress = on_progress
        self._frames = generate_diff_frames(raw, polished)
        self._index = 0
        if len(self._frames) <= 1:
            self._show_frame(0)
            self._finish()
            return
        self._show_frame(0)
        self._intro_timer.start(self.INTRO_MS)

    def _start_frames(self) -> None:
        self._index = 1
        self._show_frame(self._index)
        if self._index >= len(self._frames) - 1:
            self._finish()
            return
        self._frame_timer.start(self.FRAME_MS)

    def _next_frame(self) -> None:
        self._index += 1
        if self._index >= len(self._frames):
            self._frame_timer.stop()
            self._finish()
            return
        self._show_frame(self._index)
        if self._index >= len(self._frames) - 1:
            self._frame_timer.stop()
            QTimer.singleShot(self.FINAL_HOLD_MS, self._finish)

    def _show_frame(self, index: int) -> None:
        mode, content = self._frames[index]
        if mode == "html":
            self._edit.setHtml(content)
        else:
            self._edit.setPlainText(content)
        if self._on_progress:
            self._on_progress(index + 1, len(self._frames), mode)

    def _finish(self) -> None:
        if self._frames:
            _, final = self._frames[-1]
            self._edit.setPlainText(final)
        cb = self._on_finished
        self._on_finished = None
        self._on_progress = None
        self._frames.clear()
        if cb:
            cb()

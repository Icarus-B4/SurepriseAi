"""
ollama_settings_row.py
Ollama-Steuerung in den Einstellungen: Badge, Start, Beenden, Aktualisieren.
"""

from __future__ import annotations

import threading
from typing import Callable

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from src.services.config_service import config
from src.ui.ollama_status_badge import OllamaStatusBadge


class OllamaSettingsRow(QWidget):
    """Moderne Ollama-Zeile mit farbigem Status-Badge und Start/Stop."""

    action_finished = pyqtSignal(bool, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._busy = False
        self._build_ui()
        self.refresh_status()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 0)
        outer.setSpacing(10)

        card = QFrame(self)
        card.setObjectName("OllamaControlCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(12)

        self._badge = OllamaStatusBadge(card)
        card_layout.addWidget(self._badge, stretch=1)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self._refresh_btn = QPushButton("↻", self)
        self._refresh_btn.setObjectName("OllamaRefreshButton")
        self._refresh_btn.setFixedSize(36, 36)
        self._refresh_btn.setToolTip("Status aktualisieren")
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.refresh_status)

        self._action_btn = QPushButton("▶  Starten", self)
        self._action_btn.setObjectName("OllamaActionButton")
        self._action_btn.setProperty("ollamaAction", "start")
        self._action_btn.setMinimumWidth(118)
        self._action_btn.setMinimumHeight(36)
        self._action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_btn.clicked.connect(self._on_action_clicked)

        actions.addWidget(self._refresh_btn)
        actions.addWidget(self._action_btn)
        card_layout.addLayout(actions)

        outer.addWidget(card)

    def refresh_status(self) -> None:
        if self._busy:
            return
        from src.services.ollama_launcher import is_running

        if is_running(config.get_str("ollama_url")):
            self._set_idle_state("connected", "verbunden", "stop")
        else:
            self._set_idle_state("offline", "offline", "start")

    def _set_idle_state(self, badge: str, text: str, action: str) -> None:
        self._badge.set_state(badge, text)
        self._action_btn.setEnabled(True)
        self._refresh_btn.setEnabled(True)
        if action == "stop":
            self._action_btn.setText("■  Beenden")
            self._action_btn.setProperty("ollamaAction", "stop")
        else:
            self._action_btn.setText("▶  Starten")
            self._action_btn.setProperty("ollamaAction", "start")
        self._style_action_button()

    def _set_busy_state(self, detail: str) -> None:
        self._busy = True
        self._badge.set_state("pending", detail)
        self._action_btn.setEnabled(False)
        self._refresh_btn.setEnabled(False)

    def _on_action_clicked(self) -> None:
        if self._busy:
            return
        action = self._action_btn.property("ollamaAction")
        if action == "stop":
            self._set_busy_state("wird beendet…")
            self._run_worker(self._stop_worker)
        else:
            self._set_busy_state("wird gestartet…")
            self._run_worker(self._start_worker)

    def _run_worker(self, worker: Callable[[], tuple[bool, str]]) -> None:
        threading.Thread(target=lambda: self._finish_worker(worker()), daemon=True).start()

    def _start_worker(self) -> tuple[bool, str]:
        from src.services.ollama_launcher import start_ollama

        return start_ollama()

    def _stop_worker(self) -> tuple[bool, str]:
        from src.services.ollama_launcher import stop_ollama

        return stop_ollama()

    def _finish_worker(self, result: tuple[bool, str]) -> None:
        ok, message = result
        QTimer.singleShot(0, lambda: self._on_worker_finished(ok, message))

    def _on_worker_finished(self, ok: bool, message: str) -> None:
        self._busy = False
        self.refresh_status()
        self.action_finished.emit(ok, message)

    def _style_action_button(self) -> None:
        self._action_btn.style().unpolish(self._action_btn)
        self._action_btn.style().polish(self._action_btn)
        self._action_btn.update()

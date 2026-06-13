"""
history_dialog.py
Dialog zur Durchsicht der Diktat-Historie mit Suche und Kopieren.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QApplication, QMessageBox,
    QTextEdit, QFrame, QSlider,
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from src.services.dictation_history import DictationHistoryService
from src.services.style_definitions import style_label
from src.ui.history_export_dialog import export_history_entry
from src.ui.design_tokens import Colors, Typography


class HistoryDialog(QDialog):
    """Zeigt letzte Diktate mit Volltextsuche."""

    def __init__(self, history: DictationHistoryService, parent=None):
        super().__init__(parent)
        self.history = history
        self._current_entry: dict | None = None
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.8)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state)
        self.setWindowTitle("Diktat-Verlauf")
        self.setMinimumSize(860, 560)
        self._build_ui()
        self._apply_style()
        self._refresh_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        hint = QLabel("Letzte Diktate – suchen oder erneut kopieren")
        hint.setFont(Typography.get_font(Typography.SMALL))
        layout.addWidget(hint)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche im Text…")
        self.search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        body = QHBoxLayout()
        body.setSpacing(12)

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self._copy_selected)
        body.addWidget(self.list_widget, stretch=3)

        detail = QFrame()
        detail.setObjectName("HistoryDetail")
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(14, 12, 14, 12)
        detail_layout.setSpacing(10)

        self.detail_title = QLabel("Kein Diktat gewählt")
        self.detail_title.setFont(Typography.get_font(Typography.SMALL, bold=True))
        detail_layout.addWidget(self.detail_title)

        player_row = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedWidth(44)
        self.play_btn.clicked.connect(self._toggle_playback)
        self.audio_slider = QSlider(Qt.Orientation.Horizontal)
        self.audio_slider.sliderMoved.connect(self._seek_audio)
        self.time_label = QLabel("0:00")
        player_row.addWidget(self.play_btn)
        player_row.addWidget(self.audio_slider, stretch=1)
        player_row.addWidget(self.time_label)
        detail_layout.addLayout(player_row)

        self.audio_hint = QLabel("Keine Audio-Datei für diesen Eintrag")
        self.audio_hint.setFont(Typography.get_font(Typography.TINY))
        detail_layout.addWidget(self.audio_hint)

        self.final_label = QLabel("Finales Transkript")
        self.final_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        detail_layout.addWidget(self.final_label)
        self.final_text = QTextEdit()
        self.final_text.setReadOnly(True)
        detail_layout.addWidget(self.final_text, stretch=2)

        self.live_label = QLabel("Live-Transkription während der Aufnahme")
        self.live_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        detail_layout.addWidget(self.live_label)
        self.live_text = QTextEdit()
        self.live_text.setReadOnly(True)
        self.live_text.setMaximumHeight(110)
        detail_layout.addWidget(self.live_text)

        body.addWidget(detail, stretch=4)
        layout.addLayout(body, stretch=1)

        btn_row = QHBoxLayout()
        self.export_btn = QPushButton("Exportieren…")
        self.export_btn.clicked.connect(self._export_selected)
        self.copy_btn = QPushButton("In Zwischenablage kopieren")
        self.copy_btn.clicked.connect(self._copy_selected)
        self.open_audio_btn = QPushButton("Audio öffnen")
        self.open_audio_btn.clicked.connect(self._open_audio_file)
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.open_audio_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.SURFACE_HEX};
                color: {Colors.TEXT_PRIMARY_HEX};
            }}
            QLineEdit {{
                background: {Colors.SURFACE_ELEVATED};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 6px;
                padding: 8px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QListWidget {{
                background: {Colors.ISLAND_BG_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 8px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Colors.BORDER_SUBTLE_HEX};
            }}
            QListWidget::item:selected {{
                background: {Colors.SURFACE_ELEVATED};
            }}
            QFrame#HistoryDetail {{
                background: {Colors.ISLAND_BG_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 12px;
            }}
            QTextEdit {{
                background: {Colors.SURFACE_ELEVATED};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 8px;
                padding: 8px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
                font-size: 13px;
            }}
            QSlider::groove:horizontal {{
                height: 8px;
                border-radius: 4px;
                background: {Colors.SURFACE_ELEVATED};
            }}
            QSlider::handle:horizontal {{
                background: {Colors.ACCENT_BRIGHT_HEX};
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QPushButton {{
                background: {Colors.ACCENT_HEX};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QPushButton:hover {{
                background: {Colors.ACCENT_BRIGHT_HEX};
            }}
            QLabel {{
                color: {Colors.TEXT_SECONDARY_HEX};
            }}
        """)

    def _refresh_list(self, query: str = "") -> None:
        self.list_widget.clear()
        entries = self.history.search(query) if query else self.history.list_all()
        for entry in entries:
            ts = entry.get("timestamp", "")[:16].replace("T", " ")
            style = style_label(entry.get("style", ""))
            preview = entry.get("polished", "").replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "…"
            label = f"{ts}  ·  {style}  ·  {preview}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.list_widget.addItem(item)
        if self.list_widget.count() and self.list_widget.currentRow() < 0:
            self.list_widget.setCurrentRow(0)

    def _on_search(self, text: str) -> None:
        self._refresh_list(text)

    def _copy_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        text = entry.get("polished", "") if isinstance(entry, dict) else str(entry)
        if text:
            QApplication.clipboard().setText(text)

    def _on_selection_changed(self, current: QListWidgetItem | None, _previous=None) -> None:
        self._player.stop()
        self._current_entry = current.data(Qt.ItemDataRole.UserRole) if current else None
        entry = self._current_entry if isinstance(self._current_entry, dict) else {}

        ts = entry.get("timestamp", "")[:19].replace("T", " ")
        style = style_label(entry.get("style", ""))
        duration = entry.get("duration_s")
        title_parts = [p for p in (ts, style, f"{duration}s" if duration else "") if p]
        self.detail_title.setText(" · ".join(title_parts) or "Kein Diktat gewählt")

        self.final_text.setPlainText(entry.get("polished") or entry.get("raw") or "")
        live = entry.get("live_transcript") or ""
        self.live_text.setPlainText(live)
        self.live_text.setVisible(bool(live))
        self.live_label.setVisible(bool(live))

        audio_path = entry.get("audio_path") or ""
        has_audio = bool(audio_path and __import__("pathlib").Path(audio_path).exists())
        self.play_btn.setEnabled(has_audio)
        self.audio_slider.setEnabled(has_audio)
        self.open_audio_btn.setEnabled(has_audio)
        self.audio_hint.setText(audio_path if has_audio else "Keine Audio-Datei für diesen Eintrag")
        self.audio_slider.setValue(0)
        self.time_label.setText("0:00")
        if has_audio:
            self._player.setSource(QUrl.fromLocalFile(audio_path))

    def _toggle_playback(self) -> None:
        if self._player.source().isEmpty():
            return
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_playback_state(self, state) -> None:
        self.play_btn.setText("⏸" if state == QMediaPlayer.PlaybackState.PlayingState else "▶")

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.audio_slider.setRange(0, max(duration_ms, 0))

    def _on_position_changed(self, position_ms: int) -> None:
        if not self.audio_slider.isSliderDown():
            self.audio_slider.setValue(position_ms)
        self.time_label.setText(_fmt_ms(position_ms))

    def _seek_audio(self, position_ms: int) -> None:
        self._player.setPosition(position_ms)

    def _open_audio_file(self) -> None:
        entry = self._current_entry or {}
        audio_path = entry.get("audio_path") if isinstance(entry, dict) else ""
        if not audio_path:
            return
        import os
        os.startfile(audio_path)

    def _export_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(entry, dict) and export_history_entry(entry, self):
            QMessageBox.information(self, "Export", "Datei wurde gespeichert.")

    def closeEvent(self, event) -> None:
        self._player.stop()
        super().closeEvent(event)


def _fmt_ms(ms: int) -> str:
    seconds = max(0, ms // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"

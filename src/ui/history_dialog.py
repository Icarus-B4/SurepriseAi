"""
history_dialog.py
Dialog zur Durchsicht der Diktat-Historie mit Suche, Waveform und Aktionen.
Unterstützt dynamische Übersetzung und Design-Themenwechsel.
"""

from pathlib import Path
import time

from PyQt6.QtCore import Qt, QUrl, QTimer, QSignalBlocker
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QSizePolicy,
    QScrollArea,
    QWidget,
)

from src.services.dictation_history import DictationHistoryService
from src.services.polishing_service import PolishingService
from src.services.style_definitions import STYLE_DEFINITIONS, style_label
from src.ui.design_tokens import Colors, FluentIcons, Typography
from src.ui.history_export_dialog import export_history_entry
from src.ui.playback_waveform import PlaybackWaveform
from src.ui.text_compare_slider import TextCompareSlider
from src.utils.translation import tr

_STRUCTURED_STYLES = {"bullet_points", "key_points"}


class HistoryDialog(QDialog):
    """Zeigt letzte Diktate mit Volltextsuche."""

    def __init__(self, history: DictationHistoryService, parent=None, embedded: bool = False):
        super().__init__(parent)
        self.history = history
        self._embedded = embedded
        self._current_entry: dict | None = None
        self._polisher = PolishingService()
        self._style_buttons: dict[str, QPushButton] = {}
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.8)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state)
        self._last_waveform_paint = 0.0
        
        if embedded:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
        self._build_ui()
        self._apply_style()
        self.retranslate_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.header_title = QLabel()
        self.header_title.setFont(Typography.get_font(Typography.MEDIUM, bold=True))
        self.header_subtitle = QLabel()
        self.header_subtitle.setFont(Typography.get_font(Typography.TINY))
        title_box.addWidget(self.header_title)
        title_box.addWidget(self.header_subtitle)
        header.addLayout(title_box)
        header.addStretch()
        
        self.header_close_btn = QPushButton(FluentIcons.CLOSE)
        self.header_close_btn.setObjectName("CloseButton")
        self.header_close_btn.setFixedSize(34, 34)
        self.header_close_btn.clicked.connect(self.accept)
        header.addWidget(self.header_close_btn)
        layout.addLayout(header)

        self.search_input = QLineEdit()
        self.search_input.setMaximumHeight(42)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        self.style_row = QHBoxLayout()
        self.style_row.setSpacing(6)
        for key, label in STYLE_DEFINITIONS:
            btn = QPushButton(label, self)
            btn.setObjectName("HistoryStyleChip")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked=False, k=key: self._repolish_current(k))
            self._style_buttons[key] = btn
            self.style_row.addWidget(btn)
        self.style_row.addStretch()
        layout.addLayout(self.style_row)

        body = QVBoxLayout()
        body.setSpacing(12)

        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_scroll.setObjectName("HistoryListScroll")
        
        self.list_content = QWidget()
        self.list_content.setObjectName("HistoryListContent")
        self.list_layout = QVBoxLayout(self.list_content)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        
        self.list_scroll.setWidget(self.list_content)
        body.addWidget(self.list_scroll, stretch=1)

        self.detail = QFrame()
        self.detail.setObjectName("HistoryDetail")
        self.detail.setVisible(False)
        self.detail.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        detail_layout = QVBoxLayout(self.detail)
        detail_layout.setContentsMargins(10, 8, 10, 8)
        detail_layout.setSpacing(8)

        self.audio_container = QWidget()
        audio_layout = QVBoxLayout(self.audio_container)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        audio_layout.setSpacing(6)

        player_row = QHBoxLayout()
        self.play_btn = QToolButton()
        self.play_btn.setText("▶")
        self.play_btn.setObjectName("IconToolButton")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.clicked.connect(self._toggle_playback)
        self.audio_slider = QSlider(Qt.Orientation.Horizontal)
        self.audio_slider.sliderMoved.connect(self._seek_audio)
        self.time_label = QLabel("0:00")
        player_row.addWidget(self.play_btn)
        player_row.addWidget(self.audio_slider, stretch=1)
        player_row.addWidget(self.time_label)
        audio_layout.addLayout(player_row)

        self.waveform = PlaybackWaveform(self)
        self.waveform.seek_requested.connect(self._seek_audio)
        audio_layout.addWidget(self.waveform)

        detail_layout.addWidget(self.audio_container)

        # Text-Vergleichs-Slider (Rohtext vs. Polished)
        self.compare_slider = TextCompareSlider(self)
        self.compare_slider.setMinimumHeight(120)
        detail_layout.addWidget(self.compare_slider)

        self.live_label = QLabel()
        self.live_label.setFont(Typography.get_font(Typography.TINY, bold=True))
        detail_layout.addWidget(self.live_label)
        self.live_text = QTextEdit()
        self.live_text.setReadOnly(True)
        self.live_text.setMaximumHeight(110)
        detail_layout.addWidget(self.live_text)

        self.audio_hint = QLabel()
        self.audio_hint.setFont(Typography.get_font(Typography.TINY))
        detail_layout.addWidget(self.audio_hint)

        action_row = QHBoxLayout()
        self.copy_icon_btn = self._make_action_button("📋", "")
        self.copy_icon_btn.clicked.connect(self._copy_selected)
        self.refresh_icon_btn = self._make_action_button("↺", "")
        self.refresh_icon_btn.clicked.connect(self._reload_current)
        self.info_icon_btn = self._make_action_button("ℹ", "")
        self.info_icon_btn.clicked.connect(self._show_info)
        self.delete_icon_btn = self._make_action_button("🗑", "")
        self.delete_icon_btn.clicked.connect(self._delete_selected)
        action_row.addStretch()
        action_row.addWidget(self.copy_icon_btn)
        action_row.addWidget(self.refresh_icon_btn)
        action_row.addWidget(self.info_icon_btn)
        action_row.addWidget(self.delete_icon_btn)
        detail_layout.addLayout(action_row)
        detail_layout.addStretch(1)

        layout.addLayout(body, stretch=1)

        btn_row = QHBoxLayout()
        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self._export_selected)
        self.copy_btn = QPushButton()
        self.copy_btn.clicked.connect(self._copy_selected)
        self.open_audio_btn = QPushButton()
        self.open_audio_btn.clicked.connect(self._open_audio_file)
        self.footer_close_btn = QPushButton()
        self.footer_close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.open_audio_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.footer_close_btn)
        layout.addLayout(btn_row)

    def _make_action_button(self, text: str, tooltip: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setObjectName("IconToolButton")
        btn.setFixedSize(34, 34)
        return btn

    def _apply_style(self) -> None:
        bg_color = "transparent" if getattr(self, "_embedded", False) else Colors.SURFACE_HEX
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {Colors.TEXT_PRIMARY_HEX};
            }}
            QLineEdit {{
                background: {Colors.SURFACE_ELEVATED};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 8px;
                padding: 10px 12px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QListWidget {{
                background: {Colors.ISLAND_BG_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 12px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {Colors.BORDER_SUBTLE_HEX};
            }}
            QListWidget::item:selected {{
                background: {Colors.SURFACE_ELEVATED};
            }}
            QFrame#HistoryDetail {{
                background: {Colors.ISLAND_BG_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 14px;
            }}
            QScrollArea#HistoryListScroll {{
                background: transparent;
                border: none;
            }}
            QWidget#HistoryListContent {{
                background: transparent;
            }}
            QScrollArea#HistoryListScroll QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
            }}
            QScrollArea#HistoryListScroll QScrollBar::handle:vertical {{
                background: {Colors.CONTROL_HOVER_HEX};
                border-radius: 3px;
            }}
            QPushButton#HistoryListButton {{
                text-align: left;
                padding: 12px;
                background: {Colors.SURFACE_ELEVATED};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 8px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "{Typography.FONT_FAMILY}";
                font-size: 13px;
            }}
            QPushButton#HistoryListButton:hover {{
                background: {Colors.CONTROL_HOVER_HEX};
            }}
            QPushButton#HistoryListButton:checked {{
                border: 1px solid {Colors.ACCENT_HEX};
                background: {Colors.CONTROL_HOVER_HEX};
            }}
            QTextEdit {{
                background: {Colors.SURFACE_ELEVATED};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 10px;
                padding: 10px;
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
                border-radius: 8px;
                padding: 9px 14px;
                font-family: "{Typography.FONT_FAMILY}";
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {Colors.ACCENT_BRIGHT_HEX};
            }}
            QPushButton:checked {{
                background: {Colors.ACCENT_BRIGHT_HEX};
                color: white;
            }}
            QPushButton#HistoryStyleChip {{
                background: transparent;
                color: {Colors.TEXT_SECONDARY_HEX};
                border: 1px solid {Colors.BORDER_SUBTLE_HEX};
                border-radius: 10px;
                padding: 5px 9px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton#HistoryStyleChip:hover {{
                color: {Colors.TEXT_PRIMARY_HEX};
                background: rgba(255, 255, 255, 0.06);
                border-color: {Colors.BORDER_HEX};
            }}
            QPushButton#HistoryStyleChip:checked {{
                color: white;
                background: {Colors.ACCENT_HEX};
                border-color: {Colors.ACCENT_BRIGHT_HEX};
            }}
            QPushButton#CloseButton, QToolButton#IconToolButton {{
                background: transparent;
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 10px;
                color: {Colors.TEXT_SECONDARY_HEX};
                font-family: "Segoe UI Symbol";
                font-size: 14px;
                padding: 0px;
            }}
            QPushButton#CloseButton:hover, QToolButton#IconToolButton:hover {{
                color: {Colors.TEXT_PRIMARY_HEX};
                background: rgba(255, 255, 255, 0.06);
                border-color: {Colors.ACCENT_HEX};
            }}
            QLabel {{
                color: {Colors.TEXT_SECONDARY_HEX};
            }}
            QLabel#InfoText {{
                color: {Colors.TEXT_TERTIARY_HEX};
                font-size: 10pt;
            }}
        """)

    def retranslate_ui(self) -> None:
        """Übersetzt alle Texte und Platzhalter live."""
        self.setWindowTitle(tr("history_title"))
        self.header_title.setText(tr("history_title"))
        self.header_subtitle.setText(tr("history_subtitle"))
        self.search_input.setPlaceholderText(tr("history_search"))
        self.live_label.setText(tr("history_live"))
        self.export_btn.setText(tr("history_export"))
        self.copy_btn.setText(tr("history_copy"))
        self.open_audio_btn.setText(tr("history_open_audio"))
        self.footer_close_btn.setText(tr("history_close"))

        # Icon Tooltips
        self.copy_icon_btn.setToolTip(tr("history_copy"))
        self.refresh_icon_btn.setToolTip(tr("history_reload"))
        self.info_icon_btn.setToolTip(tr("history_info"))
        self.delete_icon_btn.setToolTip(tr("history_delete"))

        if not self._current_entry:
            self.audio_hint.setText(tr("history_no_audio"))
        else:
            self._update_detail(self._current_entry)

    def _detach_detail(self) -> None:
        """Löst das Detail-Panel ab, bevor Listeneinträge zerstört werden."""
        self._player.stop()
        self.detail.setParent(None)
        self.detail.setVisible(False)

    def _refresh_list(self, query: str = "") -> None:
        self._detach_detail()
        self._current_entry = None

        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self.history.search(query) if query else self.history.list_all()
        for entry in entries:
            ts = entry.get("timestamp", "")[:16].replace("T", " ")
            style = style_label(entry.get("style", ""))
            preview = entry.get("polished", "").replace("\n", " ")
            if len(preview) > 45:
                preview = preview[:42] + "…"
            label = f"{ts}  ·  {style}  ·  {preview}"
            
            entry_widget = QWidget()
            entry_widget.setProperty("entry_id", entry.get("id", ""))
            entry_layout = QVBoxLayout(entry_widget)
            entry_layout.setContentsMargins(0, 0, 0, 0)
            entry_layout.setSpacing(0)
            
            btn = QPushButton(label)
            btn.setObjectName("HistoryListButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, e=entry, ew=entry_widget, b=btn: self._on_entry_clicked(e, ew, b))
            
            entry_layout.addWidget(btn)
            self.list_layout.insertWidget(self.list_layout.count() - 1, entry_widget)

    def _update_entry_button_label(self, entry: dict) -> None:
        entry_id = entry.get("id", "")
        if not entry_id:
            return
        ts = entry.get("timestamp", "")[:16].replace("T", " ")
        style = style_label(entry.get("style", ""))
        preview = entry.get("polished", "").replace("\n", " ")
        if len(preview) > 45:
            preview = preview[:42] + "…"
        label = f"{ts}  ·  {style}  ·  {preview}"
        for i in range(self.list_layout.count() - 1):
            item = self.list_layout.itemAt(i)
            ew = item.widget() if item else None
            if ew is not None and ew.property("entry_id") == entry_id:
                btn = ew.findChild(QPushButton, "HistoryListButton")
                if btn is not None:
                    btn.setText(label)
                break

    def _set_active_style(self, style: str) -> None:
        for key, btn in self._style_buttons.items():
            btn.setChecked(key == style)

    def _on_search(self, text: str) -> None:
        self._refresh_list(text)

    def _current(self) -> dict:
        if isinstance(self._current_entry, dict):
            return self._current_entry
        return {}

    def _copy_selected(self) -> None:
        entry = self._current()
        text = self._display_text(entry)
        if text:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(text)

    def _reload_current(self) -> None:
        self._refresh_list(self.search_input.text())
        self._update_detail(self._current())

    def _show_info(self) -> None:
        entry = self._current()
        if not entry:
            return
        audio = tr("yes") if entry.get("audio_path") else tr("no")
        live = tr("yes") if entry.get("live_transcript") else tr("no")
        QMessageBox.information(
            self,
            tr("history_info"),
            f"Audio: {audio}\nLive-Transkript: {live}\nWörter: {entry.get('words', 0)}\nWPM: {entry.get('wpm', 0)}",
        )

    def _delete_selected(self) -> None:
        entry = self._current()
        entry_id = entry.get("id")
        if not entry_id:
            return
        if QMessageBox.question(self, tr("history_delete"), tr("history_delete_confirm")) != QMessageBox.StandardButton.Yes:
            return
        if self.history.delete(entry_id):
            self._current_entry = None
            self._refresh_list(self.search_input.text())
            self._update_detail({})

    def _on_entry_clicked(self, entry: dict, entry_widget: QWidget, button: QPushButton) -> None:
        # Uncheck all other buttons
        for i in range(self.list_layout.count() - 1):
            item = self.list_layout.itemAt(i)
            if item and item.widget():
                ew = item.widget()
                if ew != entry_widget:
                    btn = ew.findChild(QPushButton, "HistoryListButton")
                    if btn:
                        btn.setChecked(False)

        if not button.isChecked():
            # It was unchecked by clicking it again
            self._player.stop()
            self._current_entry = None
            self.detail.setVisible(False)
            self.detail.setParent(None)
            self._update_detail({})
            return

        self._player.stop()
        self._current_entry = entry
        
        # Reparent detail inside this entry widget
        self.detail.setParent(None)
        ew_layout = entry_widget.layout()
        ew_layout.addWidget(self.detail)
        
        self._update_detail(entry)
        self.detail.setVisible(True)

    def _update_detail(self, entry: dict) -> None:
        style = style_label(entry.get("style", ""))
        self._set_active_style(entry.get("style", ""))

        self.live_text.setPlainText(entry.get("live_transcript") or "")
        self.live_text.setVisible(bool(entry.get("live_transcript")))
        self.live_label.setVisible(bool(entry.get("live_transcript")))

        audio_path = entry.get("audio_path") or ""
        has_audio = bool(audio_path and Path(audio_path).exists())
        self.audio_container.setVisible(has_audio)
        self.play_btn.setEnabled(has_audio)
        self.audio_slider.setEnabled(has_audio)
        self.open_audio_btn.setEnabled(has_audio)
        self.audio_hint.setText(audio_path if has_audio else tr("history_no_audio"))
        self.audio_hint.setToolTip(audio_path if has_audio else "")
        self.audio_slider.setValue(0)
        self.time_label.setText("0:00")
        path_for_waveform = audio_path if has_audio else None
        QTimer.singleShot(0, lambda p=path_for_waveform: self.waveform.load_audio_file(p))
        if has_audio:
            self._player.setSource(QUrl.fromLocalFile(audio_path))

        raw = entry.get("raw") or ""
        polished = entry.get("polished") or raw
        self.compare_slider.set_texts(raw, polished)
        if entry.get("style") in _STRUCTURED_STYLES:
            self.compare_slider.show_polished_view()
        elif raw and polished and raw != polished:
            self.compare_slider.show_diff_view()
        else:
            self.compare_slider.show_polished_view()

    def _repolish_current(self, style_key: str) -> None:
        entry = self._current()
        if not entry:
            self._set_active_style("")
            return
        raw = entry.get("raw") or ""
        if not raw.strip():
            self._set_active_style(entry.get("style", ""))
            return

        polished = self._polisher.polish_instant(raw, style=style_key)
        if not polished:
            self._set_active_style(entry.get("style", ""))
            return

        words = len(polished.split())
        duration = entry.get("duration_s") or 0
        wpm = int((words / duration) * 60) if duration > 0.5 else 0
        entry.update({"polished": polished, "style": style_key, "words": words, "wpm": wpm})
        self.history.update(
            entry.get("id", ""),
            {"polished": polished, "style": style_key, "words": words, "wpm": wpm},
        )
        self._set_active_style(style_key)
        self._update_detail(entry)
        self._update_entry_button_label(entry)
        if style_key in _STRUCTURED_STYLES:
            self.compare_slider.show_polished_view()

    def _display_text(self, entry: dict) -> str:
        """Gibt den polierten Text für Kopieren/Export zurück."""
        return entry.get("polished") or entry.get("raw") or ""

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
            with QSignalBlocker(self.audio_slider):
                self.audio_slider.setValue(position_ms)
        self.time_label.setText(_fmt_ms(position_ms))
        if self.audio_slider.maximum() > 0:
            now = time.monotonic()
            if now - self._last_waveform_paint >= 0.05:
                self._last_waveform_paint = now
                self.waveform.set_position_ratio(
                    position_ms / float(self.audio_slider.maximum())
                )

    def _seek_audio(self, position_ms: int) -> None:
        self._player.setPosition(position_ms)
        self.waveform.set_position_ms(position_ms)

    def _open_audio_file(self) -> None:
        entry = self._current()
        audio_path = entry.get("audio_path") or ""
        if not audio_path:
            return
        import os
        os.startfile(audio_path)

    def _export_selected(self) -> None:
        entry = self._current()
        if isinstance(entry, dict) and export_history_entry(entry, self):
            QMessageBox.information(self, tr("history_export"), tr("File has been saved."))

    def closeEvent(self, event) -> None:
        self._player.stop()
        super().closeEvent(event)


def _fmt_ms(ms: int) -> str:
    seconds = max(0, ms // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"

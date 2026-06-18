"""
expanded_pill_widget.py
Widget für die Großansicht (Expanded Mode) der Dynamic Island.
Enthält Wort/WPM-Statistiken, eine Textbox mit Direktaktionen und Stil-Chips.
Unterstützt dynamische Übersetzung und Design-Themenwechsel.
"""

import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint
from PyQt6.QtGui import QCursor
from src.ui.design_tokens import Colors, Typography, FluentIcons, Radius
from src.ui.drag_handle import DragHandleButton
from src.ui.text_compare_slider import TextCompareSlider
from src.services.config_service import config
from src.services.style_definitions import STYLE_DEFINITIONS
from src.utils.live_transcript_html import format_live_transcript_html
from src.utils.translation import tr


class ExpandedPillWidget(QWidget):
    """Das Textbearbeitungs-, Statistik- und Stil-Auswahl-Widget im EXPANDED-State."""
    
    style_clicked = pyqtSignal(str)  # Emittiert den Stil-Key bei Klick
    undo_clicked = pyqtSignal()
    url_import_clicked = pyqtSignal()
    resize_requested = pyqtSignal(int)  # delta_y für Höhenänderung

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chips: dict[str, QPushButton] = {}
        self._live_mode = False
        self._init_ui()

    def _icon_button_style(self, hover_color: str, object_name: str) -> str:
        return f"""
            QPushButton#{object_name} {{
                background: transparent;
                border: none;
                border-radius: 11px;
                color: {Colors.TEXT_SECONDARY_HEX};
                font-family: "{FluentIcons.FONT_FAMILY}";
                font-size: 11px;
            }}
            QPushButton#{object_name}:hover {{
                background: {Colors.CONTROL_FILL_HEX};
                color: {hover_color};
            }}
        """

    def _chip_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: {Colors.ACCENT_TINT_STRONG};
                    color: {Colors.TEXT_PRIMARY_HEX};
                    border: 1px solid {Colors.ACCENT_BRIGHT_HEX};
                    border-radius: {Radius.MD}px;
                    padding: 3px 8px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.ACCENT_HEX};
                    border-color: {Colors.ACCENT_HEX};
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY_HEX};
                border: 1px solid {Colors.BORDER_SUBTLE_HEX};
                border-radius: {Radius.MD}px;
                padding: 3px 8px;
            }}
            QPushButton:hover {{
                color: {Colors.TEXT_PRIMARY_HEX};
                background-color: {Colors.CONTROL_FILL_HEX};
                border-color: {Colors.BORDER_HIGHLIGHT};
            }}
        """

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 10)
        main_layout.setSpacing(8)

        # Griff zum Verschieben (oben rechts)
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.drag_handle = DragHandleButton(self)
        top_bar.addWidget(self.drag_handle)
        main_layout.addLayout(top_bar)

        # ── 1. STATISTIKEN ──
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(2)
        
        # Spalten für Wörter & WPM
        cols_lay = QHBoxLayout()
        cols_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.words_val = QLabel("0", self)
        self.words_val.setObjectName("ExpandedStatsVal")
        self.words_val.setFont(Typography.get_font(Typography.TITLE, bold=True))
        
        self.words_lbl = QLabel()
        self.words_lbl.setObjectName("ExpandedStatsLbl")
        self.words_lbl.setFont(Typography.get_font(Typography.TINY))
        
        self.wpm_val = QLabel("0", self)
        self.wpm_val.setObjectName("ExpandedStatsValWpm")
        self.wpm_val.setFont(Typography.get_font(Typography.TITLE, bold=True))
        
        self.wpm_lbl = QLabel("WPM", self)
        self.wpm_lbl.setObjectName("ExpandedStatsLblWpm")
        self.wpm_lbl.setFont(Typography.get_font(Typography.TINY))
        
        # Spalten zusammenbauen
        w_box = QVBoxLayout()
        w_box.addWidget(self.words_val, alignment=Qt.AlignmentFlag.AlignCenter)
        w_box.addWidget(self.words_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        wpm_box = QVBoxLayout()
        wpm_box.addWidget(self.wpm_val, alignment=Qt.AlignmentFlag.AlignCenter)
        wpm_box.addWidget(self.wpm_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        cols_lay.addLayout(w_box)
        cols_lay.addSpacing(32)
        cols_lay.addLayout(wpm_box)
        stats_layout.addLayout(cols_lay)
        
        # Untertitel
        self.stats_desc = QLabel()
        self.stats_desc.setObjectName("ExpandedStatsDesc")
        self.stats_desc.setFont(Typography.get_font(Typography.TINY))
        stats_layout.addWidget(self.stats_desc, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Carousel-Dots (Deko zur Visualisierung)
        self.dots_lay = QHBoxLayout()
        self.dots_lay.setSpacing(4)
        self.dots_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dots: list[QLabel] = []
        for i in range(4):
            dot = QLabel("●", self)
            dot.setObjectName(f"CarouselDot_{i}")
            dot.setFont(Typography.get_font(Typography.TINY))
            self.dots.append(dot)
            self.dots_lay.addWidget(dot)
        stats_layout.addLayout(self.dots_lay)
        
        main_layout.addLayout(stats_layout)

        # ── 2. TEXT-BOX IN DER MITTE ──
        self.text_frame = QFrame(self)
        self.text_frame.setObjectName("ExpandedTextFrame")
        frame_layout = QVBoxLayout(self.text_frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)
        frame_layout.setSpacing(4)
        
        # Box Header mit Aktionen
        header_lay = QHBoxLayout()
        self.box_title = QLabel()
        self.box_title.setObjectName("ExpandedBoxTitle")
        self.box_title.setFont(Typography.get_font(Typography.TINY, bold=True))
        
        # Mini Kopieren und Edit Buttons
        self.box_copy_btn = QPushButton(FluentIcons.COPY, self)
        self.box_copy_btn.setObjectName("ExpandedCopyBtn")
        self.box_copy_btn.setFixedSize(22, 22)

        self.box_undo_btn = QPushButton(FluentIcons.RETRY, self)
        self.box_undo_btn.setObjectName("ExpandedUndoBtn")
        self.box_undo_btn.setFixedSize(22, 22)
        self.box_undo_btn.clicked.connect(self.undo_clicked.emit)

        self.url_btn = QPushButton("🔗", self)
        self.url_btn.setObjectName("ExpandedUrlBtn")
        self.url_btn.setFixedSize(22, 22)
        self.url_btn.clicked.connect(self.url_import_clicked.emit)
        
        # Wir belegen den Box Copy-Button direkt mit der Kopierfunktion
        self.exp_copy_btn = self.box_copy_btn  # Kompatibilität für AppController
        
        header_lay.addWidget(self.box_title)
        header_lay.addStretch()
        header_lay.addWidget(self.url_btn)
        header_lay.addWidget(self.box_undo_btn)
        header_lay.addWidget(self.box_copy_btn)
        frame_layout.addLayout(header_lay)

        self.polish_status = QLabel("Bereit für Polishing", self)
        self.polish_status.setObjectName("PolishStatusLabel")
        self.polish_status.setFont(Typography.get_font(Typography.TINY))
        self.polish_status.setVisible(False)
        frame_layout.addWidget(self.polish_status)

        self.live_badge = QLabel("● LIVE", self)
        self.live_badge.setObjectName("LiveTranscriptBadge")
        self.live_badge.setFont(Typography.get_font(Typography.TINY, bold=True))
        self.live_badge.hide()
        frame_layout.addWidget(self.live_badge)

        # Text-Vergleichs-Slider (Rohtext vs. Polished)
        self.compare_slider = TextCompareSlider(self)
        frame_layout.addWidget(self.compare_slider, stretch=1)
        
        # Alias für Kompatibilität mit bestehendem Code
        self.transcript_edit = self.compare_slider.text_view
        
        main_layout.addWidget(self.text_frame, stretch=1)

        # ── 3. STIL-CHIPS (zwei Zeilen, ohne Scrollbar) ──
        chips_row = QHBoxLayout()
        chips_row.setContentsMargins(0, 2, 0, 0)
        chips_row.setSpacing(8)

        chips_col = QVBoxLayout()
        chips_col.setSpacing(4)
        row1 = QHBoxLayout()
        row1.setSpacing(5)
        row2 = QHBoxLayout()
        row2.setSpacing(5)

        for index, (key, name) in enumerate(STYLE_DEFINITIONS):
            btn = QPushButton(name, self)
            btn.setFont(Typography.get_font(Typography.TINY, bold=True))
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(26)
            btn.clicked.connect(lambda _, k=key: self.style_clicked.emit(k))
            self.chips[key] = btn
            if index < 4:
                row1.addWidget(btn)
            else:
                row2.addWidget(btn)

        row1.addStretch()
        row2.addStretch()
        chips_col.addLayout(row1)
        chips_col.addLayout(row2)
        chips_row.addLayout(chips_col, stretch=1)

        self.exp_close_btn = QPushButton("✕", self)
        self.exp_close_btn.setObjectName("ExpandedCloseBtn")
        self.exp_close_btn.setFixedSize(28, 28)
        chips_row.addWidget(self.exp_close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(chips_row)

        # ── 4. RESIZE-HANDLE (unten rechts) ──
        self._resize_handle = _ResizeHandle(self)
        self._resize_handle.delta_y.connect(self.resize_requested.emit)

        self.refresh_theme()
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Übersetzt alle Labels und Tooltips live."""
        self.words_lbl.setText(tr("history_words"))
        self.stats_desc.setText(tr("stats_desc"))
        self.box_title.setText(tr("polished_text"))
        self.live_badge.setText(tr("live_badge"))
        self.box_undo_btn.setToolTip(tr("remove_last_sentence"))
        self.url_btn.setToolTip(tr("transcribe_url_tooltip"))
        self.box_copy_btn.setToolTip(tr("island_copy"))
        self.exp_close_btn.setToolTip(tr("island_close"))

    def refresh_theme(self) -> None:
        """Aktualisiert die QSS-Stile basierend auf den aktuellen Color-Tokens."""
        self.compare_slider.refresh_theme()
        
        # ID-spezifische Label-Styles zur Umgehung von Vererbungskonflikten
        self.words_val.setStyleSheet(f"QLabel#ExpandedStatsVal {{ color: {Colors.TEXT_PRIMARY_HEX}; background: transparent; }}")
        self.words_lbl.setStyleSheet(f"QLabel#ExpandedStatsLbl {{ color: {Colors.TEXT_SECONDARY_HEX}; background: transparent; }}")
        self.wpm_val.setStyleSheet(f"QLabel#ExpandedStatsValWpm {{ color: {Colors.ACCENT_BRIGHT_HEX}; background: transparent; }}")
        self.wpm_lbl.setStyleSheet(f"QLabel#ExpandedStatsLblWpm {{ color: {Colors.TEXT_SECONDARY_HEX}; background: transparent; }}")
        self.stats_desc.setStyleSheet(f"QLabel#ExpandedStatsDesc {{ color: {Colors.TEXT_SECONDARY_HEX}; background: transparent; }}")

        # Carousel-Dots
        for i, dot in enumerate(self.dots):
            color = Colors.ACCENT_HEX if i == 0 else Colors.TEXT_TERTIARY_HEX
            dot.setStyleSheet(f"QLabel#CarouselDot_{i} {{ color: {color}; background: transparent; }}")

        color_rgba = "0, 0, 0" if Colors.ISLAND_BG_HEX == "#F3F3F7" else "255, 255, 255"
        self.text_frame.setStyleSheet(f"""
            QFrame#ExpandedTextFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({color_rgba}, 0.055),
                    stop:1 rgba({color_rgba}, 0.025)
                );
                border: 1px solid {Colors.BORDER_HIGHLIGHT};
                border-radius: {Radius.MD}px;
            }}
        """)

        self.box_title.setStyleSheet(f"QLabel#ExpandedBoxTitle {{ color: {Colors.TEXT_SECONDARY_HEX}; border: none; background: transparent; }}")
        self.box_copy_btn.setStyleSheet(self._icon_button_style(Colors.SUCCESS_GREEN_HEX, "ExpandedCopyBtn"))
        self.box_undo_btn.setStyleSheet(self._icon_button_style(Colors.ACCENT_BRIGHT_HEX, "ExpandedUndoBtn"))
        self.url_btn.setStyleSheet(self._icon_button_style(Colors.ACCENT_BRIGHT_HEX, "ExpandedUrlBtn"))
        self.polish_status.setStyleSheet(f"QLabel#PolishStatusLabel {{ color: {Colors.TEXT_SECONDARY_HEX}; background: transparent; }}")
        self.live_badge.setStyleSheet(
            f"QLabel#LiveTranscriptBadge {{ color: {Colors.RECORDING_RED_HEX}; background: transparent; letter-spacing: 1px; }}"
        )

        self.exp_close_btn.setStyleSheet(f"""
            QPushButton#ExpandedCloseBtn {{
                background: transparent; color: {Colors.TEXT_SECONDARY_HEX};
                border: 1px solid {Colors.BORDER_HEX}; border-radius: 14px;
                font-family: "{Typography.FONT_FAMILY}"; font-weight: bold; font-size: 11px;
            }}
            QPushButton#ExpandedCloseBtn:hover {{ color: {Colors.RECORDING_RED_HEX}; border-color: {Colors.RECORDING_RED_HEX}; }}
        """)

        self.set_active_style(config.selected_style)
        self._resize_handle.update()

    def set_stats(self, words: int, wpm: int):
        """Aktualisiert die Statistikanzeigen."""
        self.words_val.setText(str(words))
        self.wpm_val.setText(str(wpm))

    def set_texts(self, raw: str, polished: str) -> None:
        """Setzt Rohtext und polierten Text für die Diff-Ansicht."""
        self.compare_slider.set_texts(raw, polished)

    def set_raw_text(self, text: str) -> None:
        """Setzt nur den Rohtext."""
        self.compare_slider.set_raw_text(text)

    def set_polished_text(self, text: str) -> None:
        """Setzt nur den polierten Text."""
        self.compare_slider.set_polished_text(text)

    def get_polished_text(self) -> str:
        """Gibt den aktuellen polierten Text zurück."""
        return self.compare_slider.get_polished_text()

    def show_diff_view(self) -> None:
        """Wechselt zur Diff-Ansicht."""
        self.compare_slider.show_diff_view()

    def enter_live_mode(self) -> None:
        """Schaltet die Expanded Pill in den Live-Transkriptionsmodus."""
        self._live_mode = True
        self.live_badge.show()
        self.box_title.setText(tr("live_transcript_title"))
        self.compare_slider.slider.hide()
        self.compare_slider.raw_label.hide()
        self.compare_slider.polished_label.hide()
        for btn in self.chips.values():
            btn.hide()
        self.exp_close_btn.show()
        self.set_stats(0, 0)
        self.stats_desc.setText(tr("live_transcript_hint"))
        self.set_live_text("")

    def exit_live_mode(self) -> None:
        """Beendet den Live-Modus und stellt die normale Diff-Ansicht wieder her."""
        if not self._live_mode:
            return
        self._live_mode = False
        self.live_badge.hide()
        self.box_title.setText(tr("polished_text"))
        self.compare_slider.slider.show()
        self.compare_slider.raw_label.show()
        self.compare_slider.polished_label.show()
        for btn in self.chips.values():
            btn.show()
        self.stats_desc.setText(tr("stats_desc"))

    def set_live_text(self, text: str) -> None:
        """Aktualisiert die Live-Transkription in der Textansicht."""
        if not self._live_mode:
            return
        html_body = format_live_transcript_html(text or tr("listening"))
        self.compare_slider.text_view.setHtml(
            f'<p style="margin:0;line-height:1.7;font-family:Segoe UI,sans-serif;'
            f'font-size:13px;">{html_body}</p>'
        )
        words = len(text.split()) if text else 0
        self.words_val.setText(str(words))
        self.wpm_val.setText("—")

    def set_active_style(self, active_key: str):
        """Färbt den ausgewählten Stil-Chip ein."""
        for key, btn in self.chips.items():
            btn.setEnabled(True)
            if key == active_key:
                btn.setStyleSheet(self._chip_style(active=True))
            else:
                btn.setStyleSheet(self._chip_style(active=False))

    def set_app_mode_hint(self, app_key: str | None, style_key: str | None = None) -> None:
        """Zeigt den erkannten App-Modus in der Statistik-Zeile."""
        from src.services.style_definitions import style_label

        if app_key and style_key:
            self.stats_desc.setText(f"App-Modus: {app_key} · {style_label(style_key)}")
        else:
            self.stats_desc.setText(tr("stats_desc"))

    def set_style_busy(self, busy: bool) -> None:
        """Deaktiviert Chips während Re-Polishing läuft."""
        for btn in self.chips.values():
            btn.setEnabled(not busy)

    def set_polish_status(self, text: str | None) -> None:
        """Zeigt oder verbirgt den Polishing-Status unter der Kopfzeile."""
        if text:
            self.polish_status.setText(text)
            self.polish_status.show()
        else:
            self.polish_status.hide()

    def undo_last_sentence(self) -> bool:
        """Entfernt den letzten Satz aus dem polierten Text. Gibt True zurück wenn geändert."""
        text = self.compare_slider.get_polished_text().strip()
        if not text:
            return False
        parts = re.split(r"(?<=[.!?…])\s+", text)
        if len(parts) <= 1:
            self.compare_slider.set_polished_text("")
            return True
        new_text = " ".join(parts[:-1]).strip()
        self.compare_slider.set_polished_text(new_text)
        return True

    def resizeEvent(self, event) -> None:
        """Resize-Handle immer unten rechts im Text-Frame positionieren."""
        super().resizeEvent(event)
        handle = self._resize_handle
        tf = self.findChild(QFrame, "ExpandedTextFrame")
        if tf:
            handle.move(tf.geometry().right() - handle.width() - 2, tf.geometry().bottom() - handle.height() - 2)



class _ResizeHandle(QWidget):
    """Kleiner Griff unten rechts zum Vergrößern der Expanded-Pill per Maus-Drag."""

    delta_y = pyqtSignal(int)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self._dragging = False
        self._drag_start = QPoint()
        self.setStyleSheet(f"background: transparent;")

    def paintEvent(self, event) -> None:
        """Zeichnet drei diagonale Linien als Resize-Indikator."""
        from PyQt6.QtGui import QPainter, QPen, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(255, 255, 255, 60), 1.5)
        p.setPen(pen)
        w, h = self.width(), self.height()
        # Drei parallele Linien von rechts unten
        for offset in (4, 9, 14):
            p.drawLine(w - 2, offset, offset, h - 2)
        p.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            current = event.globalPosition().toPoint()
            dy = current.y() - self._drag_start.y()
            if dy != 0:
                self.delta_y.emit(dy)
                self._drag_start = current
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._dragging = False
        super().mouseReleaseEvent(event)

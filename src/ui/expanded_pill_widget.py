"""
expanded_pill_widget.py
Widget für die Großansicht (Expanded Mode) der Dynamic Island.
Enthält Wort/WPM-Statistiken, eine Textbox mit Direktaktionen und Stil-Chips.
"""

import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt
from src.ui.design_tokens import Colors, Typography, FluentIcons, Radius
from src.ui.drag_handle import DragHandleButton
from src.ui.text_compare_slider import TextCompareSlider
from src.services.config_service import config
from src.services.style_definitions import STYLE_DEFINITIONS


class ExpandedPillWidget(QWidget):
    """Das Textbearbeitungs-, Statistik- und Stil-Auswahl-Widget im EXPANDED-State."""
    
    style_clicked = pyqtSignal(str)  # Emittiert den Stil-Key bei Klick
    undo_clicked = pyqtSignal()
    url_import_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chips: dict[str, QPushButton] = {}
        self._init_ui()

    def _icon_button_style(self, hover_color: str) -> str:
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 11px;
                color: {Colors.TEXT_SECONDARY_HEX};
                font-family: "{FluentIcons.FONT_FAMILY}";
                font-size: 11px;
            }}
            QPushButton:hover {{
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
        self.words_val.setFont(Typography.get_font(Typography.TITLE, bold=True))
        self.words_val.setStyleSheet(f"color: {Colors.TEXT_PRIMARY_HEX};")
        
        self.words_lbl = QLabel("Wörter", self)
        self.words_lbl.setFont(Typography.get_font(Typography.TINY))
        self.words_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        
        self.wpm_val = QLabel("0", self)
        self.wpm_val.setFont(Typography.get_font(Typography.TITLE, bold=True))
        self.wpm_val.setStyleSheet(f"color: {Colors.ACCENT_BRIGHT_HEX};")
        
        self.wpm_lbl = QLabel("WPM", self)
        self.wpm_lbl.setFont(Typography.get_font(Typography.TINY))
        self.wpm_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        
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
        stats_desc = QLabel("Statistiken deines letzten Diktats", self)
        stats_desc.setFont(Typography.get_font(Typography.TINY))
        stats_desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        stats_layout.addWidget(stats_desc, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Carousel-Dots (Deko zur Visualisierung)
        dots_lay = QHBoxLayout()
        dots_lay.setSpacing(4)
        dots_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for i in range(4):
            dot = QLabel("●", self)
            dot.setFont(Typography.get_font(Typography.TINY))
            color = Colors.ACCENT_HEX if i == 0 else Colors.TEXT_TERTIARY_HEX
            dot.setStyleSheet(f"color: {color};")
            dots_lay.addWidget(dot)
        stats_layout.addLayout(dots_lay)
        
        main_layout.addLayout(stats_layout)

        # ── 2. TEXT-BOX IN DER MITTE ──
        text_frame = QFrame(self)
        text_frame.setObjectName("ExpandedTextFrame")
        text_frame.setStyleSheet(f"""
            QFrame#ExpandedTextFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.055),
                    stop:1 rgba(255, 255, 255, 0.025)
                );
                border: 1px solid {Colors.BORDER_HIGHLIGHT};
                border-radius: {Radius.MD}px;
            }}
        """)
        frame_layout = QVBoxLayout(text_frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)
        frame_layout.setSpacing(4)
        
        # Box Header mit Aktionen
        header_lay = QHBoxLayout()
        box_title = QLabel("Bereinigter Text", self)
        box_title.setFont(Typography.get_font(Typography.TINY, bold=True))
        box_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX}; border: none; background: transparent;")
        
        # Mini Kopieren und Edit Buttons
        self.box_copy_btn = QPushButton(FluentIcons.COPY, self)
        self.box_copy_btn.setFixedSize(22, 22)
        self.box_copy_btn.setStyleSheet(self._icon_button_style(Colors.SUCCESS_GREEN_HEX))

        self.box_undo_btn = QPushButton(FluentIcons.RETRY, self)
        self.box_undo_btn.setFixedSize(22, 22)
        self.box_undo_btn.setToolTip("Letzten Satz entfernen")
        self.box_undo_btn.setStyleSheet(self._icon_button_style(Colors.ACCENT_BRIGHT_HEX))
        self.box_undo_btn.clicked.connect(self.undo_clicked.emit)

        self.url_btn = QPushButton("🔗", self)
        self.url_btn.setFixedSize(22, 22)
        self.url_btn.setToolTip("YouTube/URL transkribieren")
        self.url_btn.setStyleSheet(self._icon_button_style(Colors.ACCENT_BRIGHT_HEX))
        self.url_btn.clicked.connect(self.url_import_clicked.emit)
        
        # Wir belegen den Box Copy-Button direkt mit der Kopierfunktion
        self.exp_copy_btn = self.box_copy_btn  # Kompatibilität für AppController
        
        header_lay.addWidget(box_title)
        header_lay.addStretch()
        header_lay.addWidget(self.url_btn)
        header_lay.addWidget(self.box_undo_btn)
        header_lay.addWidget(self.box_copy_btn)
        frame_layout.addLayout(header_lay)

        self.polish_status = QLabel("Bereit für Polishing", self)
        self.polish_status.setObjectName("PolishStatusLabel")
        self.polish_status.setFont(Typography.get_font(Typography.TINY))
        self.polish_status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        self.polish_status.setVisible(False)
        frame_layout.addWidget(self.polish_status)

        # Text-Vergleichs-Slider (Rohtext vs. Polished)
        self.compare_slider = TextCompareSlider(self)
        frame_layout.addWidget(self.compare_slider, stretch=1)
        
        # Alias für Kompatibilität mit bestehendem Code
        self.transcript_edit = self.compare_slider.text_view
        
        main_layout.addWidget(text_frame, stretch=1)

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
        self.exp_close_btn.setFixedSize(28, 28)
        self.exp_close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_SECONDARY_HEX};
                border: 1px solid {Colors.BORDER_HEX}; border-radius: 14px;
                font-family: "{Typography.FONT_FAMILY}"; font-weight: bold; font-size: 11px;
            }}
            QPushButton:hover {{ color: {Colors.RECORDING_RED_HEX}; border-color: {Colors.RECORDING_RED_HEX}; }}
        """)
        chips_row.addWidget(self.exp_close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(chips_row)
        self.set_active_style(config.selected_style)

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

    def set_active_style(self, active_key: str):
        """Färbt den ausgewählten Stil-Chip ein."""
        for key, btn in self.chips.items():
            btn.setEnabled(True)
            if key == active_key:
                btn.setStyleSheet(self._chip_style(active=True))
            else:
                btn.setStyleSheet(self._chip_style(active=False))

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

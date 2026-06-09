"""
expanded_pill_widget.py
Widget für die Großansicht (Expanded Mode) der Dynamic Island.
Enthält Wort/WPM-Statistiken, eine Textbox mit Direktaktionen und Stil-Chips.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt
from src.ui.design_tokens import Colors, Typography, FluentIcons
from src.ui.drag_handle import DragHandleButton


class ExpandedPillWidget(QWidget):
    """Das Textbearbeitungs-, Statistik- und Stil-Auswahl-Widget im EXPANDED-State."""
    
    style_clicked = pyqtSignal(str)  # Emittiert den Stil-Key bei Klick

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chips: dict[str, QPushButton] = {}
        self._init_ui()

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
        text_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE_ELEVATED};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 8px;
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
        self.box_copy_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; border: none; color: {Colors.TEXT_SECONDARY_HEX}; 
                font-family: "{FluentIcons.FONT_FAMILY}"; font-size: 11px;
            }}
            QPushButton:hover {{ color: {Colors.SUCCESS_GREEN_HEX}; }}
        """)
        
        # Wir belegen den Box Copy-Button direkt mit der Kopierfunktion
        self.exp_copy_btn = self.box_copy_btn  # Kompatibilität für AppController
        
        header_lay.addWidget(box_title)
        header_lay.addStretch()
        header_lay.addWidget(self.box_copy_btn)
        frame_layout.addLayout(header_lay)
        
        # QTextEdit (Rahmenlos)
        self.transcript_edit = QTextEdit(self)
        self.transcript_edit.setFont(Typography.get_font(Typography.SMALL))
        self.transcript_edit.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {Colors.TEXT_PRIMARY_HEX};
                border: none;
                padding: 0px;
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 4px; }}
            QScrollBar::handle:vertical {{ background: {Colors.BORDER_HEX}; border-radius: 2px; }}
        """)
        frame_layout.addWidget(self.transcript_edit)
        main_layout.addWidget(text_frame)

        # ── 3. STIL-CHIPS (horizontal scrollbar bei Bedarf) ──
        chips_row = QHBoxLayout()
        chips_row.setContentsMargins(0, 4, 0, 0)
        chips_row.setSpacing(6)

        chips_scroll = QScrollArea(self)
        chips_scroll.setFixedHeight(34)
        chips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        chips_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        chips_inner = QWidget()
        chips_bar = QHBoxLayout(chips_inner)
        chips_bar.setContentsMargins(0, 0, 0, 0)
        chips_bar.setSpacing(5)

        style_definitions = [
            ("casual", "Bereinigen"),
            ("business", "Business"),
            ("bullet_points", "Stichpunkte"),
            ("concise", "Kompakt"),
            ("formal", "Formell"),
        ]

        for key, name in style_definitions:
            btn = QPushButton(name, chips_inner)
            btn.setFont(Typography.get_font(Typography.TINY, bold=True))
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _, k=key: self.style_clicked.emit(k))
            chips_bar.addWidget(btn)
            self.chips[key] = btn

        chips_bar.addStretch()
        chips_scroll.setWidget(chips_inner)
        chips_row.addWidget(chips_scroll, stretch=1)

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
        chips_row.addWidget(self.exp_close_btn)
        main_layout.addLayout(chips_row)
        from src.services.config_service import config
        self.set_active_style(config.selected_style)

    def set_stats(self, words: int, wpm: int):
        """Aktualisiert die Statistikanzeigen."""
        self.words_val.setText(str(words))
        self.wpm_val.setText(str(wpm))

    def set_active_style(self, active_key: str):
        """Färbt den ausgewählten Stil-Chip ein."""
        for key, btn in self.chips.items():
            btn.setEnabled(True)
            if key == active_key:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.ACCENT_HEX};
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 4px 8px;
                    }}
                    QPushButton:hover {{ background-color: {Colors.ACCENT_BRIGHT_HEX}; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {Colors.TEXT_SECONDARY_HEX};
                        border: 1px solid {Colors.BORDER_HEX};
                        border-radius: 10px;
                        padding: 4px 8px;
                    }}
                    QPushButton:hover {{ 
                        color: {Colors.TEXT_PRIMARY_HEX}; 
                        background-color: {Colors.SURFACE_ELEVATED}; 
                    }}
                """)

    def set_style_busy(self, busy: bool) -> None:
        """Deaktiviert Chips während Re-Polishing läuft."""
        for btn in self.chips.values():
            btn.setEnabled(not busy)

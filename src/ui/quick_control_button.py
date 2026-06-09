"""
quick_control_button.py
Custom kreisrunder Button für den Basics Control Hub in PyQt6.
Ausgelagert zur Einhaltung der 200-Zeilen-Regel.
"""

from PyQt6.QtWidgets import QPushButton
from src.ui.design_tokens import Colors, FluentIcons, Typography


class QuickControlButton(QPushButton):
    """Ein kreisrunder, schwebender Button mit modernem Hover-Effekt."""

    def __init__(self, icon_text: str, hover_color: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setText(icon_text)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ISLAND_BG_HEX};
                color: {Colors.TEXT_PRIMARY_HEX};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                font-family: "{FluentIcons.FONT_FAMILY}";
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                color: white;
                border: 1px solid {hover_color};
            }}
        """)

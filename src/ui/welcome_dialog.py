"""
welcome_dialog.py
Erststart-Dialog nach Installation der Setup.exe.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox,
)
from PyQt6.QtCore import Qt

from src.ui.design_tokens import Colors, Typography
from src.services.config_service import config


class WelcomeDialog(QDialog):
    """Kurze Einführung beim ersten Start."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Willkommen bei SurepriseAi")
        self.setMinimumWidth(460)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("SurepriseAi ist bereit")
        title.setFont(Typography.get_font(Typography.TITLE, bold=True))
        layout.addWidget(title)

        hotkey = config.global_hotkey.upper()
        body = QLabel(
            f"<b>So startest du:</b><br><br>"
            f"• <b>{hotkey}</b> drücken – Diktat starten/stoppen<br>"
            f"• Schwebende <b>Island</b> oben – Text & Stil-Chips<br>"
            f"• <b>Tray-Icon</b> (unten rechts) – Einstellungen & Updates<br>"
            f"• Text markieren + {hotkey} – Kontext für besseres Polishing<br><br>"
            f"Alles läuft lokal auf deinem PC."
        )
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setFont(Typography.get_font(Typography.SMALL))
        layout.addWidget(body)

        self.hide_check = QCheckBox("Beim nächsten Start nicht mehr anzeigen")
        self.hide_check.setChecked(True)
        layout.addWidget(self.hide_check)

        btn = QPushButton("Los geht's")
        btn.clicked.connect(self.accept)
        btn.setDefault(True)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.SURFACE_HEX};
                color: {Colors.TEXT_PRIMARY_HEX};
            }}
            QLabel {{ color: {Colors.TEXT_PRIMARY_HEX}; }}
            QCheckBox {{ color: {Colors.TEXT_SECONDARY_HEX}; }}
            QPushButton {{
                background: {Colors.ACCENT_HEX};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QPushButton:hover {{ background: {Colors.ACCENT_BRIGHT_HEX}; }}
        """)

    def skip_next_time(self) -> bool:
        return self.hide_check.isChecked()

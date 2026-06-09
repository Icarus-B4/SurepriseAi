"""
url_transcribe_dialog.py
Dialog zum Einfügen einer Medien-URL (YouTube, Vimeo, …).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt

from src.ui.design_tokens import Colors, Typography
from src.services.media_url_service import is_media_url, normalize_url


class UrlTranscribeDialog(QDialog):
    """Kleiner Dialog für Video-/Audio-URLs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("URL transkribieren")
        self.setMinimumWidth(480)
        self._url = ""
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        hint = QLabel("YouTube-, Vimeo- oder SoundCloud-Link einfügen")
        hint.setFont(Typography.get_font(Typography.SMALL))
        layout.addWidget(hint)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=…")
        self.url_input.textChanged.connect(self._validate)
        layout.addWidget(self.url_input)

        self.error_label = QLabel("")
        self.error_label.setFont(Typography.get_font(Typography.TINY))
        self.error_label.setStyleSheet(f"color: {Colors.RECORDING_RED_HEX};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        self.ok_btn = QPushButton("Transkribieren")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self._accept)
        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(self.ok_btn)
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
            QPushButton {{
                background: {Colors.ACCENT_HEX};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-family: "{Typography.FONT_FAMILY}";
            }}
            QPushButton:hover {{ background: {Colors.ACCENT_BRIGHT_HEX}; }}
            QPushButton:disabled {{ background: {Colors.TEXT_TERTIARY_HEX}; }}
            QLabel {{ color: {Colors.TEXT_SECONDARY_HEX}; }}
        """)

    def _validate(self) -> None:
        text = self.url_input.text()
        ok = is_media_url(text)
        self.ok_btn.setEnabled(ok)
        if text.strip() and not ok:
            self.error_label.setText("Bitte eine gültige Medien-URL eingeben.")
            self.error_label.show()
        else:
            self.error_label.hide()

    def _accept(self) -> None:
        self._url = normalize_url(self.url_input.text())
        self.accept()

    def selected_url(self) -> str:
        return self._url

    @staticmethod
    def paste_from_clipboard(parent=None) -> str:
        """Öffnet Dialog; bei gültigem Clipboard-Inhalt vorausfüllen."""
        from PyQt6.QtWidgets import QApplication
        dlg = UrlTranscribeDialog(parent)
        clip = QApplication.clipboard().text().strip()
        if clip and is_media_url(clip):
            dlg.url_input.setText(clip)
            dlg._validate()
        if dlg.exec():
            return dlg.selected_url()
        return ""

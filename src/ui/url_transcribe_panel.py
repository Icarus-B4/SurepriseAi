"""
url_transcribe_panel.py
Eingebettetes Panel für die URL-Transkription (YouTube, Vimeo, SoundCloud).
Ersetzt den separaten Dialog und bettet sich direkt im Settings-Stack ein.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.design_tokens import Colors, Typography
from src.services.media_url_service import is_media_url, normalize_url
from src.services.config_service import config
from src.utils.translation import tr


class UrlTranscribePanel(QWidget):
    """Panel zur Eingabe und Steuerung von URL-Transkriptionen."""

    transcribe_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UrlTranscribePanel")
        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(16)

        # Header Bereich
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title_label = QLabel()
        self.title_label.setObjectName("UrlTitle")
        self.title_label.setFont(Typography.get_font(Typography.MEDIUM, bold=True))

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("UrlSubtitle")
        self.subtitle_label.setFont(Typography.get_font(Typography.TINY))
        self.subtitle_label.setWordWrap(True)

        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        header.addLayout(title_box)
        layout.addLayout(header)

        # Mittige Card (gestrichelter Rahmen via QSS)
        self.card = QFrame()
        self.card.setObjectName("UrlCard")
        self.card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(24, 32, 24, 32)
        card_lay.setSpacing(14)
        card_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Riesen Link-Icon
        self.icon_label = QLabel("🔗")
        self.icon_label.setObjectName("UrlIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(self.icon_label)

        # Eingabefeld
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=…")
        self.url_input.setMinimumHeight(40)
        self.url_input.textChanged.connect(self._validate)
        card_lay.addWidget(self.url_input)

        # Fehler-Label
        self.error_label = QLabel("")
        self.error_label.setFont(Typography.get_font(Typography.TINY))
        self.error_label.setStyleSheet(f"color: {Colors.RECORDING_RED_HEX};")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        card_lay.addWidget(self.error_label)

        # Transkribieren Button
        self.action_btn = QPushButton()
        self.action_btn.setObjectName("HistoryButton")  # Nutzen den Style aus QSS
        self.action_btn.setMinimumHeight(42)
        self.action_btn.setEnabled(False)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self._on_transcribe_click)
        card_lay.addWidget(self.action_btn)

        layout.addWidget(self.card)

        # Unterer Bereich mit aktiver Modell-Info
        footer = QHBoxLayout()
        self.model_label = QLabel()
        self.model_label.setObjectName("UrlModelLabel")
        self.model_label.setFont(Typography.get_font(Typography.TINY))
        footer.addWidget(self.model_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(footer)

    def retranslate_ui(self) -> None:
        """Übersetzt alle Beschriftungen."""
        self.title_label.setText(tr("url_title"))
        self.subtitle_label.setText(tr("url_subtitle"))
        self.url_input.setPlaceholderText(tr("url_placeholder"))
        self.action_btn.setText(tr("url_button"))
        
        # Aktives Modell formatieren
        engine = config.get_str("transcription_engine", "parakeet").upper()
        if engine == "WHISPER":
            model_size = config.get_str("whisper_model_size", "tiny").upper()
            self.model_label.setText(f"Whisper Model: {model_size}")
        else:
            self.model_label.setText("NVIDIA Parakeet V3")

    def _validate(self) -> None:
        text = self.url_input.text().strip()
        if not text:
            self.action_btn.setEnabled(False)
            self.error_label.hide()
            return

        ok = is_media_url(text)
        self.action_btn.setEnabled(ok)
        if not ok:
            self.error_label.setText(tr("url_error"))
            self.error_label.show()
        else:
            self.error_label.hide()

    def _on_transcribe_click(self) -> None:
        url = normalize_url(self.url_input.text())
        if url:
            self.set_transcribing(True)
            self.transcribe_requested.emit(url)

    def set_transcribing(self, active: bool) -> None:
        """Aktiviert/Deaktiviert das Panel während der Transkription."""
        self.url_input.setEnabled(not active)
        self.action_btn.setEnabled(not active and is_media_url(self.url_input.text()))
        if active:
            self.action_btn.setText(tr("url_transcribing"))
            self.error_label.hide()
        else:
            self.action_btn.setText(tr("url_button"))
            self.url_input.clear()

    def prefill_from_clipboard(self) -> None:
        """Liest die Zwischenablage und befüllt das Textfeld, falls es eine Medien-URL ist."""
        from PyQt6.QtWidgets import QApplication
        clip = QApplication.clipboard().text().strip()
        if clip and is_media_url(clip):
            self.url_input.setText(clip)
            self._validate()

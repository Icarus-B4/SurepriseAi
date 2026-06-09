"""
settings_panel.py
Einstellungs-Panel für SurepriseAi in PyQt6.
Glas-Optik mit leicht transparentem Hintergrund und DWM-Blur.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QLineEdit, QPushButton, QWidget, QScrollArea, QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QColor

from src.ui.design_tokens import Colors, Typography, FluentIcons
from src.ui.settings_styles import settings_stylesheet
from src.ui.settings_features_section import add_features_section
from src.services.config_service import config


class SettingsWindow(QDialog):
    """Rahmenloses Einstellungsfenster mit Glassmorphism-Design."""

    setting_changed = pyqtSignal(str)

    def __init__(self, parent=None, on_open_history=None):
        super().__init__(parent)
        self._on_open_history = on_open_history
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(380, 580)
        self.drag_position = QPoint()
        self._init_ui()

    def _init_ui(self):
        container = QWidget(self)
        container.setObjectName("SettingsContainer")
        container.setStyleSheet(settings_stylesheet())

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 120))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Einstellungen")
        title.setFont(Typography.get_font(Typography.MEDIUM, bold=True))

        close_btn = QPushButton(FluentIcons.CLOSE)
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Scroll-Bereich
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(0, 4, 4, 0)
        scroll_layout.setSpacing(14)

        self._add_section(scroll_layout, "Aufnahme", FluentIcons.MICROPHONE)
        self.engine_combo = self._add_dropdown(scroll_layout, "Transkriptions-Engine", "transcription_engine", ["parakeet", "whisper"])
        self.whisper_combo = self._add_dropdown(scroll_layout, "Whisper-Modell (Fallback)", "whisper_model_size", ["tiny", "base", "small"])
        self.lang_combo = self._add_dropdown(scroll_layout, "Diktier-Sprache", "transcription_language", ["auto", "de", "en", "fr", "es", "it"])
        self.translate_check = self._add_checkbox(scroll_layout, "Auf Englisch übersetzen (Whisper)", "translate_to_english")

        self._add_section(scroll_layout, "KI-Polishing", "🤖")
        self.polish_check = self._add_checkbox(scroll_layout, "Ollama Polishing aktivieren", "ollama_polishing")
        self.url_edit = self._add_text_field(scroll_layout, "Ollama URL", "ollama_url")
        self.model_edit = self._add_text_field(scroll_layout, "Ollama Modell", "ollama_model")

        self._add_section(scroll_layout, "Verhalten", FluentIcons.SETTINGS)
        self.hotkey_check = self._add_checkbox(scroll_layout, "Globaler Hotkey aktiviert", "enable_global_hotkey")
        self.hotkey_edit = self._add_text_field(scroll_layout, "Hotkey (z. B. f8)", "global_hotkey")
        self.ptt_check = self._add_checkbox(scroll_layout, "Push-to-Talk Modus (F8 halten)", "push_to_talk")
        self.copy_check = self._add_checkbox(scroll_layout, "Automatisch in Zwischenablage", "auto_copy_to_clipboard")
        self.inject_check = self._add_checkbox(scroll_layout, "Automatisch einfügen (Auto-Typing)", "auto_inject_text")

        self._add_section(scroll_layout, "Personal Vocabulary", "📖")
        self.vocab_edit = self._add_list_field(scroll_layout, "Eigennamen (Komma-getrennt)", "personal_vocabulary")

        add_features_section(
            scroll_layout,
            self._add_section,
            lambda key: self.setting_changed.emit(key),
            on_open_history=self._on_open_history,
        )

        scroll.setWidget(content)
        layout.addWidget(scroll)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(container)
        main_layout.setContentsMargins(12, 12, 12, 12)

    def _add_section(self, layout: QVBoxLayout, title: str, icon: str) -> None:
        """Fügt eine Sektionsüberschrift mit Trennlinie ein."""
        divider = QFrame()
        divider.setObjectName("SectionDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        if layout.count() > 0:
            layout.addWidget(divider)

        row = QHBoxLayout()
        row.setSpacing(6)
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(Typography.get_font(Typography.SMALL))
        icon_lbl.setStyleSheet(f"color: {Colors.ACCENT_BRIGHT_HEX}; background: transparent;")
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("SectionTitle")
        title_lbl.setFont(Typography.get_font(Typography.TINY, bold=True))
        row.addWidget(icon_lbl)
        row.addWidget(title_lbl)
        row.addStretch()
        layout.addLayout(row)

    def _add_checkbox(self, layout: QVBoxLayout, label: str, key: str) -> QCheckBox:
        cb = QCheckBox(label)
        cb.setChecked(config.get_bool(key))
        cb.stateChanged.connect(lambda state: config.set(key, state == 2))
        layout.addWidget(cb)
        return cb

    def _add_dropdown(self, layout: QVBoxLayout, label: str, key: str, options: list) -> QComboBox:
        lbl = QLabel(label)
        lbl.setFont(Typography.get_font(Typography.TINY))
        lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX}; margin-bottom: 2px;")
        cb = QComboBox()
        cb.addItems(options)
        cb.setCurrentText(config.get_str(key))
        cb.currentTextChanged.connect(lambda val: config.set(key, val))
        layout.addWidget(lbl)
        layout.addWidget(cb)
        return cb

    def _add_text_field(self, layout: QVBoxLayout, label: str, key: str) -> QLineEdit:
        lbl = QLabel(label)
        lbl.setFont(Typography.get_font(Typography.TINY))
        lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        le = QLineEdit()
        le.setText(config.get_str(key))
        le.textChanged.connect(lambda val: config.set(key, val))
        layout.addWidget(lbl)
        layout.addWidget(le)
        return le

    def _add_list_field(self, layout: QVBoxLayout, label: str, key: str) -> QLineEdit:
        lbl = QLabel(label)
        lbl.setFont(Typography.get_font(Typography.TINY))
        lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY_HEX};")
        le = QLineEdit()
        le.setText(", ".join(config.get_list(key)))

        def _on_change(text: str):
            items = [item.strip() for item in text.split(",") if item.strip()]
            config.set(key, items)

        le.textChanged.connect(_on_change)
        layout.addWidget(lbl)
        layout.addWidget(le)
        return le

    def showEvent(self, event):
        """Aktiviert Windows DWM-Blur für Glas-Effekt."""
        super().showEvent(event)
        try:
            from src.utils.windows_overlay import enable_blur_behind
            enable_blur_behind(int(self.winId()))
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

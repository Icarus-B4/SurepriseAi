"""
settings_panel.py
Einstellungs-Panel für SurepriseAi in PyQt6.
Glas-Optik mit abgerundeten Ecken und sauberem Scroll-Layout.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QLineEdit, QPushButton, QWidget, QScrollArea, QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPainterPath, QRegion

from src.ui.design_tokens import Colors, Typography, FluentIcons
from src.ui.settings_styles import settings_stylesheet
from src.ui.settings_features_section import add_features_section
from src.services.config_service import config

_CORNER_RADIUS = 16


class SettingsWindow(QDialog):
    """Rahmenloses Einstellungsfenster mit Glassmorphism-Design."""

    setting_changed = pyqtSignal(str)

    def __init__(self, parent=None, on_open_history=None):
        super().__init__(parent)
        self._on_open_history = on_open_history
        self._container: QWidget | None = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(440, 640)
        self.resize(440, 680)
        self.drag_position = QPoint()
        self._init_ui()

    def _init_ui(self):
        container = QWidget(self)
        container.setObjectName("SettingsContainer")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet(settings_stylesheet())
        self._container = container

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 100))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(12)

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(0, 2, 10, 8)
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

        scroll_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.addWidget(container)

    def _apply_rounded_mask(self) -> None:
        """Schneidet Container und Fenster auf abgerundetes Rechteck zu."""
        if not self._container:
            return
        w = self._container.width()
        h = self._container.height()
        if w < 2 or h < 2:
            return
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), _CORNER_RADIUS, _CORNER_RADIUS)
        region = QRegion(path.toFillPolygon().toPolygon())
        self._container.setMask(region)

    def _hide_island_presence(self) -> None:
        island = self.parent()
        if island and hasattr(island, "presence_bar"):
            island._presence_hidden_for_settings = True
            island.presence_bar.stop()
            island.presence_bar.hide()

    def _restore_island_presence(self) -> None:
        island = self.parent()
        if not island or not getattr(island, "_presence_hidden_for_settings", False):
            return
        island._presence_hidden_for_settings = False
        if (island.state_machine.is_idle or island.state_machine.is_basics) and not island._idle_revealed:
            island._position_presence_bar()
            island.presence_bar.start()

    def _add_section(self, layout: QVBoxLayout, title: str, icon: str) -> None:
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
        le.home(False)
        layout.addWidget(lbl)
        layout.addWidget(le)
        return le

    def showEvent(self, event):
        super().showEvent(event)
        self._hide_island_presence()
        self._apply_rounded_mask()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_mask()

    def closeEvent(self, event):
        self._restore_island_presence()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

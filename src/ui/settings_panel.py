"""
settings_panel.py
Einstellungs-Panel für SurepriseAi in PyQt6.
Glas-Optik mit abgerundeten Ecken und sauberem Scroll-Layout.
"""

from PyQt6 import sip
from typing import Any, cast

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QWidget, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy, QStackedWidget,
)
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainterPath, QRegion

from src.ui.design_tokens import FluentIcons
from src.ui.history_dialog import HistoryDialog
from src.ui.settings_styles import settings_stylesheet
from src.ui.settings_features_section import add_features_section
from src.ui.toggle_switch import ToggleRow
from src.services.config_service import config
from src.services.dictation_history import DictationHistoryService
from src.services.recording_sound_service import RecordingSoundService
from src.ui.ollama_settings_row import OllamaSettingsRow

_CORNER_RADIUS = 16


class SettingsWindow(QDialog):
    """Rahmenloses Einstellungsfenster mit Glassmorphism-Design."""

    setting_changed = pyqtSignal(str)
    request_toggle_recording = pyqtSignal()
    request_transcribe_url = pyqtSignal()
    request_style_change = pyqtSignal(str)

    def __init__(
        self,
        parent=None,
        on_open_history=None,
        history_service: DictationHistoryService | None = None,
    ):
        super().__init__(parent)
        self._on_open_history = on_open_history
        self._history_service = history_service
        self._history_view: HistoryDialog | None = None
        self._container: QWidget | None = None
        self._container_layout: QHBoxLayout | None = None
        self._content_stack: QStackedWidget | None = None
        self._settings_page: QWidget | None = None
        self._history_nav_btn: QPushButton | None = None
        self._settings_nav_btn: QPushButton | None = None
        self._settings_widgets: list[QWidget] = []
        self._preview_sounds = RecordingSoundService(self)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(1180, 720)
        self.resize(1280, 760)
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

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._container_layout = layout

        sidebar = self._build_sidebar()
        layout.addWidget(sidebar)

        self._content_stack = QStackedWidget(container)
        self._content_stack.setObjectName("SettingsContentStack")
        self._settings_page = QWidget(container)
        settings_layout = QVBoxLayout(self._settings_page)
        settings_layout.setContentsMargins(22, 18, 22, 22)
        settings_layout.setSpacing(12)

        hero = QFrame()
        hero.setObjectName("SettingsHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 14, 16, 14)
        hero_layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("Einstellungen")
        title.setObjectName("SettingsHeroTitle")

        close_btn = QPushButton(FluentIcons.CLOSE)
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        hero_layout.addLayout(header)
        subtitle = QLabel("Design, Aufnahme, Kontext und Diktat-Verlauf an einem Ort")
        subtitle.setObjectName("SettingsHeroSubtitle")
        hero_layout.addWidget(subtitle)
        settings_layout.addWidget(hero)
        self._settings_widgets.append(hero)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(0, 2, 10, 8)
        scroll_layout.setSpacing(14)

        self._add_section(scroll_layout, "Aufnahme", FluentIcons.MICROPHONE)
        self.engine_combo = self._add_dropdown(scroll_layout, "Transkriptions-Engine", "transcription_engine", ["parakeet", "whisper"])
        self.whisper_combo = self._add_dropdown(scroll_layout, "Whisper-Modell (Fallback)", "whisper_model_size", ["tiny", "base", "small"])
        self.lang_combo = self._add_dropdown(scroll_layout, "Diktier-Sprache", "transcription_language", ["auto", "de", "en", "fr", "es", "it"])
        self.translate_de_check = self._add_checkbox(scroll_layout, "Auf Deutsch übersetzen", "translate_to_german")
        self.translate_en_check = self._add_checkbox(scroll_layout, "Auf Englisch übersetzen (Whisper)", "translate_to_english")
        self._wire_exclusive_translate_toggles()
        self.translate_hotkeys_check = self._add_checkbox(scroll_layout, "Übersetzungs-Hotkeys aktiv", "enable_translate_hotkeys")
        self.translate_de_hotkey_edit = self._add_text_field(scroll_layout, "Hotkey Deutsch (z. B. f6)", "translate_german_hotkey")
        self.translate_en_hotkey_edit = self._add_text_field(scroll_layout, "Hotkey Englisch (z. B. f7)", "translate_english_hotkey")

        self._add_section(scroll_layout, "Aufnahme-Sounds", "🔊")
        self.sounds_check = self._add_checkbox(scroll_layout, "Sounds bei Start/Stopp", "enable_recording_sounds")
        self.start_sound_combo = self._add_sound_picker(scroll_layout, "Sound beim Start", "recording_start_sound")
        self.stop_sound_combo = self._add_sound_picker(scroll_layout, "Sound beim Stopp", "recording_stop_sound")

        self._add_section(scroll_layout, "KI-Polishing", "🤖")
        self.polish_check = self._add_checkbox(scroll_layout, "Ollama Polishing aktivieren", "ollama_polishing")
        self.url_edit = self._add_text_field(scroll_layout, "Ollama URL", "ollama_url")
        self.model_edit = self._add_text_field(scroll_layout, "Ollama Modell", "ollama_model")
        self._ollama_row = OllamaSettingsRow()
        self._ollama_row.action_finished.connect(self._on_ollama_action_finished)
        scroll_layout.addWidget(self._ollama_row)

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
            on_open_history=self._open_history_inside_settings,
        )

        scroll_layout.addStretch(1)
        scroll.setWidget(content)
        settings_layout.addWidget(scroll, stretch=1)
        self._settings_widgets.append(scroll)
        self._content_stack.addWidget(self._settings_page)
        layout.addWidget(self._content_stack, stretch=1)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.addWidget(container)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget(self)
        sidebar.setObjectName("SettingsSidebar")
        sidebar.setFixedWidth(190)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(8)

        self._settings_nav_btn = self._make_nav_button("⚙  Einstellungen")
        self._history_nav_btn = self._make_nav_button("📜  Diktat-Verlauf")
        self._settings_nav_btn.clicked.connect(self.show_settings)
        self._history_nav_btn.clicked.connect(self._open_history_inside_settings)

        layout.addWidget(self._settings_nav_btn)
        layout.addWidget(self._history_nav_btn)
        
        layout.addSpacing(16)
        
        from PyQt6.QtWidgets import QMenu
        from src.services.style_definitions import STYLE_DEFINITIONS

        self._record_btn = self._make_action_button("🎙  Diktat starten")
        self._record_btn.clicked.connect(self.request_toggle_recording.emit)
        layout.addWidget(self._record_btn)

        self._style_btn = self._make_action_button("🎨  Polishing-Stil ▾")
        style_menu = QMenu(self._style_btn)
        style_menu.setStyleSheet("QMenu { background-color: #1A1A1F; border: 1px solid #333; border-radius: 6px; padding: 4px; } QMenu::item { padding: 6px 24px; color: #E0E0E0; font-size: 12px; } QMenu::item:selected { background-color: #2D2D36; border-radius: 4px; }")
        for key, name in STYLE_DEFINITIONS:
            action = style_menu.addAction(name)
            action.triggered.connect(lambda checked, k=key: self.request_style_change.emit(k))
        self._style_btn.setMenu(style_menu)
        layout.addWidget(self._style_btn)

        self._url_btn = self._make_action_button("🔗  URL transkribieren…")
        self._url_btn.clicked.connect(self.request_transcribe_url.emit)
        layout.addWidget(self._url_btn)

        layout.addStretch(1)

        from src.version import __version__

        brand_box = QWidget(sidebar)
        brand_box.setObjectName("SettingsSidebarBrandBox")
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(10, 10, 10, 10)
        brand_layout.setSpacing(2)

        brand_name = QLabel("SurepriseAi", sidebar)
        brand_name.setObjectName("SettingsSidebarBrand")
        brand_ver = QLabel(f"v{__version__}", brand_box)
        brand_ver.setObjectName("SettingsSidebarVersion")

        brand_layout.addWidget(brand_name)
        brand_layout.addWidget(brand_ver)
        layout.addWidget(brand_box)
        self._set_active_nav("settings")
        return sidebar

    def _make_nav_button(self, text: str) -> QPushButton:
        btn = QPushButton(text, self)
        btn.setObjectName("SidebarNavButton")
        btn.setCheckable(True)
        btn.setMinimumHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _make_action_button(self, text: str) -> QPushButton:
        btn = QPushButton(text, self)
        btn.setObjectName("SidebarActionButton")
        btn.setMinimumHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("text-align: left; padding-left: 12px; color: #A0A0A0; background: transparent; border: none; font-size: 14px;")
        return btn

    def _set_active_nav(self, view: str) -> None:
        if self._settings_nav_btn is not None:
            self._settings_nav_btn.setChecked(view == "settings")
        if self._history_nav_btn is not None:
            self._history_nav_btn.setChecked(view == "history")

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

    def _open_history_inside_settings(self) -> None:
        """Öffnet den Diktat-Verlauf im selben Settings-Fenster."""
        if self._history_service is None:
            if self._on_open_history:
                self._on_open_history()
            return
        self.show_history()

    def show_history(self) -> None:
        """Wechselt rechts in die eingebettete Verlauf-Ansicht."""
        if not self._content_stack or not self._container:
            return
        history_service = self._history_service
        if history_service is None:
            return

        if self._history_view is None:
            self._history_view = HistoryDialog(
                history_service,
                self._container,
                embedded=True,
            )
            self._history_view.setWindowFlags(Qt.WindowType.Widget)
            self._history_view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            self._history_view.finished.connect(lambda _result: self.show_settings())
            self._content_stack.addWidget(self._history_view)

        self._history_view._refresh_list()
        self._content_stack.setCurrentWidget(self._history_view)
        self._set_active_nav("history")
        self.setMinimumSize(1180, 720)
        self.resize(max(self.width(), 1280), max(self.height(), 760))
        self._apply_rounded_mask()

    def show_settings(self) -> None:
        """Kehrt rechts aus dem Verlauf zurück in die Einstellungen."""
        if self._history_view is not None:
            self._history_view._player.stop()
        if self._content_stack is not None and self._settings_page is not None:
            self._content_stack.setCurrentWidget(self._settings_page)
        self._set_active_nav("settings")
        self.setMinimumSize(900, 650)
        self._apply_rounded_mask()

    def _hide_island_presence(self) -> None:
        island = cast(Any, self.parent())
        if island and hasattr(island, "presence_bar"):
            island._presence_hidden_for_settings = True
            island.presence_bar.stop()
            island.presence_bar.hide()

    def _restore_island_presence(self) -> None:
        island = cast(Any, self.parent())
        if not island or not getattr(island, "_presence_hidden_for_settings", False):
            return
        island._presence_hidden_for_settings = False
        if island.state_machine.is_idle or island.state_machine.is_basics:
            if config.get_bool("enable_presence_bar", True):
                island._check_hover()
            elif not island._idle_revealed:
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
        icon_lbl.setObjectName("SectionIcon")
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("SectionTitle")
        row.addWidget(icon_lbl)
        row.addWidget(title_lbl)
        row.addStretch()
        layout.addLayout(row)

    def _add_checkbox(self, layout: QVBoxLayout, label: str, key: str) -> ToggleRow:
        row = ToggleRow(label, checked=config.get_bool(key))
        row.toggled.connect(lambda checked: config.set(key, checked))
        layout.addWidget(row)
        return row

    def _wire_exclusive_translate_toggles(self) -> None:
        """DE- und EN-Übersetzung schließen sich gegenseitig aus."""

        def _on_de(checked: bool) -> None:
            if checked and self.translate_en_check.isChecked():
                self.translate_en_check.setChecked(False)
                config.set("translate_to_english", False)

        def _on_en(checked: bool) -> None:
            if checked and self.translate_de_check.isChecked():
                self.translate_de_check.setChecked(False)
                config.set("translate_to_german", False)

        self.translate_de_check.toggled.connect(_on_de)
        self.translate_en_check.toggled.connect(_on_en)

    def _on_ollama_action_finished(self, ok: bool, message: str) -> None:
        island = cast(Any, self.parent())
        toast = getattr(island, "show_settings_toast", None)
        if callable(toast):
            toast(message, ok)
        self.setting_changed.emit("ollama_polishing")

    def _add_dropdown(self, layout: QVBoxLayout, label: str, key: str, options: list) -> QComboBox:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        cb = QComboBox()
        cb.addItems(options)
        cb.setCurrentText(config.get_str(key))
        cb.currentTextChanged.connect(lambda val: config.set(key, val))
        cb.setFixedWidth(200)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(cb)
        layout.addLayout(row)
        return cb

    def _populate_sound_combo(self, combo: QComboBox, config_key: str) -> None:
        """Lädt verfügbare Sounds in die ComboBox (beim Öffnen erneut aufrufbar)."""
        current = config.get_str(config_key)
        combo.blockSignals(True)
        combo.clear()

        sounds = RecordingSoundService.list_sounds()
        if not sounds:
            combo.addItem("— keine Sounds gefunden —", "")
            combo.setEnabled(False)
            combo.blockSignals(False)
            return

        combo.setEnabled(True)
        for filename, display in sounds:
            combo.addItem(display, filename)

        index = combo.findData(current, Qt.ItemDataRole.UserRole)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentIndex(0)
            config.set(config_key, combo.currentData(Qt.ItemDataRole.UserRole))

        combo.blockSignals(False)

    def _add_sound_picker(self, layout: QVBoxLayout, label: str, key: str) -> QComboBox:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")

        cb = QComboBox()
        self._populate_sound_combo(cb, key)

        cb.currentIndexChanged.connect(
            lambda _idx, combo=cb, config_key=key: self._on_sound_selected(combo, config_key)
        )

        preview_btn = QPushButton("▶")
        preview_btn.setObjectName("SoundPreviewButton")
        preview_btn.setFixedSize(34, 30)
        preview_btn.setToolTip("Sound testen")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.clicked.connect(
            lambda _checked=False, combo=cb: self._preview_sound(
                combo.currentData(Qt.ItemDataRole.UserRole)
            )
        )

        cb.setFixedWidth(200)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(cb)
        row.addWidget(preview_btn)
        layout.addLayout(row)
        return cb

    def _on_sound_selected(self, combo: QComboBox, config_key: str) -> None:
        filename = combo.currentData(Qt.ItemDataRole.UserRole)
        if filename:
            config.set(config_key, filename)

    def _refresh_sound_pickers(self) -> None:
        if hasattr(self, "start_sound_combo"):
            self._populate_sound_combo(self.start_sound_combo, "recording_start_sound")
        if hasattr(self, "stop_sound_combo"):
            self._populate_sound_combo(self.stop_sound_combo, "recording_stop_sound")

    def _preview_sound(self, filename: str | None) -> None:
        if not filename:
            return
        island = cast(Any, self.parent())
        preview = getattr(island, "recording_sound_preview_callback", None)
        if callable(preview):
            preview(filename)
            return
        self._preview_sounds.preview(filename)

    def _add_text_field(self, layout: QVBoxLayout, label: str, key: str) -> QLineEdit:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        le = QLineEdit()
        le.setText(config.get_str(key))
        le.textChanged.connect(lambda val: config.set(key, val))
        le.setFixedWidth(240)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(le)
        layout.addLayout(row)
        return le

    def _add_list_field(self, layout: QVBoxLayout, label: str, key: str) -> QLineEdit:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        le = QLineEdit()
        le.setText(", ".join(config.get_list(key)))

        def _on_change(text: str):
            items = [item.strip() for item in text.split(",") if item.strip()]
            config.set(key, items)

        le.textChanged.connect(_on_change)
        le.home(False)
        le.setFixedWidth(300)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(le)
        layout.addLayout(row)
        return le

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_sound_pickers()
        if hasattr(self, "_ollama_row"):
            self._ollama_row.refresh_status()
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

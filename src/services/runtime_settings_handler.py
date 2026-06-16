"""
runtime_settings_handler.py
Wendet geänderte Einstellungen ohne Neustart an (FAB, Akzent, Privacy, Theme, Sprache).
"""

from src.services.config_service import config
from src.ui.accent_theme import apply_accent_from_config, reset_accent_cache, apply_theme_from_config


class RuntimeSettingsHandler:
    """Steuert Laufzeit-Updates nach Settings-Änderungen."""

    def __init__(self, app) -> None:
        self.app = app

    def apply(self, key: str = "") -> None:
        controller = self.app.controller
        if key in ("show_privacy_badge", "ollama_polishing", "enable_screen_context", "enable_selected_text_context", ""):
            controller._update_privacy_badge()
        if key in ("use_windows_accent", ""):
            reset_accent_cache()
            if apply_accent_from_config():
                self.refresh_ui_accent()
        if key in ("theme_mode", ""):
            if apply_theme_from_config():
                self.refresh_ui_theme()
        if key in ("app_language", ""):
            self.refresh_ui_language()
        if key in ("enable_mini_fab", ""):
            self.sync_mini_fab()
        if key in ("enable_presence_bar", ""):
            self.sync_presence_bar()
        if key in ("enable_global_hotkey", "global_hotkey", "push_to_talk", "enable_translate_hotkeys", "translate_german_hotkey", "translate_english_hotkey", ""):
            self.sync_hotkey()
        if key in ("recording_sound_volume", ""):
            self.app.controller.recording_sounds.refresh_volume()

    def sync_hotkey(self) -> None:
        if config.hotkey_enabled:
            self.app.hotkey.restart()
        else:
            self.app.hotkey.stop()

    def sync_presence_bar(self) -> None:
        window = self.app.window
        if window.state_machine.is_idle or window.state_machine.is_basics:
            window._check_hover()

    def check_accent_changed(self) -> None:
        if not config.get_bool("use_windows_accent", True):
            return
        if apply_accent_from_config():
            self.refresh_ui_accent()

    def refresh_ui_accent(self) -> None:
        pill = self.app.window.pill
        pill._apply_pill_style()
        style_key = self.app.pipeline.session_style
        pill.expanded_widget.set_active_style(style_key)
        self.app.tray.setIcon(self.app.tray._create_tray_icon())
        if self.app.mini_fab:
            self.app.mini_fab.set_recording(self.app.state_machine.is_recording)

    def refresh_ui_theme(self) -> None:
        """Aktualisiert alle Fenster-Stylesheets basierend auf dem geänderten Theme."""
        window = self.app.window
        
        # 1. Haupt-Island und deren Pill aktualisieren
        window.pill._apply_pill_style()
        window.pill.expanded_widget.refresh_theme()
        style_key = self.app.pipeline.session_style
        window.pill.expanded_widget.set_active_style(style_key)
        
        # 2. Settings-Dialog aktualisieren falls vorhanden
        dlg = getattr(window, "_settings_dialog", None)
        if dlg:
            dlg.refresh_theme()
            
        # 3. History-Dialog aktualisieren falls vorhanden
        hist = getattr(self.app.controller, "_history_dialog", None)
        if hist:
            hist._apply_style()
            
        # 4. Toast-Notification aktualisieren
        if hasattr(self.app, "toast"):
            self.app.toast.refresh_theme()
            
        # 5. System-Tray aktualisieren
        if hasattr(self.app, "tray"):
            self.app.tray.refresh_theme()

    def refresh_ui_language(self) -> None:
        """Löst eine Live-Übersetzung auf allen UI-Komponenten aus."""
        window = self.app.window
        
        # 1. Settings-Dialog aktualisieren
        dlg = getattr(window, "_settings_dialog", None)
        if dlg:
            dlg.retranslate_ui()
            
        # 2. History-Dialog aktualisieren
        hist = getattr(self.app.controller, "_history_dialog", None)
        if hist:
            hist.retranslate_ui()
            
        # 3. Expanded Pill aktualisieren
        window.pill.expanded_widget.retranslate_ui()
        
        # 4. Toast-Notification aktualisieren
        if hasattr(self.app, "toast"):
            self.app.toast.retranslate_ui()

    def sync_mini_fab(self) -> None:
        enabled = config.get_bool("enable_mini_fab", False)
        if enabled and self.app.mini_fab is None:
            from src.ui.mini_fab import MiniFab
            self.app.mini_fab = MiniFab()
            self.app.mini_fab.toggle_recording.connect(self.app.pipeline.toggle)
            self.app.mini_fab.show_with_fade()
            self.app.mini_fab.set_recording(self.app.state_machine.is_recording)
        elif not enabled and self.app.mini_fab is not None:
            self.app.mini_fab.close()
            self.app.mini_fab = None

"""
settings_manager.py
Manager für das Einstellungsfenster der Dynamic Island.
Kapselt das Öffnen, Schließen und die Signalverbindungen des SettingsWindow.
"""

from src.ui.settings_panel import SettingsWindow


class SettingsManager:
    """Verwaltet das Einstellungs-Fenster (Settings Dialog)."""

    def __init__(self, window):
        self.window = window
        self._settings_dialog = None

    def toggle_settings(self):
        """Öffnet oder schließt das Einstellungsfenster."""
        if self._settings_dialog is not None and self._settings_dialog.isVisible():
            self._settings_dialog.close()
            return

        if self._settings_dialog is None:
            on_history = getattr(self.window, "open_history_callback", None)
            history_service = getattr(self.window, "history_service", None)
            usage_stats = getattr(self.window, "usage_stats", None)
            print("[Settings] Settings-Fenster wird geöffnet")
            
            self._settings_dialog = SettingsWindow(
                self.window,
                on_open_history=on_history,
                history_service=history_service,
                usage_stats=usage_stats,
            )
            
            cb = getattr(self.window, "settings_changed_callback", None)
            if cb:
                self._settings_dialog.setting_changed.connect(cb)
            self._settings_dialog.finished.connect(self.window._on_settings_closed)

            # Binde Callbacks für Aktionen im Einstellungsfenster
            self._settings_dialog.request_toggle_recording.connect(
                lambda: getattr(self.window, "request_toggle_recording_callback", lambda: None)()
            )
            self._settings_dialog.request_transcribe_media_url.connect(
                lambda url: getattr(self.window, "request_transcribe_media_url_callback", lambda x: None)(url)
            )
            self._settings_dialog.request_style_change.connect(
                lambda k: getattr(self.window, "request_style_change_callback", lambda x: None)(k)
            )

        dlg = self._settings_dialog
        dlg.prepare_for_show(reposition=not dlg._positioned_once)
        dlg._positioned_once = True
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def get_dialog(self) -> SettingsWindow | None:
        """Gibt das aktuelle SettingsWindow-Objekt zurück."""
        return self._settings_dialog

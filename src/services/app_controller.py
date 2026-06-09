"""
app_controller.py
Verwaltet die Event-Handler, Berechnungen und Signal-Kopplungen.
Hält app.py schlank und unter 200 Zeilen.
"""

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication
from src.ui.island_states import IslandState
from src.services.config_service import config


class AppController(QObject):
    """
    Controller zur Steuerung der Interaktion zwischen Benutzeroberfläche und Services.
    """

    def __init__(self, app_instance) -> None:
        super().__init__()
        self.app = app_instance
        self.current_raw = ""
        self.current_corrected = ""
        self.current_polished = ""

    def connect_all(self):
        """Verknüpft alle Signale und Callbacks."""
        self.app.signals.ready.connect(self._on_pipeline_ready)
        self.app.signals.state_changed.connect(self._on_pipeline_state)
        self.app.signals.result_ready.connect(self._on_pipeline_result)
        self.app.signals.error_occurred.connect(self._on_pipeline_error)
        self.app.signals.audio_level.connect(self._on_audio_level)
        self.app.signals.partial_ready.connect(self._on_partial_result)

        self.app.window.pill.idle_widget.mouseDoubleClickEvent = lambda e: self.app.pipeline.toggle()
        self.app.window.file_dropped_callback = self.app.pipeline.transcribe_audio_file
        self.app.window._on_style_selected = self._on_style_changed

        self.app.tray.toggle_island.connect(self._toggle_island_visibility)
        self.app.tray.open_settings.connect(self.app.window._on_open_settings)
        self.app.tray.quit_app.connect(self.shutdown)
        self.app.tray.style_selected.connect(self._on_style_changed)
        self.app.tray.toggle_recording.connect(self.app.pipeline.toggle)

        expanded = self.app.window.pill.expanded_widget
        expanded.exp_close_btn.clicked.connect(self._close_expanded)
        expanded.exp_copy_btn.clicked.connect(self._copy_expanded_text)
        expanded.style_clicked.connect(self._on_style_changed)

        self.app.state_machine.add_listener(self._on_internal_state_changed)

        self.app.pipeline.set_state_callback(self.app.signals.state_changed.emit)
        self.app.pipeline.set_result_callback(self.app.signals.result_ready.emit)
        self.app.pipeline.set_error_callback(self.app.signals.error_occurred.emit)
        self.app.pipeline.set_level_callback(self.app.signals.audio_level.emit)
        self.app.pipeline.set_partial_callback(self.app.signals.partial_ready.emit)

        self.app.hotkey.set_start_callback(self.app.pipeline.start_recording)
        self.app.hotkey.set_stop_callback(self.app.pipeline.stop_recording)

    def _source_text(self) -> str:
        """Basis-Text für Re-Polishing – Roh- oder korrigierter Text."""
        if self.current_corrected.strip():
            return self.current_corrected
        if self.current_raw.strip():
            return self.app.pipeline.replacer.apply(self.current_raw)
        return self.app.window.pill.expanded_widget.transcript_edit.toPlainText().strip()

    def _apply_text_to_ui(self, text: str, style_key: str) -> None:
        """Schreibt Ergebnis sofort ins Expanded-Widget."""
        expanded = self.app.window.pill.expanded_widget
        expanded.transcript_edit.setText(text)
        expanded.set_active_style(style_key)
        duration = self.app.pipeline.recording_duration
        words = len(text.split())
        wpm = int((words / duration) * 60) if duration > 0.5 else 0
        expanded.set_stats(words, wpm)
        if config.auto_copy:
            QApplication.clipboard().setText(text)

    def _on_pipeline_ready(self, success: bool):
        if success:
            self.app.toast.show_success("Bereit zum Diktieren")
        else:
            self.app.toast.show_error("Modell konnte nicht geladen werden")

    def _on_pipeline_state(self, state_name: str):
        self.app.state_machine.transition_by_name(state_name)
        self.app.tray.set_recording_state(self.app.state_machine.is_recording)
        if state_name == "recording":
            self.app.toast.show_live_transcript("Höre zu…")
        elif state_name == "processing":
            self.app.toast.end_live_mode()

    def _on_pipeline_result(self, raw: str, polished: str):
        self.current_raw = raw
        self.current_corrected = self.app.pipeline.replacer.apply(raw)
        self.current_polished = polished

        self._apply_text_to_ui(polished, config.selected_style)
        self.app.toast.show_success("Text bereinigt und in Zwischenablage kopiert!")

    def _on_pipeline_error(self, message: str):
        self.app.toast.show_error(message)
        self.app.state_machine.transition_to(IslandState.IDLE)

    def _on_audio_level(self, level: float):
        if self.app.state_machine.is_recording:
            self.app.window.pill.waveform.set_rms(level)

    def _on_partial_result(self, text: str):
        self.app.toast.show_live_transcript(text)

    def _on_style_changed(self, style_key: str):
        style_labels = {
            "casual": "Bereinigen",
            "business": "Business",
            "bullet_points": "Stichpunkte",
            "concise": "Kompakt",
            "formal": "Formell",
        }
        label = style_labels.get(style_key, style_key)

        config.selected_style = style_key
        config.save()
        self.app.tray.update_menu_states()

        source = self._source_text()
        if not source:
            self.app.window.pill.expanded_widget.set_active_style(style_key)
            self.app.toast.show_message(f'Stil „{label}" für nächstes Diktat gewählt', duration_ms=1500)
            return

        # Sofort auf dem UI-Thread – kein Ollama, kein Hintergrundthread
        new_text = self.app.pipeline.polisher.polish_instant(source, style=style_key)
        self.current_polished = new_text
        self._apply_text_to_ui(new_text, style_key)
        self.app.toast.show_success(f'Stil „{label}" angewendet!')
        print(f"[AppController] Stil '{style_key}' → {len(new_text)} Zeichen")

    def _on_internal_state_changed(self, prev_state, new_state):
        if new_state == IslandState.EXPANDED:
            text = self.current_polished or self.current_corrected or self.current_raw
            self.app.window.pill.set_expanded(text)
            if text:
                self._apply_text_to_ui(text, config.selected_style)

    def _close_expanded(self):
        """Schließt Expanded und setzt die Island an die Startposition (oben zentriert)."""
        self.app.window.reset_to_start_position()
        self.app.state_machine.transition_to(IslandState.IDLE)

    def _copy_expanded_text(self):
        text = self.app.window.pill.expanded_widget.transcript_edit.toPlainText()
        QApplication.clipboard().setText(text)
        self.app.toast.show_success("In Zwischenablage kopiert!")

    def _toggle_island_visibility(self):
        if self.app.window.windowOpacity() > 0.0:
            self.app.window._fade_to(0.0)
        else:
            self.app.window._fade_to(1.0)
            self.app.window.is_hovered = True

    def shutdown(self):
        self.app.hotkey.stop()
        if self.app.pipeline.is_recording:
            self.app.pipeline.stop_recording()
        self.app.window.close()
        self.app.toast.close()
        self.app.tray.hide()
        self.app.app.quit()

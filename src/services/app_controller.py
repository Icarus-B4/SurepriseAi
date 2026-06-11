"""
app_controller.py
Verwaltet die Event-Handler, Berechnungen und Signal-Kopplungen.
Hält app.py schlank und unter 200 Zeilen.
"""

from PyQt6.QtCore import QObject, QTimer, Qt
from PyQt6.QtWidgets import QApplication
from src.ui.island_states import IslandState
from src.ui.polish_animator import PolishAnimator
from src.ui.history_dialog import HistoryDialog
from src.ui.url_transcribe_dialog import UrlTranscribeDialog
from src.ui.welcome_dialog import WelcomeDialog
from src.utils.app_paths import mark_onboarding_done, needs_onboarding
from src.services.config_service import config
from src.services.style_definitions import style_label
from src.services.dictation_history import DictationHistoryService
from src.services.usage_stats import UsageStatsService
from src.services.runtime_settings_handler import RuntimeSettingsHandler
from src.services.update_controller import UpdateController


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
        self._last_live_text = ""
        self.history = DictationHistoryService()
        self.usage_stats = UsageStatsService()
        self._history_dialog: HistoryDialog | None = None
        self.runtime_settings: RuntimeSettingsHandler | None = None
        self.updates = UpdateController(app_instance)

    def connect_all(self):
        """Verknüpft alle Signale und Callbacks."""
        qc = Qt.ConnectionType.QueuedConnection
        self.app.signals.ready.connect(self._on_pipeline_ready, qc)
        self.app.signals.state_changed.connect(self._on_pipeline_state, qc)
        self.app.signals.result_ready.connect(self._on_pipeline_result, qc)
        self.app.signals.error_occurred.connect(self._on_pipeline_error, qc)
        self.app.signals.audio_level.connect(self._on_audio_level, qc)
        self.app.signals.partial_ready.connect(self._on_partial_result, qc)

        self.app.window.file_dropped_callback = self.app.pipeline.transcribe_audio_file
        self.app.window.url_dropped_callback = self._transcribe_media_url
        self.app.window._on_style_selected = self._on_style_changed

        self.app.tray.toggle_island.connect(self._toggle_island_visibility)
        self.app.tray.open_settings.connect(self.app.window._on_open_settings)
        self.app.tray.open_history.connect(self._open_history)
        self.app.tray.quit_app.connect(self.shutdown)
        self.app.tray.style_selected.connect(self._on_style_changed)
        self.app.tray.toggle_recording.connect(self.app.pipeline.toggle)
        self.app.tray.check_updates.connect(lambda: self.updates.check_now(silent=False))
        self.app.tray.open_releases.connect(self.updates.open_releases_page)
        self.app.tray.transcribe_url.connect(self._open_url_dialog)

        expanded = self.app.window.pill.expanded_widget
        self._polish_animator = PolishAnimator(expanded.transcript_edit, self)
        expanded.exp_close_btn.clicked.connect(self._close_expanded)
        expanded.exp_copy_btn.clicked.connect(self._copy_expanded_text)
        expanded.undo_clicked.connect(self._undo_last_sentence)
        expanded.style_clicked.connect(self._on_style_changed)
        expanded.url_import_clicked.connect(self._open_url_dialog)

        self.app.window.outside_dismiss_callback = self._close_expanded

        self.app.state_machine.add_listener(self._on_internal_state_changed)

        self.app.pipeline.set_state_callback(self.app.signals.state_changed.emit)
        self.app.pipeline.set_result_callback(self.app.signals.result_ready.emit)
        self.app.pipeline.set_error_callback(self.app.signals.error_occurred.emit)
        self.app.pipeline.set_level_callback(self.app.signals.audio_level.emit)
        self.app.pipeline.set_partial_callback(self.app.signals.partial_ready.emit)

        self.app.hotkey.set_start_callback(self.app.pipeline.start_recording)
        self.app.hotkey.set_stop_callback(self.app.pipeline.stop_recording)

        self.app.window.settings_changed_callback = self.apply_runtime_setting
        self.app.window.open_history_callback = self._open_history
        self.runtime_settings = RuntimeSettingsHandler(self.app)

        self._refresh_tray_tooltip()
        self._update_privacy_badge()
        self.updates.schedule_startup_check()

    def _source_text(self) -> str:
        """Basis-Text für Re-Polishing – Roh- oder korrigierter Text."""
        if self.current_corrected.strip():
            return self.current_corrected
        if self.current_raw.strip():
            return self.app.pipeline.replacer.apply(self.current_raw)
        return self.app.window.pill.expanded_widget.transcript_edit.toPlainText().strip()

    def _apply_text_to_ui(self, text: str, style_key: str) -> None:
        """Schreibt Ergebnis sofort ins Expanded-Widget."""
        self._polish_animator.cancel()
        expanded = self.app.window.pill.expanded_widget
        expanded.transcript_edit.setPlainText(text)
        expanded.set_active_style(style_key)
        duration = self.app.pipeline.recording_duration
        words = len(text.split())
        wpm = int((words / duration) * 60) if duration > 0.5 else 0
        expanded.set_stats(words, wpm)
        if config.auto_copy:
            QApplication.clipboard().setText(text)

    def apply_runtime_setting(self, key: str = "") -> None:
        """Wendet geänderte Einstellungen ohne Neustart an."""
        if self.runtime_settings:
            self.runtime_settings.apply(key)

    def check_accent_changed(self) -> None:
        if self.runtime_settings:
            self.runtime_settings.check_accent_changed()

    def _refresh_tray_tooltip(self) -> None:
        self.app.tray.refresh_tooltip(self.usage_stats.today_summary())

    def _update_privacy_badge(self) -> None:
        if not config.get_bool("show_privacy_badge", True):
            self.app.window.pill.set_privacy_badge(None)
            return
        if config.get_bool("enable_screen_context", False):
            self.app.window.pill.set_privacy_badge("OCR · lokal")
        elif config.get_bool("enable_selected_text_context", True):
            self.app.window.pill.set_privacy_badge("Kontext · lokal")
        elif not config.ollama_polishing:
            self.app.window.pill.set_privacy_badge("Offline · lokal")
        elif self.app.pipeline.polisher.ollama_available:
            self.app.window.pill.set_privacy_badge("Lokal · Ollama")
        else:
            self.app.window.pill.set_privacy_badge("Offline · lokal")

    def _on_pipeline_ready(self, success: bool):
        self._update_privacy_badge()
        self._refresh_tray_tooltip()
        if config.hotkey_enabled:
            self.app.hotkey.restart()
        if success:
            if needs_onboarding():
                QTimer.singleShot(400, self._show_welcome)
            else:
                self.app.toast.show_success("Bereit zum Diktieren")
        else:
            self.app.toast.show_error("Modell konnte nicht geladen werden")

    def _show_welcome(self) -> None:
        dlg = WelcomeDialog(self.app.window)
        dlg.exec()
        if dlg.skip_next_time():
            mark_onboarding_done()
        self.app.toast.show_success("Bereit zum Diktieren – drücke F8!")

    def _on_pipeline_state(self, state_name: str):
        self.app.state_machine.transition_by_name(state_name)
        self.app.tray.set_recording_state(self.app.state_machine.is_recording)
        if getattr(self.app, "mini_fab", None):
            self.app.mini_fab.set_recording(self.app.state_machine.is_recording)
        if state_name == "recording":
            self._last_live_text = ""
            self.app.toast.show_live_transcript("Höre zu…")
            session = self.app.pipeline.session_style
            if session != config.selected_style:
                self.app.toast.show_message(
                    f'App-Modus: {style_label(session)}',
                    duration_ms=1400,
                )
        elif state_name == "processing":
            ctx = self.app.pipeline.dictation_context.last_context
            if ctx and (
                config.get_bool("enable_screen_context", False)
                or config.get_bool("enable_selected_text_context", True)
            ):
                preview = ctx[:40] + ("…" if len(ctx) > 40 else "")
                self.app.window.pill.proc_label.setText("Bereinige mit Kontext…")
                print(f"[ScreenContext] Kontext für Polishing: {preview}")
            self.app.toast.settle_live_transcript(self._last_live_text or None)
            QTimer.singleShot(320, self.app.toast.end_live_mode)

    def _on_pipeline_result(self, raw: str, polished: str):
        self.current_raw = raw
        self.current_corrected = self.app.pipeline.replacer.apply(raw)
        self.current_polished = polished

        style_key = self.app.pipeline.session_style
        expanded = self.app.window.pill.expanded_widget
        expanded.set_active_style(style_key)
        display_text = polished or self.current_corrected or raw
        words = len(display_text.split())
        duration = self.app.pipeline.recording_duration
        wpm = int((words / duration) * 60) if duration > 0.5 else 0
        expanded.set_stats(words, wpm)

        self.history.add(raw, polished, words, wpm, style_key)
        self.usage_stats.record_dictation(words, wpm, duration)
        self._refresh_tray_tooltip()
        self._update_privacy_badge()

        self.app.window.pill.set_expanded(display_text)
        expanded.transcript_edit.setPlainText(display_text)
        self.app.state_machine.transition_by_name("expanded")

        def _after_polish_animation() -> None:
            if config.auto_copy:
                QApplication.clipboard().setText(polished)
            self.app.toast.show_success("Text bereinigt und in Zwischenablage kopiert!")

        self._polish_animator.play(raw, polished, on_finished=_after_polish_animation)

    def _on_pipeline_error(self, message: str):
        self.app.toast.show_error(message)
        self.app.state_machine.transition_to(IslandState.IDLE)

    def _on_audio_level(self, level: float):
        if self.app.state_machine.is_recording:
            self.app.window.pill.waveform.set_rms(level)

    def _on_partial_result(self, text: str):
        self._last_live_text = text
        self.app.toast.show_live_transcript(text)

    def _on_style_changed(self, style_key: str):
        self._polish_animator.cancel()
        label = style_label(style_key)

        config.selected_style = style_key
        config.save()
        self.app.tray.update_menu_states()

        source = self._source_text()
        if not source:
            self.app.window.pill.expanded_widget.set_active_style(style_key)
            self.app.toast.show_message(f'Stil „{label}" für nächstes Diktat gewählt', duration_ms=1500)
            return

        new_text = self.app.pipeline.polisher.polish_instant(source, style=style_key)
        self.current_polished = new_text
        self._apply_text_to_ui(new_text, style_key)
        self.app.toast.show_success(f'Stil „{label}" angewendet!')
        print(f"[AppController] Stil '{style_key}' → {len(new_text)} Zeichen")

    def _on_internal_state_changed(self, prev_state, new_state):
        if new_state == IslandState.EXPANDED:
            text = self.current_polished or self.current_corrected or self.current_raw
            self.app.window.pill.set_expanded(text)
            if text and not self._polish_animator.is_running():
                self._apply_text_to_ui(text, self.app.pipeline.session_style)

    def _open_history(self):
        if self._history_dialog is None:
            self._history_dialog = HistoryDialog(self.history, self.app.window)
        self._history_dialog._refresh_list()
        self._history_dialog.show()
        self._history_dialog.raise_()
        self._history_dialog.activateWindow()

    def _open_url_dialog(self) -> None:
        url = UrlTranscribeDialog.paste_from_clipboard(self.app.window)
        if url:
            self._transcribe_media_url(url)

    def _transcribe_media_url(self, url: str) -> None:
        if self.app.pipeline.is_recording:
            self.app.toast.show_error("Beende zuerst die laufende Aufnahme.")
            return
        self.app.toast.show_message("Lade Audio von URL…", duration_ms=2000)
        self.app.pipeline.transcribe_media_url(url)

    def _close_expanded(self):
        """Schließt Expanded und setzt die Island an die Startposition (oben zentriert)."""
        self.app.window.reset_to_start_position()
        self.app.window.prepare_after_expanded_dismiss()
        self.app.state_machine.transition_to(IslandState.IDLE)

    def _copy_expanded_text(self):
        text = self.app.window.pill.expanded_widget.transcript_edit.toPlainText()
        QApplication.clipboard().setText(text)
        self.app.toast.show_success("In Zwischenablage kopiert!")

    def _undo_last_sentence(self):
        expanded = self.app.window.pill.expanded_widget
        if not expanded.undo_last_sentence():
            self.app.toast.show_message("Kein Satz zum Entfernen", duration_ms=1200)
            return
        text = expanded.transcript_edit.toPlainText()
        self.current_polished = text
        words = len(text.split()) if text else 0
        duration = self.app.pipeline.recording_duration
        wpm = int((words / duration) * 60) if duration > 0.5 and words else 0
        expanded.set_stats(words, wpm)
        if text and config.auto_copy:
            QApplication.clipboard().setText(text)
        self.app.toast.show_message("Letzter Satz entfernt", duration_ms=1200)

    def _toggle_island_visibility(self):
        if self.app.window.windowOpacity() > 0.0:
            self.app.window._fade_to(0.0)
        else:
            self.app.window._fade_to(1.0)
            self.app.window.is_hovered = True

    def shutdown(self):
        try:
            from src.services import update_logger
            update_logger.write("AppController.shutdown() gestartet")
        except Exception:
            pass
        self.app.hotkey.stop()
        if self.app.pipeline.is_recording:
            self.app.pipeline.stop_recording()
        if getattr(self.app, "mini_fab", None):
            self.app.mini_fab.close()
        self.app.window.close()
        self.app.toast.close()
        self.app.tray.hide()
        self.app.app.quit()
        try:
            from src.services import update_logger
            update_logger.write("AppController.shutdown() → app.quit() aufgerufen")
        except Exception:
            pass

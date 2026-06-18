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
from src.utils import autostart
from src.services.config_service import config
from src.services.style_definitions import style_label
from src.services.dictation_history import DictationHistoryService
from src.services.usage_stats import UsageStatsService
from src.services.runtime_settings_handler import RuntimeSettingsHandler
from src.services.update_controller import UpdateController
from src.services.recording_sound_service import RecordingSoundService
from src.services.correction_learning_service import CorrectionLearningService
from src.services.app_mode_service import resolve_app_mode_match, get_foreground_hwnd_for_app_mode, is_developer_context
from src.services.text_postprocessor import apply_postprocessing
from src.utils.diff_helper import texts_differ
from src.ui.island_tooltips import refresh_island_tooltips


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
        self.recording_sounds = RecordingSoundService(self)
        self.correction_learning = CorrectionLearningService(app_instance.pipeline.replacer)
        self._active_app_mode_key: str | None = None
        self._active_app_mode_style: str | None = None
        self._last_injected_text: str = ""
        self._last_inject_hwnd: int | None = None
        self._correction_generation = 0

    def connect_all(self):
        """Verknüpft alle Signale und Callbacks."""
        autostart.sync_from_installer()
        qc = Qt.ConnectionType.QueuedConnection
        self.app.signals.ready.connect(self._on_pipeline_ready, qc)
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

        import threading

        _main = threading.main_thread()

        def _is_main_thread() -> bool:
            return threading.current_thread() is _main

        def _invoke_main(fn) -> None:
            QTimer.singleShot(0, fn)

        def _schedule_delayed(ms: int, fn) -> None:
            QTimer.singleShot(ms, fn)

        self.app.state_machine.configure_ui_thread(
            _is_main_thread, _invoke_main, _schedule_delayed
        )

        self._ui_pump = QTimer(self)
        self._ui_pump.timeout.connect(self._pump_background_ui)
        self._ui_pump.start(16)

        self._app_mode_timer = QTimer(self)
        self._app_mode_timer.timeout.connect(self._poll_app_mode)
        self._app_mode_timer.start(900)

        self.app.hotkey.set_start_callback(self.app.pipeline.start_recording)
        self.app.hotkey.set_stop_callback(self.app.pipeline.stop_recording)
        self.app.hotkey.set_translate_de_callback(lambda: self._start_dictation_translate("de"))
        self.app.hotkey.set_translate_en_callback(lambda: self._start_dictation_translate("en"))
        self.app.hotkey.set_mute_toggle_callback(
            lambda: self._schedule_ui(self._toggle_mute)
        )
        self.app.hotkey.set_device_cycle_callback(
            lambda: self._schedule_ui(self._cycle_device)
        )
        self.app.hotkey.set_rewrite_callback(self._trigger_selected_text_rewrite)
        self.app.hotkey.set_escape_callback(self._dismiss_basics)
        self.app.hotkey.set_basics_nav_callback(self._on_basics_nav_key)
        self.app.hotkey.set_open_settings_callback(self.app.window._on_open_settings)

        self.app.window.settings_changed_callback = self.apply_runtime_setting
        self.app.window.open_history_callback = self._open_history
        self.app.window.request_toggle_recording_callback = self.app.pipeline.toggle
        self.app.window.request_transcribe_url_callback = self._open_url_dialog
        self.app.window.request_transcribe_media_url_callback = self._transcribe_media_url
        self.app.window.request_style_change_callback = self._on_style_changed
        self.app.window.history_service = self.history
        self.app.window.usage_stats = self.usage_stats
        self.app.window.recording_sound_preview_callback = self.recording_sounds.preview
        self.app.window.show_settings_toast = self._show_settings_toast
        self.app.window.mute_toggle_callback = self._toggle_mute
        self.app.window.device_cycle_callback = self._cycle_device
        self.app.window.hub_history_callback = self._open_history
        self.app.window.hub_transcript_callback = self._open_hub_transcript
        self.app.window.hub_rewrite_callback = self._trigger_selected_text_rewrite
        self.runtime_settings = RuntimeSettingsHandler(self.app)

        self._refresh_tray_tooltip()
        self._update_privacy_badge()
        self._sync_audio_ui()
        refresh_island_tooltips(self.app.window)
        self.updates.schedule_startup_check()
        self._poll_app_mode()

    def _poll_app_mode(self) -> None:
        """Aktualisiert den sichtbaren App-Modus-Badge im Idle-Zustand."""
        sm = self.app.state_machine
        if not (sm.is_idle or sm.is_basics):
            return
        if not config.get_bool("enable_app_modes", True):
            self._set_app_mode_badge(None, None)
            return

        match = resolve_app_mode_match(get_foreground_hwnd_for_app_mode())
        if match:
            if (
                match.app_key != self._active_app_mode_key
                or match.style != self._active_app_mode_style
            ):
                self._active_app_mode_key = match.app_key
                self._active_app_mode_style = match.style
                self._set_app_mode_badge(match.app_key, style_label(match.style))
        else:
            if self._active_app_mode_key is not None:
                self._active_app_mode_key = None
                self._active_app_mode_style = None
                self._set_app_mode_badge(None, None)

    def _set_app_mode_badge(self, app_key: str | None, label: str | None) -> None:
        self.app.window.pill.set_app_mode_badge(app_key, label)

    def _show_app_mode_on_recording(self) -> None:
        session = self.app.pipeline.session_style
        match = resolve_app_mode_match(self.app.pipeline._target_hwnd)
        if match:
            self._set_app_mode_badge(match.app_key, style_label(match.style))
            self.app.window.pill.expanded_widget.set_app_mode_hint(
                match.app_key, match.style
            )
        elif session != config.selected_style:
            self._set_app_mode_badge(None, style_label(session))
        else:
            self._set_app_mode_badge(None, None)

    def _schedule_correction_learning(
        self, injected_text: str, target_hwnd: int | None
    ) -> None:
        if not config.get_bool("enable_correction_learning", True):
            return
        if not config.get_bool("auto_inject_text", True) or not target_hwnd:
            return
        if not injected_text.strip():
            return

        self._last_injected_text = injected_text
        self._last_inject_hwnd = target_hwnd
        self._correction_generation += 1
        generation = self._correction_generation
        delay_ms = config.get_int("correction_learning_delay_s", 5) * 1000
        QTimer.singleShot(delay_ms, lambda: self._check_post_inject_edit(generation))

    def _check_post_inject_edit(self, generation: int) -> None:
        if generation != self._correction_generation:
            return
        if self.app.state_machine.is_recording:
            return

        injected = self._last_injected_text
        hwnd = self._last_inject_hwnd
        if not injected or not hwnd:
            return

        import threading

        def _worker() -> None:
            try:
                edited = self.app.pipeline.clipboard.capture_all_text(hwnd)
            except Exception:
                return
            if not edited or edited.strip() == injected.strip():
                return
            QTimer.singleShot(
                0,
                lambda: self._apply_correction_learning(injected, edited, generation),
            )

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_correction_learning(
        self, injected: str, edited: str, generation: int
    ) -> None:
        if generation != self._correction_generation:
            return

        def _notify(applied) -> None:
            if not applied:
                return
            parts = [
                f'„{c.source}" -> „{c.target}"'
                for c in applied[:2]
            ]
            suffix = f" (+{len(applied) - 2})" if len(applied) > 2 else ""
            self.app.toast.show_message(
                f"Gelernt: {', '.join(parts)}{suffix}",
                duration_ms=4500,
            )

        applied = self.correction_learning.learn_from_edit(
            injected, edited, on_learned=_notify
        )
        if applied:
            print(f"[CorrectionLearning] {len(applied)} Eintrag/Einträge gespeichert")

    def _schedule_ui(self, fn) -> None:
        """Führt einen Callback auf dem Qt-Hauptthread aus (Hotkeys laufen in pynput-Threads)."""
        QTimer.singleShot(0, fn)

    def _pump_background_ui(self) -> None:
        """Holt Pipeline-Events aus Hintergrund-Threads auf den UI-Thread."""
        level = self.app.pipeline.audio.drain_levels()
        if level is not None:
            self._on_audio_level(level)

        partial = self.app.pipeline.drain_partials()
        if partial:
            self._on_partial_result(partial)

        for state in self.app.pipeline.drain_state_events():
            self._on_pipeline_state(state)

        for message in self.app.pipeline.drain_error_events():
            self._on_pipeline_error(message)

        for raw, polished in self.app.pipeline.drain_result_events():
            self._on_pipeline_result(raw, polished)

        for raw, instant, deep in self.app.pipeline.drain_upgrade_events():
            self._on_pipeline_upgrade(raw, instant, deep)

    def _source_text(self) -> str:
        """Basis-Text für Re-Polishing – Roh- oder korrigierter Text."""
        if self.current_corrected.strip():
            return self.current_corrected
        if self.current_raw.strip():
            return self.app.pipeline.replacer.apply(self.current_raw)
        expanded = self.app.window.pill.expanded_widget
        return expanded.get_polished_text().strip() or expanded.transcript_edit.toPlainText().strip()

    def _apply_text_to_ui(self, text: str, style_key: str, raw: str = "") -> None:
        """Schreibt Ergebnis sofort ins Expanded-Widget mit Diff-Ansicht."""
        self._polish_animator.cancel()
        expanded = self.app.window.pill.expanded_widget
        # Setze beide Texte für die Diff-Ansicht
        raw_text = raw or self.current_raw or self.current_corrected or ""
        expanded.set_texts(raw_text, text)
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

    def _show_settings_toast(self, message: str, success: bool) -> None:
        if success:
            self.app.toast.show_success(message)
        else:
            self.app.toast.show_error(message)
        self.app.pipeline.polisher.check_ollama_status()
        self._update_privacy_badge()

    def _start_dictation_translate(self, lang: str) -> None:
        """Startet Diktat mit Übersetzungsmodus (F6=DE, F7=EN)."""
        if self.app.pipeline.is_recording:
            return
        label = "Deutsch" if lang == "de" else "Englisch"
        if self.app.pipeline.start_recording(translate_mode=lang):
            self.app.toast.show_message(
                f"Diktat mit Übersetzung ({label})…",
                duration_ms=1600,
            )

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
        was_recording = self.app.state_machine.is_recording
        if state_name == "recording":
            self.recording_sounds.play_start()
        elif state_name == "processing" and was_recording:
            self.recording_sounds.play_stop()

        self.app.state_machine.transition_by_name(state_name)
        self.app.tray.set_recording_state(self.app.state_machine.is_recording)
        if state_name == "recording":
            self._last_live_text = ""
            self.app.toast.show_live_transcript("Höre zu…")
            self._show_app_mode_on_recording()
            if is_developer_context(self.app.pipeline._target_hwnd):
                self.app.toast.show_message(
                    "Developer Mode aktiv (IDE)",
                    duration_ms=1400,
                )
            session = self.app.pipeline.session_style
            if session != config.selected_style:
                match = resolve_app_mode_match(self.app.pipeline._target_hwnd)
                if match:
                    self.app.toast.show_message(
                        f'App-Modus: {match.app_key} → {style_label(session)}',
                        duration_ms=1600,
                    )
        elif state_name == "processing":
            if getattr(self.app.pipeline, "_rewrite_mode", False):
                self.app.window.pill.proc_widget.set_message("Umschreiben...")
            ctx = self.app.pipeline.dictation_context.last_context
            if ctx and (
                config.get_bool("enable_screen_context", False)
                or config.get_bool("enable_selected_text_context", True)
            ):
                preview = ctx[:40] + ("…" if len(ctx) > 40 else "")
                self.app.window.pill.proc_widget.set_message("Bereinige mit Kontext…")
                print(f"[ScreenContext] Kontext für Polishing: {preview}")
            self.app.toast.settle_live_transcript(self._last_live_text or None)
            QTimer.singleShot(320, self.app.toast.end_live_mode)

    def _on_pipeline_result(self, raw: str, polished: str):
        dlg = self.app.window._settings_dialog
        if dlg and hasattr(dlg, "_url_panel"):
            dlg._url_panel.set_transcribing(False)

        self.current_raw = raw
        self.current_corrected = self.app.pipeline.replacer.apply(raw)
        self.current_polished = polished

        style_key = self.app.pipeline.session_style
        expanded = self.app.window.pill.expanded_widget
        expanded.set_active_style(style_key)
        display_text = polished or self.current_corrected or raw
        raw_for_diff = self.current_corrected or raw
        words = len(display_text.split())
        duration = self.app.pipeline.recording_duration
        wpm = int((words / duration) * 60) if duration > 0.5 else 0
        expanded.set_stats(words, wpm)

        match = resolve_app_mode_match(self.app.pipeline._target_hwnd)
        if match:
            expanded.set_app_mode_hint(match.app_key, match.style)
        else:
            expanded.set_app_mode_hint(None, None)

        self.history.add(
            raw,
            polished,
            words,
            wpm,
            style_key,
            audio_path=self.app.pipeline.last_audio_path,
            live_transcript=self._last_live_text,
            duration_s=duration,
        )
        self.usage_stats.record_dictation(
            words, wpm, duration, app_key=match.app_key if match else None
        )
        self._refresh_tray_tooltip()
        self._update_privacy_badge()

        expanded.set_texts(raw_for_diff, display_text)
        has_diff = texts_differ(raw_for_diff, display_text)

        if config.get_bool("auto_inject_text", True):
            self._schedule_correction_learning(
                display_text, self.app.pipeline._target_hwnd
            )

        if config.get_bool("auto_show_diff_on_result", True) and has_diff:
            expanded.show_diff_view()
            self.app.window.pill.show_success(display_text, raw=raw_for_diff)
            self.app.state_machine.transition_by_name("expanded")
        else:
            self.app.window.pill.show_success(display_text, raw=raw_for_diff)
            self.app.state_machine.transition_by_name("success")

        if config.auto_copy:
            QApplication.clipboard().setText(polished)
            if not has_diff:
                self.app.toast.show_success("Text bereinigt und in Zwischenablage kopiert!")
            else:
                self.app.toast.show_success("Diff geöffnet – Vorher/Nachher vergleichen")

    def _on_pipeline_upgrade(self, raw: str, instant: str, deep: str) -> None:
        """Hybrid-Pipeline: Ollama-Verfeinerung nach Instant-Ergebnis."""
        if not deep or deep.strip() == instant.strip():
            return

        self.current_polished = deep
        style_key = self.app.pipeline.session_style
        raw_for_diff = self.current_corrected or raw
        expanded = self.app.window.pill.expanded_widget
        expanded.set_texts(instant, deep)
        expanded.show_diff_view()
        expanded.set_polish_status("Ollama-Verfeinerung")

        if self.app.state_machine.is_expanded or self.app.state_machine.is_success:
            self.app.toast.show_message(
                "Verfeinert (Ollama) – Diff aktualisiert",
                duration_ms=3200,
            )

        if config.auto_copy:
            QApplication.clipboard().setText(deep)

        words = len(deep.split())
        duration = self.app.pipeline.recording_duration
        wpm = int((words / duration) * 60) if duration > 0.5 else 0
        expanded.set_stats(words, wpm)
        print(f"[Hybrid] Deep-Polish: {len(instant)} → {len(deep)} Zeichen")

    def _on_pipeline_error(self, message: str):
        dlg = self.app.window._settings_dialog
        if dlg and hasattr(dlg, "_url_panel"):
            dlg._url_panel.set_transcribing(False)

        self.app.toast.show_error(message)
        self.app.state_machine.transition_to(IslandState.IDLE)

    def _on_audio_level(self, level: float):
        if self.app.state_machine.is_recording:
            rec = self.app.window.pill.rec_widget
            rec.waveform.set_rms(level)
            rec.set_level(level)

    def _dismiss_basics(self):
        if self.app.state_machine.is_basics:
            print("[Basics] Escape – schließe Basics-Modus")
            self.app.state_machine.transition_to(IslandState.IDLE)

    def _on_basics_nav_key(self, key_name: str):
        """Tastaturnavigation im Hub-Modus."""
        if not self.app.state_machine.is_basics:
            return
        basics = self.app.window.pill.basics_widget
        if key_name == "left":
            basics.btn_history.click()
        elif key_name == "right":
            basics.btn_transcript.click()
        elif key_name == "down":
            basics.btn_rewrite.click()

    def _open_hub_transcript(self):
        """Öffnet das letzte Transkript im Expanded-Modus."""
        self.app.state_machine.transition_by_name("expanded")

    def _trigger_selected_text_rewrite(self):
        self.app.pipeline.rewrite_selected_text()

    def _on_partial_result(self, text: str):
        self._last_live_text = text
        self.app.toast.show_live_transcript(text)
        expanded = self.app.window.pill.expanded_widget
        if self.app.state_machine.is_expanded and expanded._live_mode:
            expanded.set_live_text(text)

    def _toggle_mute(self):
        """Schaltet die Mikrofon-Stummschaltung um und aktualisiert das UI."""
        audio = self.app.pipeline.audio
        is_muted = audio.toggle_mute()
        self._sync_audio_ui()
        label = "Mikrofon stumm" if is_muted else "Mikrofon aktiv"
        self.app.toast.show_message(label, duration_ms=1200)

    def _cycle_device(self):
        """Wechselt zyklisch durch verfügbare Aufnahmegeräte."""
        if self.app.pipeline.audio.is_recording:
            from src.services import dictation_logger as dlog
            msg = "Wechsel waehrend der Aufnahme ignoriert"
            print(f"[Audio] {msg}")
            dlog.write(msg)
            self.app.toast.show_message("Gerätewechsel nur im Idle", duration_ms=1500)
            return
        next_name = self.app.pipeline.audio.next_input_device()
        if not next_name:
            self.app.toast.show_error("Keine Aufnahmegeräte gefunden")
            return
        print(f"[Overlay] Device gewechselt: {next_name}")
        self._sync_audio_ui()
        self.app.window.pill.basics_widget.set_device_name(next_name)
        self.app.toast.show_message(f"🎤 {next_name}", duration_ms=2500)

    def _sync_audio_ui(self) -> None:
        """Synchronisiert Mute-Status und Gerätename in Island-Widgets."""
        from src.services.audio_devices import input_device_display_name

        device_name = input_device_display_name(
            config.get_str("recording_device", "default")
        )
        is_muted = self.app.pipeline.audio.is_muted
        self.app.window.pill.basics_widget.set_mute_state(is_muted)
        self.app.window.pill.basics_widget.set_active_device(device_name)
        self.app.window.pill.idle_widget.set_audio_hint(device_name, is_muted)
        refresh_island_tooltips(self.app.window)

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
        new_text = apply_postprocessing(
            new_text,
            style_key,
            hwnd=self.app.pipeline._target_hwnd,
        )
        self.current_polished = new_text
        self._apply_text_to_ui(new_text, style_key)
        self.app.toast.show_success(f'Stil „{label}" angewendet!')
        print(f"[AppController] Stil '{style_key}' → {len(new_text)} Zeichen")

    def _on_internal_state_changed(self, prev_state, new_state):
        if new_state == IslandState.EXPANDED:
            expanded = self.app.window.pill.expanded_widget
            if self.app.pipeline.is_recording or prev_state == IslandState.RECORDING:
                if self._last_live_text:
                    expanded.set_live_text(self._last_live_text)
                return
            polished = self.current_polished or self.current_corrected or self.current_raw
            raw = self.current_corrected or self.current_raw
            self.app.window.pill.set_expanded(polished)
            expanded.set_texts(raw, polished)
            if texts_differ(raw, polished):
                expanded.show_diff_view()
            elif polished and not self._polish_animator.is_running():
                self._apply_text_to_ui(
                    polished, self.app.pipeline.session_style, raw
                )
        elif new_state == IslandState.IDLE:
            self._poll_app_mode()
            self.app.window.pill.expanded_widget.set_app_mode_hint(None, None)
            self._set_app_mode_badge(None, None)

    def _open_history(self):
        if self._history_dialog is None:
            self._history_dialog = HistoryDialog(self.history, self.app.window)
        self._history_dialog._refresh_list()
        self._history_dialog.show()
        self._history_dialog.raise_()
        self._history_dialog.activateWindow()

    def _open_url_dialog(self) -> None:
        self.app.window._on_open_settings()
        dlg = self.app.window._settings_dialog
        if dlg:
            dlg.show_url_transcribe()
            dlg._url_panel.prefill_from_clipboard()

    def _transcribe_media_url(self, url: str) -> None:
        if self.app.pipeline.is_recording:
            self.app.toast.show_error("Beende zuerst die laufende Aufnahme.")
            return
        self.app.toast.show_message("Lade Audio von URL…", duration_ms=2000)
        self.app.pipeline.transcribe_media_url(url)

    def _close_expanded(self):
        """Schließt Expanded; bei laufender Aufnahme zurück zur Recording-Pill."""
        if self.app.pipeline.is_recording:
            self.app.window.pill.expanded_widget.exit_live_mode()
            self.app.state_machine.transition_to(IslandState.RECORDING)
            return
        self.app.window.reset_to_start_position()
        self.app.window.prepare_after_expanded_dismiss()
        self.app.state_machine.transition_to(IslandState.IDLE)

    def _copy_expanded_text(self):
        text = self.app.window.pill.expanded_widget.get_polished_text()
        if not text:
            text = self.app.window.pill.expanded_widget.transcript_edit.toPlainText()
        QApplication.clipboard().setText(text)
        self.app.toast.show_success("In Zwischenablage kopiert!")

    def _undo_last_sentence(self):
        expanded = self.app.window.pill.expanded_widget
        if not expanded.undo_last_sentence():
            self.app.toast.show_message("Kein Satz zum Entfernen", duration_ms=1200)
            return
        text = expanded.get_polished_text()
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
            from src.services import dictation_logger as dlog
            from src.services import update_logger

            dlog.write("AppController.shutdown() gestartet", sync=True)
            update_logger.write("AppController.shutdown() gestartet")
        except Exception:
            pass
        self._ui_pump.stop()
        self._app_mode_timer.stop()
        if hasattr(self.app.window, "presence_controller"):
            self.app.window.presence_controller.hover_timer.stop()
        pill = self.app.window.pill
        if hasattr(pill, "presence_bar"):
            pill.presence_bar.stop()
        if hasattr(pill, "rec_widget"):
            wf = getattr(pill.rec_widget, "waveform", None)
            if wf is not None and hasattr(wf, "_timer"):
                wf._timer.stop()
        self.app.hotkey.stop()
        if self.app.pipeline.is_recording:
            self.app.pipeline.stop_recording()
        self.app.window.close()
        self.app.toast.close()
        self.app.tray.hide()
        self.app.app.quit()
        try:
            from src.services import dictation_logger as dlog
            from src.services import update_logger

            dlog.write("App sauber beendet → app.quit()", sync=True)
            update_logger.write("AppController.shutdown() → app.quit() aufgerufen")
        except Exception:
            pass

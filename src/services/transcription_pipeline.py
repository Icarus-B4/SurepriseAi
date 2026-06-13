"""
transcription_pipeline.py
Orchestriert den Ablauf: Aufnahme -> Filter -> Polishing -> Clipboard.
Nutzt PipelineWorker für Hintergrundaufgaben zur Einhaltung der 200-Zeilen-Regel.
"""

import threading
import time
from typing import Callable, Optional
import numpy as np
import wave

try:
    import ctypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from .audio_service import AudioService
from .transcription_service import TranscriptionService
from .polishing_service import PolishingService
from .clipboard_service import ClipboardService
from .word_replacement_service import WordReplacementService
from .pipeline_worker import PipelineWorker
from .config_service import config
from .app_mode_service import resolve_style_for_hwnd
from .dictation_context_service import DictationContextService
from . import dictation_logger as dlog
from src.utils.app_paths import user_data_dir

# Live-Transkription: niedrige Latenz durch kurzes Polling und kleines Audiopuffer
LIVE_POLL_INTERVAL_S = 0.45
LIVE_MIN_SAMPLES = 3200       # ~0,2 s bei 16 kHz
LIVE_MAX_SAMPLES = 16000 * 12  # Sliding Window: max. 12 s für schnelle Inferenz


class TranscriptionPipeline:
    """
    Verbindet Services zur Diktat-Pipeline.
    Startet Live-Transkriptions-Threads und misst Aufnahmedauern.
    """

    def __init__(self) -> None:
        self.audio       = AudioService()
        self.transcriber = TranscriptionService()
        self.polisher    = PolishingService()
        self.clipboard   = ClipboardService()
        self.replacer    = WordReplacementService()
        self.dictation_context = DictationContextService()

        # UI-Callbacks
        self._on_state_change: Optional[Callable[[str], None]] = None
        self._on_result:       Optional[Callable[[str, str], None]] = None
        self._on_error:        Optional[Callable[[str], None]] = None
        self._on_level:        Optional[Callable[[float], None]] = None
        self._on_partial:      Optional[Callable[[str], None]] = None

        self._initialized = False
        self._target_hwnd: Optional[int] = None
        self._session_style: Optional[str] = None
        
        # Live-Transkription
        self._partial_thread: Optional[threading.Thread] = None
        self._stop_partial_thread = threading.Event()
        self.recording_start_time: float = 0.0
        self.recording_duration: float = 0.0
        self._last_partial_text: str = ""
        self.last_audio_path: Optional[str] = None

    def set_state_callback(self, cb: Callable[[str], None]) -> None:
        self._on_state_change = cb

    def set_result_callback(self, cb: Callable[[str, str], None]) -> None:
        self._on_result = cb

    def set_error_callback(self, cb: Callable[[str], None]) -> None:
        self._on_error = cb

    def set_level_callback(self, cb: Callable[[float], None]) -> None:
        self._on_level = cb
        self.audio.set_level_callback(cb)

    def set_partial_callback(self, cb: Callable[[str], None]) -> None:
        """Callback für Live-Zwischenergebnisse."""
        self._on_partial = cb

    def initialize(self) -> bool:
        print("[Pipeline] Initialisierung...")
        ok = self.transcriber.initialize()
        self.polisher.check_ollama_status()
        self._initialized = ok
        return ok

    def initialize_async(self, on_ready: Optional[Callable[[bool], None]] = None) -> None:
        def _worker():
            res = self.initialize()
            if on_ready: on_ready(res)
        threading.Thread(target=_worker, daemon=True).start()

    def start_recording(self) -> bool:
        """Startet die Aufnahme und den Live-Transkriptionstypist."""
        if self.audio.is_recording:
            return True

        self._capture_target_window()
        device = config.get_str("recording_device")
        success = self.audio.start_recording(device if device != "default" else None)

        if success:
            dlog.begin_dictation()
            dlog.log_kv(
                "Aufnahme-Start",
                device=device or "default",
                target_hwnd=self._target_hwnd,
            )
            self.recording_start_time = time.time()
            self.recording_duration = 0.0
            self._last_partial_text = ""
            self.last_audio_path = None
            resolved = resolve_style_for_hwnd(self._target_hwnd)
            self._session_style = resolved or config.selected_style
            self.dictation_context.capture_async(self._target_hwnd)
            self._emit_state("recording")
            
            # Live-Transkriptions-Thread starten
            self._stop_partial_thread.clear()
            self._partial_thread = threading.Thread(target=self._live_transcription_worker, daemon=True)
            self._partial_thread.start()
        else:
            dlog.write("Aufnahme-Start FEHLGESCHLAGEN: Mikrofon nicht geoeffnet")
            self._emit_error("Mikrofon konnte nicht geöffnet werden.")
        return success

    def stop_recording(self) -> None:
        """Stoppt Aufnahme, beendet Live-Transkription und verarbeitet das Audio."""
        self._stop_partial_thread.set()
        if self._partial_thread and self._partial_thread.is_alive():
            self._partial_thread.join(timeout=3.0)
        audio_data = self.audio.stop_recording()
        dlog.log_audio("Stop-Audio", audio_data)

        if audio_data is None or len(audio_data) < 1600:
            n = 0 if audio_data is None else len(audio_data)
            dlog.end_dictation(f"abgebrochen – zu kurz ({n} samples, min 1600)")
            self._emit_error("Aufnahme zu kurz. Bitte etwas länger sprechen.")
            self._emit_state("idle")
            return

        self.recording_duration = time.time() - self.recording_start_time
        dlog.log_kv("Aufnahme-Stop", dauer_s=round(self.recording_duration, 2))
        self.last_audio_path = self._save_recording_audio(audio_data)
        self._emit_state("processing")

        context = self.dictation_context.get_context(
            timeout_s=config.get_int("screen_context_timeout_s", 3)
        )

        worker = PipelineWorker(
            self.transcriber, self.replacer, self.polisher, self.clipboard,
            self._on_result, self._emit_state, self._emit_error
        )
        worker.process_audio_async(
            audio_data,
            self._target_hwnd,
            style=self._session_style,
            screen_context=context,
            live_fallback_text=self._last_partial_text or None,
        )

    def _save_recording_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Speichert das Diktat als WAV für Verlauf/Playback."""
        try:
            audio_dir = user_data_dir() / "recordings"
            audio_dir.mkdir(parents=True, exist_ok=True)
            path = audio_dir / f"diktat_{time.strftime('%Y%m%d_%H%M%S')}.wav"
            samples = np.asarray(audio_data, dtype=np.float32).flatten()
            samples = np.clip(samples, -1.0, 1.0)
            pcm = (samples * 32767.0).astype(np.int16)
            with wave.open(str(path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm.tobytes())
            dlog.write(f"Audio gespeichert: {path}")
            return str(path)
        except Exception:
            dlog.write_exception("Audio speichern")
            return None

    def toggle(self) -> None:
        if self.audio.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def transcribe_audio_file(self, file_path: str) -> None:
        """Datei-Transkription im Hintergrund starten."""
        self._start_file_worker(file_path)

    def transcribe_media_url(self, url: str) -> None:
        """Lädt Audio von einer URL (yt-dlp) und transkribiert es."""
        threading.Thread(target=self._media_url_worker, args=(url,), daemon=True).start()

    def _media_url_worker(self, url: str) -> None:
        from .media_url_service import download_media_audio

        self._emit_state("processing")
        path, err = download_media_audio(url)
        if err or not path:
            self._emit_error(err or "Download fehlgeschlagen.")
            self._emit_state("idle")
            return
        self._start_file_worker(str(path))

    def _start_file_worker(self, file_path: str) -> None:
        """Gemeinsamer Einstieg für Datei- und URL-Transkription."""
        self._capture_target_window()
        self.dictation_context.capture_async(self._target_hwnd)
        worker = PipelineWorker(
            self.transcriber, self.replacer, self.polisher, self.clipboard,
            self._on_result, self._emit_state, self._emit_error
        )
        context = self.dictation_context.get_context(timeout_s=2.0)
        worker.process_file_async(
            file_path,
            style=config.selected_style,
            screen_context=context,
        )

    def _live_transcription_worker(self) -> None:
        """Periodische Zwischen-Transkription im Hintergrund."""
        last_text = ""
        self._partial_running = False
        while not self._stop_partial_thread.wait(LIVE_POLL_INTERVAL_S):
            if not self.audio.is_recording:
                break
            if self._partial_running:
                continue
            audio_data = self.audio.get_accumulated_audio()
            if audio_data is None or len(audio_data) < LIVE_MIN_SAMPLES:
                continue

            # Sliding Window: nur die letzten N Sekunden transkribieren
            if len(audio_data) > LIVE_MAX_SAMPLES:
                audio_data = audio_data[-LIVE_MAX_SAMPLES:]

            try:
                self._partial_running = True
                text = self.transcriber.transcribe_partial(audio_data)
                if text and text.strip() and text != last_text:
                    last_text = text
                    corrected = self.replacer.apply(text)
                    self._last_partial_text = corrected
                    dlog.write(f"Live-Partial: '{corrected[:60]}'")
                    if self._on_partial:
                        self._on_partial(corrected)
            except Exception as e:
                dlog.write_exception("Live-Transkript")
                print(f"[Pipeline] Fehler Live-Transkript: {e}")
            finally:
                self._partial_running = False

    def _capture_target_window(self):
        if not WIN32_AVAILABLE:
            self._target_hwnd = None
            return
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            import os
            my_pid = os.getpid()
            target_pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_pid))
            self._target_hwnd = None if target_pid.value == my_pid else hwnd
        except Exception:
            self._target_hwnd = None

    def _emit_state(self, state: str) -> None:
        if self._on_state_change: self._on_state_change(state)

    def _emit_error(self, msg: str) -> None:
        if self._on_error: self._on_error(msg)

    @property
    def session_style(self) -> str:
        return self._session_style or config.selected_style

    @property
    def is_recording(self) -> bool:
        return self.audio.is_recording

    @property
    def is_ready(self) -> bool:
        return self._initialized

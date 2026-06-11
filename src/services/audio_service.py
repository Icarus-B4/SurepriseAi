"""
audio_service.py
Non-blocking Audioaufnahme via sounddevice.
Speichert aufgenommene Chunks im Speicher für spätere Transkription.
"""

import threading
import queue
import time
import numpy as np
from typing import Callable, Optional

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

# ── Aufnahme-Parameter ────────────────────────────────────────────────────────
SAMPLE_RATE   = 16000   # Hz – Parakeet und Whisper erwarten 16kHz
CHANNELS      = 1       # Mono
DTYPE         = "float32"
BLOCK_SIZE    = 1024    # Samples pro Block (~64ms bei 16kHz)


class AudioService:
    """
    Verwaltet die Mikrofonaufnahme in einem separaten Thread.
    Stellt aufgezeichnete Audio-Daten als numpy-Array bereit.
    """

    def __init__(self) -> None:
        self._recording: bool = False
        self._chunks: list[np.ndarray] = []
        self._stream: Optional[object] = None
        self._lock = threading.Lock()

        # Callbacks
        self._on_level_change: Optional[Callable[[float], None]] = None
        self._on_recording_start: Optional[Callable[[], None]] = None
        self._on_recording_stop: Optional[Callable[[], None]] = None

        # Audio-Level-Queue für Wellenform
        self._level_queue: queue.Queue[float] = queue.Queue(maxsize=32)

    # ── Callbacks registrieren ────────────────────────────────────────────────

    def set_level_callback(self, cb: Callable[[float], None]) -> None:
        self._on_level_change = cb

    def set_start_callback(self, cb: Callable[[], None]) -> None:
        self._on_recording_start = cb

    def set_stop_callback(self, cb: Callable[[], None]) -> None:
        self._on_recording_stop = cb

    # ── Aufnahme-Steuerung ────────────────────────────────────────────────────

    def start_recording(self, device: Optional[str] = None) -> bool:
        """
        Startet die Aufnahme vom angegebenen Gerät.

        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not SOUNDDEVICE_AVAILABLE:
            print("[Audio] sounddevice nicht verfügbar!")
            return False

        if self._recording:
            return True  # Bereits aktiv

        with self._lock:
            self._chunks.clear()
            self._recording = True

        try:
            device_id = None if (device in (None, "default")) else device

            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=BLOCK_SIZE,
                device=device_id,
                callback=self._audio_callback,
            )
            self._stream.start()

            if self._on_recording_start:
                self._on_recording_start()

            try:
                from src.services import dictation_logger as dlog
                dlog.write(f"Audio-Stream gestartet (device={device_id!r}, rate=16000)")
            except Exception:
                pass
            print("[Audio] Aufnahme gestartet")
            return True

        except Exception as e:
            try:
                from src.services import dictation_logger as dlog
                dlog.write(f"Audio-Start FEHLER: {e}")
            except Exception:
                pass
            print(f"[Audio] Fehler beim Starten: {e}")
            self._recording = False
            return False

    def get_accumulated_audio(self) -> Optional[np.ndarray]:
        """Gibt die bisher aufgenommenen Audiodaten zurück, ohne die Aufnahme zu stoppen."""
        with self._lock:
            if not self._chunks:
                return None
            return np.concatenate(self._chunks, axis=0).flatten()

    def stop_recording(self) -> Optional[np.ndarray]:
        """
        Stoppt die Aufnahme und gibt alle aufgenommenen Daten zurück.

        Returns:
            Zusammengeführtes numpy-Array oder None bei Fehler
        """
        if not self._recording:
            return None

        self._recording = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"[Audio] Fehler beim Stoppen: {e}")
            finally:
                self._stream = None

        with self._lock:
            if not self._chunks:
                return None
            audio_data = np.concatenate(self._chunks, axis=0).flatten()

        if self._on_recording_stop:
            self._on_recording_stop()

        duration = len(audio_data) / SAMPLE_RATE
        print(f"[Audio] Aufnahme gestoppt – {duration:.1f}s, {len(audio_data)} Samples")
        return audio_data

    def toggle_recording(self, device: Optional[str] = None):
        """Push-to-Talk Umschalter."""
        if self._recording:
            return self.stop_recording()
        else:
            self.start_recording(device)
            return None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def duration(self) -> float:
        """Aktuelle Aufnahmedauer in Sekunden."""
        with self._lock:
            total = sum(len(c) for c in self._chunks)
        return total / SAMPLE_RATE

    # ── Interner Callback ─────────────────────────────────────────────────────

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: object,
    ) -> None:
        """Wird von sounddevice für jeden Audioblock aufgerufen."""
        if status:
            print(f"[Audio] Status: {status}")

        if self._recording:
            chunk = indata.copy()
            with self._lock:
                self._chunks.append(chunk)

            # Pegel berechnen und Callback auslösen
            if self._on_level_change:
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                level = min(rms / 0.2, 1.0)
                self._on_level_change(level)

    # ── Geräteliste ───────────────────────────────────────────────────────────

    @staticmethod
    def list_input_devices() -> list[dict]:
        """Gibt alle verfügbaren Eingabegeräte zurück."""
        if not SOUNDDEVICE_AVAILABLE:
            return []
        try:
            devices = sd.query_devices()
            return [
                {"id": i, "name": d["name"], "channels": d["max_input_channels"]}
                for i, d in enumerate(devices)
                if d["max_input_channels"] > 0
            ]
        except Exception as e:
            print(f"[Audio] Fehler beim Abrufen der Geräte: {e}")
            return []

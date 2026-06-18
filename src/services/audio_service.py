"""
audio_service.py
Non-blocking Audioaufnahme via sounddevice.
Speichert aufgenommene Chunks im Speicher für spätere Transkription.
"""

import threading
import queue
import numpy as np
from typing import Callable, Optional

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

from src.services.audio_devices import (
    list_input_devices,
    get_next_input_device,
    supported_input_sample_rates,
    resample_audio,
)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
BLOCK_SIZE = 1024


class AudioService:
    """Verwaltet die Mikrofonaufnahme in einem separaten Thread."""

    def __init__(self) -> None:
        self._recording: bool = False
        self._muted: bool = False
        self._chunks: list[np.ndarray] = []
        self._stream: Optional[object] = None
        self._lock = threading.Lock()
        self._on_level_change: Optional[Callable[[float], None]] = None
        self._on_recording_start: Optional[Callable[[], None]] = None
        self._on_recording_stop: Optional[Callable[[], None]] = None
        self._level_queue: queue.Queue[float] = queue.Queue(maxsize=32)
        self._capture_rate = SAMPLE_RATE
        devices = list_input_devices()
        print(f"[Audio] {len(devices)} Eingabegeräte gefunden (default verfügbar)")

    @property
    def is_muted(self) -> bool:
        return self._muted

    def toggle_mute(self) -> bool:
        self._muted = not self._muted
        print(f"[Audio] Mute: {'AN' if self._muted else 'AUS'} (muted={self._muted})")
        return self._muted

    def set_mute(self, muted: bool) -> None:
        self._muted = muted
        print(f"[Audio] muted={muted}")

    def set_muted(self, muted: bool) -> None:
        """Alias für Tests und API-Kompatibilität."""
        self.set_mute(muted)

    def next_input_device(self) -> str:
        return get_next_input_device()

    @staticmethod
    def list_input_devices() -> list[dict]:
        return list_input_devices()

    def set_level_callback(self, cb: Callable[[float], None]) -> None:
        """Legacy-Hook – Pegel laufen über drain_levels() auf dem UI-Thread."""
        self._on_level_change = cb

    def drain_levels(self) -> float | None:
        """Liefert den zuletzt gepufferten Pegel (nur vom UI-Thread abrufen)."""
        latest: float | None = None
        while True:
            try:
                latest = self._level_queue.get_nowait()
            except queue.Empty:
                break
        return latest

    def set_start_callback(self, cb: Callable[[], None]) -> None:
        self._on_recording_start = cb

    def set_stop_callback(self, cb: Callable[[], None]) -> None:
        self._on_recording_stop = cb

    def start_recording(self, device: Optional[str] = None) -> bool:
        if not SOUNDDEVICE_AVAILABLE:
            print("[Audio] sounddevice nicht verfügbar!")
            return False
        if self._recording:
            return True

        with self._lock:
            self._chunks.clear()
            self._recording = True

        resolved = self._resolve_device(device)
        if not self._open_stream(resolved):
            if resolved not in (None, "default"):
                print("[Audio] Fallback auf default-Gerät")
                try:
                    from src.services import dictation_logger as dlog
                    dlog.write("Audio-Gerät Fallback auf default")
                except Exception:
                    pass
                if self._open_stream(None):
                    return True
            self._recording = False
            return False
        return True

    def _resolve_device(self, device: Optional[str]) -> Optional[str | int]:
        from src.services.audio_devices import resolve_input_device_id
        resolved = resolve_input_device_id(device)
        if resolved is not None:
            return resolved
        if device in (None, "", "default"):
            return None
        return device

    def _open_stream(self, device_id) -> bool:
        last_error: Exception | None = None
        for rate in supported_input_sample_rates(device_id):
            try:
                self._stream = sd.InputStream(
                    samplerate=rate,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    blocksize=BLOCK_SIZE,
                    device=device_id,
                    callback=self._audio_callback,
                )
                self._stream.start()
                self._capture_rate = rate
                if self._on_recording_start:
                    self._on_recording_start()
                try:
                    from src.services import dictation_logger as dlog
                    dlog.write(
                        f"Audio-Stream gestartet (device={device_id!r}, rate={rate})"
                    )
                except Exception:
                    pass
                print(f"[Audio] Aufnahme gestartet (device={device_id!r}, rate={rate} Hz)")
                return True
            except Exception as e:
                last_error = e
                self._stream = None
                continue

        try:
            from src.services import dictation_logger as dlog
            dlog.write(f"Audio-Start fehlgeschlagen: {last_error}")
        except Exception:
            pass
        print(f"[Audio] Fehler beim Starten: {last_error}")
        return False

    def _finalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        if self._capture_rate != SAMPLE_RATE:
            audio_data = resample_audio(audio_data, self._capture_rate, SAMPLE_RATE)
        return audio_data

    def get_accumulated_audio(self) -> Optional[np.ndarray]:
        with self._lock:
            if not self._chunks:
                return None
            audio_data = np.concatenate(self._chunks, axis=0).flatten()
        return self._finalize_audio(audio_data)

    def stop_recording(self) -> Optional[np.ndarray]:
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
        audio_data = self._finalize_audio(audio_data)
        if self._on_recording_stop:
            self._on_recording_stop()
        duration = len(audio_data) / SAMPLE_RATE
        print(f"[Audio] Aufnahme gestoppt – {duration:.1f}s")
        return audio_data

    def toggle_recording(self, device: Optional[str] = None):
        if self._recording:
            return self.stop_recording()
        self.start_recording(device)
        return None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def duration(self) -> float:
        with self._lock:
            total = sum(len(c) for c in self._chunks)
        rate = self._capture_rate or SAMPLE_RATE
        return total / rate

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: object,
    ) -> None:
        if status:
            print(f"[Audio] Status: {status}")
        if not self._recording:
            return
        chunk = indata.copy()
        if self._muted:
            chunk = np.zeros_like(chunk)
        with self._lock:
            self._chunks.append(chunk)
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        level = min(rms / 0.2, 1.0)
        try:
            self._level_queue.put_nowait(level)
        except queue.Full:
            try:
                self._level_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._level_queue.put_nowait(level)
            except queue.Full:
                pass

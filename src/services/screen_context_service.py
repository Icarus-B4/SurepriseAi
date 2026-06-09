"""
screen_context_service.py
Erfasst beim Diktatstart Text vom aktiven Fenster (VoiceInk-inspiriert).
"""

import re
import threading
from typing import Optional

from src.services.config_service import config
from src.services.screen_ocr_service import recognize_image, ocr_available
from src.utils.window_capture import (
    capture_bbox,
    get_primary_monitor_bbox,
    get_window_bbox,
)


class ScreenContextService:
    """Asynchrone Bildschirm-OCR beim Aufnahmestart."""

    def __init__(self) -> None:
        self._text: Optional[str] = None
        self._ready = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def last_context(self) -> Optional[str]:
        return self._text

    def capture_async(self, target_hwnd: Optional[int]) -> None:
        """Startet OCR im Hintergrund – blockiert die Aufnahme nicht."""
        if not config.get_bool("enable_screen_context", False):
            self._text = None
            self._ready.set()
            return
        if not ocr_available():
            print("[ScreenContext] winocr/Pillow nicht verfügbar – Kontext übersprungen")
            self._text = None
            self._ready.set()
            return

        self._text = None
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._capture_worker,
            args=(target_hwnd,),
            daemon=True,
        )
        self._thread.start()

    def get_context(self, timeout_s: float = 2.5) -> Optional[str]:
        """Wartet kurz auf OCR und liefert den Kontexttext."""
        if not config.get_bool("enable_screen_context", False):
            return None
        self._ready.wait(timeout=timeout_s)
        return self._text

    def _capture_worker(self, target_hwnd: Optional[int]) -> None:
        try:
            mode = config.get_str("screen_context_mode", "active_window")
            if mode == "monitor":
                bbox = get_primary_monitor_bbox()
            else:
                bbox = get_window_bbox(target_hwnd) or get_primary_monitor_bbox()

            img = capture_bbox(bbox)
            if img is None:
                return

            raw = recognize_image(img)
            if not raw:
                return

            max_chars = config.get_int("screen_context_max_chars", 1200)
            self._text = _normalize_context(raw, max_chars)
            if self._text:
                print(f"[ScreenContext] {len(self._text)} Zeichen erkannt")
        except Exception as exc:
            print(f"[ScreenContext] Erfassung fehlgeschlagen: {exc}")
        finally:
            self._ready.set()


def _normalize_context(text: str, max_chars: int) -> str:
    """Bereinigt und kürzt OCR-Text."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + "…"

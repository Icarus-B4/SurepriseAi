"""
selected_text_service.py
Liest markierten Text aus der Ziel-App via Ctrl+C (VoiceInk SelectedTextKit).
"""

import re
import threading
from typing import Optional

from src.services.config_service import config


class SelectedTextService:
    """Asynchrone Erfassung markierten Textes beim Diktatstart."""

    def __init__(self) -> None:
        self._text: Optional[str] = None
        self._ready = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def last_context(self) -> Optional[str]:
        return self._text

    def capture_async(self, target_hwnd: Optional[int]) -> None:
        """Startet Ctrl+C-Erfassung im Hintergrund."""
        if not config.get_bool("enable_selected_text_context", True):
            self._text = None
            self._ready.set()
            return
        if target_hwnd is None:
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

    def get_context(self, timeout_s: float = 0.8) -> Optional[str]:
        """Wartet kurz auf Erfassung und liefert den markierten Text."""
        if not config.get_bool("enable_selected_text_context", True):
            return None
        self._ready.wait(timeout=timeout_s)
        return self._text

    def _capture_worker(self, target_hwnd: int) -> None:
        try:
            from src.services.clipboard_service import ClipboardService

            clip = ClipboardService()
            raw = clip.capture_selection(target_hwnd)
            if not raw:
                return

            max_chars = config.get_int("selected_text_max_chars", 800)
            self._text = _normalize_selection(raw, max_chars)
            if self._text:
                print(f"[SelectedText] {len(self._text)} Zeichen erfasst")
        except Exception as exc:
            print(f"[SelectedText] Erfassung fehlgeschlagen: {exc}")
        finally:
            self._ready.set()


def _normalize_selection(text: str, max_chars: int) -> str:
    """Bereinigt und kürzt markierten Text."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 2:
        return ""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + "…"

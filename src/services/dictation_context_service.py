"""
dictation_context_service.py
Kombiniert Bildschirm-OCR und markierten Text für Ollama-Polishing.
"""

from typing import Optional

from src.services.config_service import config
from src.services.screen_context_service import ScreenContextService
from src.services.selected_text_service import SelectedTextService


class DictationContextService:
    """Orchestriert parallele Kontext-Erfassung beim Diktat."""

    def __init__(self) -> None:
        self.screen = ScreenContextService()
        self.selected = SelectedTextService()

    @property
    def last_context(self) -> Optional[str]:
        return merge_polish_context(
            self.screen.last_context,
            self.selected.last_context,
        )

    def capture_async(self, target_hwnd: Optional[int]) -> None:
        self.screen.capture_async(target_hwnd)
        self.selected.capture_async(target_hwnd)

    def get_context(self, timeout_s: float = 3.0) -> Optional[str]:
        screen_timeout = config.get_int("screen_context_timeout_s", 3)
        selected_timeout = 0.8

        screen = self.screen.get_context(timeout_s=screen_timeout)
        selected = self.selected.get_context(timeout_s=selected_timeout)
        return merge_polish_context(screen, selected)


def merge_polish_context(
    screen: Optional[str],
    selected: Optional[str],
) -> Optional[str]:
    """Führt OCR- und Markierungstext zu einem Prompt-Kontext zusammen."""
    parts: list[str] = []
    if selected and selected.strip():
        parts.append("Markierter Text (nur zur Korrektur – nicht zitieren):\n" + selected.strip())
    if screen and screen.strip():
        parts.append("Bildschirmkontext OCR (nur zur Korrektur – nicht zitieren):\n" + screen.strip())
    if not parts:
        return None
    merged = "\n\n".join(parts)
    max_chars = config.get_int("screen_context_max_chars", 1200)
    if len(merged) <= max_chars:
        return merged
    return merged[:max_chars].rsplit("\n", 1)[0] + "…"

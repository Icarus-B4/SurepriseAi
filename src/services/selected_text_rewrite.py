"""
selected_text_rewrite.py
In-Place-Umschrift für markierten Text (SelectedTextKit).
"""

import threading
from typing import Callable, Optional

from src.services.config_service import config
from src.services.app_mode_service import resolve_style_for_hwnd
from src.services.text_postprocessor import apply_postprocessing
from src.services import dictation_logger as dlog


class SelectedTextRewriteService:
    """Erfasst markierten Text, poliert ihn und fügt ihn per Auto-Inject ein."""

    def __init__(
        self,
        clipboard,
        polisher,
        emit_state: Callable[[str], None],
        emit_error: Callable[[str], None],
        capture_hwnd: Callable[[], Optional[int]],
    ) -> None:
        self._clipboard = clipboard
        self._polisher = polisher
        self._emit_state = emit_state
        self._emit_error = emit_error
        self._capture_hwnd = capture_hwnd
        self._busy = False

    def capture_and_rewrite(self, style: Optional[str] = None) -> None:
        if self._busy:
            return
        threading.Thread(
            target=self._worker,
            args=(style,),
            daemon=True,
        ).start()

    def _worker(self, style: Optional[str]) -> None:
        self._busy = True
        try:
            if not config.get_bool("enable_selected_text_context", True):
                dlog.write("SelectedText Umschrift deaktiviert")
                return

            target_hwnd = self._capture_hwnd()
            self._emit_state("processing")
            print("[SelectedText] Umschreiben... – Erfassung via Ctrl+C")
            dlog.write("SelectedText Erfassung via Ctrl+C gestartet")

            captured = None
            if target_hwnd:
                captured = self._clipboard.capture_selection(target_hwnd)
            if not captured:
                captured = self._clipboard.read_clipboard().strip()
                if captured:
                    print("[SelectedText] Erfassung aus Zwischenablage (ohne Ctrl+C)")
                    dlog.write("SelectedText Erfassung aus Zwischenablage")

            if not captured or len(captured) < 2:
                dlog.write("SelectedText: leere Selektion – Abbruch")
                self._emit_state("idle")
                return

            active_style = style
            if active_style is None and target_hwnd:
                resolved = resolve_style_for_hwnd(target_hwnd)
                if resolved:
                    active_style = resolved
            if not active_style:
                active_style = config.selected_style
            print(f"[Polishing] SelectedText Umschrift ({active_style})")
            dlog.write(f"Polishing SelectedText ({active_style})")

            if config.ollama_polishing:
                ollama_result = self._polisher._call_ollama(captured, active_style)
                if ollama_result:
                    polished = ollama_result
                elif "invalid-url" in config.get_str("ollama_url", ""):
                    self._emit_error("Ollama Polishing fehlgeschlagen")
                    self._emit_state("error")
                    return
                else:
                    polished = self._polisher.polish_instant(
                        captured, style=active_style
                    )
            else:
                polished = self._polisher.polish_instant(captured, style=active_style)
            polished = apply_postprocessing(
                polished, active_style, hwnd=target_hwnd
            )
            if not polished or not polished.strip():
                self._emit_error("Umschrift fehlgeschlagen.")
                self._emit_state("error")
                return

            print("[Clipboard] Auto-Inject via Ctrl+V")
            self._clipboard.inject_text(polished, target_hwnd=target_hwnd)
            dlog.write("SelectedText Inject via Ctrl+V ausgelöst")
            self._emit_state("success")
            print("[SelectedText] Umschrift eingefügt")
        except Exception as exc:
            dlog.write_exception("SelectedText Umschrift")
            print(f"[SelectedText] Fehler: {exc}")
            self._emit_error(str(exc))
            self._emit_state("error")
        finally:
            self._busy = False

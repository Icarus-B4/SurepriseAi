"""
polishing_service.py
Text-Polishing via Ollama oder regelbasierten Fallback bei Offline-Status.
Garantiert unter 200 Zeilen für Clean Code.
"""

import json
import threading
from typing import Callable, Optional
import urllib.request
import urllib.error

from .config_service import config
from ..utils.text_cleaner import bereinige_text

STYLE_PROMPTS = {
    "business": "Schreibe den Text in einem klaren, sachlichen Business-Stil um. Antworte NUR mit dem Text.",
    "casual": "Bereinige den Text, behalte den lockeren Ton bei. Antworte NUR mit dem Text.",
    "bullet_points": "Wandle den Text in prägnante Stichpunkte um (mit '•'). Antworte NUR mit dem Text.",
    "concise": "Fasse den Text auf das Wesentliche zusammen. Antworte NUR mit dem Text.",
    "formal": "Formuliere den Text in einem formellen, höflichen Stil um. Antworte NUR mit dem Text."
}


class PolishingService:
    """Sendet Text an Ollama oder führt regelbasierte Fallbacks durch."""

    def __init__(self) -> None:
        self._on_result: Optional[Callable[[str], None]] = None
        self._ollama_available: Optional[bool] = None

    def set_result_callback(self, cb: Callable[[str], None]) -> None:
        self._on_result = cb

    def polish_async(self, text: str, style: Optional[str] = None) -> None:
        threading.Thread(target=self._polish_worker, args=(text, style), daemon=True).start()

    def polish(self, text: str, style: Optional[str] = None) -> str:
        """Volles Polishing nach Diktat (optional mit Ollama, kann dauern)."""
        if not text or not text.strip():
            return text
        active_style = style or config.selected_style
        cleaned = bereinige_text(text)
        ollama_result: Optional[str] = None

        if config.ollama_polishing:
            ollama_result = self._call_ollama(cleaned, active_style)

        if ollama_result and ollama_result.strip() != cleaned.strip():
            return ollama_result
        return self._style_fallback(cleaned, active_style)

    def polish_instant(self, text: str, style: Optional[str] = None) -> str:
        """Sofortiges Stil-Umschalten ohne Ollama – für Chip-Klicks im UI."""
        if not text or not text.strip():
            return text
        active_style = style or config.selected_style
        return self._style_fallback(bereinige_text(text), active_style)

    def _style_fallback(self, text: str, style: str) -> str:
        """Sichtbare Stiländerungen ohne Ollama – immer sofort."""
        import re

        if style == "bullet_points":
            parts = [s.strip() for s in re.split(r'(?<=[.!?])\s+|,\s+|\s+und\s+', text) if s.strip()]
            if len(parts) <= 1:
                t = text.strip()
                return f"• {t[0].upper() + t[1:]}" if t else text
            return "\n".join(f"• {s[0].upper() + s[1:]}" for s in parts)

        if style == "concise":
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
            if len(sentences) > 1:
                return " ".join(sentences[:2])
            words = text.split()
            if len(words) > 8:
                return " ".join(words[: max(6, len(words) // 2)]) + " …"
            return text

        if style == "business":
            repl = {
                "ich glaube": "es ist anzunehmen", "wir müssen": "es ist erforderlich",
                "ich will": "ich beabsichtige zu", "ich muss": "es ist notwendig, dass ich",
                "jedes mal": "jeweils", "zuerst": "initial", "okay": "in Ordnung",
                "machen": "erstellen", "tun": "durchführen", "funktioniert": "funktioniert zuverlässig",
                "das heißt": "das bedeutet", "dann kann ich": "anschließend kann ich",
                " nimmt mich": " beschäftigt mich", "ob das": "inwieweit das",
            }
            result = text
            for k, v in repl.items():
                result = result.replace(k, v)
            if result.strip() == text.strip():
                t = text.strip()
                result = f"Zusammenfassend: {t[0].upper() + t[1:]}" if t else text
            return result[0].upper() + result[1:] if result else result

        if style == "formal":
            result = re.sub(r'\bhallo\b', 'Sehr geehrte Damen und Herren', text, flags=re.I)
            result = re.sub(r'\bhi\b', 'Sehr geehrte Damen und Herren', result, flags=re.I)
            result = re.sub(r'\bdanke\b', 'Vielen Dank', result, flags=re.I)
            result = re.sub(r'\bdu\b', 'Sie', result, flags=re.I)
            result = result.replace("dein", "Ihr").replace("dir", "Ihnen")
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', result) if s.strip()]
            return " ".join(s[0].upper() + s[1:] for s in sentences) if sentences else result

        if style == "casual":
            return bereinige_text(text)

        return text

    def _call_ollama(self, text: str, style: str) -> Optional[str]:
        url = f"{config.ollama_url}/api/generate"
        payload = json.dumps({
            "model": config.ollama_model,
            "prompt": f"{STYLE_PROMPTS.get(style, '')}\n\nText:\n{text}",
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 500}
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=config.polishing_timeout) as r:
                res = json.loads(r.read().decode("utf-8"))
                polished = res.get("response", "").strip()
                if polished:
                    self._ollama_available = True
                    return polished
        except Exception:
            self._ollama_available = False
        return None

    def _polish_worker(self, text: str, style: Optional[str]) -> None:
        res = self.polish(text, style)
        if self._on_result and res: self._on_result(res)

    def check_ollama_status(self) -> bool:
        try:
            req = urllib.request.Request(f"{config.ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as r:
                self._ollama_available = r.status == 200
        except Exception:
            self._ollama_available = False
        return self._ollama_available or False

    @property
    def ollama_available(self) -> bool:
        return self._ollama_available is True

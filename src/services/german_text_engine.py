"""
german_text_engine.py
Deutsch-native Nachbearbeitung: Sie/Du, Zahlen, Datums- und Währungsformat.
"""

from __future__ import annotations

import re
from typing import Optional

from src.services.config_service import config

_SPOKEN_DECIMAL = re.compile(
    r"\b(\d+)\s+komma\s+(\d+)\b",
    flags=re.IGNORECASE,
)
_SPOKEN_EURO_CENTS = re.compile(
    r"\b(\d+)\s+euro\s+(\d{1,2})\b",
    flags=re.IGNORECASE,
)
_SPOKEN_EURO = re.compile(
    r"\b(\d+)\s+euro\b",
    flags=re.IGNORECASE,
)
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DOT_DATE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")

_SIE_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bdu\b", re.I), "Sie"),
    (re.compile(r"\bdein\b", re.I), "Ihr"),
    (re.compile(r"\bdeine\b", re.I), "Ihre"),
    (re.compile(r"\bdeinen\b", re.I), "Ihren"),
    (re.compile(r"\bdeinem\b", re.I), "Ihrem"),
    (re.compile(r"\bdeiner\b", re.I), "Ihrer"),
    (re.compile(r"\bdeines\b", re.I), "Ihres"),
    (re.compile(r"\bdir\b", re.I), "Ihnen"),
    (re.compile(r"\bdich\b", re.I), "Sie"),
    (re.compile(r"\bcanst\b", re.I), "können"),
    (re.compile(r"\bkannst\b", re.I), "können"),
    (re.compile(r"\bmusst\b", re.I), "müssen"),
    (re.compile(r"\bwillst\b", re.I), "möchten"),
    (re.compile(r"\bbitte\b(?=\s+(?:schick|sende|gib))", re.I), "Bitte"),
]

_DU_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bSie\b"), "du"),
    (re.compile(r"\bIhnen\b"), "dir"),
    (re.compile(r"\bIhr\b"), "dein"),
    (re.compile(r"\bIhre\b"), "deine"),
    (re.compile(r"\bIhren\b"), "deinen"),
    (re.compile(r"\bIhrem\b"), "deinem"),
    (re.compile(r"\bIhrer\b"), "deiner"),
    (re.compile(r"\bIhres\b"), "deines"),
]


def resolve_german_register(style: Optional[str]) -> Optional[str]:
    """Liefert 'sie', 'du' oder None (neutral) für einen Stil."""
    if not style:
        return None
    if style in ("formal", "business"):
        return "sie"
    if style in ("casual", "concise"):
        return "du"
    return None


def apply_german_native(text: str, style: Optional[str] = None) -> str:
    """Wendet deutsch-native Formatierung und Anrede-Regeln an."""
    if not text or not text.strip():
        return text
    if not config.get_bool("enable_german_native_engine", True):
        return text

    result = text
    result = _format_numbers_and_currency(result)
    result = _format_dates(result)
    result = _apply_vocabulary_compounds(result)

    register = resolve_german_register(style)
    if register == "sie":
        result = _apply_register(result, _SIE_REPLACEMENTS)
    elif register == "du":
        result = _apply_register(result, _DU_REPLACEMENTS)

    return result


def _format_numbers_and_currency(text: str) -> str:
    text = _SPOKEN_DECIMAL.sub(r"\1,\2", text)
    text = _SPOKEN_EURO_CENTS.sub(r"\1,\2 €", text)
    text = _SPOKEN_EURO.sub(r"\1 €", text)
    text = re.sub(r"\bEUR\b", "€", text)
    text = re.sub(r"\b(\d+)\s*%\b", lambda m: f"{m.group(1)}\u00a0%", text)
    return text


def _format_dates(text: str) -> str:
    def _iso_to_de(match: re.Match[str]) -> str:
        y, m, d = match.group(1), match.group(2), match.group(3)
        return f"{int(d):02d}.{int(m):02d}.{y}"

    return _ISO_DATE.sub(_iso_to_de, text)


def _apply_vocabulary_compounds(text: str) -> str:
    """Führt bekannte Komposita aus dem Vokabular zusammen (z. B. Web Stark → Webstark)."""
    vocabulary = config.get_list("personal_vocabulary")
    for entry in vocabulary:
        if not isinstance(entry, str) or len(entry) < 4:
            continue
        spaced = _split_compound(entry)
        if spaced and spaced.lower() in text.lower():
            pattern = re.compile(re.escape(spaced), flags=re.IGNORECASE)
            text = pattern.sub(entry, text)
    return text


def _split_compound(word: str) -> Optional[str]:
    """Heuristik: CamelCase/Komposita in gesprochene Teile splitten."""
    if " " in word:
        return None
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)", word)
    if len(parts) >= 2:
        return " ".join(parts)
    return None


def _apply_register(text: str, rules: list[tuple[re.Pattern[str], str]]) -> str:
    result = text
    for pattern, repl in rules:
        result = pattern.sub(repl, result)
    return result

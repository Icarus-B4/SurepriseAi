"""
text_cleaner.py
Regex-basierter Fallback-Bereiniger.
Entfernt Füllwörter, Selbstkorrekturen und Wiederholungen ohne LLM-Aufruf.
"""

import re
from typing import Optional

# ── Füllwörter (Deutsch & Englisch) ──────────────────────────────────────────
FUELLWOERTER_DE = [
    r"\bähm+\b", r"\bähh*\b", r"\bumm*\b", r"\bäh\b", r"\bja\b",
    r"\bnaja\b", r"\bsozusagen\b", r"\birgendwie\b", r"\bquasi\b",
    r"\beigentlich\b", r"\balso\b", r"\bgut\b", r"\bokay\b", r"\bok\b",
    r"\brichtig\b", r"\bgenau\b", r"\bhal+o+\b",
]

FUELLWOERTER_EN = [
    r"\bum+\b", r"\buh+\b", r"\ber+\b", r"\blike\b", r"\byou know\b",
    r"\bbasically\b", r"\bliterally\b", r"\bactually\b", r"\bright\b",
    r"\bso\b", r"\bwel+\b", r"\bokay\b", r"\bok\b",
]

# Kombiniert, case-insensitive
_FUELL_PATTERN = re.compile(
    "|".join(FUELLWOERTER_DE + FUELLWOERTER_EN),
    flags=re.IGNORECASE
)

# Selbstkorrektur-Muster: "Wort- Wort" → "Wort"
_ABBRUCH_PATTERN = re.compile(r"\b(\w+)-\s+\1\b", flags=re.IGNORECASE)

# Doppelte Wörter: "das das" → "das"
_DOPPELUNG_PATTERN = re.compile(r"\b(\w+)\s+\1\b", flags=re.IGNORECASE)

# Mehrfache Leerzeichen/Zeilenumbrüche
_WHITESPACE_PATTERN = re.compile(r" {2,}")

# Satzanfang nach Punkt/Ausrufe/Fragezeichen
_SATZ_ANFANG = re.compile(r"([.!?])\s+([a-z])")

# Gesprochene Selbstkorrekturen: „… nein, ich meine …“
_SELBSTKORREKTUR_MARKER = re.compile(
    r"\b(?:"
    r"nein(?:,\s*)?(?:ich meine|meine ich)?|"
    r"nee(?:,\s*)?(?:ich meine|meine ich)?|"
    r"stop|warte|moment|"
    r"ich meine(?:,\s*)?|eigentlich meine ich|"
    r"or rather|i mean|"
    r"sorry(?:,\s*)?(?:i mean|ich meine)?|"
    r"oder besser(?: gesagt)?|"
    r"korrigiert|lass mich das nochmal sagen"
    r")\b",
    flags=re.IGNORECASE,
)


def entferne_fuellwoerter(text: str) -> str:
    """Entfernt Füllwörter aus dem Text."""
    return _FUELL_PATTERN.sub("", text)


def entferne_abbrueche(text: str) -> str:
    """Bereinigt Selbstkorrekturen wie 'Projek- Projekt'."""
    return _ABBRUCH_PATTERN.sub(r"\1", text)


def entferne_doppelungen(text: str) -> str:
    """Entfernt direkte Wortwiederholungen wie 'das das'."""
    return _DOPPELUNG_PATTERN.sub(r"\1", text)


def entferne_selbstkorrekturen(text: str) -> str:
    """
    Filtert gesprochene Korrekturen wie „Sende an John nein ich meine James“.
    Entfernt das falsch gesprochene Wort vor dem Marker und behält den Rest.
    """
    if not text or not text.strip():
        return text

    def _fix_segment(segment: str) -> str:
        parts = _SELBSTKORREKTUR_MARKER.split(segment)
        if len(parts) <= 1:
            return segment.strip()

        prefix = parts[0]
        for tail in parts[1:]:
            corrected = tail.strip().strip(",").strip()
            if not corrected:
                continue
            words = prefix.strip().split()
            if words:
                words = words[:-1]
            prefix = " ".join(words + [corrected])
        return prefix.strip()

    segments = re.split(r"(?<=[.!?])\s+", text.strip())
    cleaned = [_fix_segment(seg) for seg in segments if seg.strip()]
    return " ".join(cleaned)


def entferne_satz_wiederholungen(text: str) -> str:
    """Entfernt direkt aufeinanderfolgende, identische Sätze (case-insensitive)."""
    if not text:
        return text
    # Nach Satzzeichen splitten, Lookbehind hält die Satzzeichen im Satz
    sentences = re.split(r'(?<=[.!?])\s+', text)
    cleaned = []
    last_s_norm = ""
    for s in sentences:
        s_norm = re.sub(r'[^\w\s]', '', s.lower().strip())
        if s_norm == last_s_norm and s_norm != "":
            continue
        cleaned.append(s.strip())
        last_s_norm = s_norm
    return " ".join(cleaned)


def grossschreibung_satzanfang(text: str) -> str:
    """Stellt sicher, dass nach Satzzeichen großgeschrieben wird."""
    def _upper(match: re.Match) -> str:
        return f"{match.group(1)} {match.group(2).upper()}"
    return _SATZ_ANFANG.sub(_upper, text)


def normalisiere_leerzeichen(text: str) -> str:
    """Entfernt mehrfache Leerzeichen und trimmt."""
    text = _WHITESPACE_PATTERN.sub(" ", text)
    # Leerzeichen vor Satzzeichen entfernen
    text = re.sub(r"\s+([,;:.!?])", r"\1", text)
    return text.strip()


def bereinige_text(
    text: str,
    entferne_fuell: bool = True,
    entferne_doppel: bool = True,
    grossschreibung: bool = True,
) -> str:
    """
    Vollständige Textbereinigung ohne LLM.
    Führt alle Bereinigungsschritte in der richtigen Reihenfolge aus.
    """
    if not text or not text.strip():
        return text

    if entferne_fuell:
        text = entferne_fuellwoerter(text)

    text = entferne_selbstkorrekturen(text)
    text = entferne_abbrueche(text)

    if entferne_doppel:
        text = entferne_doppelungen(text)

    # Satzwiederholungen entfernen
    text = entferne_satz_wiederholungen(text)

    text = normalisiere_leerzeichen(text)

    if grossschreibung and text:
        # Führende Satzzeichen entfernen, die von gelöschten Füllwörtern stammen können
        text = re.sub(r"^[,;:\s]+", "", text)
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
            text = grossschreibung_satzanfang(text)

    return text

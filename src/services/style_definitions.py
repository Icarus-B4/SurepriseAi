"""
style_definitions.py
Zentrale Stil-Chips für Polishing (UI, Tray, Ollama-Prompts).
"""

from __future__ import annotations

STYLE_DEFINITIONS: list[tuple[str, str]] = [
    ("casual", "Bereinigen"),
    ("business", "Business"),
    ("bullet_points", "Stichpunkte"),
    ("key_points", "Kernpunkte"),
    ("concise", "Kompakt"),
    ("long", "Lang"),
    ("formal", "Formell"),
]

STYLE_LABELS: dict[str, str] = dict(STYLE_DEFINITIONS)


def style_label(key: str) -> str:
    """Deutsches Chip-Label für einen Stil-Key."""
    return STYLE_LABELS.get(key, key)

"""
live_transcript_html.py
Gemeinsame HTML-Formatierung für Live-Transkript-Anzeigen (Toast + Expanded Pill).
"""

from __future__ import annotations

import html
import re

from src.ui.design_tokens import Colors
from src.utils.translation import tr

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")


def format_live_transcript_html(text: str, *, settled: bool = False) -> str:
    """Formatiert Live-Text mit festem Satzteil + kursivem Partial-Tail."""
    text = (text or "").strip()
    if not text or text == tr("listening"):
        return (
            f'<span style="color:{Colors.TEXT_SECONDARY_HEX};'
            f'font-style:italic;">{html.escape(text or tr("listening"))}</span>'
        )

    if settled:
        return (
            f'<span style="color:{Colors.TEXT_PRIMARY_HEX};">'
            f"{html.escape(text)}</span>"
        )

    parts = _SENTENCE_SPLIT.split(text)
    if len(parts) == 1 and not re.search(r"[.!?…]$", text):
        return (
            f'<span style="color:{Colors.TEXT_SECONDARY_HEX};'
            f'font-style:italic;">{html.escape(text)}</span>'
        )

    if re.search(r"[.!?…]$", text):
        final_part, partial_part = text, ""
    else:
        final_part = " ".join(parts[:-1]).strip()
        partial_part = parts[-1].strip()

    chunks: list[str] = []
    if final_part:
        chunks.append(
            f'<span style="color:{Colors.TEXT_PRIMARY_HEX};">'
            f"{html.escape(final_part)}</span>"
        )
    if partial_part:
        chunks.append(
            f'<span style="color:{Colors.TEXT_SECONDARY_HEX};'
            f'font-style:italic;">{html.escape(partial_part)}</span>'
        )
    return " ".join(chunks) if chunks else html.escape(text)

"""
diff_helper.py
Wort-basierte Diff-Frames für die Polish-Animation (Rohtext → poliert).
"""

from __future__ import annotations

import difflib
import html
from typing import List, Tuple

Frame = Tuple[str, str]  # ("plain"|"html", inhalt)


def count_text_changes(raw: str, polished: str) -> int:
    """Zählt geänderte Wort-Segmente zwischen Rohtext und poliertem Text."""
    raw = (raw or "").strip()
    polished = (polished or "").strip()
    if not raw or not polished or raw == polished:
        return 0

    raw_words = raw.split()
    pol_words = polished.split()
    matcher = difflib.SequenceMatcher(None, raw_words, pol_words)
    changes = 0
    for tag, _i1, _i2, _j1, _j2 in matcher.get_opcodes():
        if tag != "equal":
            changes += 1
    return changes


def texts_differ(raw: str, polished: str) -> bool:
    """True wenn Rohtext und polierter Text inhaltlich abweichen."""
    return (raw or "").strip() != (polished or "").strip()


def generate_diff_frames(
    raw: str,
    polished: str,
    batch_size: int = 1,
) -> List[Frame]:
    """Erzeugt Animations-Frames: Rohtext → Diff-HTML → finales Plain-Polish."""
    raw = (raw or "").strip()
    polished = (polished or "").strip()
    if not polished:
        return [("plain", "")]
    if not raw or raw == polished:
        return [("plain", polished)]

    raw_words = raw.split()
    pol_words = polished.split()
    matcher = difflib.SequenceMatcher(None, raw_words, pol_words)
    segments: List[tuple[str, List[str]]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            segments.append(("eq", raw_words[i1:i2]))
        elif tag == "delete":
            segments.append(("del", raw_words[i1:i2]))
        elif tag == "insert":
            segments.append(("ins", pol_words[j1:j2]))
        elif tag == "replace":
            segments.append(("del", raw_words[i1:i2]))
            segments.append(("ins", pol_words[j1:j2]))

    change_indices = [i for i, (kind, _) in enumerate(segments) if kind != "eq"]
    if not change_indices:
        return [("plain", raw), ("plain", polished)]

    frames: List[Frame] = [("plain", raw)]
    revealed: set[int] = set()
    for start in range(0, len(change_indices), batch_size):
        for idx in change_indices[start : start + batch_size]:
            revealed.add(idx)
        frames.append(("html", _build_html(segments, revealed)))

    frames.append(("plain", polished))
    return frames


def _build_html(segments: List[tuple[str, List[str]]], revealed: set[int]) -> str:
    parts: List[str] = []
    for i, (kind, words) in enumerate(segments):
        if not words:
            continue
        text = html.escape(" ".join(words))
        if kind == "eq":
            parts.append(f'<span style="color:#F5F5F7;">{text}</span>')
        elif kind == "del":
            if i in revealed:
                parts.append(
                    f'<span style="color:#FF453A;text-decoration:line-through;">{text}</span>'
                )
            else:
                parts.append(f'<span style="color:#F5F5F7;">{text}</span>')
        elif kind == "ins" and i in revealed:
            parts.append(
                f'<span style="color:#818CF8;background-color:rgba(99,102,241,0.22);'
                f'border-radius:3px;padding:0 2px;">{text}</span>'
            )

    body = " ".join(parts)
    return (
        f'<p style="margin:0;line-height:1.5;font-family:Segoe UI,sans-serif;'
        f'font-size:12px;">{body}</p>'
    )

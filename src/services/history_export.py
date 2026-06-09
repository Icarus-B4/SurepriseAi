"""
history_export.py
Exportiert Diktat-Einträge als TXT, Markdown oder SRT.
"""

import re
from pathlib import Path
from typing import Any


def export_entry(entry: dict[str, Any], fmt: str, path: Path) -> None:
    """Schreibt einen Historien-Eintrag in die gewünschte Datei."""
    fmt = fmt.lower().lstrip(".")
    if fmt == "txt":
        content = _as_txt(entry)
    elif fmt == "md":
        content = _as_markdown(entry)
    elif fmt == "srt":
        content = _as_srt(entry)
    else:
        raise ValueError(f"Unbekanntes Format: {fmt}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _as_txt(entry: dict[str, Any]) -> str:
    polished = entry.get("polished", "")
    raw = entry.get("raw", "")
    ts = entry.get("timestamp", "")
    if raw and raw.strip() != polished.strip():
        return f"{polished}\n\n--- Rohtext ---\n{raw}\n\n({ts})"
    return f"{polished}\n\n({ts})"


def _as_markdown(entry: dict[str, Any]) -> str:
    ts = entry.get("timestamp", "")[:19].replace("T", " ")
    style = entry.get("style", "")
    words = entry.get("words", 0)
    wpm = entry.get("wpm", 0)
    polished = entry.get("polished", "")
    raw = entry.get("raw", "")

    lines = [
        f"# Diktat – {ts}",
        "",
        f"- **Stil:** {style}",
        f"- **Wörter:** {words}",
        f"- **WPM:** {wpm}",
        "",
        "## Polierter Text",
        "",
        polished,
    ]
    if raw and raw.strip() != polished.strip():
        lines.extend(["", "## Rohtext", "", raw])
    return "\n".join(lines) + "\n"


def _as_srt(entry: dict[str, Any]) -> str:
    """Erzeugt einfache SRT-Untertitel aus dem polierten Text."""
    text = entry.get("polished", "").strip()
    if not text:
        return ""

    words = max(int(entry.get("words", 0)), 1)
    wpm = max(int(entry.get("wpm", 0)), 60)
    total_ms = int((words / wpm) * 60 * 1000)
    total_ms = max(total_ms, 3000)

    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text]

    blocks: list[str] = []
    elapsed = 0
    slice_ms = total_ms // len(sentences)

    for i, sentence in enumerate(sentences, start=1):
        start = elapsed
        end = elapsed + slice_ms if i < len(sentences) else total_ms
        blocks.append(
            f"{i}\n{_ms_to_srt(start)} --> {_ms_to_srt(end)}\n{sentence.strip()}\n"
        )
        elapsed = end

    return "\n".join(blocks)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _ms_to_srt(ms: int) -> str:
    ms = max(0, ms)
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

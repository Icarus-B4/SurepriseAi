"""
dictation_history.py
Persistente Diktat-Historie mit Suche und erneutem Kopieren.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config_service import config
from src.utils.app_paths import user_data_dir

_HISTORY_PATH = user_data_dir() / "dictation_history.json"


class DictationHistoryService:
    """Speichert die letzten Diktate lokal."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not _HISTORY_PATH.exists():
            self._entries = []
            return
        try:
            with open(_HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            self._entries = []

    def _save(self) -> None:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Historie] Speichern fehlgeschlagen: {e}")

    def add(
        self,
        raw: str,
        polished: str,
        words: int,
        wpm: int,
        style: str,
        audio_path: str | None = None,
        live_transcript: str | None = None,
        duration_s: float | None = None,
    ) -> None:
        """Neuen Historien-Eintrag vorne einfügen."""
        entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "raw": raw,
            "polished": polished,
            "words": words,
            "wpm": wpm,
            "style": style,
            "audio_path": audio_path or "",
            "live_transcript": live_transcript or "",
            "duration_s": round(duration_s, 2) if duration_s is not None else None,
        }
        self._entries.insert(0, entry)
        limit = config.get_int("dictation_history_max", 50)
        self._entries = self._entries[:limit]
        self._save()

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            return self.list_all()
        return [
            e for e in self._entries
            if q in e.get("polished", "").lower()
            or q in e.get("raw", "").lower()
        ]

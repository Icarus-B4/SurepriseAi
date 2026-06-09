"""
usage_stats.py
Tagesstatistik für Diktate (Wörter, Ø WPM) – lokal persistiert.
"""

import json
from datetime import date
from typing import Any

from src.utils.app_paths import user_data_dir

_STATS_PATH = user_data_dir() / "usage_stats.json"


class UsageStatsService:
    """Aggregiert Nutzungsdaten pro Kalendertag."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {"days": {}}
        self._load()

    def _load(self) -> None:
        if not _STATS_PATH.exists():
            return
        try:
            with open(_STATS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "days" in data:
                self._data = data
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self) -> None:
        _STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(_STATS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Stats] Speichern fehlgeschlagen: {e}")

    def record_dictation(self, words: int, wpm: int, duration_s: float) -> None:
        """Einen abgeschlossenen Diktat-Lauf verbuchen."""
        key = date.today().isoformat()
        day = self._data["days"].setdefault(
            key, {"dictations": 0, "words": 0, "wpm_sum": 0, "duration_s": 0.0}
        )
        day["dictations"] += 1
        day["words"] += max(0, words)
        day["wpm_sum"] += max(0, wpm)
        day["duration_s"] += max(0.0, duration_s)
        self._save()

    def today_summary(self) -> str:
        """Kurztext für Tray-Tooltip."""
        key = date.today().isoformat()
        day = self._data["days"].get(key)
        if not day or day.get("dictations", 0) == 0:
            return "Heute: noch keine Diktate"
        avg_wpm = int(day["wpm_sum"] / day["dictations"])
        return f"Heute: {day['words']} Wörter · Ø {avg_wpm} WPM"

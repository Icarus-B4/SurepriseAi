"""
usage_stats.py
Nutzungsstatistik für Diktate (Wörter, WPM, Apps, Streak) – lokal persistiert.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from src.utils.app_paths import user_data_dir

_STATS_PATH = user_data_dir() / "usage_stats.json"


class UsageStatsService:
    """Aggregiert Nutzungsdaten pro Kalendertag und liefert Insights."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {"days": {}, "app_totals": {}}
        self._load()

    def _load(self) -> None:
        if not _STATS_PATH.exists():
            return
        try:
            with open(_STATS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "days" in data:
                self._data = data
                self._data.setdefault("app_totals", {})
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self) -> None:
        _STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(_STATS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Stats] Speichern fehlgeschlagen: {e}")

    def record_dictation(
        self,
        words: int,
        wpm: int,
        duration_s: float,
        app_key: str | None = None,
    ) -> None:
        """Einen abgeschlossenen Diktat-Lauf verbuchen."""
        key = date.today().isoformat()
        day = self._data["days"].setdefault(
            key,
            {
                "dictations": 0,
                "words": 0,
                "wpm_sum": 0,
                "duration_s": 0.0,
                "apps": {},
            },
        )
        day["dictations"] += 1
        day["words"] += max(0, words)
        day["wpm_sum"] += max(0, wpm)
        day["duration_s"] += max(0.0, duration_s)

        if app_key:
            apps = day.setdefault("apps", {})
            apps[app_key] = apps.get(app_key, 0) + 1
            totals = self._data.setdefault("app_totals", {})
            totals[app_key] = totals.get(app_key, 0) + 1

        self._save()

    def today_summary(self) -> str:
        """Kurztext für Tray-Tooltip."""
        snap = self.get_insights()
        if snap["today_dictations"] == 0:
            return "Heute: noch keine Diktate"
        streak = snap["streak_days"]
        streak_txt = f" · 🔥 {streak}d" if streak > 1 else ""
        return (
            f"Heute: {snap['today_words']} Wörter · "
            f"Ø {snap['today_avg_wpm']} WPM{streak_txt}"
        )

    def get_insights(self) -> dict[str, Any]:
        """Liefert aggregierte Kennzahlen für das Insights-Dashboard."""
        today_key = date.today().isoformat()
        today = self._data["days"].get(today_key, {})
        today_dictations = int(today.get("dictations", 0))
        today_words = int(today.get("words", 0))
        today_avg_wpm = (
            int(today.get("wpm_sum", 0) / today_dictations)
            if today_dictations
            else 0
        )
        today_duration_min = round(float(today.get("duration_s", 0.0)) / 60.0, 1)

        week_words = 0
        week_dictations = 0
        week_wpm_sum = 0
        daily_series: list[dict[str, Any]] = []
        for offset in range(6, -1, -1):
            day_date = date.today() - timedelta(days=offset)
            day_key = day_date.isoformat()
            day = self._data["days"].get(day_key, {})
            d_count = int(day.get("dictations", 0))
            d_words = int(day.get("words", 0))
            week_words += d_words
            week_dictations += d_count
            week_wpm_sum += int(day.get("wpm_sum", 0))
            daily_series.append(
                {
                    "date": day_key,
                    "label": day_date.strftime("%a"),
                    "dictations": d_count,
                    "words": d_words,
                }
            )

        week_avg_wpm = (
            int(week_wpm_sum / week_dictations) if week_dictations else 0
        )

        app_totals: dict[str, int] = dict(self._data.get("app_totals", {}))
        top_apps = sorted(app_totals.items(), key=lambda x: x[1], reverse=True)[:6]

        total_dictations = sum(
            int(d.get("dictations", 0)) for d in self._data["days"].values()
        )
        total_words = sum(int(d.get("words", 0)) for d in self._data["days"].values())

        return {
            "today_dictations": today_dictations,
            "today_words": today_words,
            "today_avg_wpm": today_avg_wpm,
            "today_duration_min": today_duration_min,
            "week_words": week_words,
            "week_dictations": week_dictations,
            "week_avg_wpm": week_avg_wpm,
            "streak_days": self._compute_streak(),
            "top_apps": top_apps,
            "daily_series": daily_series,
            "total_dictations": total_dictations,
            "total_words": total_words,
        }

    def _compute_streak(self) -> int:
        """Zählt aufeinanderfolgende Tage mit mindestens einem Diktat (heute rückwärts)."""
        streak = 0
        cursor = date.today()
        while True:
            day = self._data["days"].get(cursor.isoformat(), {})
            if int(day.get("dictations", 0)) <= 0:
                break
            streak += 1
            cursor -= timedelta(days=1)
        return streak

"""Tests für UsageStatsService."""

import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

import src.services.usage_stats as usage_stats_mod
from src.services.usage_stats import UsageStatsService


def test_record_and_streak():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "usage_stats.json"
        old_path = usage_stats_mod._STATS_PATH
        usage_stats_mod._STATS_PATH = path
        try:
            svc = UsageStatsService()
            svc.record_dictation(120, 95, 45.0, app_key="slack")
            svc.record_dictation(80, 110, 30.0, app_key="OUTLOOK")

            insights = svc.get_insights()
            assert insights["today_words"] == 200
            assert insights["today_dictations"] == 2
            assert insights["streak_days"] == 1
            assert ("slack", 1) in insights["top_apps"]

            yesterday = (date.today() - timedelta(days=1)).isoformat()
            svc._data["days"][yesterday] = {
                "dictations": 1, "words": 10, "wpm_sum": 80, "duration_s": 5.0, "apps": {}
            }
            svc._save()
            assert svc.get_insights()["streak_days"] == 2
        finally:
            usage_stats_mod._STATS_PATH = old_path


def test_today_summary_with_streak():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "usage_stats.json"
        old_path = usage_stats_mod._STATS_PATH
        usage_stats_mod._STATS_PATH = path
        try:
            svc = UsageStatsService()
            svc.record_dictation(50, 90, 20.0)
            summary = svc.today_summary()
            assert "Wörter" in summary
            assert "WPM" in summary

            svc2 = UsageStatsService()
            assert svc2.get_insights()["today_words"] == 50
        finally:
            usage_stats_mod._STATS_PATH = old_path

# -*- coding: utf-8 -*-
"""
conftest.py
Pytest-Fixtures für die E2E-Tests von SurepriseAi.
"""

import json
import shutil
import time
import pytest
from pathlib import Path
from app_runner import AppRunner

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config.json"
CONFIG_BACKUP_PATH = ROOT_DIR / "config.json.bak"


@pytest.fixture(scope="session", autouse=True)
def session_config_backup():
    """Sichert die config.json vor dem Testlauf und stellt sie danach wieder her."""
    backup_created = False
    if CONFIG_PATH.exists():
        shutil.copy2(CONFIG_PATH, CONFIG_BACKUP_PATH)
        backup_created = True
    yield
    if backup_created and CONFIG_BACKUP_PATH.exists():
        shutil.move(CONFIG_BACKUP_PATH, CONFIG_PATH)
    elif not backup_created and CONFIG_PATH.exists():
        try:
            CONFIG_PATH.unlink()
        except OSError:
            pass


@pytest.fixture(autouse=True)
def reset_test_config():
    """Setzt testkritische Config-Werte vor jedem Test auf einen sauberen Stand."""
    example_path = ROOT_DIR / "config.example.json"
    example = {}
    if example_path.exists():
        with open(example_path, "r", encoding="utf-8") as f:
            example = json.load(f)

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = dict(example)

    data["push_to_talk"] = False
    data["enable_global_hotkey"] = True
    data["ollama_url"] = example.get("ollama_url", "http://localhost:11434")
    data["ollama_polishing"] = example.get("ollama_polishing", False)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    yield
    # Nach dem Test kritische Werte zurücksetzen (Tests dürfen config nicht dauerhaft korrumpieren)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            after = json.load(f)
        after["ollama_url"] = example.get("ollama_url", "http://localhost:11434")
        after["ollama_polishing"] = example.get("ollama_polishing", False)
        after["push_to_talk"] = example.get("push_to_talk", True)
        after["enable_global_hotkey"] = True
        if after.get("recording_device") in ("Mic-A", "Ungueltiges_Geraet"):
            after["recording_device"] = "default"
        if "invalid-url" in str(after.get("ollama_url", "")):
            after["ollama_url"] = example.get("ollama_url", "http://localhost:11434")
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(after, f, indent=4)
    except OSError:
        pass


@pytest.fixture
def config_manager():
    """Fixture zur sicheren Manipulation der config.json."""
    class ConfigManager:
        def read(self):
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            example = ROOT_DIR / "config.example.json"
            if example.exists():
                with open(example, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}

        def write(self, data):
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        def update_key(self, key, value):
            data = self.read()
            data[key] = value
            self.write(data)
    return ConfigManager()


@pytest.fixture
def app_runner():
    """Bietet eine gesteuerte Instanz der App für die Tests."""
    runner = AppRunner()
    yield runner
    runner.stop()
    # pynput-Global-Hook braucht Zeit zum Freigeben (Windows)
    time.sleep(2.0)

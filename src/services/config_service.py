"""
config_service.py
Verwaltet die Anwendungskonfiguration (config.json).
Liest, schreibt und stellt typsichere Zugriffsmethoden bereit.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from src.utils.app_paths import config_path as _config_file, ensure_first_run_config, models_dir

# Standardwerte – werden verwendet, wenn config.json fehlt
_DEFAULTS: dict[str, Any] = {
    "ollama_url":              "http://localhost:11434",
    "ollama_model":            "gemma2:2b",
    "transcription_engine":    "parakeet",
    "transcription_model":     "parakeet-tdt-0.6b-v3",
    "whisper_model_size":      "tiny",
    "selected_style":          "concise",
    "auto_copy_to_clipboard":  True,
    "auto_inject_text":        True,
    "personal_vocabulary":     [],
    "word_replacements":       [],
    "theme_mode":              "system",
    "recording_device":        "default",
    "global_hotkey":           "f8",
    "enable_global_hotkey":    True,
    "enable_dynamic_island":   True,
    "dynamic_island_position": "top_center",
    "accent_color":            "indigo",
    "font_family":             "segoe_ui",
    "border_radius":           18,
    "animation_speed":         "normal",
    "ollama_polishing":        True,
    "polishing_timeout_s":     30,
    "push_to_talk":            False,
    "transcription_language":  "auto",
    "translate_to_english":    False,
    "enable_app_modes":        True,
    "app_modes": {
        "OUTLOOK": "formal",
        "slack":   "business",
        "teams":   "business",
        "discord": "casual",
        "notepad": "concise",
    },
    "enable_mini_fab":         True,
    "use_windows_accent":      True,
    "show_privacy_badge":      True,
    "dictation_history_max":   50,
    "enable_screen_context":   False,
    "enable_selected_text_context": True,
    "selected_text_max_chars": 800,
    "screen_context_mode":     "active_window",
    "screen_context_max_chars": 1200,
    "screen_context_timeout_s": 3,
    "check_updates_on_startup":  True,
}


class ConfigService:
    """Singleton-artiger Konfigurations-Service."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self.load()

    # ── Laden & Speichern ────────────────────────────────────────────────────

    def load(self) -> None:
        """Liest config.json und merged mit Standardwerten."""
        ensure_first_run_config()
        path = _config_file()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Defaults als Basis, dann überschreiben
                self._config = {**_DEFAULTS, **data}
            except (json.JSONDecodeError, OSError) as e:
                print(f"[Config] Fehler beim Laden: {e} – nutze Defaults")
                self._config = dict(_DEFAULTS)
        else:
            self._config = dict(_DEFAULTS)
            self.save()  # Initiale config.json anlegen

    def save(self) -> None:
        """Schreibt die aktuelle Konfiguration in config.json."""
        path = _config_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except OSError as e:
            print(f"[Config] Fehler beim Speichern: {e}")

    # ── Getter ───────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Liest einen Konfigurationswert."""
        return self._config.get(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        return str(self._config.get(key, default))

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self._config.get(key, default)
        return bool(val)

    def get_int(self, key: str, default: int = 0) -> int:
        return int(self._config.get(key, default))

    def get_list(self, key: str) -> list:
        val = self._config.get(key, [])
        return val if isinstance(val, list) else []

    # ── Setter ───────────────────────────────────────────────────────────────

    def set(self, key: str, value: Any, autosave: bool = True) -> None:
        """Setzt einen Konfigurationswert und speichert optional."""
        self._config[key] = value
        if autosave:
            self.save()

    # ── Bequeme Properties ───────────────────────────────────────────────────

    @property
    def ollama_url(self) -> str:
        return self.get_str("ollama_url")

    @property
    def ollama_model(self) -> str:
        return self.get_str("ollama_model")

    @property
    def transcription_engine(self) -> str:
        return self.get_str("transcription_engine", "parakeet")

    @property
    def selected_style(self) -> str:
        return self.get_str("selected_style", "concise")

    @selected_style.setter
    def selected_style(self, value: str) -> None:
        self.set("selected_style", value)

    @property
    def auto_copy(self) -> bool:
        return self.get_bool("auto_copy_to_clipboard", True)

    @property
    def global_hotkey(self) -> str:
        return self.get_str("global_hotkey", "f8")

    @property
    def hotkey_enabled(self) -> bool:
        return self.get_bool("enable_global_hotkey", True)

    @property
    def push_to_talk(self) -> bool:
        return self.get_bool("push_to_talk", False)

    @property
    def ollama_polishing(self) -> bool:
        return self.get_bool("ollama_polishing", True)

    @property
    def polishing_timeout(self) -> int:
        return self.get_int("polishing_timeout_s", 30)

    @property
    def transcription_language(self) -> Optional[str]:
        val = self.get_str("transcription_language", "auto")
        return None if val == "auto" else val

    @property
    def translate_to_english(self) -> bool:
        return self.get_bool("translate_to_english", False)

    @property
    def models_dir(self) -> Path:
        return models_dir()

    @property
    def parakeet_model_dir(self) -> Path:
        return self.models_dir / "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"


# Globale Singleton-Instanz
config = ConfigService()

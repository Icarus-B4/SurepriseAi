"""
recording_sound_service.py
Feedback-Sounds beim Start/Stopp der Diktat-Aufnahme.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from src.services.config_service import config
from src.utils.app_paths import install_root

_SOUND_LABELS: dict[str, str] = {
    "start.mp3": "Standard Start",
    "end.mp3": "Standard Stopp",
    "aufnahme_open.ogg": "Öffnen",
    "aufnahme_close.ogg": "Schließen",
    "select.ogg": "Auswahl",
    "confirm.ogg": "Bestätigung",
    "pluck.ogg": "Pluck",
    "tick.ogg": "Tick",
    "click.ogg": "Klick",
}

_SUPPORTED_SUFFIXES = {".mp3", ".ogg", ".wav"}


class RecordingSoundService(QObject):
    """Spielt konfigurierbare UI-Sounds für Aufnahme-Events ab."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)
        self._apply_volume()

    @staticmethod
    def sounds_dir() -> Path:
        return install_root() / "sounds"

    @classmethod
    def list_sounds(cls) -> list[tuple[str, str]]:
        """Liefert [(dateiname, anzeigename), ...] sortiert nach Label."""
        directory = cls.sounds_dir()
        if not directory.is_dir():
            return []

        items: list[tuple[str, str]] = []
        for path in sorted(directory.iterdir()):
            if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
                continue
            label = _SOUND_LABELS.get(path.name, path.stem.replace("_", " ").title())
            items.append((path.name, label))
        return items

    @classmethod
    def sound_filenames(cls) -> list[str]:
        return [name for name, _ in cls.list_sounds()]

    def play_start(self) -> None:
        if not config.get_bool("enable_recording_sounds", True):
            return
        self._play(config.get_str("recording_start_sound", "start.mp3"))

    def play_stop(self) -> None:
        if not config.get_bool("enable_recording_sounds", True):
            return
        self._play(config.get_str("recording_stop_sound", "end.mp3"))

    def preview(self, filename: str) -> None:
        """Vorschau in den Einstellungen – unabhängig vom Hauptschalter."""
        self._play(filename, force=True)

    def refresh_volume(self) -> None:
        self._apply_volume()

    def _apply_volume(self) -> None:
        volume = max(0, min(100, config.get_int("recording_sound_volume", 75)))
        self._output.setVolume(volume / 100.0)

    def _play(self, filename: str, *, force: bool = False) -> None:
        if not filename:
            return
        if not force and not config.get_bool("enable_recording_sounds", True):
            return

        path = self.sounds_dir() / filename
        if not path.is_file():
            print(f"[Sound] Datei nicht gefunden: {path}")
            return

        self._apply_volume()
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self._player.play()

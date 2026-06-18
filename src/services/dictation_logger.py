"""
dictation_logger.py
Detailliertes Diagnose-Log für Aufnahme, UI und Abstürze.
Dateien: Desktop\\SurepriseAi-Diktat.log + %APPDATA%\\SurepriseAi\\dictation.log
         (Dev: zusätzlich .agent\\dictation.log)
"""

from __future__ import annotations

import os
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

from src.utils.app_paths import desktop_dir, install_root, is_frozen, user_data_dir
from src.version import __version__

_LOG_FILENAME = "SurepriseAi-Diktat.log"
_session_id: str = ""
_dictation_id: str = ""
_log_paths: list[Path] | None = None
_boot_written = False


def _build_log_paths() -> list[Path]:
    paths: list[Path] = []
    desktop_log = desktop_dir() / _LOG_FILENAME
    paths.append(desktop_log)
    paths.append(user_data_dir() / "dictation.log")
    if not is_frozen():
        paths.append(install_root() / ".agent" / "dictation.log")

    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def all_log_paths() -> list[Path]:
    global _log_paths
    if _log_paths is None:
        _log_paths = _build_log_paths()
    return list(_log_paths)


def primary_log_path() -> Path:
    return all_log_paths()[0]


def desktop_log_path() -> Path:
    return desktop_dir() / _LOG_FILENAME


def appdata_log_path() -> Path:
    return user_data_dir() / "dictation.log"


def current_session_id() -> str:
    return _session_id


def current_dictation_id() -> str:
    return _dictation_id


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _append_line(line: str, *, sync: bool = False) -> list[str]:
    """Schreibt eine Zeile in alle Log-Ziele. Gibt Fehler pro Pfad zurück."""
    errors: list[str] = []
    for path in all_log_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8", buffering=1) as fh:
                fh.write(line + "\n")
                fh.flush()
                if sync:
                    os.fsync(fh.fileno())
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    return errors


def write(message: str, *, also_print: bool = True, sync: bool = False) -> None:
    prefix = ""
    if _dictation_id:
        prefix = f"[{_dictation_id}] "
    elif _session_id:
        prefix = f"[{_session_id}] "
    line = f"{_stamp()}  {prefix}{message}"
    if also_print:
        try:
            print(f"[Diktat] {message}")
        except Exception:
            pass
    errors = _append_line(line, sync=sync)
    if errors and also_print:
        for err in errors:
            try:
                print(f"[Diktat] LOG-SCHREIBFEHLER {err}", file=sys.stderr)
            except Exception:
                pass


def write_boot_probe() -> None:
    """Sofort beim Start – prüft, ob Log-Dateien beschreibbar sind."""
    global _boot_written
    if _boot_written:
        return
    _boot_written = True
    paths = all_log_paths()
    write("=" * 72, also_print=False, sync=True)
    write(
        f"BOOT pid={os.getpid()} python={sys.version.split()[0]} cwd={os.getcwd()}",
        also_print=False,
        sync=True,
    )
    for path in paths:
        write(f"Log-Ziel: {path}", also_print=False, sync=True)
    write("Crash-Diagnose aktiv (faulthandler + Exception-Hooks)", also_print=False, sync=True)
    write("=" * 72, also_print=False, sync=True)


def write_crash(kind: str, detail: str) -> None:
    """Markiert einen schweren Fehler / Absturz im Log."""
    banner = "!" * 72
    write(banner, also_print=True, sync=True)
    write(f"CRASH / FATAL: {kind}", also_print=True, sync=True)
    for chunk in detail.strip().splitlines():
        write(chunk, also_print=False, sync=False)
    write(banner, also_print=True, sync=True)
    _append_line("", sync=True)


def write_exception(context: str) -> None:
    write_crash(context, traceback.format_exc())


def write_session_header(phase: str = "App-Start") -> None:
    global _session_id
    _session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    write("=" * 72, also_print=False, sync=True)
    write(phase, also_print=False, sync=True)
    write(f"Version: {__version__}", also_print=False, sync=True)
    write(f"Session: {_session_id}", also_print=False, sync=True)
    write(f"Frozen (PyInstaller): {is_frozen()}", also_print=False, sync=True)
    write(f"sys.executable: {sys.executable}", also_print=False, sync=True)
    write(f"install_root: {install_root()}", also_print=False, sync=True)
    write(f"Desktop-Ordner: {desktop_dir()}", also_print=False, sync=True)
    for path in all_log_paths():
        write(f"Log-Datei: {path}", also_print=False, sync=True)
    write(f"PID: {os.getpid()}", also_print=False, sync=True)
    write(f"CWD: {os.getcwd()}", also_print=False, sync=True)
    try:
        from src.services.config_service import config
        from src.utils.app_paths import config_path

        write(f"Config-Pfad: {config_path()}", also_print=False, sync=True)
        write(
            "Config: "
            f"engine={config.transcription_engine}, "
            f"whisper_size={config.get_str('whisper_model_size', '?')}, "
            f"lang={config.get_str('transcription_language', 'auto')}, "
            f"hotkey={config.global_hotkey}, "
            f"ptt={config.push_to_talk}, "
            f"device={config.get_str('recording_device', 'default')}",
            also_print=False,
            sync=True,
        )
    except Exception as exc:
        write(f"Config-Snapshot fehlgeschlagen: {exc}", also_print=False, sync=True)
    write("=" * 72, also_print=False, sync=True)


def begin_dictation() -> str:
    global _dictation_id
    _dictation_id = "D" + uuid.uuid4().hex[:8]
    write("--- Diktat gestartet ---", sync=True)
    return _dictation_id


def end_dictation(outcome: str) -> None:
    write(f"--- Diktat beendet: {outcome} ---", sync=True)
    global _dictation_id
    _dictation_id = ""


def log_audio(label: str, audio: Optional[np.ndarray]) -> None:
    if audio is None:
        write(f"{label}: audio=None")
        return
    flat = np.asarray(audio, dtype=np.float32).flatten()
    n = len(flat)
    if n == 0:
        write(f"{label}: 0 Samples (leer)")
        return
    rms = float(np.sqrt(np.mean(flat ** 2)))
    peak = float(np.max(np.abs(flat)))
    zc = int(np.sum(np.abs(np.diff(np.signbit(flat)))))
    write(
        f"{label}: samples={n}, "
        f"dauer={n / 16000:.2f}s, "
        f"rms={rms:.5f}, peak={peak:.5f}, "
        f"dtype={audio.dtype}, "
        f"aktivitaet_zc={zc}"
    )
    if peak < 0.002:
        write(f"{label}: WARNUNG sehr leises Signal (peak < 0.002) – VAD koennte alles verwerfen")
    elif peak < 0.01:
        write(f"{label}: HINWEIS niedrige Pegel (peak < 0.01)")


def log_transcription_attempt(
    engine: str,
    *,
    vad: Optional[bool] = None,
    partial: bool = False,
    text: str = "",
    segment_count: int = 0,
    error: Optional[str] = None,
) -> None:
    mode = "partial" if partial else "final"
    vad_s = "n/a" if vad is None else str(vad)
    preview = (text[:80] + "…") if len(text) > 80 else text
    write(
        f"Transkription [{mode}] engine={engine} vad={vad_s} "
        f"segments={segment_count} zeichen={len(text)} text='{preview}'"
    )
    if error:
        write(f"Transkription FEHLER: {error}", sync=True)


def log_kv(label: str, **fields: Any) -> None:
    parts = [f"{k}={v!r}" for k, v in fields.items()]
    write(f"{label}: " + ", ".join(parts))

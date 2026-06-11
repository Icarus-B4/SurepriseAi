"""
dictation_logger.py
Detailliertes Diagnose-Log für Aufnahme und Transkription.
Dateien: Desktop + %APPDATA%\\SurepriseAi\\dictation.log
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

from src.utils.app_paths import install_root, is_frozen, user_data_dir
from src.version import __version__

_DESKTOP_LOG = (
    Path(os.environ.get("USERPROFILE", Path.home()))
    / "Desktop"
    / "SurepriseAi-Diktat.log"
)
_APPDATA_LOG = user_data_dir() / "dictation.log"

_session_id: str = ""
_dictation_id: str = ""


def desktop_log_path() -> Path:
    return _DESKTOP_LOG


def appdata_log_path() -> Path:
    return _APPDATA_LOG


def current_session_id() -> str:
    return _session_id


def current_dictation_id() -> str:
    return _dictation_id


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def write(message: str, *, also_print: bool = True) -> None:
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
    for path in (_DESKTOP_LOG, _APPDATA_LOG):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass


def write_exception(context: str) -> None:
    write(f"{context}:\n{traceback.format_exc()}", also_print=False)


def write_session_header(phase: str = "App-Start") -> None:
    global _session_id
    _session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    write("=" * 72, also_print=False)
    write(phase, also_print=False)
    write(f"Version: {__version__}", also_print=False)
    write(f"Session: {_session_id}", also_print=False)
    write(f"Frozen (PyInstaller): {is_frozen()}", also_print=False)
    write(f"sys.executable: {sys.executable}", also_print=False)
    write(f"install_root: {install_root()}", also_print=False)
    write(f"Desktop-Log: {_DESKTOP_LOG}", also_print=False)
    write(f"AppData-Log: {_APPDATA_LOG}", also_print=False)
    write(f"PID: {os.getpid()}", also_print=False)
    write(f"CWD: {os.getcwd()}", also_print=False)
    try:
        from src.services.config_service import config

        from src.utils.app_paths import config_path

        write(f"Config-Pfad: {config_path()}", also_print=False)
        write(
            "Config: "
            f"engine={config.transcription_engine}, "
            f"whisper_size={config.get_str('whisper_model_size', '?')}, "
            f"lang={config.get_str('transcription_language', 'auto')}, "
            f"hotkey={config.global_hotkey}, "
            f"ptt={config.push_to_talk}, "
            f"device={config.get_str('recording_device', 'default')}",
            also_print=False,
        )
    except Exception as exc:
        write(f"Config-Snapshot fehlgeschlagen: {exc}", also_print=False)
    write("=" * 72, also_print=False)


def begin_dictation() -> str:
    global _dictation_id
    _dictation_id = "D" + uuid.uuid4().hex[:8]
    write("--- Diktat gestartet ---")
    return _dictation_id


def end_dictation(outcome: str) -> None:
    write(f"--- Diktat beendet: {outcome} ---")
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
    zc = int(np.sum(np.abs(np.diff(np.signbit(flat)))))  # grobe Aktivitaet
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
        write(f"Transkription FEHLER: {error}")


def log_kv(label: str, **fields: Any) -> None:
    parts = [f"{k}={v!r}" for k, v in fields.items()]
    write(f"{label}: " + ", ".join(parts))

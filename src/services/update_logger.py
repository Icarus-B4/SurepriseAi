"""
update_logger.py
Diagnose-Log für Auto-Update – Desktop + AppData (mit Zeitstempel).
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from src.utils.app_paths import install_root, is_frozen, user_data_dir
from src.version import __version__

_DESKTOP_LOG = (
    Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop" / "SurepriseAi-Update.log"
)
_APPDATA_LOG = user_data_dir() / "update.log"


def desktop_log_path() -> Path:
    return _DESKTOP_LOG


def write(message: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {message}"
    print(f"[Update] {message}")
    for path in (_DESKTOP_LOG, _APPDATA_LOG):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass


def write_exception(context: str) -> None:
    write(f"{context}:\n{traceback.format_exc()}")


def write_session_header(phase: str) -> None:
    write("=" * 60)
    write(phase)
    write(f"Version: {__version__}")
    write(f"Frozen (PyInstaller): {is_frozen()}")
    write(f"sys.executable: {sys.executable}")
    write(f"install_root: {install_root()}")
    write(f"Desktop-Log: {_DESKTOP_LOG}")
    write(f"AppData-Log: {_APPDATA_LOG}")
    write(f"PID: {os.getpid()}")
    write(f"CWD: {os.getcwd()}")

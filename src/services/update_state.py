"""
update_state.py
Kurzer Schutz gegen Update-Schleifen – blockiert nicht dauerhaft.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.services import update_logger
from src.services.update_service import parse_version
from src.utils.app_paths import user_data_dir
from src.version import __version__

PENDING_FILE = user_data_dir() / "update_pending.json"
_ACTIVE_INSTALL_S = 120  # 2 min – vermutlich läuft Installation noch
_STALE_PENDING_S = 300  # 5 min – fehlgeschlagen, Pending verwerfen


def mark_pending(target_version: str, setup_path: str) -> None:
    PENDING_FILE.write_text(
        json.dumps(
            {
                "target": target_version,
                "from_version": __version__,
                "setup": setup_path,
                "started_at": time.time(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def clear_pending() -> None:
    try:
        PENDING_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def _read_pending() -> dict | None:
    if not PENDING_FILE.exists():
        return None
    try:
        return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        clear_pending()
        return None


def reconcile_pending() -> None:
    """Beim Start: erfolgreiches Update oder veraltetes Pending aufräumen."""
    data = _read_pending()
    if not data:
        return

    target = str(data.get("target", ""))
    age = time.time() - float(data.get("started_at", 0))

    if target and parse_version(__version__) >= parse_version(target):
        clear_pending()
        update_logger.write(f"Pending v{target} entfernt – jetzt v{__version__}")
        return

    if age > _STALE_PENDING_S:
        clear_pending()
        update_logger.write(
            f"Veraltetes Pending v{target} entfernt "
            f"(nach {int(age)} s, noch v{__version__})"
        )


def is_duplicate_attempt(target_version: str) -> bool:
    data = _read_pending()
    if not data:
        return False
    target = str(data.get("target", ""))
    age = time.time() - float(data.get("started_at", 0))
    if age > _ACTIVE_INSTALL_S:
        return False
    return (
        target == target_version
        and parse_version(__version__) < parse_version(target_version)
    )


def should_auto_update(*, manual: bool = False) -> tuple[bool, str]:
    """manual=True: Pending immer verwerfen und erneut versuchen."""
    reconcile_pending()

    if manual:
        if PENDING_FILE.exists():
            data = _read_pending()
            target = str(data.get("target", "?")) if data else "?"
            clear_pending()
            update_logger.write(f"Manueller Check: Pending v{target} verworfen")
        return True, ""

    data = _read_pending()
    if not data:
        return True, ""

    target = str(data.get("target", "?"))
    age = time.time() - float(data.get("started_at", 0))

    if parse_version(__version__) >= parse_version(target):
        clear_pending()
        return True, ""

    if age < _ACTIVE_INSTALL_S:
        return False, (
            f"Startup-Check übersprungen: Installation v{target} "
            f"vermutlich aktiv (vor {int(age)} s)"
        )

    clear_pending()
    return True, f"Altes Pending v{target} verworfen – Startup-Check läuft"

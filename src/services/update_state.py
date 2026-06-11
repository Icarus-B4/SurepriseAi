"""
update_state.py
Verhindert Update-Schleifen (Pending-Marker + Cooldown).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.services.update_service import parse_version
from src.utils.app_paths import user_data_dir
from src.version import __version__

PENDING_FILE = user_data_dir() / "update_pending.json"
_COOLDOWN_S = 6 * 3600  # 6 h kein Auto-Retry nach fehlgeschlagenem Versuch


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


def clear_if_updated() -> None:
    if not PENDING_FILE.exists():
        return
    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        clear_pending()
        return
    target = str(data.get("target", ""))
    if target and parse_version(__version__) >= parse_version(target):
        clear_pending()


def is_duplicate_attempt(target_version: str) -> bool:
    if not PENDING_FILE.exists():
        return False
    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    target = str(data.get("target", ""))
    return (
        target == target_version
        and parse_version(__version__) < parse_version(target_version)
    )


def should_auto_update(*, manual: bool = False) -> tuple[bool, str]:
    """False = kein automatischer Download/Check (Schleifen-Schutz)."""
    clear_if_updated()
    if not PENDING_FILE.exists():
        return True, ""

    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        clear_pending()
        return True, ""

    target = str(data.get("target", "?"))
    age = time.time() - float(data.get("started_at", 0))

    if parse_version(__version__) >= parse_version(target):
        clear_pending()
        return True, ""

    if age > _COOLDOWN_S:
        clear_pending()
        return True, f"Pending abgelaufen nach {int(age)}s – erneuter Versuch erlaubt"

    if manual:
        return False, (
            f"Update v{target} wurde bereits gestartet (vor {int(age)} s).\n"
            "Bitte warten oder SurepriseAi-Setup.exe manuell ausführen."
        )

    return False, (
        f"Startup-Check übersprungen: Update v{target} ausstehend "
        f"(seit {int(age)} s, installiert v{__version__})"
    )

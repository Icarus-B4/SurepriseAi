"""
ollama_launcher.py
Ollama auf Windows finden, Status prüfen und im Hintergrund starten.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

from src.services.config_service import config

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def is_running(url: Optional[str] = None) -> bool:
    """True wenn die Ollama-API erreichbar ist."""
    base = (url or config.ollama_url).rstrip("/")
    try:
        req = urllib.request.Request(f"{base}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def find_ollama_executable() -> Optional[Path]:
    """Sucht die Ollama-Installation (PATH oder Standard-Windows-Pfad)."""
    which = shutil.which("ollama")
    if which:
        return Path(which)

    local_app = os.environ.get("LOCALAPPDATA", "")
    if not local_app:
        return None

    ollama_dir = Path(local_app) / "Programs" / "Ollama"
    for name in ("Ollama.exe", "ollama.exe"):
        candidate = ollama_dir / name
        if candidate.is_file():
            return candidate
    return None


def start_ollama(*, wait_s: float = 12.0) -> tuple[bool, str]:
    """
    Startet Ollama im Hintergrund und wartet kurz auf die API.

    Returns:
        (erfolg, nutzer_message)
    """
    if is_running():
        return True, "Ollama läuft bereits."

    exe = find_ollama_executable()
    if exe is None:
        return False, (
            "Ollama nicht gefunden. Bitte von ollama.com installieren "
            "oder „ollama“ in den PATH legen."
        )

    name = exe.name.lower()
    cmd = [str(exe), "serve"] if name == "ollama.exe" else [str(exe)]

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            cwd=str(exe.parent),
        )
    except OSError as exc:
        return False, f"Ollama konnte nicht gestartet werden: {exc}"

    deadline = time.time() + wait_s
    while time.time() < deadline:
        if is_running():
            return True, "Ollama ist bereit."
        time.sleep(0.5)

    return False, (
        "Ollama wurde gestartet, antwortet aber noch nicht. "
        "Bitte einige Sekunden warten und erneut prüfen."
    )


def stop_ollama(*, wait_s: float = 8.0) -> tuple[bool, str]:
    """Beendet Ollama-Prozesse unter Windows und prüft die API."""
    if not is_running():
        return True, "Ollama läuft nicht."

    if sys.platform == "win32":
        for image in ("ollama.exe", "Ollama.exe"):
            subprocess.run(
                ["taskkill", "/IM", image, "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_CREATE_NO_WINDOW,
            )
    else:
        subprocess.run(
            ["pkill", "-f", "ollama"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    deadline = time.time() + wait_s
    while time.time() < deadline:
        if not is_running():
            return True, "Ollama wurde beendet."
        time.sleep(0.5)

    return False, (
        "Ollama antwortet noch. "
        "Beende den Dienst ggf. über das Tray-Icon."
    )

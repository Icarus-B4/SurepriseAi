"""
ollama_launcher.py
Ollama auf Windows finden, Status prüfen und im Hintergrund starten/beenden.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from src.services.config_service import config

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_API_TIMEOUT_S = 1.5


def _api_base(url: Optional[str] = None) -> str:
    return (url or config.ollama_url).rstrip("/")


def _api_port(url: Optional[str] = None) -> int:
    parsed = urllib.parse.urlparse(_api_base(url))
    if parsed.port:
        return parsed.port
    return 11434


def is_running(url: Optional[str] = None) -> bool:
    """True wenn die Ollama-API erreichbar ist."""
    try:
        req = urllib.request.Request(f"{_api_base(url)}/api/tags")
        with urllib.request.urlopen(req, timeout=_API_TIMEOUT_S) as response:
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


def _run_quiet(cmd: list[str], *, timeout_s: float = 6.0) -> None:
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_s,
            creationflags=_CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except Exception:
        pass


def _kill_windows_processes() -> None:
    """Beendet typische Ollama-Prozesse inkl. Kindprozesse."""
    # Tray-App zuerst – sonst startet sie ollama.exe oft neu.
    for image in ("Ollama.exe", "ollama.exe", "ollama app.exe"):
        _run_quiet(["taskkill", "/F", "/T", "/IM", image])


def _kill_windows_port_listener(port: int) -> None:
    """Beendet den Prozess, der auf dem Ollama-Port lauscht."""
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=_CREATE_NO_WINDOW,
        )
    except Exception:
        return

    suffix = f":{port}"
    for line in result.stdout.splitlines():
        upper = line.upper()
        if suffix not in line or "LISTENING" not in upper:
            continue
        match = re.search(r"(\d+)\s*$", line.strip())
        if not match:
            continue
        _run_quiet(["taskkill", "/F", "/T", "/PID", match.group(1)])


def start_ollama(*, wait_s: float = 12.0) -> tuple[bool, str]:
    """Startet Ollama im Hintergrund und wartet kurz auf die API."""
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
        time.sleep(0.4)

    return False, (
        "Ollama wurde gestartet, antwortet aber noch nicht. "
        "Bitte einige Sekunden warten und erneut prüfen."
    )


def stop_ollama(*, wait_s: float = 6.0) -> tuple[bool, str]:
    """Beendet Ollama unter Windows und prüft, ob die API offline ist."""
    if not is_running():
        return True, "Ollama läuft nicht."

    port = _api_port()

    if sys.platform == "win32":
        _kill_windows_processes()
        _kill_windows_port_listener(port)
    else:
        _run_quiet(["pkill", "-f", "ollama"])

    deadline = time.time() + wait_s
    while time.time() < deadline:
        if not is_running():
            return True, "Ollama wurde beendet."
        time.sleep(0.35)

    # Nochmals härter beenden, falls der Tray-Dienst neu gestartet hat.
    if sys.platform == "win32":
        _kill_windows_processes()
        _kill_windows_port_listener(port)
        time.sleep(0.6)
        if not is_running():
            return True, "Ollama wurde beendet."

    return False, (
        "Ollama läuft noch im Hintergrund. "
        "Rechtsklick auf das Tray-Icon → Beenden."
    )

"""
app_paths.py
Installations- und Benutzerdaten-Pfade (Dev vs. PyInstaller-Bundle).
"""

import os
import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    """True wenn die App als PyInstaller-EXE läuft."""
    return getattr(sys, "frozen", False)


def install_root() -> Path:
    """Projektstamm (Dev) oder EXE-Ordner (Installation)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundle_path(*parts: str) -> Path:
    """
    Sucht eine gebündelte Ressource (Dev, PyInstaller onedir/_internal, onefile).
    Gibt den ersten existierenden Pfad zurück, sonst den wahrscheinlichsten Kandidaten.
    """
    rel = Path(*parts)
    candidates: list[Path] = []

    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / rel)
        root = install_root()
        candidates.extend([root / rel, root / "_internal" / rel])
    else:
        candidates.append(install_root() / rel)

    for path in candidates:
        if path.exists():
            return path
    return candidates[0] if candidates else install_root() / rel


def sounds_dir() -> Path:
    """Ordner mit UI-Sounds (start/end, Kenney-Paket, …)."""
    return bundle_path("sounds")


def user_data_dir() -> Path:
    """Persistente Nutzerdaten (Config, Historie, Stats)."""
    if is_frozen():
        base = Path(os.environ.get("APPDATA", Path.home()))
        data = base / "SurepriseAi"
    else:
        data = install_root() / ".agent"
    data.mkdir(parents=True, exist_ok=True)
    return data


def config_path() -> Path:
    """Pfad zur config.json."""
    if is_frozen():
        return user_data_dir() / "config.json"
    return install_root() / "config.json"


def models_dir() -> Path:
    """ML-Modelle – neben der EXE oder im Projekt."""
    path = install_root() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_first_run_config() -> None:
    """Legt config.json aus config.example.json an (Erststart nach Installation)."""
    target = config_path()
    if target.exists():
        return
    example = install_root() / "config.example.json"
    if example.exists():
        shutil.copy(example, target)
        print(f"[Config] Erstkonfiguration angelegt: {target}")


def onboarding_marker_path() -> Path:
    return user_data_dir() / ".onboarding_done"


def needs_onboarding() -> bool:
    """True beim ersten Start nach Installation."""
    return not onboarding_marker_path().exists()


def mark_onboarding_done() -> None:
    onboarding_marker_path().touch()

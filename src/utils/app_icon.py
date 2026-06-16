"""
app_icon.py
Zentrale App-Icon-Auflösung (App_icon.png / SurepriseAi.ico) für Dev und Installation.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon

from src.utils.app_paths import bundle_path, install_root


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def icon_source_png() -> Path:
    """Quell-PNG im Projektroot."""
    return _project_root() / "App_icon.png"


def icon_candidates() -> list[Path]:
    """Suchreihenfolge: installiert → gebündelt → Dev-Build."""
    root = install_root()
    project = _project_root()
    return [
        root / "SurepriseAi.ico",
        bundle_path("App_icon.png"),
        bundle_path("SurepriseAi.ico"),
        root / "App_icon.png",
        project / "App_icon.png",
        project / "build" / "assets" / "app_icon.ico",
    ]


def resolve_icon_path() -> Path | None:
    for path in icon_candidates():
        if path.is_file():
            return path
    return None


def load_app_icon() -> QIcon:
    path = resolve_icon_path()
    if path is not None:
        return QIcon(str(path.resolve()))
    return QIcon()

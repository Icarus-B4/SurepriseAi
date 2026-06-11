"""
update_downloader.py
Lädt Installer von GitHub Releases in den Downloads-Ordner (versionierter Dateiname).
"""

import os
import re
import urllib.request
from pathlib import Path
from typing import Optional

from src.services import update_logger
from src.services.update_service import APP_UA, _ssl_context


def _versioned_dest(filename: str, target_version: str) -> Path:
    dest_dir = Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads"
    dest_dir.mkdir(parents=True, exist_ok=True)
    ver = re.sub(r"^v", "", target_version.strip(), flags=re.IGNORECASE)
    stem = Path(filename).stem
    return dest_dir / f"{stem}-v{ver}.exe"


def download_release_asset(
    url: str,
    filename: str,
    target_version: str = "",
) -> Optional[Path]:
    """Lädt Setup für die Zielversion – immer frisch, kein falscher Cache."""
    update_logger.write(f"download_release_asset: url={url}")
    update_logger.write(f"  filename={filename!r} target_version={target_version!r}")
    if not url:
        update_logger.write("Abbruch: leere URL")
        return None

    dest = (
        _versioned_dest(filename, target_version)
        if target_version
        else Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads" / filename
    )

    if dest.is_file():
        update_logger.write(f"Vorhandenes Setup für diese Version: {dest} – wird überschrieben")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": APP_UA()})
        with urllib.request.urlopen(req, timeout=180, context=_ssl_context()) as resp:
            data = resp.read()
        dest.write_bytes(data)
        update_logger.write(f"Download OK: {dest} ({len(data)} bytes)")
        return dest
    except Exception as exc:
        update_logger.write_exception(f"Download fehlgeschlagen ({exc})")
        return None

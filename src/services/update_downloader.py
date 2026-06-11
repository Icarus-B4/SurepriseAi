"""
update_downloader.py
Lädt Installer/ZIP von GitHub Releases in den Downloads-Ordner.
"""

import os
import urllib.request
from pathlib import Path
from typing import Optional

from src.services import update_logger
from src.services.update_service import APP_UA, _ssl_context


def download_release_asset(url: str, filename: str) -> Optional[Path]:
    """Lädt eine Release-Datei herunter und gibt den lokalen Pfad zurück."""
    update_logger.write(f"download_release_asset: url={url}")
    update_logger.write(f"  filename={filename!r}")
    if not url:
        update_logger.write("Abbruch: leere URL")
        return None
    dest_dir = Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    try:
        req = urllib.request.Request(url, headers={"User-Agent": APP_UA()})
        with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as resp:
            data = resp.read()
        dest.write_bytes(data)
        update_logger.write(f"Download OK: {dest} ({len(data)} bytes)")
        return dest
    except Exception as exc:
        update_logger.write_exception(f"Download fehlgeschlagen ({exc})")
        return None

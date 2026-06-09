"""
update_service.py
Prüft GitHub-Releases auf neuere SurepriseAi-Versionen.
"""

import json
import re
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

from src.version import GITHUB_REPO, __version__


@dataclass
class UpdateInfo:
    version: str
    page_url: str
    download_url: Optional[str]
    notes: str


def parse_version(version: str) -> tuple[int, ...]:
    """Wandelt 'v0.1.0' in (0, 1, 0) um."""
    nums = re.findall(r"\d+", version.lstrip("vV"))
    return tuple(int(n) for n in nums) if nums else (0,)


def is_newer(remote: str, local: str = __version__) -> bool:
    return parse_version(remote) > parse_version(local)


class UpdateService:
    """Asynchroner Update-Check über die GitHub-API."""

    def __init__(self) -> None:
        self._latest: Optional[UpdateInfo] = None

    @property
    def latest(self) -> Optional[UpdateInfo]:
        return self._latest

    def check_async(self, on_done: Callable[[Optional[UpdateInfo]], None]) -> None:
        threading.Thread(target=self._worker, args=(on_done,), daemon=True).start()

    def _worker(self, on_done: Callable[[Optional[UpdateInfo]], None]) -> None:
        info = self._fetch_latest()
        self._latest = info
        on_done(info)

    def _fetch_latest(self) -> Optional[UpdateInfo]:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/vnd.github+json", "User-Agent": APP_UA()},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"[Update] Prüfung fehlgeschlagen: {exc}")
            return None

        tag = str(data.get("tag_name", "")).strip()
        if not tag or not is_newer(tag):
            return None

        download = _pick_installer_asset(data.get("assets", []))
        return UpdateInfo(
            version=tag.lstrip("vV"),
            page_url=str(data.get("html_url", "")),
            download_url=download,
            notes=str(data.get("body", "")).strip()[:500],
        )


def APP_UA() -> str:
    from src.version import APP_NAME, __version__
    return f"{APP_NAME}/{__version__}"


def _pick_installer_asset(assets: list) -> Optional[str]:
    """Sucht ein Setup-EXE oder ZIP im Release."""
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        if name.endswith(".exe") or name.endswith(".zip"):
            return str(asset.get("browser_download_url", "")) or None
    return None

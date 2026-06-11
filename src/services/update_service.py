"""
update_service.py
Prüft GitHub-Releases auf neuere SurepriseAi-Versionen.
"""

import json
import re
import ssl
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


@dataclass
class UpdateCheckResult:
    """Ergebnis einer Update-Prüfung (Update, aktuell oder Fehler)."""

    info: Optional[UpdateInfo] = None
    error: Optional[str] = None


def parse_version(version: str) -> tuple[int, ...]:
    """Wandelt 'v0.1.0' in (0, 1, 0) um."""
    nums = re.findall(r"\d+", version.lstrip("vV"))
    return tuple(int(n) for n in nums) if nums else (0,)


def is_newer(remote: str, local: str = __version__) -> bool:
    return parse_version(remote) > parse_version(local)


def _ssl_context() -> ssl.SSLContext:
    """SSL-Kontext inkl. certifi für PyInstaller-Bundles."""
    from src.utils.ssl_bootstrap import certifi_bundle_path

    bundle = certifi_bundle_path()
    if bundle:
        return ssl.create_default_context(cafile=bundle)
    return ssl.create_default_context()


def _github_get(url: str, timeout: int = 12) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": APP_UA(),
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _release_from_payload(data: dict) -> Optional[UpdateInfo]:
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


class UpdateService:
    """Asynchroner Update-Check über die GitHub-API."""

    def __init__(self) -> None:
        self._latest: Optional[UpdateInfo] = None

    @property
    def latest(self) -> Optional[UpdateInfo]:
        return self._latest

    def check_async(self, on_done: Callable[[UpdateCheckResult], None]) -> None:
        threading.Thread(target=self._worker, args=(on_done,), daemon=True).start()

    def _worker(self, on_done: Callable[[UpdateCheckResult], None]) -> None:
        result = self._fetch_latest()
        if result.info:
            self._latest = result.info
        on_done(result)

    def _fetch_latest(self) -> UpdateCheckResult:
        base = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        try:
            data = _github_get(f"{base}/latest")
            info = _release_from_payload(data)
            return UpdateCheckResult(info=info)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                msg = f"GitHub API HTTP {exc.code}"
                print(f"[Update] Prüfung fehlgeschlagen: {msg}")
                return UpdateCheckResult(error=msg)
            print("[Update] /releases/latest → 404, Fallback auf Release-Liste")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ssl.SSLError) as exc:
            msg = str(exc)
            print(f"[Update] Prüfung fehlgeschlagen: {msg}")
            return UpdateCheckResult(error=msg)

        try:
            releases = _github_get(f"{base}?per_page=8")
            if not isinstance(releases, list):
                return UpdateCheckResult(error="Ungültige GitHub-Antwort")
            for entry in releases:
                if entry.get("draft") or entry.get("prerelease"):
                    continue
                info = _release_from_payload(entry)
                if info:
                    return UpdateCheckResult(info=info)
            return UpdateCheckResult()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                json.JSONDecodeError, ssl.SSLError) as exc:
            msg = str(exc)
            print(f"[Update] Fallback fehlgeschlagen: {msg}")
            return UpdateCheckResult(error=msg)


def APP_UA() -> str:
    from src.version import APP_NAME, __version__
    return f"{APP_NAME}/{__version__}"


def _pick_installer_asset(assets: list) -> Optional[str]:
    """Sucht Setup-EXE bevorzugt, sonst ZIP im Release."""
    zip_url: Optional[str] = None
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        url = str(asset.get("browser_download_url", "")) or None
        if not url:
            continue
        if name.endswith(".exe"):
            return url
        if name.endswith(".zip") and zip_url is None:
            zip_url = url
    return zip_url

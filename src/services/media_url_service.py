"""
media_url_service.py
Lädt Audio von YouTube/Vimeo o. Ä. via yt-dlp für die Transkription.
"""

import re
import tempfile
from pathlib import Path
from typing import Optional

# Unterstützte Plattformen (yt-dlp kann mehr – diese prüfen wir explizit)
_SUPPORTED_HOSTS = (
    "youtube.com",
    "youtu.be",
    "m.youtube.com",
    "music.youtube.com",
    "vimeo.com",
    "soundcloud.com",
    "tiktok.com",
    "twitch.tv",
)

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def normalize_url(text: str) -> str:
    """Trimmt Whitespace und entfernt umschließende Anführungszeichen."""
    url = text.strip().strip('"').strip("'")
    return url


def is_media_url(text: str) -> bool:
    """Prüft ob der Text wie eine unterstützte Medien-URL aussieht."""
    url = normalize_url(text)
    if not _URL_RE.match(url):
        return False
    lower = url.lower()
    return any(host in lower for host in _SUPPORTED_HOSTS)


def download_media_audio(url: str) -> tuple[Optional[Path], Optional[str]]:
    """
    Lädt das beste Audio-Format in einen Temp-Ordner.
    Returns: (pfad, fehlermeldung)
    """
    url = normalize_url(url)
    if not is_media_url(url):
        return None, "Keine unterstützte Video-/Audio-URL (YouTube, Vimeo, …)."

    try:
        import yt_dlp
    except ImportError:
        return None, "yt-dlp fehlt. Bitte: pip install yt-dlp"

    temp_dir = Path(tempfile.gettempdir()) / "SurepriseAi" / "media"
    temp_dir.mkdir(parents=True, exist_ok=True)

    out_path: Optional[Path] = None
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(temp_dir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None, "Medieninformationen konnten nicht gelesen werden."
            if info.get("entries"):
                info = info["entries"][0]
            candidate = Path(ydl.prepare_filename(info))
            if candidate.exists():
                out_path = candidate
            else:
                # Fallback: neueste Datei im Temp-Ordner mit gleicher ID
                vid = str(info.get("id", ""))
                matches = sorted(temp_dir.glob(f"{vid}.*"), key=lambda p: p.stat().st_mtime)
                if matches:
                    out_path = matches[-1]
        if out_path and out_path.exists():
            print(f"[MediaURL] Geladen: {out_path.name} ({out_path.stat().st_size // 1024} KB)")
            return out_path, None
        return None, "Audiodatei nach Download nicht gefunden."
    except Exception as exc:
        print(f"[MediaURL] Download-Fehler: {exc}")
        return None, f"Download fehlgeschlagen: {exc}"

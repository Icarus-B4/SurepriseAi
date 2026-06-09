"""
screen_ocr_service.py
Windows-OCR (lokal via winocr / WinRT) für Bildschirmkontext.
"""

from typing import Optional

from src.services.config_service import config

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False

try:
    from winocr import recognize_pil_sync
    _WINOCR = True
except ImportError:
    _WINOCR = False


def ocr_available() -> bool:
    return _PIL and _WINOCR


def resolve_ocr_language() -> str:
    """OCR-Sprache aus Diktier-Sprache ableiten."""
    lang = config.get_str("transcription_language", "auto").lower()
    if lang.startswith("de"):
        return "de"
    if lang.startswith("en"):
        return "en"
    if lang.startswith("fr"):
        return "fr"
    return "de"


def recognize_image(img: "Image.Image") -> str:
    """Führt Windows-OCR auf einem PIL-Bild aus."""
    if not ocr_available():
        return ""
    lang = resolve_ocr_language()
    try:
        result = recognize_pil_sync(img, lang=lang)
        if isinstance(result, dict):
            return (result.get("text") or "").strip()
        return str(result).strip() if result else ""
    except Exception as exc:
        print(f"[ScreenOCR] Fehler: {exc}")
        return ""

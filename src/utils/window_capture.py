"""
window_capture.py
Win32-Fenster-Rechteck und Screenshot-Erfassung für Screen-OCR.
"""

import ctypes
from ctypes import wintypes
from typing import Optional

try:
    from PIL import Image, ImageGrab
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


def get_window_bbox(hwnd: Optional[int]) -> Optional[tuple[int, int, int, int]]:
    """Liefert (left, top, right, bottom) für ein HWND."""
    if not hwnd:
        return None
    rect = wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width < 80 or height < 60:
        return None
    return rect.left, rect.top, rect.right, rect.bottom


def get_primary_monitor_bbox() -> tuple[int, int, int, int]:
    """Bounding Box des primären Monitors."""
    user32 = ctypes.windll.user32
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    return 0, 0, w, h


def capture_bbox(
    bbox: tuple[int, int, int, int],
    max_width: int = 1600,
) -> Optional["Image.Image"]:
    """Screenshot einer Bildschirmregion, optional verkleinert für schnelleres OCR."""
    if not _PIL_AVAILABLE:
        return None
    left, top, right, bottom = bbox
    if right <= left or bottom <= top:
        return None
    img = ImageGrab.grab(bbox=bbox)
    if img.width > max_width:
        ratio = max_width / img.width
        new_h = max(1, int(img.height * ratio))
        img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
    return img

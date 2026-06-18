"""
win32_backdrop.py
Natives Windows 11 Acryl/Mica-Backdrop über DwmSetWindowAttribute.
Nutzt ctypes für den direkten Zugriff auf die Windows DWM API.
Fallback auf bestehende CSS-Transparenz bei Windows 10 oder Fehler.
"""

import ctypes
import sys
from typing import Optional

print("[Backdrop] win32/dwmapi Modul geladen")


# DWM-Attribute für Windows 11 (Build 22000+)
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38

# Backdrop-Typen
BACKDROP_AUTO = 0     # System-Standard
BACKDROP_NONE = 1     # Kein Backdrop
BACKDROP_MICA = 2     # Mica-Effekt (subtil, Performance-freundlich)
BACKDROP_ACRYLIC = 3  # Acryl-Effekt (stark verwischt, moderner Look)
BACKDROP_TABBED = 4   # Tabbed-Mica (ab Win11 22H2)


def _get_hwnd(widget) -> Optional[int]:
    """Extrahiert das native Win32 HWND aus einem QWidget."""
    try:
        return int(widget.winId())
    except Exception:
        return None


def _set_dwm_attribute(hwnd: int, attribute: int, value: int) -> bool:
    """Setzt ein DWM-Attribut über ctypes. Gibt True bei Erfolg zurück."""
    try:
        dwmapi = ctypes.windll.dwmapi
        val = ctypes.c_int(value)
        result = dwmapi.DwmSetWindowAttribute(
            hwnd, attribute,
            ctypes.byref(val), ctypes.sizeof(val)
        )
        return result == 0  # S_OK
    except (OSError, AttributeError):
        return False


def _is_win11() -> bool:
    """Prüft, ob Windows 11 (Build 22000+) vorliegt."""
    if sys.platform != "win32":
        return False
    try:
        version = sys.getwindowsversion()
        return version.build >= 22000
    except AttributeError:
        return False


def apply_dark_mode(widget) -> bool:
    """Aktiviert den Immersive Dark Mode für das Fenster."""
    hwnd = _get_hwnd(widget)
    if hwnd is None:
        return False
    return _set_dwm_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1)


def apply_acrylic(widget) -> bool:
    """
    Wendet den Acryl-Backdrop-Effekt auf das Fenster an.
    Gibt True bei Erfolg zurück, False bei Fallback.
    """
    if not _is_win11():
        print("[Backdrop] Kein Windows 11 – Fallback auf CSS-Transparenz")
        return False

    hwnd = _get_hwnd(widget)
    if hwnd is None:
        return False

    apply_dark_mode(widget)
    success = _set_dwm_attribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, BACKDROP_ACRYLIC)
    if success:
        print("[Backdrop] Acryl-Effekt aktiviert (Windows 11 DWM)")
        print("[Backdrop] CSS-Fallback als Reserve verfügbar")
        try:
            from src.services import dictation_logger as dlog
            dlog.write("Windows theme backdrop: Acrylic via dwmapi", also_print=False)
        except Exception:
            pass
    else:
        print("[Backdrop] Acryl-Effekt fehlgeschlagen – Fallback")
    return success


def apply_mica(widget) -> bool:
    """
    Wendet den Mica-Backdrop-Effekt auf das Fenster an.
    Gibt True bei Erfolg zurück, False bei Fallback.
    """
    if not _is_win11():
        print("[Backdrop] Kein Windows 11 – Fallback auf CSS-Transparenz")
        return False

    hwnd = _get_hwnd(widget)
    if hwnd is None:
        return False

    apply_dark_mode(widget)

    success = _set_dwm_attribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, BACKDROP_MICA)
    if success:
        print("[Backdrop] Mica-Effekt aktiviert")
    else:
        print("[Backdrop] Mica-Effekt fehlgeschlagen – Fallback")
    return success


def apply_tabbed_mica(widget) -> bool:
    """Wendet den Tabbed-Mica-Effekt an (Win11 22H2+)."""
    if not _is_win11():
        return False

    hwnd = _get_hwnd(widget)
    if hwnd is None:
        return False

    apply_dark_mode(widget)
    return _set_dwm_attribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, BACKDROP_TABBED)


def remove_backdrop(widget) -> bool:
    """Entfernt den System-Backdrop vom Fenster."""
    hwnd = _get_hwnd(widget)
    if hwnd is None:
        return False
    return _set_dwm_attribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, BACKDROP_NONE)

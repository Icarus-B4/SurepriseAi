"""
windows_accent.py
Liest die Windows-Akzentfarbe aus der Registry (DWM ColorizationColor).
"""

from typing import Optional

try:
    import winreg
    _WINREG_AVAILABLE = True
except ImportError:
    _WINREG_AVAILABLE = False


def _abgr_to_hex(abgr: int) -> str:
    """Konvertiert Windows-ABGR (DWORD) in #RRGGBB."""
    b = abgr & 0xFF
    g = (abgr >> 8) & 0xFF
    r = (abgr >> 16) & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}"


def _adjust_brightness(hex_color: str, factor: float) -> str:
    """Hellt oder verdunkelt eine Hex-Farbe."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02X}{g:02X}{b:02X}"


def read_accent_hex() -> Optional[str]:
    """Gibt die System-Akzentfarbe als #RRGGBB zurück oder None."""
    if not _WINREG_AVAILABLE:
        return None
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\DWM",
        )
        value, _ = winreg.QueryValueEx(key, "ColorizationColor")
        winreg.CloseKey(key)
        if isinstance(value, int) and value > 0:
            return _abgr_to_hex(value)
    except OSError:
        pass
    return None


def accent_variants(hex_color: str) -> tuple[str, str, str]:
    """Liefert (primary, bright, dark) Varianten."""
    return hex_color, _adjust_brightness(hex_color, 1.15), _adjust_brightness(hex_color, 0.82)

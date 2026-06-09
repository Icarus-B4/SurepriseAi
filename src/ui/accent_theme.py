"""
accent_theme.py
Wendet die Windows-System-Akzentfarbe auf die Design-Tokens an.
"""

from src.ui.design_tokens import Colors
from src.utils.windows_accent import read_accent_hex, accent_variants
from src.services.config_service import config

_LAST_APPLIED_HEX: str | None = None


def apply_windows_accent() -> bool:
    """
    Liest die Windows-Akzentfarbe und aktualisiert Colors.
    Gibt True zurück, wenn sich die Farbe geändert hat.
    """
    global _LAST_APPLIED_HEX
    hex_color = read_accent_hex()
    if not hex_color:
        return False
    if hex_color == _LAST_APPLIED_HEX:
        return False
    primary, bright, dark = accent_variants(hex_color)
    Colors.ACCENT_HEX = primary
    Colors.ACCENT_BRIGHT_HEX = bright
    Colors.ACCENT_DARK_HEX = dark
    _LAST_APPLIED_HEX = hex_color
    return True


_DEFAULT_ACCENT = ("#6366F1", "#818CF8", "#4F46E5")


def apply_accent_from_config() -> bool:
    """Wendet Windows-Akzent oder Standard-Indigo laut Config an."""
    global _LAST_APPLIED_HEX
    if not config.get_bool("use_windows_accent", True):
        if _LAST_APPLIED_HEX == _DEFAULT_ACCENT[0]:
            return False
        Colors.ACCENT_HEX, Colors.ACCENT_BRIGHT_HEX, Colors.ACCENT_DARK_HEX = _DEFAULT_ACCENT
        _LAST_APPLIED_HEX = _DEFAULT_ACCENT[0]
        return True
    return apply_windows_accent()


def reset_accent_cache() -> None:
    """Erzwingt erneutes Anwenden beim nächsten Refresh."""
    global _LAST_APPLIED_HEX
    _LAST_APPLIED_HEX = None

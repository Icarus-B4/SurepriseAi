"""
accent_theme.py
Wendet die Windows-System-Akzentfarbe sowie das Farbthema (Dunkel/Hell/System) auf die Design-Tokens an.
"""

from src.ui.design_tokens import Colors
from src.utils.windows_accent import read_accent_hex, accent_variants, is_windows_light_theme
from src.services.config_service import config

_LAST_APPLIED_HEX: str | None = None
_CURRENT_THEME: str | None = None

_DEFAULT_ACCENT = ("#6366F1", "#818CF8", "#4F46E5")

_DARK_TOKENS = {
    "ISLAND_BG_HEX": "#0D0D0F",
    "ISLAND_BG_ALPHA": "rgba(13, 13, 15, 0.90)",
    "SURFACE_HEX": "#1A1A1E",
    "SURFACE_ELEVATED": "#242428",
    "PILL_GRADIENT_TOP": "rgba(32, 32, 40, 0.94)",
    "PILL_GRADIENT_BOTTOM": "rgba(12, 12, 16, 0.96)",
    "TEXT_PRIMARY_HEX": "#F5F5F7",
    "TEXT_SECONDARY_HEX": "#8E8E93",
    "TEXT_TERTIARY_HEX": "#48484A",
    "BORDER_HEX": "rgba(255, 255, 255, 0.08)",
    "BORDER_SUBTLE_HEX": "rgba(255, 255, 255, 0.04)",
    "BORDER_HIGHLIGHT": "rgba(255, 255, 255, 0.12)",
    "CONTROL_FILL_HEX": "rgba(255, 255, 255, 0.06)",
    "CONTROL_HOVER_HEX": "rgba(255, 255, 255, 0.10)",
}

_LIGHT_TOKENS = {
    "ISLAND_BG_HEX": "#F3F3F7",
    "ISLAND_BG_ALPHA": "rgba(243, 243, 247, 0.90)",
    "SURFACE_HEX": "#F9F9FB",
    "SURFACE_ELEVATED": "#FFFFFF",
    "PILL_GRADIENT_TOP": "rgba(255, 255, 255, 0.96)",
    "PILL_GRADIENT_BOTTOM": "rgba(240, 240, 245, 0.94)",
    "TEXT_PRIMARY_HEX": "#111112",
    "TEXT_SECONDARY_HEX": "#3A3A3C",
    "TEXT_TERTIARY_HEX": "#68686E",
    "BORDER_HEX": "rgba(0, 0, 0, 0.15)",
    "BORDER_SUBTLE_HEX": "rgba(0, 0, 0, 0.08)",
    "BORDER_HIGHLIGHT": "rgba(0, 0, 0, 0.12)",
    "CONTROL_FILL_HEX": "rgba(0, 0, 0, 0.06)",
    "CONTROL_HOVER_HEX": "rgba(0, 0, 0, 0.12)",
}


def update_accent_tints() -> None:
    """Aktualisiert die ACCENT_GLOW und ACCENT_TINT-Werte basierend auf ACCENT_HEX."""
    hex_color = Colors.ACCENT_HEX.lstrip("#")
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        Colors.ACCENT_GLOW = f"rgba({r}, {g}, {b}, 0.45)"
        Colors.ACCENT_TINT_HEX = f"rgba({r}, {g}, {b}, 0.14)"
        Colors.ACCENT_TINT_STRONG = f"rgba({r}, {g}, {b}, 0.22)"
    except (ValueError, IndexError):
        pass


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
    update_accent_tints()
    _LAST_APPLIED_HEX = hex_color
    return True


def apply_accent_from_config() -> bool:
    """Wendet Windows-Akzent oder Standard-Indigo laut Config an."""
    global _LAST_APPLIED_HEX
    if not config.get_bool("use_windows_accent", True):
        if _LAST_APPLIED_HEX == _DEFAULT_ACCENT[0]:
            return False
        Colors.ACCENT_HEX, Colors.ACCENT_BRIGHT_HEX, Colors.ACCENT_DARK_HEX = _DEFAULT_ACCENT
        update_accent_tints()
        _LAST_APPLIED_HEX = _DEFAULT_ACCENT[0]
        return True
    return apply_windows_accent()


def apply_theme_from_config() -> bool:
    """Wendet das Farbthema (Dunkel/Hell/System) laut Config an."""
    global _CURRENT_THEME
    mode = config.get_str("theme_mode", "system")
    
    if mode == "system":
        resolved = "light" if is_windows_light_theme() else "dark"
    else:
        resolved = mode if mode in ("dark", "light") else "dark"
        
    if resolved == _CURRENT_THEME:
        return False
        
    tokens = _LIGHT_TOKENS if resolved == "light" else _DARK_TOKENS
    for key, value in tokens.items():
        setattr(Colors, key, value)
        
    _CURRENT_THEME = resolved
    return True


def reset_accent_cache() -> None:
    """Erzwingt erneutes Anwenden beim nächsten Refresh."""
    global _LAST_APPLIED_HEX, _CURRENT_THEME
    _LAST_APPLIED_HEX = None
    _CURRENT_THEME = None

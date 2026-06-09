"""
design_tokens.py
Zentrales Design-System für SurepriseAi (PyQt6 Edition).
Alle Farben, Abstände, Animationszeiten und Typografie an einem Ort.
Folgt dem Design-Guide (8px Grid, ONE Akzentfarbe, Emil Kowalski Motion).
"""

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import QPoint

# ── Windows Fluent Icons (Segoe MDL2 Assets / Segoe Fluent Icons) ─────────────
# Nutzt die nativen System-Icon-Fonts von Windows für perfekten Windows-Look.
class FluentIcons:
    FONT_FAMILY = "Segoe UI Symbol, Segoe UI, sans-serif"
    
    MICROPHONE = "🎙"
    SETTINGS   = "⚙"
    STYLE      = "⚗"
    CHECKMARK  = "✓"
    PROCESSING = "⟳"
    CLOSE      = "✕"
    EXPAND     = "▾"
    COLLAPSE   = "▴"
    DRAG_GRIP  = "⠿"
    INFO       = "ℹ"
    ERROR      = "⚠"
    COPY       = "📋"
    RETRY      = "↺"

# ── Farben (Hex und QColor) ───────────────────────────────────────────────────

class Colors:
    # Hintergründe (Dunkles Theme)
    ISLAND_BG_HEX      = "#0D0D0F"
    ISLAND_BG_ALPHA    = "rgba(13, 13, 15, 0.90)"
    SURFACE_HEX        = "#1A1A1E"
    SURFACE_ELEVATED   = "#242428"
    
    # Text
    TEXT_PRIMARY_HEX   = "#F5F5F7"
    TEXT_SECONDARY_HEX = "#8E8E93"
    TEXT_TERTIARY_HEX  = "#48484A"
    
    # Akzente (Indigo)
    ACCENT_HEX         = "#6366F1"
    ACCENT_BRIGHT_HEX  = "#818CF8"
    ACCENT_DARK_HEX    = "#4F46E5"
    
    # State-Farben
    RECORDING_RED_HEX  = "#FF453A"
    SUCCESS_GREEN_HEX  = "#30D158"
    PROCESSING_BLUE_HEX = "#64D2FF"

    # Rahmen
    BORDER_HEX         = "rgba(255, 255, 255, 0.08)"
    BORDER_SUBTLE_HEX  = "rgba(255, 255, 255, 0.04)"

    @classmethod
    def island_bg(cls) -> QColor:
        return QColor(13, 13, 15, 230) # ~90% Alpha

    @classmethod
    def text_primary(cls) -> QColor:
        return QColor("#F5F5F7")

    @classmethod
    def text_secondary(cls) -> QColor:
        return QColor("#8E8E93")

    @classmethod
    def accent(cls) -> QColor:
        return QColor("#6366F1")

    @classmethod
    def recording_red(cls) -> QColor:
        return QColor("#FF453A")

    @classmethod
    def success_green(cls) -> QColor:
        return QColor("#30D158")

    @classmethod
    def processing_blue(cls) -> QColor:
        return QColor("#64D2FF")

# ── Abstände (8px Grid) ───────────────────────────────────────────────────────

class Spacing:
    XS  = 4
    SM  = 8
    MD  = 16
    LG  = 24
    XL  = 32
    
    ISLAND_PADDING_H = 16
    ISLAND_PADDING_V = 8

# ── Typography ────────────────────────────────────────────────────────────────

class Typography:
    FONT_FAMILY = "Segoe UI Variable Display, Segoe UI, sans-serif"

    # Schriftgrößen
    TINY   = 10
    SMALL  = 12
    BODY   = 14
    MEDIUM = 16
    LARGE  = 18
    TITLE  = 22

    @classmethod
    def get_font(cls, size: int, bold: bool = False) -> QFont:
        font = QFont(cls.FONT_FAMILY, size)
        if bold:
            font.setBold(True)
        return font

    @classmethod
    def get_icon_font(cls, size: int) -> QFont:
        font = QFont(FluentIcons.FONT_FAMILY, size)
        return font

# ── Dynamic Island Dimensionen ────────────────────────────────────────────────

class IslandSize:
    # IDLE: Kleine Pill
    IDLE_WIDTH  = 290
    IDLE_HEIGHT = 38

    # RECORDING: Expandierte Pill mit Waveform
    RECORDING_WIDTH  = 360
    RECORDING_HEIGHT = 56

    # PROCESSING: Mittlere Größe mit Spinner
    PROCESSING_WIDTH  = 300
    PROCESSING_HEIGHT = 48

    # SUCCESS: Breitere Kapsel für Text
    SUCCESS_WIDTH  = 400
    SUCCESS_HEIGHT = 50

    # EXPANDED: Große Kapsel für volles Transkript
    EXPANDED_WIDTH  = 580
    EXPANDED_HEIGHT = 320
    EXPANDED_RADIUS = 16

    # Trägerfenster – muss größer als EXPANDED sein, sonst werden Ecken abgeschnitten
    WINDOW_WIDTH  = EXPANDED_WIDTH + 32
    WINDOW_HEIGHT = EXPANDED_HEIGHT + 48

    # Rundung (Pill-Form)
    BORDER_RADIUS = 19 # (Für standardmäßig 38px Höhe = 19px Radius)

    # Waveform-Balken
    WAVEFORM_BARS    = 5
    WAVEFORM_BAR_W   = 3
    WAVEFORM_BAR_GAP = 3
    WAVEFORM_MAX_H   = 20
    WAVEFORM_MIN_H   = 3

# ── Animationszeiten (Emil Kowalski) ──────────────────────────────────────────

class AnimationTokens:
    # Dauer (ms)
    FAST       = 140
    NORMAL     = 200 # State-Wechsel
    SLOW       = 300
    
    # Wartezeiten
    SUCCESS_DISPLAY_MS = 2500
    
    # Waveform
    WAVEFORM_STAGGER_MS = 20

"""
design_tokens.py
Zentrales Design-System für SurepriseAi (PyQt6 Edition).
Alle Farben, Abstände, Animationszeiten und Typografie an einem Ort.

Design-Prinzipien (abgeleitet aus DESIGN.md):
  • Flat statt verschachtelt – Gruppierung über Whitespace + eine Haarlinie.
  • Elevation durch weiche Schatten, nicht durch harte Rahmen.
  • Eine Primitive pro Zweck (ein Schatten-Helfer, eine Motion-Kurve, ein Radius-Set).
  • Tokens statt Literale – nie rohe Hex/rgba direkt in Widgets.
Folgt dem 8px-Grid und EINER Akzentfarbe (Indigo, Laufzeit-überschreibbar).
"""

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import QPoint, QPointF, QEasingCurve

# ── Windows Fluent Icons (Segoe MDL2 Assets / Segoe Fluent Icons) ─────────────
# Nutzt die nativen System-Icon-Fonts von Windows für perfekten Windows-Look.
class FluentIcons:
    FONT_FAMILY = "Segoe UI Symbol"
    
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
    # Hintergründe (Dunkles Theme – leicht blau-entsättigtes Near-Black für Tiefe)
    ISLAND_BG_HEX      = "#0D0D0F"
    ISLAND_BG_ALPHA    = "rgba(13, 13, 15, 0.90)"
    SURFACE_HEX        = "#1A1A1E"
    SURFACE_ELEVATED   = "#242428"

    # Glas-Gradient für die Pill (oben heller → unten tiefer = subtile Tiefe/Lichtkante)
    PILL_GRADIENT_TOP    = "rgba(32, 32, 40, 0.94)"
    PILL_GRADIENT_BOTTOM = "rgba(12, 12, 16, 0.96)"

    # Text
    TEXT_PRIMARY_HEX   = "#F5F5F7"
    TEXT_SECONDARY_HEX = "#8E8E93"
    TEXT_TERTIARY_HEX  = "#48484A"
    
    # Akzente (Indigo)
    ACCENT_HEX         = "#6366F1"
    ACCENT_BRIGHT_HEX  = "#818CF8"
    ACCENT_DARK_HEX    = "#4F46E5"

    # Akzent-Tints (für Glows, getönte Ränder, Hover-Fills)
    ACCENT_GLOW        = "rgba(99, 102, 241, 0.45)"
    ACCENT_TINT_HEX    = "rgba(99, 102, 241, 0.14)"
    ACCENT_TINT_STRONG = "rgba(99, 102, 241, 0.22)"

    # State-Farben
    RECORDING_RED_HEX  = "#FF453A"
    SUCCESS_GREEN_HEX  = "#30D158"
    PROCESSING_BLUE_HEX = "#64D2FF"

    # Rahmen / Haarlinien (in absteigender Stärke)
    BORDER_HEX         = "rgba(255, 255, 255, 0.08)"
    BORDER_SUBTLE_HEX  = "rgba(255, 255, 255, 0.04)"
    # Obere Lichtkante – simuliert Glas-Reflexion am oberen Pill-Rand
    BORDER_HIGHLIGHT   = "rgba(255, 255, 255, 0.12)"
    # Soft-Fill für ruhige Controls / Hover (vgl. --ui-bg-quaternary)
    CONTROL_FILL_HEX   = "rgba(255, 255, 255, 0.06)"
    CONTROL_HOVER_HEX  = "rgba(255, 255, 255, 0.10)"

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
    FONT_FAMILY = "Segoe UI"
    # Variable-Optical-Sizing-Familie für UI; Segoe UI Variable falls verfügbar (Win11),
    # sonst sauberer Fallback auf Segoe UI.
    FONT_FAMILY_VARIABLE = "Segoe UI Variable Text"

    # Schriftgrößen (pt) – eine Skala für die gesamte App
    TINY   = 10
    SMALL  = 12
    BODY   = 14
    MEDIUM = 16
    LARGE  = 18
    TITLE  = 22

    # Gewichte (QFont.Weight) – feinere Hierarchie als nur bold/regular
    WEIGHT_REGULAR  = QFont.Weight.Normal      # 400
    WEIGHT_MEDIUM   = QFont.Weight.Medium      # 500
    WEIGHT_SEMIBOLD = QFont.Weight.DemiBold    # 600
    WEIGHT_BOLD     = QFont.Weight.Bold        # 700

    @classmethod
    def get_font(
        cls,
        size: int,
        bold: bool = False,
        weight: QFont.Weight | None = None,
        letter_spacing: float | None = None,
    ) -> QFont:
        font = QFont(cls.FONT_FAMILY)
        font.setPointSize(size)
        if weight is not None:
            font.setWeight(weight)
        else:
            font.setBold(bold)
        if letter_spacing is not None:
            # Negative Werte verdichten Headlines – modernes, kompaktes Tracking
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 100 + letter_spacing)
        return font

    @classmethod
    def get_icon_font(cls, size: int) -> QFont:
        font = QFont("Segoe UI Symbol")
        font.setPointSize(size)
        return font


# ── Radius (Ecken-Rundungen, zentral) ─────────────────────────────────────────

class Radius:
    XS   = 6
    SM   = 8
    MD   = 12
    LG   = 16
    XL   = 20
    PILL = 999  # voll abgerundet (Kapselform)


# ── Elevation (weiche Schatten = Tiefe, statt harter Rahmen) ──────────────────

class Elevation:
    """Wiederverwendbare Drop-Shadow-Ebenen. Eine Primitive für alle Overlays."""

    # (blur, dy, alpha) – downward-weighted Kontakt→Ambient-Falloff
    LOW    = (18, 4, 120)
    MEDIUM = (28, 8, 150)
    HIGH   = (44, 14, 170)

    @staticmethod
    def apply(widget, level: tuple[int, int, int] = MEDIUM, dx: int = 0):
        """Hängt einen weichen Schatten an ein Widget (überschreibt vorhandenen Effekt)."""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect

        blur, dy, alpha = level
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(blur)
        effect.setOffset(dx, dy)
        effect.setColor(QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(effect)
        return effect


# ── Motion (Easing-Kurven als Token = ein Motion-System) ──────────────────────

class Motion:
    """Premium-Bewegung. Schnelle, funktionale Übergänge mit ruhigem Ausklang."""

    # Dauer (ms) – Spiegel der AnimationTokens, für neuen Motion-Code
    FAST   = 140
    BASE   = 200
    SLOW   = 320
    SLOWER = 420

    @staticmethod
    def spring(overshoot: float = 1.1) -> QEasingCurve:
        """Sanfter Überschwinger – lebendig, aber ohne Wackel-Bounce (default 1.7)."""
        curve = QEasingCurve(QEasingCurve.Type.OutBack)
        curve.setOvershoot(overshoot)
        return curve

    @staticmethod
    def smooth() -> QEasingCurve:
        """Schneller Start, weiches Settle – ideal für Größen-/Opacity-Wechsel."""
        return QEasingCurve(QEasingCurve.Type.OutExpo)

    @staticmethod
    def emphasized() -> QEasingCurve:
        """Material-3 emphasized decelerate (cubic-bezier 0.05, 0.7, 0.1, 1.0)."""
        curve = QEasingCurve(QEasingCurve.Type.BezierSpline)
        curve.addCubicBezierSegment(QPointF(0.05, 0.7), QPointF(0.1, 1.0), QPointF(1.0, 1.0))
        return curve

# ── Dynamic Island Dimensionen ────────────────────────────────────────────────

class IslandSize:
    # IDLE: Kleine Pill (mit optionalem Privacy-Badge)
    IDLE_WIDTH  = 290
    IDLE_HEIGHT = 44

    # Presence-Bar (kollabierte Dynamic Island, immer sichtbar im Idle)
    PRESENCE_WIDTH          = 118
    PRESENCE_HEIGHT         = 11
    PRESENCE_TOP_Y          = 4
    PRESENCE_IDLE_TIMEOUT_S = 5.0
    PRESENCE_TRIGGER_HALF_W = 250
    PRESENCE_TRIGGER_MAX_Y  = 120

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
    EXPANDED_WIDTH  = 620
    EXPANDED_HEIGHT = 348
    EXPANDED_RADIUS = 16
    EXPANDED_MIN_HEIGHT = 348
    EXPANDED_MAX_HEIGHT = 348

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

"""
windows_overlay.py
Win32 API-Hilfsfunktionen für das transparente Dynamic Island Overlay.
Steuert: Always-on-Top, Transparenz, Click-Through, Blur-Effekt.
"""

import ctypes
import ctypes.wintypes as wintypes
from ctypes import windll, byref
import sys

# ── Win32 Konstanten ─────────────────────────────────────────────────────────
GWL_EXSTYLE        = -20
WS_EX_LAYERED      = 0x00080000
WS_EX_TRANSPARENT  = 0x00000020
WS_EX_TOPMOST      = 0x00000008
WS_EX_NOACTIVATE   = 0x08000000
WS_EX_TOOLWINDOW   = 0x00000080

HWND_TOPMOST       = -1
HWND_NOTOPMOST     = -2
SWP_NOMOVE         = 0x0002
SWP_NOSIZE         = 0x0001
SWP_NOACTIVATE     = 0x0010

LWA_ALPHA          = 0x00000002
LWA_COLORKEY       = 0x00000001

# DWM Blur
DWM_BB_ENABLE      = 0x00000001
DWM_BB_BLURREGION  = 0x00000002


class _BLURBEHIND(ctypes.Structure):
    _fields_ = [
        ("dwFlags",     wintypes.DWORD),
        ("fEnable",     wintypes.BOOL),
        ("hRgnBlur",    wintypes.HANDLE),
        ("fTransitionOnMaximized", wintypes.BOOL),
    ]


def _get_hwnd(window_title: str) -> int | None:
    """Sucht HWND anhand des Fenstertitels."""
    hwnd = windll.user32.FindWindowW(None, window_title)
    return hwnd if hwnd else None


def set_always_on_top(hwnd: int) -> None:
    """Setzt das Fenster auf HWND_TOPMOST (immer im Vordergrund)."""
    windll.user32.SetWindowPos(
        hwnd, HWND_TOPMOST, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    )


def remove_always_on_top(hwnd: int) -> None:
    """Entfernt HWND_TOPMOST."""
    windll.user32.SetWindowPos(
        hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    )


def enable_layered_window(hwnd: int, alpha: int = 230) -> None:
    """Aktiviert WS_EX_LAYERED und setzt Fenster-Transparenz (alpha 0-255)."""
    ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
    windll.user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)


def enable_click_through(hwnd: int) -> None:
    """Macht das Fenster click-through (Mausklicks ignoriert)."""
    ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE,
        ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
    )


def disable_click_through(hwnd: int) -> None:
    """Deaktiviert click-through (Fenster nimmt Klicks wieder an)."""
    ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE,
        ex_style & ~WS_EX_TRANSPARENT
    )


def enable_blur_behind(hwnd: int) -> None:
    """Aktiviert den DWM-Blur-Hintergrundeffekt (Aero Glass)."""
    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        blur = _BLURBEHIND()
        blur.dwFlags = DWM_BB_ENABLE
        blur.fEnable = True
        blur.hRgnBlur = None
        dwmapi.DwmEnableBlurBehindWindow(hwnd, byref(blur))
    except Exception as e:
        print(f"[Overlay] DWM-Blur nicht verfügbar: {e}")


def set_no_taskbar(hwnd: int) -> None:
    """Versteckt das Fenster aus der Taskleiste (WS_EX_TOOLWINDOW)."""
    ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE,
        (ex_style | WS_EX_TOOLWINDOW) & ~0x00040000  # ~WS_EX_APPWINDOW
    )


def get_screen_dimensions() -> tuple[int, int]:
    """Gibt die primäre Bildschirmauflösung zurück (Breite, Höhe)."""
    width  = windll.user32.GetSystemMetrics(0)   # SM_CXSCREEN
    height = windll.user32.GetSystemMetrics(1)   # SM_CYSCREEN
    return width, height


def apply_dynamic_island_style(hwnd: int, alpha: int = 230) -> None:
    """Wendet alle Dynamic Island Overlay-Stile in einem Schritt an."""
    set_always_on_top(hwnd)
    enable_layered_window(hwnd, alpha)
    enable_blur_behind(hwnd)
    set_no_taskbar(hwnd)

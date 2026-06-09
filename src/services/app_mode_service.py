"""
app_mode_service.py
Ermittelt den Polishing-Stil anhand des aktiven Fensters (App-Modi).
"""

import ctypes
from typing import Optional

from .config_service import config

try:
    import ctypes.wintypes as wintypes
    _WIN32 = True
except ImportError:
    _WIN32 = False


def _window_title(hwnd: int) -> str:
    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _process_exe(hwnd: int) -> str:
    pid = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
    if not handle:
        return ""
    buf = ctypes.create_unicode_buffer(260)
    size = wintypes.DWORD(260)
    ok = ctypes.windll.kernel32.QueryFullProcessImageNameW(
        handle, 0, buf, ctypes.byref(size)
    )
    ctypes.windll.kernel32.CloseHandle(handle)
    if not ok:
        return ""
    return buf.value.rsplit("\\", 1)[-1].lower()


def resolve_style_for_hwnd(hwnd: Optional[int]) -> Optional[str]:
    """
    Sucht in config.app_modes nach Treffern im Fenstertitel oder Prozessnamen.
    """
    if not hwnd or not _WIN32:
        return None
    if not config.get_bool("enable_app_modes", True):
        return None

    modes = config.get("app_modes", {})
    if not isinstance(modes, dict) or not modes:
        return None

    try:
        title = _window_title(hwnd).lower()
        exe = _process_exe(hwnd)
    except Exception:
        return None

    for key, style in modes.items():
        needle = str(key).lower()
        if needle and (needle in title or needle in exe):
            return str(style)
    return None

"""
app_mode_service.py
Ermittelt den Polishing-Stil anhand des aktiven Fensters (App-Modi).
"""

from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from typing import Optional

from .config_service import config

try:
    import ctypes.wintypes as wintypes
    _WIN32 = True
except ImportError:
    _WIN32 = False

_own_pid: Optional[int] = None
_last_external_hwnd: Optional[int] = None


@dataclass(frozen=True)
class _AppRule:
    display: str
    style: str
    exes: frozenset[str]
    title_hints: frozenset[str]


# Eingebaute Erkennung – unabhängig von config.app_modes (User-Config ergänzt/überschreibt).
_BUILTIN_RULES: tuple[_AppRule, ...] = (
    _AppRule("VS Code", "concise", frozenset({"code.exe"}), frozenset({"visual studio code", "vscode"})),
    _AppRule("Cursor", "concise", frozenset({"cursor.exe"}), frozenset({"cursor"})),
    _AppRule("Antigravity", "developer", frozenset({"antigravity.exe"}), frozenset({"antigravity"})),
    _AppRule("Visual Studio", "developer", frozenset({"devenv.exe"}), frozenset({"visual studio"})),
    _AppRule("Windsurf", "concise", frozenset({"windsurf.exe"}), frozenset({"windsurf"})),
    _AppRule("PyCharm", "developer", frozenset({"pycharm64.exe", "pycharm.exe"}), frozenset({"pycharm"})),
    _AppRule("IntelliJ", "developer", frozenset({"idea64.exe"}), frozenset({"intellij"})),
    _AppRule("WebStorm", "developer", frozenset({"webstorm64.exe"}), frozenset({"webstorm"})),
    _AppRule("Sublime Text", "concise", frozenset({"sublime_text.exe"}), frozenset({"sublime text"})),
    _AppRule("Notepad++", "concise", frozenset({"notepad++.exe"}), frozenset({"notepad++"})),
    _AppRule("Notepad", "concise", frozenset({"notepad.exe"}), frozenset()),
    _AppRule("Outlook", "formal", frozenset({"outlook.exe"}), frozenset({"outlook"})),
    _AppRule("Slack", "business", frozenset({"slack.exe"}), frozenset({"slack"})),
    _AppRule("Teams", "business", frozenset({"ms-teams.exe", "teams.exe"}), frozenset({"microsoft teams", "teams"})),
    _AppRule("Discord", "casual", frozenset({"discord.exe"}), frozenset({"discord"})),
    _AppRule("Terminal", "concise", frozenset({"windowsterminal.exe", "wt.exe", "powershell.exe", "cmd.exe"}), frozenset()),
)


@dataclass(frozen=True)
class AppModeMatch:
    app_key: str
    style: str
    exe: str
    title: str


def _own_process_id() -> int:
    global _own_pid
    if _own_pid is None:
        _own_pid = os.getpid()
    return _own_pid


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


def _is_own_window(hwnd: int) -> bool:
    pid = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value) == _own_process_id()


def get_foreground_hwnd() -> Optional[int]:
    """Liefert das aktuell fokussierte Fenster (Win32)."""
    if not _WIN32:
        return None
    try:
        return int(ctypes.windll.user32.GetForegroundWindow())
    except Exception:
        return None


def get_foreground_hwnd_for_app_mode() -> Optional[int]:
    """
    Foreground-Fenster für App-Modi – ignoriert SurepriseAi selbst,
    merkt sich das zuletzt fokussierte externe Fenster.
    """
    global _last_external_hwnd
    if not _WIN32:
        return None
    hwnd = get_foreground_hwnd()
    if not hwnd:
        return _last_external_hwnd
    if _is_own_window(hwnd):
        return _last_external_hwnd
    _last_external_hwnd = hwnd
    return hwnd


def _match_builtin(exe: str, title: str) -> Optional[AppModeMatch]:
    title_lower = title.lower()
    if exe:
        for rule in _BUILTIN_RULES:
            if exe in rule.exes:
                return AppModeMatch(rule.display, rule.style, exe, title)
    for rule in _BUILTIN_RULES:
        for hint in rule.title_hints:
            if hint and hint in title_lower:
                return AppModeMatch(rule.display, rule.style, exe, title)
    return None


def _match_user_config(exe: str, title_lower: str, modes: dict) -> Optional[AppModeMatch]:
    items = sorted(modes.items(), key=lambda item: len(str(item[0])), reverse=True)
    for key, style in items:
        needle = str(key).lower().strip()
        if not needle:
            continue
        if needle.endswith(".exe"):
            if exe == needle:
                return AppModeMatch(str(key), str(style), exe, title_lower)
            continue
        if exe and (exe == f"{needle}.exe" or exe == needle):
            return AppModeMatch(str(key), str(style), exe, title_lower)
        if exe == "notepad++.exe" and needle == "notepad":
            continue
        if needle in title_lower:
            return AppModeMatch(str(key), str(style), exe, title_lower)
    return None


def resolve_app_mode_match(hwnd: Optional[int]) -> Optional[AppModeMatch]:
    """Sucht App-Modus per EXE, Titel und User-Config."""
    if not hwnd or not _WIN32:
        return None
    if not config.get_bool("enable_app_modes", True):
        return None

    try:
        title = _window_title(hwnd)
        exe = _process_exe(hwnd)
    except Exception:
        return None

    title_lower = title.lower()
    match = _match_builtin(exe, title)
    if match:
        return match

    modes = config.get("app_modes", {})
    if isinstance(modes, dict) and modes:
        user_match = _match_user_config(exe, title_lower, modes)
        if user_match:
            return AppModeMatch(user_match.app_key, user_match.style, exe, title)
    return None


def resolve_style_for_hwnd(hwnd: Optional[int]) -> Optional[str]:
    match = resolve_app_mode_match(hwnd)
    return match.style if match else None


def resolve_style_for_foreground() -> Optional[str]:
    return resolve_style_for_hwnd(get_foreground_hwnd_for_app_mode())


_DEV_IDE_HINTS = (
    "cursor", "code.exe", "devenv", "windsurf", "pycharm", "idea64",
    "webstorm", "rider64", "sublime_text", "notepad++", "terminal",
    "windowsterminal", "powershell", "cmd.exe", "githubdesktop",
    "antigravity", "visual studio code", "vscode",
)


def is_developer_context(hwnd: Optional[int]) -> bool:
    if not hwnd or not _WIN32:
        return False
    try:
        title = _window_title(hwnd).lower()
        exe = _process_exe(hwnd)
    except Exception:
        return False
    haystack = f"{title} {exe}"
    return any(needle in haystack for needle in _DEV_IDE_HINTS)

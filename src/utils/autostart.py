"""
autostart.py
Windows-Autostart über HKCU\\...\\Run mit verstecktem VBS-Launcher (Working Directory).
"""

from __future__ import annotations

import sys
from pathlib import Path

from src.utils.app_paths import install_root, is_frozen

APP_NAME = "SurepriseAi"
APP_EXE = "SurepriseAi.exe"
LAUNCHER_NAME = "LaunchSurepriseAi.vbs"
REG_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launcher_path() -> Path:
    return install_root() / LAUNCHER_NAME


def _launcher_content(exe_name: str = APP_EXE) -> str:
    return (
        'Set sh = CreateObject("WScript.Shell")\r\n'
        'Set fso = CreateObject("Scripting.FileSystemObject")\r\n'
        "dir = fso.GetParentFolderName(WScript.ScriptFullName)\r\n"
        "sh.CurrentDirectory = dir\r\n"
        f'sh.Run Chr(34) & dir & "\\{exe_name}" & Chr(34), 0, False\r\n'
    )


def write_launcher() -> Path:
    """Erstellt den VBS-Launcher neben der EXE."""
    path = _launcher_path()
    path.write_text(_launcher_content(), encoding="utf-8")
    return path


def is_enabled() -> bool:
    """True wenn ein Autostart-Eintrag in der Registry existiert."""
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except OSError:
        return False


def set_enabled(enabled: bool) -> bool:
    """
    Autostart aktivieren/deaktivieren.
    Gibt True zurück, wenn die Operation erfolgreich war.
    """
    if sys.platform != "win32":
        return False
    if not is_frozen():
        return False

    import winreg

    try:
        if enabled:
            launcher = write_launcher()
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REG_RUN, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{launcher}"')
        else:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, REG_RUN, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
            launcher = _launcher_path()
            if launcher.is_file():
                launcher.unlink()
        return True
    except OSError:
        return False


def sync_from_installer() -> None:
    """
    Stellt sicher, dass ein vorhandener Autostart-Eintrag den VBS-Launcher nutzt.
    Hilfreich nach Updates von älteren Versionen ohne Launcher.
    """
    if not is_frozen() or not is_enabled():
        return
    set_enabled(True)

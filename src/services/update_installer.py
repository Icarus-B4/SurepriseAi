"""
update_installer.py
Startet das NSIS-Setup nach einem Update (stille Installation).
"""

import os
import subprocess
import tempfile
from pathlib import Path

from src.services import update_logger
from src.utils.app_paths import install_root, is_frozen

_DESKTOP_LOG = r"%USERPROFILE%\Desktop\SurepriseAi-Update.log"


def launch_update_installer(setup_path: Path) -> None:
    """
    Installierte App: Batch beendet SurepriseAi.exe, wartet, startet NSIS /S.
    Dev (run.py): normaler Wizard.
    """
    path = Path(setup_path)
    update_logger.write(f"launch_update_installer: path={path}")
    update_logger.write(
        f"  exists={path.is_file()} "
        f"size={path.stat().st_size if path.is_file() else 'n/a'}"
    )

    if not path.is_file():
        raise FileNotFoundError(f"Setup nicht gefunden: {path}")

    if not is_frozen():
        update_logger.write("Dev-Modus: os.startfile (Wizard)")
        os.startfile(str(path))
        return

    inst = str(install_root())
    update_logger.write(f"Silent-Install Ziel: {inst}")
    _launch_windows_update_batch(path, inst)


def _launch_windows_update_batch(setup: Path, inst_dir: str) -> None:
    """
    Batch: taskkill → Wartezeit → NSIS /S → Log Exit-Code.
    Kein App-shutdown nötig – taskkill beendet die laufende Instanz.
    """
    bat_path = Path(tempfile.gettempdir()) / f"sureprise_update_{os.getpid()}.bat"
    setup_str = str(setup.resolve())
    log = _DESKTOP_LOG
    lines = [
        "@echo off",
        f'echo [%date% %time%] Batch-Update gestartet >> "{log}"',
        f'echo   Setup={setup_str} >> "{log}"',
        f'echo   INSTDIR={inst_dir} >> "{log}"',
        "taskkill /IM SurepriseAi.exe /F >> \"%USERPROFILE%\\Desktop\\SurepriseAi-Update.log\" 2>&1",
        "ping 127.0.0.1 -n 4 >nul",
        f'echo [%date% %time%] NSIS /S startet >> "{log}"',
        f'"{setup_str}" /S /D={inst_dir}',
        f'echo [%date% %time%] NSIS exit=%ERRORLEVEL% >> "{log}"',
        'del /f /q "%~f0" 2>nul',
    ]
    bat_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    update_logger.write(f"Batch-Launcher: {bat_path}")
    for line in lines:
        update_logger.write(f"  {line}")

    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        ["cmd.exe", "/c", str(bat_path)],
        close_fds=True,
        creationflags=flags,
    )
    update_logger.write("Batch via cmd.exe /c gestartet (detached)")

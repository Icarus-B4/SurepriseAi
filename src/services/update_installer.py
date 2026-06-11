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
_APP_EXE = "SurepriseAi.exe"


def _batch_restart_lines(inst_dir: str) -> list[str]:
    """Batch-Zeilen: App nach erfolgreichem NSIS /S zuverlässig neu starten."""
    exe = str(Path(inst_dir) / _APP_EXE)
    return [
        "ping 127.0.0.1 -n 2 >nul",
        f'cd /d "{inst_dir}"',
        f'echo [%date% %time%] Starte App: {exe} >> "%LOG%"',
        f'start "" /D "{inst_dir}" "{exe}"',
        "ping 127.0.0.1 -n 3 >nul",
        f'tasklist /FI "IMAGENAME eq {_APP_EXE}" 2>nul | find /I "{_APP_EXE}" >nul',
        "if %ERRORLEVEL% NEQ 0 (",
        '  echo [%date% %time%] start fehlgeschlagen – PowerShell-Fallback >> "%LOG%"',
        f'  powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath ''{exe}'' -WorkingDirectory ''{inst_dir}''"',
        "  ping 127.0.0.1 -n 2 >nul",
        ")",
        f'tasklist /FI "IMAGENAME eq {_APP_EXE}" 2>nul | find /I "{_APP_EXE}" >nul',
        "if %ERRORLEVEL%==0 (",
        '  echo [%date% %time%] App neu gestartet OK >> "%LOG%"',
        ") else (",
        '  echo [%date% %time%] WARNUNG: App nicht gestartet – bitte SurepriseAi manuell oeffnen >> "%LOG%"',
        ")",
    ]


def launch_update_installer(setup_path: Path) -> None:
    """
    Installierte App: Batch killt alle SurepriseAi-Prozesse, NSIS /S, Neustart bei Erfolg.
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

    inst = str(install_root())
    write_desktop_install_helper(path, inst)

    if not is_frozen():
        update_logger.write("Dev-Modus: os.startfile (Wizard)")
        os.startfile(str(path))
        return

    update_logger.write(f"Silent-Install Ziel (Registry): {inst}")
    _launch_windows_update_batch(path, inst)


def _batch_body(setup_str: str, inst_dir: str, *, delete_self: bool) -> list[str]:
    log = _DESKTOP_LOG
    lines = [
        "@echo off",
        f'set "SETUP={setup_str}"',
        f'set "INSTDIR={inst_dir}"',
        f'set "LOG={log}"',
        'echo [%date% %time%] === Batch-Update gestartet === >> "%LOG%"',
        f'echo   Setup=%SETUP% >> "%LOG%"',
        f'echo   INSTDIR=%INSTDIR% >> "%LOG%"',
        ":killloop",
        f'taskkill /IM {_APP_EXE} /F /T >> "%LOG%" 2>&1',
        "ping 127.0.0.1 -n 2 >nul",
        f'tasklist /FI "IMAGENAME eq {_APP_EXE}" 2>nul | find /I "{_APP_EXE}" >nul',
        "if %ERRORLEVEL%==0 goto killloop",
        "ping 127.0.0.1 -n 3 >nul",
        'echo [%date% %time%] NSIS /S startet >> "%LOG%"',
        '"%SETUP%" /S',
        "set NSIS_ERR=%ERRORLEVEL%",
        'echo [%date% %time%] NSIS exit=%NSIS_ERR% >> "%LOG%"',
        "if %NSIS_ERR% NEQ 0 exit /b 1",
    ]
    lines.extend(_batch_restart_lines(inst_dir))
    if delete_self:
        lines.append('del /f /q "%~f0" 2>nul')
    return lines


def write_desktop_install_helper(setup: Path, inst_dir: str) -> None:
    """Notfall-Batch auf dem Desktop."""
    desktop = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
    helper = desktop / "SurepriseAi-JETZT-INSTALLIEREN.bat"
    lines = _batch_body(str(setup.resolve()), inst_dir, delete_self=False)
    lines[0] = "@echo off"
    lines.insert(7, 'echo [%date% %time%] === Manuelles Update === >> "%LOG%"')
    helper.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    update_logger.write(f"Desktop-Hilfe: {helper}")


def _launch_windows_update_batch(setup: Path, inst_dir: str) -> None:
    """Detached Batch: taskkill → NSIS /S → App-Neustart mit Fallback."""
    bat_path = Path(tempfile.gettempdir()) / f"sureprise_update_{os.getpid()}.bat"
    lines = _batch_body(str(setup.resolve()), inst_dir, delete_self=True)
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

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

_BATCH_WAIT_PINGS = 4  # ~3 s – App beendet sich, EXE wird freigegeben


def launch_update_installer(setup_path: Path) -> None:
    """
    Führt das Setup aus.
    Installierte App: verzögerter Batch-Launcher → NSIS /S, Neustart via installer.nsi.
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

    if os.name == "nt":
        _launch_windows_delayed_batch(path, inst)
    else:
        cmd = [str(path), "/S", f"/D={inst}"]
        proc = subprocess.Popen(cmd, close_fds=True)
        update_logger.write(f"Popen PID={proc.pid}")


def _launch_windows_delayed_batch(setup: Path, inst_dir: str) -> None:
    """
    Schreibt eine Batch-Datei, wartet kurz und startet NSIS /S.
    Zuverlässiger als direkter Aufruf aus der laufenden PyInstaller-EXE
    (EXE ist dann bereits geschlossen, NSIS kann überschreiben).
    """
    bat_path = Path(tempfile.gettempdir()) / f"sureprise_update_{os.getpid()}.bat"
    setup_str = str(setup.resolve())
    lines = [
        "@echo off",
        f"ping 127.0.0.1 -n {_BATCH_WAIT_PINGS} >nul",
        f'"{setup_str}" /S /D={inst_dir}',
        'if errorlevel 1 echo SurepriseAi Update fehlgeschlagen >> "%USERPROFILE%\\Desktop\\SurepriseAi-Update.log"',
        'del /f /q "%~f0" 2>nul',
    ]
    bat_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    update_logger.write(f"Batch-Launcher: {bat_path}")
    for line in lines:
        update_logger.write(f"  {line}")

    try:
        os.startfile(str(bat_path))
        update_logger.write("Batch via os.startfile gestartet")
        return
    except Exception:
        update_logger.write_exception("os.startfile Batch")

    _launch_windows_shell_execute(setup, inst_dir)


def _launch_windows_shell_execute(setup: Path, inst_dir: str) -> None:
    """Fallback: ShellExecuteW, dann Popen."""
    params = f'/S /D={inst_dir}'
    cmd = [str(setup), "/S", f"/D={inst_dir}"]
    try:
        import ctypes

        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "open",
            str(setup),
            params,
            str(setup.parent),
            0,
        )
        update_logger.write(f"ShellExecuteW return={ret}")
        if int(ret) > 32:
            update_logger.write("ShellExecuteW: Installer gestartet")
            return
        update_logger.write(f"ShellExecuteW fehlgeschlagen (code {ret})")
    except Exception:
        update_logger.write_exception("ShellExecuteW")

    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        proc = subprocess.Popen(cmd, close_fds=True, creationflags=flags)
        update_logger.write(f"Popen Fallback PID={proc.pid}")
    except Exception:
        update_logger.write_exception("Popen Fallback")
        update_logger.write("Letzter Versuch: os.startfile Setup")
        os.startfile(str(setup))

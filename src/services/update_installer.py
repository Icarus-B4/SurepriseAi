"""
update_installer.py
Startet das NSIS-Setup nach einem Update (stille Installation).
"""

import os
import subprocess
from pathlib import Path

from src.services import update_logger
from src.utils.app_paths import install_root, is_frozen


def launch_update_installer(setup_path: Path) -> None:
    """
    Führt das Setup aus.
    Installierte App: NSIS /S (silent) in bestehenden Ordner, danach Neustart via installer.nsi.
    Dev (run.py): normaler Wizard.
    """
    path = Path(setup_path)
    update_logger.write(f"launch_update_installer: path={path}")
    update_logger.write(f"  exists={path.is_file()} size={path.stat().st_size if path.is_file() else 'n/a'}")

    if not path.is_file():
        raise FileNotFoundError(f"Setup nicht gefunden: {path}")

    if not is_frozen():
        update_logger.write("Dev-Modus: os.startfile (Wizard)")
        os.startfile(str(path))
        return

    inst = str(install_root())
    params = f'/S /D={inst}'
    cmd = [str(path), "/S", f"/D={inst}"]
    update_logger.write(f"Silent-Install Ziel: {inst}")
    update_logger.write(f"NSIS-Parameter: {params}")

    if os.name == "nt":
        _launch_windows(path, params, cmd)
    else:
        proc = subprocess.Popen(cmd, close_fds=True)
        update_logger.write(f"Popen PID={proc.pid}")


def _launch_windows(setup: Path, params: str, cmd: list[str]) -> None:
    """Windows: ShellExecute zuerst (zuverlässiger aus PyInstaller), Popen als Fallback."""
    try:
        import ctypes

        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "open",
            str(setup),
            params,
            str(setup.parent),
            0,  # SW_HIDE
        )
        update_logger.write(f"ShellExecuteW return={ret}")
        if int(ret) > 32:
            update_logger.write("ShellExecuteW: Installer gestartet")
            return
        update_logger.write(f"ShellExecuteW fehlgeschlagen (code {ret}), Fallback Popen")
    except Exception:
        update_logger.write_exception("ShellExecuteW")

    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        proc = subprocess.Popen(cmd, close_fds=True, creationflags=flags)
        update_logger.write(f"Popen Fallback PID={proc.pid}")
    except Exception:
        update_logger.write_exception("Popen Fallback")
        update_logger.write("Letzter Versuch: os.startfile")
        os.startfile(str(setup))

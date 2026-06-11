"""
update_installer.py
Startet das NSIS-Setup nach einem Update (stille Installation).
"""

import os
import subprocess
from pathlib import Path

from src.utils.app_paths import install_root, is_frozen


def launch_update_installer(setup_path: Path) -> None:
    """
    Führt das Setup aus.
    Installierte App: NSIS /S (silent) in bestehenden Ordner, danach Neustart via installer.nsi.
    Dev (run.py): normaler Wizard.
    """
    path = Path(setup_path)
    if not path.is_file():
        raise FileNotFoundError(f"Setup nicht gefunden: {path}")

    if not is_frozen():
        os.startfile(str(path))
        return

    inst = str(install_root())
    cmd = [str(path), "/S", f"/D={inst}"]
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        flags = 0
    subprocess.Popen(cmd, close_fds=True, creationflags=flags)
    print(f"[Update] Installer gestartet: {' '.join(cmd)}")

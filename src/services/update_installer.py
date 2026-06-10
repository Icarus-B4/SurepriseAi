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
    path = str(setup_path)
    if not is_frozen():
        os.startfile(path)
        return

    inst = str(install_root())
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    # NSIS: /D= muss letzter Parameter sein
    subprocess.Popen(
        [path, "/S", f"/D={inst}"],
        close_fds=True,
        creationflags=flags,
    )

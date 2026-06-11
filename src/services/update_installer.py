"""
update_installer.py
Auto-Update: Prozesse beenden → stille Deinstallation → Neuinstallation → Neustart.
Nutzerdaten in %APPDATA%\\SurepriseAi bleiben unberührt. Keine Desktop-Dateien.
"""

import os
import subprocess
import tempfile
from pathlib import Path

from src.services import update_logger
from src.utils.app_paths import install_root, is_frozen, user_data_dir

_APP_EXE = "SurepriseAi.exe"
_UNINSTALL_EXE = "Uninstall.exe"
_LEGACY_DESKTOP_BAT = "SurepriseAi-JETZT-INSTALLIEREN.bat"


def cleanup_desktop_update_artifacts() -> None:
    """Entfernt veraltete Update-Hilfsdateien vom Desktop (wird nie neu angelegt)."""
    desktop = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
    for name in (_LEGACY_DESKTOP_BAT,):
        path = desktop / name
        if not path.is_file():
            continue
        try:
            path.unlink()
            update_logger.write(f"Desktop-Artefakt entfernt: {path}")
        except OSError as exc:
            update_logger.write(f"Desktop-Artefakt nicht löschbar ({path}): {exc}")


def _desktop_log_path() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop" / "SurepriseAi-Update.log"


def launch_update_installer(setup_path: Path) -> None:
    """
    Installierte App: PowerShell in %TEMP%.
    Dev (run.py): Setup-Wizard.
    """
    cleanup_desktop_update_artifacts()

    path = Path(setup_path)
    update_logger.write(f"launch_update_installer: path={path}")
    update_logger.write(f"  user_data={user_data_dir()} (bleibt erhalten)")
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
    uninst = str(Path(inst) / _UNINSTALL_EXE)
    update_logger.write(f"Installationsordner: {inst}")
    _launch_windows_update_powershell(path, inst, uninst)


def _launch_windows_update_powershell(setup: Path, inst_dir: str, uninstaller: str) -> None:
    """Deinstall → Install → Neustart; %APPDATA%\\SurepriseAi wird nicht gelöscht."""
    log = str(_desktop_log_path())
    setup_str = str(setup.resolve())
    exe = str(Path(inst_dir) / _APP_EXE)
    appdata = str(user_data_dir())
    ps_path = Path(tempfile.gettempdir()) / f"sureprise_update_{os.getpid()}.ps1"

    script = f"""$ErrorActionPreference = 'Continue'
$Log = '{log}'
function Log($m) {{ Add-Content -Path $Log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" -Encoding UTF8 }}
Log '=== Auto-Update gestartet ==='
Log 'Nutzerdaten bleiben in: {appdata}'
Log "Setup={setup_str}"
Log "InstDir={inst_dir}"

# Prozesse beenden (max. 25 s)
$deadline = (Get-Date).AddSeconds(25)
while ((Get-Process -Name SurepriseAi -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {{
    Stop-Process -Name SurepriseAi -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 600
}}
Start-Sleep -Seconds 2

# Alte Version deinstallieren (nur Programmordner – kein AppData)
$uninst = '{uninstaller}'
if (Test-Path -LiteralPath $uninst) {{
    Log "Deinstallation: $uninst /S"
    $u = Start-Process -FilePath $uninst -ArgumentList '/S','_?={inst_dir}' -Wait -PassThru
    Log "Deinstallation exit=$($u.ExitCode)"
    Start-Sleep -Seconds 3
}} else {{
    Log 'Kein Uninstall.exe – direkte Neuinstallation'
}}

# Frische Installation
Log 'NSIS Setup /S startet'
$p = Start-Process -FilePath '{setup_str}' -ArgumentList '/S' -Wait -PassThru
Log "NSIS exit=$($p.ExitCode)"
if ($p.ExitCode -ne 0) {{ exit $p.ExitCode }}

Start-Sleep -Seconds 2
Log 'Starte App: {exe}'
Start-Process -FilePath '{exe}' -WorkingDirectory '{inst_dir}'
Start-Sleep -Seconds 3
if (Get-Process -Name SurepriseAi -ErrorAction SilentlyContinue) {{
    Log 'App neu gestartet OK'
}} else {{
    Log 'WARNUNG: App nicht gestartet – bitte SurepriseAi aus dem Startmenü öffnen'
}}
Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
"""
    ps_path.write_text(script, encoding="utf-8")
    update_logger.write(f"PowerShell-Launcher: {ps_path}")

    ps_cmd = (
        f'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden '
        f'-File "{ps_path}"'
    )
    subprocess.Popen(
        f'cmd /c start "" /min {ps_cmd}',
        shell=True,
        close_fds=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    update_logger.write("Auto-Update gestartet (Deinstall → Install → Neustart)")

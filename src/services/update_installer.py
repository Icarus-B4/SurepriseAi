"""
update_installer.py
Startet das NSIS-Setup nach einem Update (stille Installation, nur %TEMP%).
"""

import os
import subprocess
import tempfile
from pathlib import Path

from src.services import update_logger
from src.utils.app_paths import install_root, is_frozen

_APP_EXE = "SurepriseAi.exe"
_LEGACY_DESKTOP_BAT = "SurepriseAi-JETZT-INSTALLIEREN.bat"


def _desktop_log_path() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop" / "SurepriseAi-Update.log"


def _remove_legacy_desktop_helper() -> None:
    """Entfernt alte Notfall-.bat vom Desktop (wird nicht mehr angelegt)."""
    helper = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop" / _LEGACY_DESKTOP_BAT
    if not helper.is_file():
        return
    try:
        helper.unlink()
        update_logger.write(f"Alte Desktop-Datei entfernt: {helper}")
    except OSError as exc:
        update_logger.write(f"Desktop-Datei nicht löschbar: {exc}")


def launch_update_installer(setup_path: Path) -> None:
    """
    Installierte App: PowerShell in %TEMP% – taskkill, NSIS /S, Neustart.
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

    _remove_legacy_desktop_helper()

    if not is_frozen():
        update_logger.write("Dev-Modus: os.startfile (Wizard)")
        os.startfile(str(path))
        return

    inst = str(install_root())
    update_logger.write(f"Silent-Install Ziel (Registry): {inst}")
    _launch_windows_update_powershell(path, inst)


def _launch_windows_update_powershell(setup: Path, inst_dir: str) -> None:
    """Detached PowerShell – kein Desktop, nur %TEMP%."""
    log = str(_desktop_log_path())
    setup_str = str(setup.resolve())
    exe = str(Path(inst_dir) / _APP_EXE)
    ps_path = Path(tempfile.gettempdir()) / f"sureprise_update_{os.getpid()}.ps1"

    script = f"""$ErrorActionPreference = 'Continue'
$Log = '{log}'
function Log($m) {{ Add-Content -Path $Log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" -Encoding UTF8 }}
Log '=== PS-Update gestartet ==='
Log "Setup={setup_str}"
Log "InstDir={inst_dir}"
$deadline = (Get-Date).AddSeconds(25)
while ((Get-Process -Name SurepriseAi -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {{
    Stop-Process -Name SurepriseAi -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 600
}}
Start-Sleep -Seconds 2
Log 'NSIS /S startet'
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
    Log 'WARNUNG: App nicht gestartet'
}}
Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
"""
    ps_path.write_text(script, encoding="utf-8")
    update_logger.write(f"PowerShell-Launcher: {ps_path}")

    # cmd start /min – zuverlässiger als detached Popen direkt auf powershell.exe
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
    update_logger.write("PowerShell-Update gestartet (cmd start /min)")

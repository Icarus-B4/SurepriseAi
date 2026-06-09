"""
run.py
Bequemes Start-Skript fuer SurepriseAi (PyQt6-Edition).
Prueft Dependencies und startet die App.
"""
import sys
import os
from pathlib import Path

# UTF-8 Ausgabe erzwingen (PowerShell cp1252 Problem)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).parent

def check_dependencies() -> bool:
    """Prueft ob alle kritischen Packages installiert sind."""
    required = ["PyQt6", "sounddevice", "numpy", "pyperclip"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"WARNUNG: Fehlende Packages: {', '.join(missing)}")
        print("   Installiere mit: pip install -r requirements.txt")
        return False
    return True

def main() -> None:
    print("SurepriseAi startet...")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Arbeitsverzeichnis: {_ROOT}")
    print("   Lade Dynamic Island (PyQt6)...")

    if not check_dependencies():
        sys.exit(1)

    from src.main import main as app_main
    app_main()

if __name__ == "__main__":
    os.chdir(_ROOT)
    sys.path.insert(0, str(_ROOT))
    main()

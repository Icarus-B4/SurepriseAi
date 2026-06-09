"""
main.py
Einstiegspunkt für SurepriseAi (PyQt6-Version).
Initialisiert die SurepriseApp und startet die Qt-Event-Schleife.
"""

import sys
import os

# Projektstamm zum Python-Pfad hinzufügen
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.app import SurepriseApp

def main():
    app = SurepriseApp()
    
    # Beim Schließen aufräumen
    sys.exit_handler = app.shutdown
    
    app.start()

if __name__ == "__main__":
    main()

"""
outside_click_overlay.py
Verwendet pynput, um Klicks außerhalb der Island zuverlässig abzufangen.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from pynput import mouse

class OutsideClickOverlay(QObject):
    """
    Nutzt pynput für einen globalen Mouse-Hook statt eines fehleranfälligen
    transparenten Fensters in Windows.
    """

    global_click = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = None

    def show_below(self, anchor) -> None:
        """Aktiviert den globalen Mouse-Hook."""
        if self._listener is None:
            self._listener = mouse.Listener(on_click=self._on_click)
            self._listener.start()

    def hide_overlay(self) -> None:
        """Deaktiviert den globalen Mouse-Hook."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            self.global_click.emit(int(x), int(y))

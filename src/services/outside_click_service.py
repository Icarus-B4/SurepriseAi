"""
outside_click_service.py
Globaler Linksklick via pynput – Dispatch per Qt-Signal (thread-sicher).
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

try:
    from pynput import mouse as pynput_mouse
    PYNPUT_MOUSE_AVAILABLE = True
except ImportError:
    PYNPUT_MOUSE_AVAILABLE = False


class OutsideClickBridge(QObject):
    """Thread-sichere Brücke: pynput-Thread → Qt-Hauptthread."""

    clicked = pyqtSignal(int, int)


class OutsideClickService:
    def __init__(self, bridge: OutsideClickBridge) -> None:
        self._bridge = bridge
        self._listener: Optional[object] = None

    def start(self) -> bool:
        if not PYNPUT_MOUSE_AVAILABLE:
            return False
        if self._listener is not None:
            return True
        try:
            self._listener = pynput_mouse.Listener(on_click=self._on_click)
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception as exc:
            print(f"[OutsideClick] Listener konnte nicht starten: {exc}")
            return False

    def stop(self) -> None:
        if self._listener is None:
            return
        try:
            self._listener.stop()
        except Exception:
            pass
        self._listener = None

    def _on_click(self, x: int, y: int, button: object, pressed: bool) -> None:
        if not pressed or button != pynput_mouse.Button.left:
            return
        self._bridge.clicked.emit(int(x), int(y))

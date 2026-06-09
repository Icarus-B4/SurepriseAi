"""
hotkey_service.py
Globaler Hotkey-Listener via pynput.
Unterstützt Push-to-Talk und Toggle-Modus.
Läuft in einem separaten Thread – kein Admin nötig.
"""

import threading
from typing import Callable, Optional

try:
    from pynput import keyboard as pynput_kb
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("[Hotkey] pynput nicht verfügbar – Hotkey deaktiviert")

from .config_service import config

# Mapping von Hotkey-Strings zu pynput Key-Objekten
_SPECIAL_KEYS = {
    "f1":  pynput_kb.Key.f1  if PYNPUT_AVAILABLE else None,
    "f2":  pynput_kb.Key.f2  if PYNPUT_AVAILABLE else None,
    "f3":  pynput_kb.Key.f3  if PYNPUT_AVAILABLE else None,
    "f4":  pynput_kb.Key.f4  if PYNPUT_AVAILABLE else None,
    "f5":  pynput_kb.Key.f5  if PYNPUT_AVAILABLE else None,
    "f6":  pynput_kb.Key.f6  if PYNPUT_AVAILABLE else None,
    "f7":  pynput_kb.Key.f7  if PYNPUT_AVAILABLE else None,
    "f8":  pynput_kb.Key.f8  if PYNPUT_AVAILABLE else None,
    "f9":  pynput_kb.Key.f9  if PYNPUT_AVAILABLE else None,
    "f10": pynput_kb.Key.f10 if PYNPUT_AVAILABLE else None,
    "f11": pynput_kb.Key.f11 if PYNPUT_AVAILABLE else None,
    "f12": pynput_kb.Key.f12 if PYNPUT_AVAILABLE else None,
} if PYNPUT_AVAILABLE else {}


class HotkeyService:
    """
    Überwacht globale Tastatureingaben und löst Recording-Callbacks aus.
    
    Modi:
    - Toggle: Einmal drücken → Start, nochmal → Stop
    - Push-to-Talk: Halten → Aufnahme, Loslassen → Stop
    """

    def __init__(self) -> None:
        self._listener: Optional[object] = None
        self._active_keys: set = set()
        self._pressed_keys: set = set()
        self._is_running: bool = False
        self._recording_active: bool = False


        # Callbacks
        self._on_start: Optional[Callable[[], None]] = None
        self._on_stop: Optional[Callable[[], None]] = None

    def set_start_callback(self, cb: Callable[[], None]) -> None:
        self._on_start = cb

    def set_stop_callback(self, cb: Callable[[], None]) -> None:
        self._on_stop = cb

    # ── Listener-Steuerung ────────────────────────────────────────────────────

    def start(self) -> bool:
        """Startet den globalen Keyboard-Listener in einem separaten Thread."""
        if not PYNPUT_AVAILABLE:
            print("[Hotkey] pynput nicht verfügbar")
            return False

        if not config.hotkey_enabled:
            print("[Hotkey] Globaler Hotkey ist deaktiviert")
            return False

        if self._is_running:
            return True

        try:
            self._listener = pynput_kb.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self._listener.daemon = True
            self._listener.start()
            self._is_running = True
            hotkey = config.global_hotkey
            mode = "Push-to-Talk" if config.push_to_talk else "Toggle"
            print(f"[Hotkey] Listener gestartet – '{hotkey}' ({mode}-Modus)")
            return True
        except Exception as e:
            print(f"[Hotkey] Fehler beim Starten: {e}")
            return False

    def stop(self) -> None:
        """Stoppt den Keyboard-Listener."""
        self._is_running = False
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        print("[Hotkey] Listener gestoppt")

    # ── Key-Handler ───────────────────────────────────────────────────────────

    def _get_hotkey_key(self) -> Optional[object]:
        """Gibt den konfigurierten Hotkey als pynput-Key zurück."""
        hotkey_str = config.global_hotkey.lower().strip()

        # Sondertatsten (F1–F12)
        if hotkey_str in _SPECIAL_KEYS:
            return _SPECIAL_KEYS[hotkey_str]

        # Normale Buchstaben/Zahlen
        try:
            return pynput_kb.KeyCode.from_char(hotkey_str)
        except Exception:
            return None

    def _key_matches(self, key: object) -> bool:
        """Prüft ob der gedrückte Tastendruck dem konfigurierten Hotkey entspricht."""
        target = self._get_hotkey_key()
        if target is None:
            return False
        return key == target

    def _on_press(self, key: object) -> None:
        """Wird aufgerufen wenn eine Taste gedrückt wird."""
        # Key-Repeat von Windows unterdrücken
        if key in self._pressed_keys:
            return
        self._pressed_keys.add(key)

        if not self._key_matches(key):
            return

        if config.push_to_talk:
            # Push-to-Talk: Starten wenn noch nicht aktiv
            if not self._recording_active:
                self._recording_active = True
                if self._on_start:
                    threading.Thread(target=self._on_start, daemon=True).start()
        else:
            # Toggle-Modus: Umschalten
            if not self._recording_active:
                self._recording_active = True
                if self._on_start:
                    threading.Thread(target=self._on_start, daemon=True).start()
            else:
                self._recording_active = False
                if self._on_stop:
                    threading.Thread(target=self._on_stop, daemon=True).start()

    def _on_release(self, key: object) -> None:
        """Wird aufgerufen wenn eine Taste losgelassen wird."""
        # Taste aus dem Set der gedrückten Tasten entfernen
        self._pressed_keys.discard(key)

        if not config.push_to_talk:
            return

        if self._key_matches(key) and self._recording_active:
            self._recording_active = False
            if self._on_stop:
                threading.Thread(target=self._on_stop, daemon=True).start()


    @property
    def is_running(self) -> bool:
        return self._is_running

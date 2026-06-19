"""
hotkey_service.py
Globaler Hotkey-Listener via pynput.
Unterstützt Push-to-Talk und Toggle-Modus.
Läuft in einem separaten Thread – kein Admin nötig.
"""

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
        self._on_translate_de: Optional[Callable[[], None]] = None
        self._on_translate_en: Optional[Callable[[], None]] = None
        self._on_mute_toggle: Optional[Callable[[], None]] = None
        self._on_device_cycle: Optional[Callable[[], None]] = None
        self._on_rewrite: Optional[Callable[[], None]] = None
        self._on_escape: Optional[Callable[[], None]] = None
        self._on_basics_nav: Optional[Callable[[str], None]] = None
        self._on_open_settings: Optional[Callable[[], None]] = None
        self._is_basics_active: Optional[Callable[[], bool]] = None

    def set_start_callback(self, cb: Callable[[], None]) -> None:
        self._on_start = cb

    def set_stop_callback(self, cb: Callable[[], None]) -> None:
        self._on_stop = cb

    def set_translate_de_callback(self, cb: Callable[[], None]) -> None:
        self._on_translate_de = cb

    def set_translate_en_callback(self, cb: Callable[[], None]) -> None:
        self._on_translate_en = cb

    def set_mute_toggle_callback(self, cb: Callable[[], None]) -> None:
        self._on_mute_toggle = cb

    def set_device_cycle_callback(self, cb: Callable[[], None]) -> None:
        self._on_device_cycle = cb

    def set_rewrite_callback(self, cb: Callable[[], None]) -> None:
        self._on_rewrite = cb

    def set_escape_callback(self, cb: Callable[[], None]) -> None:
        self._on_escape = cb

    def set_basics_nav_callback(self, cb: Callable[[str], None]) -> None:
        self._on_basics_nav = cb

    def set_open_settings_callback(self, cb: Callable[[], None]) -> None:
        self._on_open_settings = cb

    def set_basics_active_callback(self, cb: Callable[[], bool]) -> None:
        """Gibt an, ob Buchstaben-Hotkeys (m/d/s) und Hub-Navigation aktiv sind."""
        self._is_basics_active = cb

    def _basics_keys_allowed(self) -> bool:
        if self._is_basics_active is None:
            return False
        try:
            return bool(self._is_basics_active())
        except Exception:
            return False

    def _fire(self, cb: Optional[Callable[..., None]], *args: object) -> None:
        """Ruft Callback direkt auf – UI-Marshalling liegt beim Empfänger."""
        if cb is None:
            return
        try:
            cb(*args)
        except Exception as exc:
            print(f"[Hotkey] Callback-Fehler: {exc}")

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
            extras = ""
            if config.get_bool("enable_translate_hotkeys", True):
                extras = (
                    f", Übersetzung DE={config.get_str('translate_german_hotkey', 'f6')}"
                    f", EN={config.get_str('translate_english_hotkey', 'f7')}"
                )
            print(f"[Hotkey] Listener gestartet – '{hotkey}' ({mode}-Modus){extras}")
            rewrite_key = config.get_str("selected_text_hotkey", "f9")
            print(f"[Hotkey] SelectedText Umschrift gebunden: {rewrite_key}")
            print(
                "[Hotkey] Basics-Steuerung (nur im Basics-Modus): "
                "m=Mute, d=Device, s=Einstellungen, Escape=schließen"
            )
            try:
                from src.services import dictation_logger as dlog
                dlog.write(
                    f"SelectedText Hotkey gebunden: {rewrite_key}",
                    also_print=False,
                )
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"[Hotkey] Fehler beim Starten: {e}")
            return False

    def stop(self) -> None:
        """Stoppt den Keyboard-Listener."""
        self._is_running = False
        self._recording_active = False
        self._pressed_keys.clear()
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        print("[Hotkey] Listener gestoppt")

    def restart(self) -> bool:
        """Stoppt und startet den Listener neu (z. B. nach Einstellungsänderung)."""
        self.stop()
        return self.start()

    # ── Key-Handler ───────────────────────────────────────────────────────────

    def _resolve_key(self, hotkey_str: str) -> Optional[object]:
        """Gibt einen Hotkey-String als pynput-Key zurück."""
        key_name = hotkey_str.lower().strip()
        if key_name.startswith("key."):
            key_name = key_name[4:]
        if key_name in _SPECIAL_KEYS:
            return _SPECIAL_KEYS[key_name]
        if len(key_name) == 1:
            return pynput_kb.KeyCode.from_char(key_name)
        return None

    def _get_hotkey_key(self) -> Optional[object]:
        """Gibt den konfigurierten Aufnahme-Hotkey als pynput-Key zurück."""
        return self._resolve_key(config.global_hotkey)

    def _key_matches(self, key: object, hotkey_str: Optional[str] = None) -> bool:
        """Prüft ob der gedrückte Tastendruck dem Hotkey entspricht."""
        target = self._resolve_key(hotkey_str) if hotkey_str else self._get_hotkey_key()
        if target is None:
            return False
        return key == target

    def _on_press(self, key: object) -> None:
        """Wird aufgerufen wenn eine Taste gedrückt wird."""
        # Key-Repeat von Windows unterdrücken
        if key in self._pressed_keys:
            return
        self._pressed_keys.add(key)

        if config.get_bool("enable_translate_hotkeys", True):
            de_key = config.get_str("translate_german_hotkey", "f6")
            en_key = config.get_str("translate_english_hotkey", "f7")
            if self._key_matches(key, de_key) and self._on_translate_de:
                self._fire(self._on_translate_de)
                return
            if self._key_matches(key, en_key) and self._on_translate_en:
                self._fire(self._on_translate_en)
                return

        if self._key_matches(key, config.get_str("selected_text_hotkey", "f9")) and self._on_rewrite:
            self._fire(self._on_rewrite)
            return

        if self._basics_keys_allowed():
            if self._key_matches(key, "m") and self._on_mute_toggle:
                self._fire(self._on_mute_toggle)
                return

            if self._key_matches(key, "d") and self._on_device_cycle:
                self._fire(self._on_device_cycle)
                return

            if self._key_matches(key, "s") and self._on_open_settings:
                self._fire(self._on_open_settings)
                return

            if key == pynput_kb.Key.esc and self._on_escape:
                self._fire(self._on_escape)
                return

            if self._on_basics_nav:
                nav_map = {
                    pynput_kb.Key.right: "right",
                    pynput_kb.Key.left: "left",
                }
                if key in nav_map:
                    self._fire(self._on_basics_nav, nav_map[key])
                    return

        if not self._key_matches(key):
            return

        if config.push_to_talk:
            if not self._recording_active:
                self._recording_active = True
                self._fire(self._on_start)
        else:
            if not self._recording_active:
                self._recording_active = True
                self._fire(self._on_start)
            else:
                self._recording_active = False
                self._fire(self._on_stop)

    def _on_release(self, key: object) -> None:
        """Wird aufgerufen wenn eine Taste losgelassen wird."""
        # Taste aus dem Set der gedrückten Tasten entfernen
        self._pressed_keys.discard(key)

        if not config.push_to_talk:
            return

        if self._key_matches(key, config.global_hotkey) and self._recording_active:
            self._recording_active = False
            self._fire(self._on_stop)


    @property
    def is_running(self) -> bool:
        return self._is_running

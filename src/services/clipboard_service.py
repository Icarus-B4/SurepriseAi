"""
clipboard_service.py
Verwaltet die Zwischenablage und (optionale) Text-Injektion in andere Apps.
Primär: pyperclip. Sekundär: Win32 SendKeys für Auto-Inject.
"""

import time
import threading
from typing import Optional

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("[Clipboard] pyperclip nicht verfügbar")

try:
    import ctypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from .config_service import config


class ClipboardService:
    """Kopiert Text in die Zwischenablage und injiziert ihn optional."""

    def __init__(self) -> None:
        self._last_text: str = ""

    def copy(self, text: str) -> bool:
        """
        Kopiert Text in die Windows-Zwischenablage.

        Returns:
            True bei Erfolg
        """
        if not text:
            return False

        if PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(text)
                self._last_text = text
                print(f"[Clipboard] Kopiert: '{text[:40]}...'")
                return True
            except Exception as e:
                print(f"[Clipboard] pyperclip-Fehler: {e}")

        # Fallback: Win32 API direkt
        return self._copy_win32(text)

    def _copy_win32(self, text: str) -> bool:
        """Win32 Clipboard API als Fallback."""
        if not WIN32_AVAILABLE:
            return False
        try:
            import ctypes
            CF_UNICODETEXT = 13
            GMEM_MOVEABLE = 0x0002

            # Clipboard öffnen
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()

            # Speicher allozieren
            encoded = text.encode("utf-16-le") + b"\x00\x00"
            handle = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
            ptr = ctypes.windll.kernel32.GlobalLock(handle)
            ctypes.memmove(ptr, encoded, len(encoded))
            ctypes.windll.kernel32.GlobalUnlock(handle)

            # In Clipboard setzen
            ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, handle)
            ctypes.windll.user32.CloseClipboard()
            self._last_text = text
            return True
        except Exception as e:
            print(f"[Clipboard] Win32-Fehler: {e}")
            return False

    def inject_text(self, text: str, delay_ms: int = 100, target_hwnd: Optional[int] = None) -> bool:
        """
        Fügt Text automatisch an der aktuellen Cursor-Position ein.
        Simuliert Ctrl+V nach kurzem Delay und stellt das Clipboard optional wieder her.

        Args:
            text: Einzufügender Text
            delay_ms: Wartezeit vor Einfügen (ms)
            target_hwnd: Optionale Win32 HWND der Zielanwendung

        Returns:
            True bei Erfolg
        """
        if not config.get_bool("auto_inject_text", True):
            return False

        # Zwischenablage sichern, falls auto_copy deaktiviert ist
        original_text = None
        if not config.auto_copy:
            if PYPERCLIP_AVAILABLE:
                try:
                    original_text = pyperclip.paste()
                except Exception as e:
                    print(f"[Clipboard] Fehler beim Lesen der Zwischenablage vor Inject: {e}")

        # Erst kopieren
        if not self.copy(text):
            return False

        # Dann Ctrl+V simulieren
        thread = threading.Thread(
            target=self._send_paste,
            args=(delay_ms, target_hwnd, original_text),
            daemon=True,
        )
        thread.start()
        return True

    def _force_foreground(self, hwnd: int) -> None:
        if not WIN32_AVAILABLE:
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd == hwnd:
                return
                
            # Threads verknüpfen, um die Focus Stealing Prevention zu umgehen
            fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
            current_thread = kernel32.GetCurrentThreadId()
            
            user32.AttachThreadInput(current_thread, fg_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            user32.AttachThreadInput(current_thread, fg_thread, False)
            
            print(f"[Clipboard] force_foreground: Ziel-Fenster {hwnd} erzwungen fokussiert")
        except Exception as e:
            print(f"[Clipboard] force_foreground Fehler: {e}")
            try:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except:
                pass

    def _send_paste(self, delay_ms: int, target_hwnd: Optional[int] = None, original_text: Optional[str] = None) -> None:
        """Simuliert das Eintippen des Textes via Ctrl+V an der aktiven Cursorposition."""
        if WIN32_AVAILABLE and target_hwnd:
            self._force_foreground(target_hwnd)
            time.sleep(0.05)  # 50ms warten, bis Fokus aktiv ist

        time.sleep(delay_ms / 1000.0)

        if not WIN32_AVAILABLE:
            return

        text_to_inject = self._last_text
        if not text_to_inject:
            return

        try:
            import ctypes
            import ctypes.wintypes as wintypes

            # Struktur für SendInput (vollständig deklariert für korrekte 64-Bit-Größe)
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx",          wintypes.LONG),
                    ("dy",          wintypes.LONG),
                    ("mouseData",   wintypes.DWORD),
                    ("dwFlags",     wintypes.DWORD),
                    ("time",        wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t),
                ]

            class HARDWAREINPUT(ctypes.Structure):
                _fields_ = [
                    ("uMsg",    wintypes.DWORD),
                    ("wParamL", wintypes.WORD),
                    ("wParamH", wintypes.WORD),
                ]

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk",         wintypes.WORD),
                    ("wScan",       wintypes.WORD),
                    ("dwFlags",     wintypes.DWORD),
                    ("time",        wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t),
                ]

            class INPUT(ctypes.Structure):
                class _INPUT(ctypes.Union):
                    _fields_ = [
                        ("mi", MOUSEINPUT),
                        ("ki", KEYBDINPUT),
                        ("hi", HARDWAREINPUT),
                    ]
                _anonymous_ = ("_input",)
                _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP   = 0x0002

            # Universelle Ctrl+V Injektion
            VK_CONTROL = 0x11
            VK_V       = 0x56
            scan_ctrl = ctypes.windll.user32.MapVirtualKeyW(VK_CONTROL, 0)
            scan_v = ctypes.windll.user32.MapVirtualKeyW(VK_V, 0)

            inputs = (INPUT * 4)()
            inputs[0].type = INPUT_KEYBOARD
            inputs[0].ki.wVk = VK_CONTROL
            inputs[0].ki.wScan = scan_ctrl
            inputs[0].ki.dwFlags = 0

            inputs[1].type = INPUT_KEYBOARD
            inputs[1].ki.wVk = VK_V
            inputs[1].ki.wScan = scan_v
            inputs[1].ki.dwFlags = 0

            inputs[2].type = INPUT_KEYBOARD
            inputs[2].ki.wVk = VK_V
            inputs[2].ki.wScan = scan_v
            inputs[2].ki.dwFlags = KEYEVENTF_KEYUP

            inputs[3].type = INPUT_KEYBOARD
            inputs[3].ki.wVk = VK_CONTROL
            inputs[3].ki.wScan = scan_ctrl
            inputs[3].ki.dwFlags = KEYEVENTF_KEYUP

            res = ctypes.windll.user32.SendInput(4, inputs, ctypes.sizeof(INPUT))
            print(f"[Clipboard] Text via Ctrl+V injiziert (SendInput-Resultat: {res})")

            # Falls nötig, stellen wir das originale Clipboard nach einer kurzen Verzögerung wieder her
            if original_text is not None:
                time.sleep(0.15)  # 150ms warten, damit die Ziel-App den Text einlesen kann
                if PYPERCLIP_AVAILABLE:
                    try:
                        pyperclip.copy(original_text)
                        print("[Clipboard] Ursprüngliche Zwischenablage wiederhergestellt")
                    except Exception as e:
                        print(f"[Clipboard] Fehler bei Wiederherstellung: {e}")

        except Exception as e:
            print(f"[Clipboard] Inject-Fehler: {e}")

    @property
    def last_text(self) -> str:
        """Zuletzt kopierter Text."""
        return self._last_text

    def read_clipboard(self) -> str:
        """Liest den aktuellen Zwischenablage-Inhalt."""
        if PYPERCLIP_AVAILABLE:
            try:
                return pyperclip.paste() or ""
            except Exception as e:
                print(f"[Clipboard] Lesen fehlgeschlagen: {e}")
        return ""

    def capture_selection(self, target_hwnd: int, delay_ms: int = 80) -> Optional[str]:
        """
        Kopiert markierten Text aus der Ziel-App via Ctrl+C.
        Stellt die ursprüngliche Zwischenablage danach wieder her.
        """
        if not WIN32_AVAILABLE or not target_hwnd:
            return None

        original = self.read_clipboard()
        self._force_foreground(target_hwnd)
        time.sleep(0.04)

        if not self._send_ctrl_c():
            return None

        time.sleep(delay_ms / 1000.0)
        captured = self.read_clipboard().strip()

        if original:
            self._copy_win32(original) if not PYPERCLIP_AVAILABLE else self._restore_clipboard(original)
        elif captured:
            # Leere Zwischenablage wiederherstellen
            self._clear_clipboard()

        if not captured or len(captured) < 2:
            return None
        if captured == original.strip():
            return None
        return captured

    def _restore_clipboard(self, text: str) -> None:
        try:
            pyperclip.copy(text)
        except Exception as e:
            print(f"[Clipboard] Wiederherstellung fehlgeschlagen: {e}")

    def _clear_clipboard(self) -> None:
        if not WIN32_AVAILABLE:
            return
        try:
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass

    def _send_ctrl_c(self) -> bool:
        """Sendet Ctrl+C an das fokussierte Fenster."""
        if not WIN32_AVAILABLE:
            return False
        try:
            import ctypes
            import ctypes.wintypes as wintypes

            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t),
                ]

            class HARDWAREINPUT(ctypes.Structure):
                _fields_ = [
                    ("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD),
                ]

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t),
                ]

            class INPUT(ctypes.Structure):
                class _INPUT(ctypes.Union):
                    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]
                _anonymous_ = ("_input",)
                _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP = 0x0002
            VK_CONTROL, VK_C = 0x11, 0x43
            scan_ctrl = ctypes.windll.user32.MapVirtualKeyW(VK_CONTROL, 0)
            scan_c = ctypes.windll.user32.MapVirtualKeyW(VK_C, 0)

            inputs = (INPUT * 4)()
            for i, (vk, scan, flags) in enumerate([
                (VK_CONTROL, scan_ctrl, 0),
                (VK_C, scan_c, 0),
                (VK_C, scan_c, KEYEVENTF_KEYUP),
                (VK_CONTROL, scan_ctrl, KEYEVENTF_KEYUP),
            ]):
                inputs[i].type = INPUT_KEYBOARD
                inputs[i].ki.wVk = vk
                inputs[i].ki.wScan = scan
                inputs[i].ki.dwFlags = flags

            res = ctypes.windll.user32.SendInput(4, inputs, ctypes.sizeof(INPUT))
            return res == 4
        except Exception as e:
            print(f"[Clipboard] Ctrl+C fehlgeschlagen: {e}")
            return False

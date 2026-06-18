# -*- coding: utf-8 -*-
"""
app_runner.py
Steuerungsklasse für SurepriseAi E2E-Tests.
"""

import json
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
import pyperclip
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_PATH_DEV = ROOT_DIR / ".agent" / "dictation.log"
LOG_PATH_PROD = Path(os.environ.get("APPDATA", "")) / "SurepriseAi" / "dictation.log"


def _island_screen_pos() -> tuple[int, int]:
    """Bildschirmmitte oben – ohne PyQt6 (vermeidet Segfaults im Test-Runner)."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0) // 2, 25
    except Exception:
        return 960, 25


class AppRunner:
    """Hilfsklasse zur Steuerung der Anwendung während des E2E-Tests."""
    def __init__(self):
        self.process = None
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.stdout_lines = []
        self._reader_thread = None

    def start(self):
        """Startet die Applikation als Subprozess."""
        if self.process and self.process.poll() is None:
            self.stop()
            time.sleep(1.0)
        self.clear_log()
        self.stdout_lines = []
        # E2E-Tests erwarten Toggle-Modus für F8-Aufnahme
        self._ensure_toggle_mode()
        cmd = [sys.executable, "-u", str(ROOT_DIR / "run.py")]
        self.process = subprocess.Popen(
            cmd,
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader_thread.start()
        
        # Warten bis die App vollständig initialisiert ist
        start_time = time.time()
        while time.time() - start_time < 20.0:
            out = self.get_stdout_content()
            log = self.get_log_content()
            ready = (
                "SurepriseAi gestartet" in out or "SurepriseAi gestartet" in log
            ) and (
                "[Backdrop]" in out
                or "[Pipeline]" in out
                or "[Hotkey]" in out
            )
            model_ready = (
                "Transkriptions-Modell bereit" in log
                or "Transkriptions-Modell bereit" in out
                or "Whisper" in out and "geladen" in out
            )
            if ready and model_ready:
                break
            time.sleep(0.15)
        time.sleep(0.2)

        # Wenn möglich, das Fenster über win32gui in den Vordergrund bringen
        try:
            import win32gui
            import win32process
            def enum_windows_callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if win_pid == self.process.pid:
                        try:
                            win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
                            win32gui.SetForegroundWindow(hwnd)
                        except Exception:
                            pass
                return True
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception:
            pass

        # Maus über die Island positionieren (kein Klick – Klick würde Expanded öffnen)
        try:
            x, y = _island_screen_pos()
            self.mouse.position = (x, y)
            time.sleep(0.15)
        except Exception:
            pass

    def _read_stdout(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                self.stdout_lines.append(line)
        except Exception:
            pass

    def stop(self):
        """Stoppt die Applikation."""
        if self.process:
            pid = self.process.pid
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
            # Windows: Kindprozesse mitbeenden (verhindert hängende pynput-Listener)
            if sys.platform == "win32" and pid:
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        timeout=5,
                    )
                except Exception:
                    pass
            self.process = None

    def clear_log(self):
        """Löscht das Diktat-Log."""
        for path in (LOG_PATH_DEV, LOG_PATH_PROD):
            if path.exists():
                try:
                    path.write_text("", encoding="utf-8")
                except OSError:
                    pass

    def get_log_content(self) -> str:
        """Gibt den Inhalt des Diktat-Logs zurück."""
        for path in (LOG_PATH_DEV, LOG_PATH_PROD):
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8")
                except OSError:
                    pass
        return ""

    def wait_for_log(self, text: str, timeout: float = 6.0) -> bool:
        """Wartet, bis ein Text im Log auftaucht."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if text in self.get_log_content():
                return True
            time.sleep(0.1)
        return False

    def get_stdout_content(self) -> str:
        """Gibt die gesammelten Konsolenausgaben zurück."""
        return "".join(self.stdout_lines)

    def wait_for_stdout(self, text: str, timeout: float = 6.0) -> bool:
        """Wartet, bis ein Text in den Konsolenausgaben auftaucht."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if text in self.get_stdout_content():
                return True
            time.sleep(0.1)
        return False

    def _ensure_toggle_mode(self):
        """Setzt push_to_talk auf False für zuverlässige F8-Toggle-Tests."""
        config_path = ROOT_DIR / "config.json"
        try:
            if config_path.exists():
                data = json.loads(config_path.read_text(encoding="utf-8"))
            else:
                example = ROOT_DIR / "config.example.json"
                data = json.loads(example.read_text(encoding="utf-8")) if example.exists() else {}
            data["push_to_talk"] = False
            data["enable_global_hotkey"] = True
            config_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        except Exception:
            pass

    def _press_escape_win32(self) -> None:
        """Escape per Win32 keybd_event – zuverlässiger für globale pynput-Hooks."""
        import ctypes
        user32 = ctypes.windll.user32
        vk = 0x1B
        scan = user32.MapVirtualKeyW(vk, 0)
        user32.keybd_event(vk, scan, 0, 0)
        time.sleep(0.03)
        user32.keybd_event(vk, scan, 0x0002, 0)
        time.sleep(0.1)

    def dismiss_basics_via_escape(self, timeout: float = 12.0) -> bool:
        """Drückt Escape bis BASICS → IDLE im Log erscheint."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if "[State] BASICS → IDLE" in self.get_stdout_content():
                return True
            self._press_escape_win32()
            time.sleep(0.35)
        return False

    def press_key(self, key_name: str):
        """Simuliert einen Tastendruck."""
        key_lower = key_name.lower()
        if key_lower == "escape":
            self._press_escape_win32()
            return
        if hasattr(Key, key_lower):
            key = getattr(Key, key_lower)
        else:
            key = key_name
        self.keyboard.press(key)
        self.keyboard.release(key)
        time.sleep(0.1)

    def simulate_hotkey(self, modifier, key):
        """Simuliert eine Tastenkombination wie Ctrl+C."""
        with self.keyboard.pressed(modifier):
            self.keyboard.press(key)
            self.keyboard.release(key)
        time.sleep(0.1)

    def scroll_mouse(self, dx: int, dy: int):
        """Simuliert das Scrollen des Mausrades über der Dynamic Island."""
        old_pos = self.mouse.position
        try:
            x, y = _island_screen_pos()
            self.mouse.position = (x, y)
            time.sleep(0.2)
            self.mouse.scroll(dx, dy)
            time.sleep(0.2)
        finally:
            self.mouse.position = old_pos
        time.sleep(0.1)

    def finish_recording(self, timeout: float = 10.0) -> bool:
        """Stoppt die Aufnahme per F8 und wartet auf das Audio-Stop-Log."""
        self.press_key("f8")
        start = time.time()
        while time.time() - start < timeout:
            log = self.get_log_content()
            if "Stop-Audio" in log or "rms=" in log:
                return True
            time.sleep(0.1)
        return False

    def wait_for_processing_state(self, timeout: float = 10.0) -> bool:
        """Wartet auf den PROCESSING-Zustand nach Aufnahmeende."""
        start = time.time()
        while time.time() - start < timeout:
            out = self.get_stdout_content()
            if "[State] RECORDING → PROCESSING" in out or "processing" in out.lower():
                return True
            time.sleep(0.1)
        return False

    def wait_for_rewrite_done(self, timeout: float = 8.0) -> bool:
        """Wartet auf Abschluss einer SelectedText-Umschrift."""
        start = time.time()
        while time.time() - start < timeout:
            out = self.get_stdout_content()
            log = self.get_log_content()
            combined = out + log
            if (
                "SUCCESS" in out
                or "PROCESSING → IDLE" in out
                or "→ ERROR" in out
                or "Umschrift eingefügt" in combined
                or "Ctrl+V" in combined
                or "Inject" in combined
            ):
                return True
            time.sleep(0.1)
        return False

    def set_clipboard(self, text: str):
        """Setzt den Text der Zwischenablage."""
        pyperclip.copy(text)

    def get_clipboard(self) -> str:
        """Gibt den Inhalt der Zwischenablage zurück."""
        return pyperclip.paste()

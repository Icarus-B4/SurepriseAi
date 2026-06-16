"""
create_demo.py
Automatisiertes Demo-Aufnahme-Skript für SurepriseAi.
Mockt die KI-Services, positioniert die Widgets über einem neutralen Farbverlauf-Hintergrund,
steuert den App-Ablauf per Timer und speichert die Screenshots als animierte GIF-Datei ab.
"""

import sys
import os
import time
import shutil
import random
import traceback
from pathlib import Path

# Custom Exception Hook für PyQt6 Fehlerdiagnose
def qt_exception_hook(exctype, value, tb):
    print("!!! QT UNHANDLED EXCEPTION !!!")
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

sys.excepthook = qt_exception_hook

# UTF-8 Ausgabe erzwingen (PowerShell cp1252 Problem)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Projektstamm zum Python-Pfad hinzufügen
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt, QPoint, QRect
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtGui import QFont, QColor, QPixmap

# --- MOCK KLASSEN ---

class MockAudioService:
    def __init__(self):
        self.is_recording = False
        self._level_cb = None
    def start_recording(self, device=None):
        self.is_recording = True
        return True
    def stop_recording(self):
        self.is_recording = False
        import numpy as np
        return np.zeros(1600)
    def set_level_callback(self, cb):
        self._level_cb = cb
    def get_accumulated_audio(self):
        import numpy as np
        return np.zeros(1600)

class MockHotkeyService:
    def __init__(self) -> None:
        self.is_running = False
    def set_start_callback(self, cb): pass
    def set_stop_callback(self, cb): pass
    def set_translate_de_callback(self, cb): pass
    def set_translate_en_callback(self, cb): pass
    def start(self):
        self.is_running = True
        return True
    def stop(self):
        self.is_running = False
    def restart(self):
        return True

class MockOutsideClickOverlay(QObject):
    global_click = pyqtSignal(int, int)
    def show_below(self, anchor) -> None: pass
    def hide_overlay(self) -> None: pass

class MockUpdateController:
    def __init__(self, app) -> None: pass
    def schedule_startup_check(self) -> None: pass
    def check_now(self, silent=True) -> None: pass
    def open_releases_page(self) -> None: pass

# Monkeypatching vor dem Import der App
import src.services.transcription_pipeline as tp
import src.services.hotkey_service as hs
import src.ui.outside_click_overlay as oco
import src.services.update_controller as uc

tp.AudioService = MockAudioService
hs.HotkeyService = MockHotkeyService
oco.OutsideClickOverlay = MockOutsideClickOverlay
uc.UpdateController = MockUpdateController

# Mock stop_recording in tp.TranscriptionPipeline, damit PipelineWorker nicht läuft
def mock_stop_recording(self):
    self._stop_partial_thread.set()
    if self._partial_thread and self._partial_thread.is_alive():
        self._partial_thread.join(timeout=1.0)
    self.audio.stop_recording()
    self._emit_state("processing")

tp.TranscriptionPipeline.stop_recording = mock_stop_recording

# Importiere die echten App-Komponenten
from src.app import SurepriseApp
from src.services.config_service import config
from src.services.polishing_service import PolishingService

# --- DEMO TEXTE ---
DEMO_TEXTS = {
    "casual": "Hallo, das ist eine automatisierte Demonstration der neuen Dynamic Island von SurepriseAi.",
    "business": "Sehr geehrte Damen und Herren, dies ist eine automatisierte Demonstration der neuen Dynamic Island von SurepriseAi.",
    "bullet_points": "• Automatisierte Demonstration\n• Neue Dynamic Island\n• SurepriseAi Voice-Dictation",
    "key_points": "• Automatische Präsentation der App-Funktionen\n• Demonstration der Dynamic Island\n• Integration von SurepriseAi",
    "concise": "Automatisierte Demo der Dynamic Island von SurepriseAi.",
    "long": "Herzlich willkommen zu dieser automatisierten Demonstration der neuen Dynamic Island von SurepriseAi. Dieses Tool ermöglicht es Ihnen, gesprochenen Text in Echtzeit aufzunehmen und durch fortschrittliche Algorithmen stilistisch anzupassen.",
    "formal": "Guten Tag, hiermit präsentieren wir Ihnen die automatisierte Demonstration der neuen Dynamic Island von SurepriseAi."
}

# PolishingService patchen für Instant-Antworten in der Demo
def mock_polish(self, text: str, style: str = None, screen_context: str = None) -> str:
    active = style or config.selected_style
    return DEMO_TEXTS.get(active, text)

def mock_polish_instant(self, text: str, style: str = None) -> str:
    active = style or config.selected_style
    return DEMO_TEXTS.get(active, text)

PolishingService.polish = mock_polish
PolishingService.polish_instant = mock_polish_instant

# --- HINTERGRUND WIDGET ---

class DemoBackgroundWindow(QWidget):
    """Präsentiert die App vor einem hochwertigen, einheitlichen Hintergrund."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(1360, 850)
        
        # Solid Gradient QSS
        self.setStyleSheet("""
            QWidget#DemoBackground {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #110E24, stop:1 #06040E);
                border: 2px solid #2B2354;
                border-radius: 24px;
            }
        """)
        self.setObjectName("DemoBackground")
        
        # Titel
        self.title_label = QLabel("SurepriseAi", self)
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 0.85); background: transparent; border: none;")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        self.title_label.move(40, 35)

        # Untertitel
        self.subtitle_label = QLabel("AUTOMATISIERTE PRÄSENTATION", self)
        self.subtitle_label.setStyleSheet("color: #6366F1; background: transparent; border: none; letter-spacing: 2px;")
        self.subtitle_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.subtitle_label.move(40, 70)

        # Status
        self.status_label = QLabel("Initialisiere Demo...", self)
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.35); background: transparent; border: none;")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setGeometry(40, 780, 500, 30)

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = int(geom.left() + (geom.width() - self.width()) / 2.0)
            y = int(geom.top() + (geom.height() - self.height()) / 2.0)
            self.move(x, y)

    def set_status(self, text: str):
        self.status_label.setText(text)
        QApplication.processEvents()

# --- DEMO STEUERUNG ---

class DemoRunner(QObject):
    def __init__(self, bg_win: DemoBackgroundWindow, app: SurepriseApp):
        super().__init__()
        self.bg_win = bg_win
        self.app = app
        
        self.temp_dir = _ROOT / "screenshots" / "temp_demo"
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.frame_index = 0
        self.elapsed_ms = 0
        
        # Timer für die Screenshots (10 FPS = alle 100ms)
        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self.capture_frame)
        
        # Timer für die Ablaufsteuerung
        self.flow_timer = QTimer(self)
        self.flow_timer.timeout.connect(self.tick)
        
    def start(self):
        self.capture_timer.start(100)
        self.flow_timer.start(100)
        self.bg_win.set_status("Aufnahme gestartet (10 FPS)...")

    def capture_frame(self):
        rect = self.bg_win.geometry()
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            filename = self.temp_dir / f"frame_{self.frame_index:05d}.png"
            pixmap.save(str(filename), "PNG")
            self.frame_index += 1

    def tick(self):
        self.elapsed_ms += 100
        
        # --- SEQUENZ STEUERUNG ---
        
        # 1. Hover auf Presence-Bar (T = 0.5s)
        if self.elapsed_ms == 500:
            self.bg_win.set_status("Schritt 1: Hover über Dynamic Island Shimmer-Bar...")
            self.app.window._set_idle_revealed(True)
            self.app.window.is_hovered = True
            
        # 2. Aufnahme Start (T = 1.5s)
        elif self.elapsed_ms == 1500:
            self.bg_win.set_status("Schritt 2: Starte Aufnahme (F8 / Klick)...")
            self.app.pipeline.start_recording()
            
        # 3. Aufnahme-Phase mit Audiopegel und Live-Transkript (T = 1.5s - 5.0s)
        elif 1500 < self.elapsed_ms < 5000:
            rms = random.uniform(0.1, 0.95)
            self.app.signals.audio_level.emit(rms)
            
            if self.elapsed_ms == 2200:
                self.app.signals.partial_ready.emit("Hallo")
            elif self.elapsed_ms == 2800:
                self.app.signals.partial_ready.emit("Hallo, das ist eine")
            elif self.elapsed_ms == 3400:
                self.app.signals.partial_ready.emit("Hallo, das ist eine automatisierte")
            elif self.elapsed_ms == 4000:
                self.app.signals.partial_ready.emit("Hallo, das ist eine automatisierte Demonstration der")
            elif self.elapsed_ms == 4600:
                self.app.signals.partial_ready.emit("Hallo, das ist eine automatisierte Demonstration der neuen Dynamic Island")

        # 4. Aufnahme Stop & Processing (T = 5.0s)
        elif self.elapsed_ms == 5000:
            self.bg_win.set_status("Schritt 3: Beende Aufnahme. Polishing aktiv...")
            self.app.pipeline.stop_recording()

        # 5. Resultat bereit (T = 5.5s)
        elif self.elapsed_ms == 5500:
            self.bg_win.set_status("Schritt 4: Polierter Text fertiggestellt (SUCCESS)...")
            # Resultat emittieren
            self.app.signals.result_ready.emit(
                "Hallo, das ist eine ähm automatisierte Demonstration der neuen Dynamic Island von SurepriseAi, ja.",
                DEMO_TEXTS["casual"]
            )
            
        # 6. Expanded-Modus öffnen (T = 6.5s)
        elif self.elapsed_ms == 6500:
            self.bg_win.set_status("Schritt 5: Öffne Expanded-Widget für Detailansicht...")
            self.app.state_machine.transition_by_name("expanded")
            
        # 7. Klick auf Stil: Business (T = 7.8s)
        elif self.elapsed_ms == 7800:
            self.bg_win.set_status("Schritt 6: Wende Stil 'Business' an...")
            self.app.window.pill.expanded_widget.chips["business"].click()
            
        # 8. Klick auf Stil: Stichpunkte (T = 9.2s)
        elif self.elapsed_ms == 9200:
            self.bg_win.set_status("Schritt 7: Wende Stil 'Stichpunkte' an...")
            self.app.window.pill.expanded_widget.chips["bullet_points"].click()
            
        # 9. Klick auf Stil: Kompakt (T = 10.6s)
        elif self.elapsed_ms == 10600:
            self.bg_win.set_status("Schritt 8: Wende Stil 'Kompakt' an...")
            self.app.window.pill.expanded_widget.chips["concise"].click()

        # 10. Einstellungsmenü öffnen (T = 12.0s)
        elif self.elapsed_ms == 12000:
            self.bg_win.set_status("Schritt 9: Öffne Einstellungs-Panel (Doppelklick)...")
            self.app.window._toggle_settings()

        # 11. Verlauf zeigen (T = 13.2s)
        elif self.elapsed_ms == 13200:
            self.bg_win.set_status("Schritt 10: Zeige Diktat-Verlauf in den Einstellungen...")
            self.app.window._settings_dialog._history_nav_btn.click()

        # 12. URL transkribieren zeigen (T = 14.5s)
        elif self.elapsed_ms == 14500:
            self.bg_win.set_status("Schritt 11: Zeige URL-Audio-Transkription...")
            self.app.window._settings_dialog._url_nav_btn.click()

        # 13. Einstellungen schließen (T = 15.8s)
        elif self.elapsed_ms == 15800:
            self.bg_win.set_status("Schritt 12: Schließe Einstellungen...")
            self.app.window._settings_dialog.close()

        # 14. Expanded-Modus verlassen (T = 16.5s)
        elif self.elapsed_ms == 16500:
            self.bg_win.set_status("Schritt 13: Schließe Dynamic Island...")
            self.app.controller._close_expanded()

        # 15. Beenden & Kompilieren (T = 17.5s)
        elif self.elapsed_ms == 17500:
            self.flow_timer.stop()
            self.capture_timer.stop()
            self.bg_win.set_status("Ablauf beendet. Generiere GIF...")
            self.compile_gif()
            self.cleanup()
            QApplication.quit()

    def compile_gif(self):
        output_file = _ROOT / "screenshots" / "demo.gif"
        self.bg_win.set_status(f"Kompiliere {self.frame_index} Frames zu {output_file}...")
        
        frames = sorted(list(self.temp_dir.glob("frame_*.png")))
        if not frames:
            print("[Demo] Keine Frames zum Kompilieren gefunden!")
            return
            
        from PIL import Image
        images = []
        for path in frames:
            img = Image.open(path)
            # Skalieren auf 900x562
            img_resized = img.resize((900, 562), Image.Resampling.BILINEAR)
            images.append(img_resized)

        if images:
            images[0].save(
                str(output_file),
                save_all=True,
                append_images=images[1:],
                optimize=True,
                duration=100,
                loop=0
            )
            print(f"[Demo] GIF erfolgreich erstellt: {output_file}")
            
    def cleanup(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

# --- BOOTSTRAP ---

def main():
    # Lokale Demo-Konfiguration erzwingen (Zwischenablage/Typing blockieren, Dark Mode erzwingen)
    config.set("enable_presence_bar", True)
    config.set("show_privacy_badge", True)
    config.set("auto_copy_to_clipboard", False)
    config.set("auto_inject_text", False)
    config.set("enable_recording_sounds", False)
    config.set("theme_mode", "dark")
    config.save = lambda: None # Verhindert permanentes Speichern im User-Config.json

    # App-Initialisierung
    app = SurepriseApp()

    # Hintergrund-Fenster instanziieren
    bg_win = DemoBackgroundWindow()
    bg_win.show()

    # Positionierungs-Patches auf das Hintergrund-Fenster anwenden
    
    # 1. DynamicIslandWindow zentrieren
    def patch_island_position(self_win, force=False, *args, **kwargs):
        x = int(bg_win.x() + (bg_win.width() - app.window.width()) / 2.0)
        y = int(bg_win.y() + 60)
        app.window.move(x, y)
    
    import types
    app.window._setup_position = types.MethodType(patch_island_position, app.window)
    patch_island_position(app.window, force=True)

    # 2. ToastNotification zentrieren
    def patch_toast_position(self_toast, *args, **kwargs):
        self_toast.adjustSize()
        x = int(bg_win.x() + (bg_win.width() - self_toast.width()) / 2.0)
        y = int(bg_win.y() + 140)
        self_toast.move(x, y)
        self_toast.show()
        self_toast.raise_()
    
    app.toast._position_and_show = types.MethodType(patch_toast_position, app.toast)

    # 3. SettingsWindow zentrieren
    from src.ui.settings_panel import SettingsWindow
    def patch_settings_center(self_settings, *args, **kwargs):
        x = int(bg_win.x() + (bg_win.width() - self_settings.width()) / 2.0)
        y = int(bg_win.y() + (bg_win.height() - self_settings.height()) / 2.0)
        self_settings.move(x, y)
    SettingsWindow._center_on_screen = patch_settings_center

    # 4. History und Settings Größe einschränken (sollte im BG-Fenster bleiben)
    def patch_show_history(self_settings, *args, **kwargs):
        if not self_settings._content_stack or not self_settings._container:
            return
        if self_settings._history_view is None:
            from src.ui.history_dialog import HistoryDialog
            from PyQt6.QtWidgets import QSizePolicy
            self_settings._history_view = HistoryDialog(self_settings._history_service, self_settings._container, embedded=True)
            self_settings._history_view.setWindowFlags(Qt.WindowType.Widget)
            self_settings._history_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self_settings._history_view.finished.connect(lambda: self_settings.show_settings())
            self_settings._content_stack.addWidget(self_settings._history_view)

        self_settings._history_view.retranslate_ui()
        self_settings._history_view._refresh_list()
        self_settings._content_stack.setCurrentWidget(self_settings._history_view)
        self_settings._set_active_nav("history")
        self_settings.setMinimumSize(900, 650)
        self_settings.resize(900, 650)
        self_settings._center_on_screen()
        self_settings._apply_rounded_mask()
    SettingsWindow.show_history = patch_show_history

    # Start-Event für die Demo vorbereiten
    runner = DemoRunner(bg_win, app)
    
    # Warte bis die Pipeline bereit signalisiert
    def on_app_ready(success):
        if success:
            QTimer.singleShot(1000, runner.start)
        else:
            bg_win.set_status("FEHLER: Pipeline-Mocks fehlgeschlagen.")
            
    app.signals.ready.connect(on_app_ready)

    # App-Initialisierung im Demo-Zustand abschließen
    app.pipeline._initialized = True
    app.signals.ready.emit(True)

    # Event Schleife starten
    sys.exit(app.app.exec())

if __name__ == "__main__":
    main()

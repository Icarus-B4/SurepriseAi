"""
pipeline_worker.py
Hintergrund-Worker für die Transkriptions-Pipeline.
Übernimmt die rechenintensiven Aufgaben der Audio- und Dateitranskription,
um den Haupt-Thread und die Benutzeroberfläche nicht zu blockieren.
"""

import threading
from typing import Callable, Optional
import numpy as np

from src.services.config_service import config
from src.services import dictation_logger as dlog
from src.utils.text_cleaner import bereinige_text


class PipelineWorker:
    """
    Klasse zur Durchführung der eigentlichen Diktatverarbeitung in Threads.
    """

    def __init__(
        self,
        transcriber,
        replacer,
        polisher,
        clipboard,
        on_result: Callable[[str, str], None],
        on_state_change: Callable[[str], None],
        on_error: Callable[[str], None]
    ) -> None:
        self.transcriber = transcriber
        self.replacer = replacer
        self.polisher = polisher
        self.clipboard = clipboard
        
        self.on_result = on_result
        self.on_state_change = on_state_change
        self.on_error = on_error

    def process_audio_async(
        self,
        audio_data: np.ndarray,
        target_hwnd: Optional[int],
        style: Optional[str] = None,
        screen_context: Optional[str] = None,
        live_fallback_text: Optional[str] = None,
    ) -> None:
        """Startet die Verarbeitung von Audiodaten in einem Daemon-Thread."""
        thread = threading.Thread(
            target=self._process_audio,
            args=(audio_data, target_hwnd, style, screen_context, live_fallback_text),
            daemon=True
        )
        thread.start()

    def process_file_async(
        self,
        file_path: str,
        style: Optional[str] = None,
        screen_context: Optional[str] = None,
    ) -> None:
        """Startet die Datei-Transkription in einem Daemon-Thread."""
        thread = threading.Thread(
            target=self._process_file,
            args=(file_path, style, screen_context),
            daemon=True
        )
        thread.start()

    def _process_audio(
        self,
        audio_data: np.ndarray,
        target_hwnd: Optional[int],
        style: Optional[str] = None,
        screen_context: Optional[str] = None,
        live_fallback_text: Optional[str] = None,
    ) -> None:
        """Verarbeitet aufgezeichnete Audiodaten (Transkription, Korrektur, Polishing)."""
        try:
            dlog.write("PipelineWorker: Final-Transkription startet")
            raw_text = self.transcriber.transcribe(audio_data)
            if (not raw_text or not raw_text.strip()) and live_fallback_text:
                dlog.write(f"Final leer – nutze letztes Live-Partial ({len(live_fallback_text)} Zeichen)")
                raw_text = live_fallback_text.strip()
            if not raw_text or not raw_text.strip():
                dlog.end_dictation("FEHLER – keine Sprache erkannt (leerer Rohtext)")
                dlog.write(
                    "HINWEIS: Log-Datei an Support senden: "
                    f"{dlog.desktop_log_path()} oder {dlog.appdata_log_path()}"
                )
                self.on_error("Keine Sprache erkannt. Bitte nochmal versuchen.")
                self.on_state_change("idle")
                return

            # 2. Lokale Auto-Korrektur + Vokabular-Korrekturen
            corrected_text = bereinige_text(raw_text)
            corrected_text = self.replacer.apply(corrected_text)

            # 3. KI-Polishing mit Session- oder Standard-Stil
            active_style = style or config.selected_style
            polished_text = self.polisher.polish(
                corrected_text,
                style=active_style,
                screen_context=screen_context,
            )
            final_text = polished_text or corrected_text

            # 4. Zwischenablage & optionales Einfügen
            if config.auto_copy:
                self.clipboard.copy(final_text)

            if config.get_bool("auto_inject_text", True):
                self.clipboard.inject_text(final_text, delay_ms=150, target_hwnd=target_hwnd)

            dlog.end_dictation(
                f"OK – raw={len(raw_text)} zeichen, final={len(final_text)} zeichen"
            )
            # Expanded-UI wird in AppController._on_pipeline_result geöffnet (Race vermeiden)
            self.on_result(raw_text, final_text)

        except Exception as e:
            dlog.write_exception("PipelineWorker Audio")
            dlog.end_dictation(f"EXCEPTION – {e}")
            print(f"[PipelineWorker] Fehler bei Audio-Verarbeitung: {e}")
            self.on_error(f"Verarbeitungsfehler: {str(e)}")
            self.on_state_change("idle")

    def _process_file(
        self,
        file_path: str,
        style: Optional[str] = None,
        screen_context: Optional[str] = None,
    ) -> None:
        """Transkribiert gezogene Audio- oder Videodateien."""
        try:
            self.on_state_change("processing")
            
            raw_text = self.transcriber.transcribe_file(file_path)
            if not raw_text or not raw_text.strip():
                self.on_error("Audiodatei konnte nicht transkribiert werden oder ist leer.")
                self.on_state_change("idle")
                return

            corrected_text = bereinige_text(raw_text)
            corrected_text = self.replacer.apply(corrected_text)
            active_style = style or config.selected_style
            polished_text = self.polisher.polish(
                corrected_text,
                style=active_style,
                screen_context=screen_context,
            )
            final_text = polished_text or corrected_text

            if config.auto_copy:
                self.clipboard.copy(final_text)

            self.on_result(raw_text, final_text)
            self.on_state_change("expanded")

        except Exception as e:
            print(f"[PipelineWorker] Fehler bei Datei-Verarbeitung: {e}")
            self.on_error(f"Datei-Verarbeitungsfehler: {str(e)}")
            self.on_state_change("idle")

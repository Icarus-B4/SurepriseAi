"""
transcription_service.py
Lokale Spracherkennung via sherpa-onnx (Parakeet TDT) mit faster-whisper Fallback.
Verarbeitung läuft in einem separaten Thread, um die UI nicht zu blockieren.
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional
import numpy as np

from .config_service import config


def _log(msg: str) -> None:
    """Konsolen-Log – darf die Pipeline nie abbrechen (Windows cp1252)."""
    try:
        print(msg)
    except Exception:
        try:
            print(msg.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass


# ── Sherpa-ONNX Import ────────────────────────────────────────────────────────
try:
    import sherpa_onnx
    SHERPA_AVAILABLE = True
except ImportError:
    SHERPA_AVAILABLE = False
    print("[Transcription] sherpa-onnx nicht verfügbar")

# ── faster-whisper Import ─────────────────────────────────────────────────────
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[Transcription] faster-whisper nicht verfügbar")


class TranscriptionService:
    """
    Transkribiert Audio-Daten lokal.
    Primär: sherpa-onnx mit Parakeet TDT 0.6B int8
    Fallback: faster-whisper (tiny)
    """

    def __init__(self) -> None:
        self._parakeet_recognizer: Optional[object] = None
        self._whisper_model: Optional[object] = None
        self._partial_whisper_model: Optional[object] = None
        self._lock = threading.Lock()
        self._initialized = False

        # Callback bei Fertigstellung
        self._on_result: Optional[Callable[[str], None]] = None

    def set_result_callback(self, cb: Callable[[str], None]) -> None:
        self._on_result = cb

    # ── Initialisierung ───────────────────────────────────────────────────────

    def initialize(self) -> bool:
        """
        Lädt das Transkriptionsmodell.
        Wird beim App-Start einmalig aufgerufen.
        """
        engine = config.transcription_engine

        if engine == "parakeet" and SHERPA_AVAILABLE:
            ok = self._init_parakeet()
        elif WHISPER_AVAILABLE:
            ok = self._init_whisper()
        else:
            print("[Transcription] Kein Transkriptions-Engine verfügbar!")
            return False

        if ok:
            self._init_partial_model()
        return ok

    def _init_parakeet(self) -> bool:
        """Initialisiert den Parakeet TDT Recognizer via sherpa-onnx."""
        model_dir = config.parakeet_model_dir

        if not model_dir.exists():
            print(f"[Transcription] Parakeet-Modell nicht gefunden: {model_dir}")
            # Fallback zu Whisper
            return self._init_whisper()

        try:
            encoder = str(model_dir / "encoder.int8.onnx")
            decoder = str(model_dir / "decoder.int8.onnx")
            joiner  = str(model_dir / "joiner.int8.onnx")
            tokens  = str(model_dir / "tokens.txt")

            recognizer_config = sherpa_onnx.OnlineRecognizerConfig(
                feat_config=sherpa_onnx.FeatureExtractorConfig(
                    sampling_rate=16000,
                    feature_dim=80,
                ),
                model_config=sherpa_onnx.OnlineTransducerModelConfig(
                    encoder=encoder,
                    decoder=decoder,
                    joiner=joiner,
                    tokens=tokens,
                    num_threads=4,
                ),
                decoding_method="greedy_search",
                enable_endpoint_detection=True,
                rule1_min_trailing_silence=2.4,
                rule2_min_trailing_silence=1.2,
                rule3_min_utterance_length=20,
            )

            self._parakeet_recognizer = sherpa_onnx.OnlineRecognizer(
                recognizer_config
            )
            self._initialized = True
            print("[Transcription] Parakeet TDT geladen OK")
            return True

        except Exception as e:
            _log(f"[Transcription] Parakeet-Fehler: {e} -> Fallback zu Whisper")
            return self._init_whisper()

    def _init_whisper(self) -> bool:
        """Initialisiert faster-whisper als Fallback."""
        if not WHISPER_AVAILABLE:
            return False

        try:
            model_size = config.get_str("whisper_model_size", "tiny")
            self._whisper_model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
            )
            self._initialized = True
            print(f"[Transcription] Whisper '{model_size}' geladen OK")
            return True
        except Exception as e:
            print(f"[Transcription] Whisper-Fehler: {e}")
            return False

    def _init_partial_model(self) -> None:
        """Lädt ein schnelles Whisper-Modell für Live-Zwischenergebnisse."""
        if not WHISPER_AVAILABLE:
            return

        main_size = config.get_str("whisper_model_size", "tiny")
        if main_size == "tiny" and self._whisper_model is not None:
            self._partial_whisper_model = self._whisper_model
            return

        try:
            self._partial_whisper_model = WhisperModel(
                "tiny",
                device="cpu",
                compute_type="int8",
            )
            print("[Transcription] Whisper 'tiny' für Live-Partials geladen OK")
        except Exception as e:
            print(f"[Transcription] Partial-Modell-Fehler: {e} – nutze Hauptmodell")
            self._partial_whisper_model = self._whisper_model

    # ── Transkription ─────────────────────────────────────────────────────────

    def transcribe_async(self, audio_data: np.ndarray) -> None:
        """Startet die Transkription in einem separaten Thread."""
        thread = threading.Thread(
            target=self._transcribe_worker,
            args=(audio_data,),
            daemon=True,
        )
        thread.start()

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Synchrone Transkription (blockierend). Für Tests geeignet."""
        if not self._initialized:
            if not self.initialize():
                return ""

        with self._lock:
            if self._parakeet_recognizer is not None:
                return self._transcribe_parakeet(audio_data, is_partial=False)
            if self._whisper_model is not None:
                return self._transcribe_whisper(audio_data)
        return ""

    def transcribe_partial(self, audio_data: np.ndarray) -> str:
        """Schnelle Zwischen-Transkription für die Live-Anzeige."""
        if not self._initialized:
            if not self.initialize():
                return ""

        with self._lock:
            if self._partial_whisper_model is not None:
                return self._transcribe_whisper_partial(audio_data)
            if self._parakeet_recognizer is not None:
                return self._transcribe_parakeet(audio_data, is_partial=True)
            if self._whisper_model is not None:
                return self._transcribe_whisper_partial(audio_data)
        return ""

    def _transcribe_worker(self, audio_data: np.ndarray) -> None:
        """Thread-Worker für asynchrone Transkription."""
        result = self.transcribe(audio_data)
        if self._on_result and result:
            self._on_result(result)

    def _transcribe_parakeet(self, audio_data: np.ndarray, is_partial: bool = False) -> str:
        """Transkription mit Parakeet via sherpa-onnx."""
        try:
            stream = self._parakeet_recognizer.create_stream()
            stream.accept_waveform(16000, audio_data)

            if not is_partial:
                # End-of-Stream nur bei finaler Transkription signalisieren
                tail_paddings = np.zeros(int(0.5 * 16000), dtype=np.float32)
                stream.accept_waveform(16000, tail_paddings)
                stream.input_finished()

            while self._parakeet_recognizer.is_ready(stream):
                self._parakeet_recognizer.decode_stream(stream)

            result = self._parakeet_recognizer.get_result(stream)
            text = result.text.strip() if result else ""
        except Exception as e:
            _log(f"[Transcription] Parakeet-Transkriptions-Fehler: {e}")
            return ""

        mode = "Partial" if is_partial else "Final"
        preview = text[:50] + ("..." if len(text) > 50 else "")
        _log(f"[Transcription] Parakeet ({mode}): '{preview}'")
        return text

    def _transcribe_whisper(self, audio_data: np.ndarray) -> str:
        """Transkription mit faster-whisper."""
        try:
            task = "translate" if config.translate_to_english else "transcribe"
            segments, _ = self._whisper_model.transcribe(
                audio_data,
                beam_size=1,
                language=config.transcription_language,
                task=task,
                vad_filter=True,
            )
            text = " ".join(seg.text for seg in segments).strip()
        except Exception as e:
            _log(f"[Transcription] Whisper-Transkriptions-Fehler: {e}")
            return ""

        preview = text[:50] + ("..." if len(text) > 50 else "")
        _log(
            f"[Transcription] Whisper ({config.transcription_language or 'auto'}, {task}): "
            f"'{preview}'"
        )
        return text

    def _transcribe_whisper_partial(self, audio_data: np.ndarray) -> str:
        """Schnelle Live-Transkription ohne VAD und mit minimalem Beam-Search."""
        model = self._partial_whisper_model or self._whisper_model
        if model is None:
            return ""

        try:
            segments, _ = model.transcribe(
                audio_data,
                beam_size=1,
                best_of=1,
                language=config.transcription_language,
                task="transcribe",
                vad_filter=False,
                condition_on_previous_text=False,
            )
            text = " ".join(seg.text for seg in segments).strip()
            return text
        except Exception as e:
            print(f"[Transcription] Whisper-Partial-Fehler: {e}")
            return ""

    def load_audio_file(self, file_path: str) -> Optional[np.ndarray]:
        """Lädt eine Audio- oder Videodatei und konvertiert sie auf 16000 Hz Mono Float32."""
        if WHISPER_AVAILABLE:
            try:
                from faster_whisper.audio import decode_audio
                audio = decode_audio(file_path, sampling_rate=16000)
                return audio
            except Exception as e:
                print(f"[Transcription] Fehler beim Laden via faster-whisper decode_audio: {e}")
        
        try:
            import soundfile as sf
            data, samplerate = sf.read(file_path, dtype='float32')
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            if samplerate != 16000:
                duration = len(data) / samplerate
                new_len = int(duration * 16000)
                data = np.interp(np.linspace(0, len(data), new_len), np.arange(len(data)), data).astype(np.float32)
            return data
        except Exception as e:
            print(f"[Transcription] Fehler beim Laden via soundfile: {e}")
            
        return None

    def transcribe_file(self, file_path: str) -> str:
        """Transkribiert eine Audiodatei von der Festplatte."""
        audio_data = self.load_audio_file(file_path)
        if audio_data is None or len(audio_data) == 0:
            print(f"[Transcription] Audiodatei konnte nicht geladen oder dekodiert werden: {file_path}")
            return ""
        return self.transcribe(audio_data)

    @property
    def is_ready(self) -> bool:
        return self._initialized

"""
test_transcription.py
Prüft, dass Windows-Konsolen-Encoding die Transkription nicht zerstört.
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_whisper_log_does_not_swallow_result() -> None:
    from src.services.transcription_service import TranscriptionService

    svc = TranscriptionService()
    svc._initialized = True
    model = SimpleNamespace()
    fake_segments = [SimpleNamespace(text="Hallo Welt")]
    model.transcribe = lambda *_a, **_k: (fake_segments, {})
    svc._whisper_model = model

    audio = np.zeros(16000, dtype=np.float32)
    text = svc._transcribe_whisper(audio)
    assert text == "Hallo Welt", f"Erwartet 'Hallo Welt', bekam {text!r}"

    with patch("builtins.print", side_effect=UnicodeEncodeError("charmap", "x", 0, 1, "x")):
        text2 = svc._transcribe_whisper(audio)
    assert text2 == "Hallo Welt", f"Log-Fehler darf Ergebnis nicht loeschen: {text2!r}"


def main() -> None:
    test_whisper_log_does_not_swallow_result()
    print("Transcription test OK")


if __name__ == "__main__":
    main()

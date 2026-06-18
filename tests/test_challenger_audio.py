# -*- coding: utf-8 -*-
"""
test_challenger_audio.py
Tier-5 Adversarial-Tests für Audio-Steuerung (R2).
"""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.services.audio_service import AudioService
from src.services.audio_devices import get_next_input_device
from src.services.config_service import config


def test_mute_zeroes_recorded_frames():
    """Stummschaltung muss Audiodaten im Callback mit Nullen überschreiben."""
    audio = AudioService()
    audio.set_mute(True)
    audio._recording = True
    chunk = np.ones((64, 1), dtype=np.float32) * 0.8
    audio._audio_callback(chunk, 64, None, None)
    stored = audio._chunks[-1]
    assert float(np.max(np.abs(stored))) == 0.0


def test_toggle_mute_returns_state():
    audio = AudioService()
    assert audio.is_muted is False
    assert audio.toggle_mute() is True
    assert audio.is_muted is True
    assert audio.toggle_mute() is False


def test_set_rms_level_callback_on_muted_audio():
    """Level-Queue enthält bei Mute Null-Pegel."""
    audio = AudioService()
    audio.set_mute(True)
    audio._recording = True
    chunk = np.ones((64, 1), dtype=np.float32) * 0.5
    audio._audio_callback(chunk, 64, None, None)
    assert audio.drain_levels() == 0.0


def test_resample_audio_downsamples_to_16k():
    from src.services.audio_devices import resample_audio, SAMPLE_RATE

    src = np.ones(48000, dtype=np.float32)
    out = resample_audio(src, 48000, SAMPLE_RATE)
    assert out.shape[0] == SAMPLE_RATE


def test_device_cycle_updates_config(monkeypatch):
    """Zyklischer Gerätewechsel aktualisiert recording_device."""
    monkeypatch.setattr(
        "src.services.audio_devices.list_input_devices",
        lambda: [{"id": 0, "name": "Mic-A", "channels": 1}],
    )
    config.set("recording_device", "default")
    nxt = get_next_input_device()
    assert nxt in ("Mic-A", "default")
    assert config.get_str("recording_device") == nxt


def test_device_cycle_empty_list_returns_default(monkeypatch):
    monkeypatch.setattr(
        "src.services.audio_devices.list_input_devices", lambda: []
    )
    assert get_next_input_device() == "default"


def test_supported_rates_prefers_16k_when_available(monkeypatch):
    from src.services import audio_devices as ad

    monkeypatch.setattr(ad, "SOUNDDEVICE_AVAILABLE", True)
    monkeypatch.setattr(
        ad.sd,
        "query_devices",
        lambda _dev, _kind: {"default_samplerate": 48000.0},
    )
    def check(**kwargs):
        if kwargs.get("samplerate") != 16000:
            raise Exception("bad rate")

    monkeypatch.setattr(ad.sd, "check_input_settings", check)
    assert ad.supported_input_sample_rates(1) == [16000]


def test_supported_rates_falls_back_to_device_default(monkeypatch):
    from src.services import audio_devices as ad

    monkeypatch.setattr(ad, "SOUNDDEVICE_AVAILABLE", True)
    monkeypatch.setattr(
        ad.sd,
        "query_devices",
        lambda _dev, _kind: {"default_samplerate": 48000.0},
    )

    def check(**kwargs):
        if kwargs.get("samplerate") == 48000:
            return None
        raise Exception("bad rate")

    monkeypatch.setattr(ad.sd, "check_input_settings", check)
    assert ad.supported_input_sample_rates(1) == [48000]


def test_invalid_device_fallback_opens_default(monkeypatch):
    """Ungültiges Gerät fällt auf default zurück."""
    audio = AudioService()
    calls: list = []

    def fake_open(device_id):
        calls.append(device_id)
        return device_id in (None, "default")

    audio._open_stream = fake_open  # type: ignore[method-assign]
    ok = audio.start_recording("Ungueltiges_Geraet")
    assert ok is True
    assert calls[0] == "Ungueltiges_Geraet"
    assert calls[-1] is None

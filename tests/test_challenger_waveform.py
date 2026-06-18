# -*- coding: utf-8 -*-
"""
test_challenger_waveform.py
Tier-5 Adversarial-Tests für Siri-HSL-Wellenform (R3).
"""

import os
import sys

import pytest
from PyQt6.QtWidgets import QApplication

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ui.waveform_widget import WaveformWidget, FRAME_MS, IDLE_AMPLITUDE, NUM_WAVES


@pytest.fixture(scope="module")
def q_app():
    app = QApplication.instance() or QApplication(sys.argv)
    return app


def test_waveform_timer_60fps(q_app):
    wf = WaveformWidget()
    assert wf._timer.interval() == FRAME_MS
    assert FRAME_MS == 16


def test_set_rms_clamps_extreme_values(q_app):
    wf = WaveformWidget()
    wf.set_rms(-5.0)
    assert wf._target_rms == 0.0
    wf.set_rms(99.0)
    assert wf._target_rms == 1.0


def test_set_rms_increases_amplitude(q_app):
    wf = WaveformWidget()
    wf.set_rms(0.0)
    low = list(wf._target_amplitudes)
    wf.set_rms(0.9)
    high = list(wf._target_amplitudes)
    assert max(high) > max(low)


def test_reset_waveform_returns_to_idle(q_app):
    wf = WaveformWidget()
    wf.set_rms(0.8)
    wf.reset_waveform()
    assert wf._target_rms == 0.0
    assert all(a == IDLE_AMPLITUDE for a in wf._target_amplitudes)


def test_animate_does_not_crash_on_zero_rms(q_app):
    wf = WaveformWidget()
    wf.set_rms(0.0)
    for _ in range(30):
        wf._animate()
    assert wf._rms >= 0.0


def test_wave_colors_configured(q_app):
    from src.ui.waveform_widget import WAVE_COLORS
    assert len(WAVE_COLORS) == NUM_WAVES

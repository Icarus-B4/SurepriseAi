# -*- coding: utf-8 -*-
"""
test_challenger_rewrite.py
Tier-5 Adversarial-Tests für SelectedText-Umschrift (R4).
"""

import os
import sys
import time
from unittest.mock import MagicMock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.services.config_service import config
from src.services.selected_text_rewrite import SelectedTextRewriteService


@pytest.fixture
def rewrite_svc():
    states: list[str] = []
    errors: list[str] = []
    clip = MagicMock()
    clip.read_clipboard.return_value = "Rohtext zum Polieren."
    clip.capture_selection.return_value = None
    clip.inject_text.return_value = True
    polish = MagicMock()
    polish.polish_instant.return_value = "Polierter Text."
    polish._call_ollama.return_value = None
    polish.ollama_available = False
    svc = SelectedTextRewriteService(
        clip, polish, states.append, errors.append, lambda: None
    )
    return svc, states, errors, clip, polish


def test_rewrite_happy_path(rewrite_svc):
    svc, states, errors, clip, _ = rewrite_svc
    config.set("enable_selected_text_context", True)
    config.set("ollama_polishing", False)
    svc.capture_and_rewrite()
    time.sleep(0.5)
    assert "processing" in states
    assert "success" in states
    clip.inject_text.assert_called_once()
    assert not errors


def test_rewrite_empty_clipboard_aborts_to_idle(rewrite_svc):
    svc, states, _, clip, _ = rewrite_svc
    clip.read_clipboard.return_value = ""
    svc.capture_and_rewrite()
    time.sleep(0.4)
    assert "processing" in states
    assert "idle" in states


def test_rewrite_ollama_invalid_url_errors(rewrite_svc):
    svc, states, errors, clip, polish = rewrite_svc
    clip.read_clipboard.return_value = "Text"
    config.set("ollama_polishing", True)
    config.set("ollama_url", "http://invalid-url-12345.local")
    polish._call_ollama.return_value = None
    polish.ollama_available = False
    svc.capture_and_rewrite()
    time.sleep(0.5)
    assert "error" in states
    assert errors


def test_rewrite_busy_guard(rewrite_svc):
    svc, _, _, _, _ = rewrite_svc
    svc._busy = True
    svc.capture_and_rewrite()
    time.sleep(0.2)
    assert svc._busy is True

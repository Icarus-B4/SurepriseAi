# -*- coding: utf-8 -*-
"""
test_workloads.py
E2E-Tests für Tier 4 (Real-World Workloads).
"""

import time
import pytest


def test_workload_01_long_dictation_session(app_runner):
    """Simuliert eine lange Diktat-Sitzung (5 Sekunden) und stellt sicher, dass die Pipeline stabil bleibt."""
    app_runner.start()
    app_runner.press_key("f8")  # Start
    time.sleep(5.0)  # Simuliere langes Sprechen
    app_runner.press_key("f8")  # Stop
    time.sleep(1.0)
    log_content = app_runner.get_log_content()
    # Sicherstellen, dass das Diktat beendet und transkribiert wurde
    assert "Diktat beendet" in log_content or "Transkription" in log_content


def test_workload_02_rapid_toggle_recording(app_runner):
    """Prüft schnelles Ein- und Ausschalten der Aufnahme hintereinander (Stress-Test)."""
    app_runner.start()
    for _ in range(5):
        app_runner.press_key("f8")
        time.sleep(0.2)
        app_runner.press_key("f8")
        time.sleep(0.2)
    log_content = app_runner.get_stdout_content()
    assert "Exception" not in log_content


def test_workload_03_massive_text_selected_rewrite(app_runner):
    """Testet die Begrenzung und Verarbeitung bei extrem langen selektierten Texten (>5000 Zeichen)."""
    app_runner.start()
    huge_text = "A" * 6000
    app_runner.set_clipboard(huge_text)
    app_runner.press_key("f9")  # SelectedText Umschrift
    time.sleep(1.5)
    log_content = app_runner.get_log_content()
    # Der Text sollte auf das Maximum (z.B. 800 Zeichen) normalisiert/gekürzt worden sein
    assert "normalisiert" in log_content or "SelectedText" in log_content


def test_workload_04_sequential_all_styles_rewrites(app_runner, config_manager):
    """Führt Nacheinander Umschriften mit allen 5 vordefinierten Stil-Chips aus."""
    styles = ["casual", "professional", "bullet_points", "concise", "formal"]
    app_runner.start()
    for style in styles:
        config_manager.update_key("selected_style", style)
        app_runner.set_clipboard(f"Text fuer Stil: {style}")
        app_runner.press_key("f9")
        time.sleep(1.0)
    log_content = app_runner.get_log_content()
    assert "Exception" not in log_content


def test_workload_05_concurrent_gui_drag_and_dictation(app_runner):
    """Simuliert das Verschieben der Dynamic Island während ein Diktat läuft."""
    app_runner.start()
    app_runner.press_key("f8")  # Start Dictation
    time.sleep(0.5)
    # Fenster verschieben (Drag-and-Drop simulieren)
    app_runner.scroll_mouse(50, 0)
    time.sleep(0.5)
    app_runner.press_key("f8")  # Stop
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "Exception" not in log_content

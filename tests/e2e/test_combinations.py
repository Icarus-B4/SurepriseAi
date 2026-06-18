# -*- coding: utf-8 -*-
"""
test_combinations.py
E2E-Tests für Tier 3 (Cross-Feature Kombinationen).
"""

import time
import pytest


def test_comb_01_rec_start_mute_active(app_runner):
    """Kombiniert Stummschaltung und Aufnahme: Prüft, ob Aufnahme bei aktivem Mute lautlos bleibt."""
    app_runner.start()
    app_runner.press_key("m")  # Mute an
    app_runner.press_key("f8")  # Start Recording
    time.sleep(1.0)
    app_runner.press_key("f8")  # Stop
    time.sleep(1.0)
    log_content = app_runner.get_log_content()
    # Das Signal muss als extrem leise oder lautlos erkannt werden
    assert "rms=0.00000" in log_content or "sehr leises Signal" in log_content


def test_comb_02_theme_switch_during_recording(app_runner, config_manager):
    """Prüft Theme-Wechsel während einer laufenden Aufnahme, um Abstürze zu verhindern."""
    app_runner.start()
    app_runner.press_key("f8")
    time.sleep(0.5)
    # Wechselt das Theme während der Aufnahme
    config_manager.update_key("theme_mode", "light")
    time.sleep(0.5)
    app_runner.press_key("f8")
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "Exception" not in log_content


def test_comb_03_scroll_to_basics_during_recording(app_runner):
    """Überprüft, ob Scrollen (für Basics) während der Aufnahme ignoriert wird."""
    app_runner.start()
    app_runner.press_key("f8")  # Aufnahme
    time.sleep(0.5)
    app_runner.scroll_mouse(0, 10)  # Versuch Basics zu öffnen
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    # Der Zustand RECORDING darf sich durch Scrollen nicht ändern
    assert "[State] RECORDING → BASICS" not in log_content


def test_comb_04_selected_text_rewrite_and_immediate_dictation(app_runner):
    """Führt eine Text-Umschrift aus und startet sofort danach ein normales Diktat."""
    app_runner.start()
    app_runner.set_clipboard("Testtext")
    app_runner.press_key("f9")  # Umschrift
    time.sleep(1.0)
    app_runner.press_key("f8")  # Sofort Diktat
    time.sleep(0.5)
    app_runner.press_key("f8")
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "Exception" not in log_content


def test_comb_05_cyclic_device_switch_during_dictation(app_runner):
    """Prüft, ob ein Gerätewechsel während eines Diktats ignoriert wird, um Datenverlust zu vermeiden."""
    app_runner.start()
    app_runner.press_key("f8")
    time.sleep(0.5)
    app_runner.press_key("d")  # Gerätewechsel-Tastendruck
    time.sleep(0.5)
    app_runner.press_key("f8")
    time.sleep(0.5)
    log_content = app_runner.get_log_content()
    # Der Gerätewechsel darf während der Aufnahme nicht ausgeführt werden
    assert "Wechsel waehrend der Aufnahme ignoriert" in log_content

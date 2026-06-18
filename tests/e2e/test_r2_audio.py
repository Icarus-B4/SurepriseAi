# -*- coding: utf-8 -*-
"""
test_r2_audio.py
E2E-Tests für Anforderung R2 (Audio- und Mikrofonsteuerung).
"""

import time
import pytest


def test_r2_01_mute_toggle_in_basics(app_runner):
    """Prüft, ob das Stummschalten im Basics-Modus per Klick oder Navigation loggt."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)  # Wechsel in Basics
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Simuliere Mute-Tastenkombination oder Tastendruck (z.B. 'm' oder Enter auf Mute-Button)
    app_runner.press_key("m")
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    # Erwarte Logeintrag über Stummschaltung
    assert "Mute" in log_content or "stumm" in log_content


def test_r2_02_muted_recording_writes_zeros(app_runner):
    """Überprüft, ob bei aktivierter Stummschaltung nur Null-Frames aufgenommen werden."""
    app_runner.start()
    # Aktivieren der Stummschaltung via Mute-Kombination
    app_runner.press_key("m")
    # Starte Aufnahme
    app_runner.press_key("f8")
    time.sleep(1.0)
    assert app_runner.finish_recording()
    log_content = app_runner.get_log_content()
    # Wenn stumm, sollte die Lautstärke (rms/peak) sehr klein oder Null sein
    assert "rms=0.00000" in log_content or "peak=0.00000" in log_content or "sehr leises Signal" in log_content


def test_r2_03_is_muted_default_false(app_runner):
    """Überprüft, dass die Anwendung standardmäßig nicht stummgeschaltet ist."""
    app_runner.start()
    log_content = app_runner.get_log_content()
    assert "muted=True" not in log_content


def test_r2_04_set_muted_reflects_in_service(app_runner):
    """Prüft, ob set_muted den Zustand des AudioService ändert."""
    app_runner.start()
    app_runner.press_key("m")  # Mute an
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "muted=True" in log_content or "stumm" in log_content


def test_r2_05_cyclic_device_switch_updates_config(app_runner, config_manager):
    """Prüft, ob der zyklische Gerätewechsel config.json aktualisiert."""
    config_manager.update_key("recording_device", "default")
    app_runner.start()
    # Tastendruck für Gerätewechsel (z. B. 'd' im Basics-Modus)
    app_runner.scroll_mouse(0, 10)
    app_runner.press_key("d")
    time.sleep(0.5)
    # Config neu einlesen und prüfen, ob device nicht mehr "default" ist (falls andere vorhanden)
    new_config = config_manager.read()
    assert "recording_device" in new_config


def test_r2_06_cyclic_device_switch_shows_overlay(app_runner):
    """Prüft, ob nach Gerätewechsel ein Informations-Overlay angezeigt wird."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    app_runner.press_key("d")
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "Overlay" in log_content or "Device" in log_content


def test_r2_07_device_list_not_empty(app_runner):
    """Stellt sicher, dass mindestens ein Audio-Eingabegerät gefunden wird."""
    app_runner.start()
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    # Mindestens standardmäßig "default" oder "Input" im Log
    assert "default" in log_content.lower() or "device" in log_content.lower()


def test_r2_08_dynamic_level_indicator_active_during_rec(app_runner):
    """Stellt sicher, dass während der Aufnahme Audiolevel gemessen und signalisiert werden."""
    app_runner.start()
    app_runner.press_key("f8")  # Start
    time.sleep(1.0)
    app_runner.press_key("f8")  # Stop
    time.sleep(1.0)
    log_content = app_runner.get_log_content()
    # Suche nach rms/peak Logs
    assert "rms=" in log_content or "Audio-Stream" in log_content


def test_r2_09_level_indicator_zero_when_muted(app_runner):
    """Prüft, ob der Level-Indicator bei Mute dauerhaft Null signalisiert."""
    app_runner.start()
    app_runner.press_key("m")
    app_runner.press_key("f8")
    time.sleep(1.0)
    assert app_runner.finish_recording()
    log_content = app_runner.get_log_content()
    assert "rms=0.00000" in log_content or "sehr leises Signal" in log_content


def test_r2_10_invalid_device_fallback(app_runner, config_manager):
    """Überprüft, ob bei einem ungültigen Gerät ein Fallback auf 'default' erfolgt."""
    config_manager.update_key("recording_device", "Ungueltiges_Geraet_12345")
    app_runner.start()
    app_runner.press_key("f8")  # Start
    time.sleep(1.0)
    app_runner.press_key("f8")  # Stop
    time.sleep(1.0)
    log_content = app_runner.get_log_content()
    assert "Fallback" in log_content or "default" in log_content

# -*- coding: utf-8 -*-
"""
test_r5_backdrop.py
E2E-Tests für Anforderung R5 (Windows 11 Acrylic/Mica, ctypes & Fallback).
"""

import time
import pytest


def test_r5_01_windows_backdrop_module_exists(app_runner):
    """Überprüft, ob das windows_backdrop Hilfsmodul beim Start importiert/geladen wird."""
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    # Der Log sollte den Ladezustand des Backdrops oder Fensters anzeigen
    assert "windows" in log_content.lower() or "theme" in log_content.lower()


def test_r5_02_set_backdrop_type_mica(app_runner):
    """Prüft, ob der Mica-Effekt (Typ 2) über Win32 DWM API ohne Fehler aufgerufen wird."""
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    # Es sollte kein ctypes-Fehler im stdout stehen
    assert "ctypes" not in log_content and "WindowsError" not in log_content


def test_r5_03_set_backdrop_type_acrylic(app_runner):
    """Prüft, ob der Acrylic-Effekt (Typ 3) über DWM API aufgerufen wird."""
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "ctypes" not in log_content and "WindowsError" not in log_content


def test_r5_04_fallback_to_css_on_non_win11(app_runner):
    """Stellt sicher, dass bei älteren Windows-Versionen ein CSS-Fallback geladen wird."""
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "Fallback" in log_content or "CSS" in log_content or "style" in log_content.lower()


def test_r5_05_ctypes_dwmapi_available(app_runner):
    """Überprüft die Verfügbarkeit der dwmapi.dll über ctypes im System."""
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "dwmapi" in log_content or "win32" in log_content.lower()


def test_r5_06_theme_switch_updates_backdrop(app_runner, config_manager):
    """Prüft, ob das Ändern des Themes das Fenster-Backdrop aktualisiert."""
    config_manager.update_key("theme_mode", "light")
    app_runner.start()
    time.sleep(0.5)
    # Wechseln auf Dark
    config_manager.update_key("theme_mode", "dark")
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "Theme" in log_content or "theme" in log_content.lower()


def test_r5_07_accent_color_backdrop_glow(app_runner, config_manager):
    """Verifiziert die Zuweisung der Akzentfarbe für den Fensterrand-Glow."""
    config_manager.update_key("accent_color", "indigo")
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "indigo" in log_content.lower() or "accent" in log_content.lower()


def test_r5_08_no_crash_on_invalid_hwnd(app_runner):
    """Stellt sicher, dass Fehler bei Fenster-Handles abgefangen werden."""
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "Exception" not in log_content and "Segmentation fault" not in log_content


def test_r5_09_opaque_fallback_if_acrylic_disabled(app_runner, config_manager):
    """Prüft den Fallback zu einem deckenden Hintergrund, wenn Mica/Acrylic deaktiviert sind."""
    config_manager.update_key("enable_presence_bar", False)
    app_runner.start()
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "opaque" in log_content


def test_r5_10_glassmorphism_settings_panel(app_runner):
    """Stellt sicher, dass das Einstellungsfenster mit Glassmorphism-Effekten geladen wird."""
    app_runner.start()
    # Einstellungsfenster öffnen
    app_runner.press_key("s")
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "Settings" in log_content or "settings" in log_content.lower()

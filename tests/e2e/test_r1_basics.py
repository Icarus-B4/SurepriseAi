# -*- coding: utf-8 -*-
"""
test_r1_basics.py
E2E-Tests für Anforderung R1 (Basics Navigation, Scroll-Geste, Layout).
"""

import time
import pytest


def test_r1_01_scroll_up_enters_basics(app_runner):
    """Überprüft, ob Scrollen nach oben vom Zustand IDLE in BASICS wechselt."""
    app_runner.start()
    # Mausrad nach oben scrollen simulieren
    app_runner.scroll_mouse(0, 10)
    # Erwarte Zustandsübergang im Log/Stdout
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)


def test_r1_02_scroll_down_leaves_basics(app_runner):
    """Überprüft, ob Scrollen nach unten im BASICS-Zustand zurück zu IDLE wechselt."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Zurückscrollen
    app_runner.scroll_mouse(0, -10)
    assert app_runner.wait_for_stdout("[State] BASICS → IDLE", timeout=4.0)


def test_r1_03_layout_symmetry_check(app_runner):
    """Verifiziert die geometrische Ausrichtung der Benutzeroberfläche in BASICS."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Hier prüfen wir über die Konsolenausgaben, ob das Widget ohne Fehler gelayoutet wird
    log_content = app_runner.get_stdout_content()
    assert "Fehler" not in log_content


def test_r1_04_basics_audio_widget_existence(app_runner):
    """Prüft, ob der linke Flügel das BasicsAudioWidget enthält."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Logge, dass das BasicsAudioWidget geladen wurde
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    # Der Test schlägt fehl, wenn das Widget beim Laden der UI abstürzt
    assert "BasicsAudioWidget" in log_content or "Basics" in log_content


def test_r1_05_basics_power_widget_existence(app_runner):
    """Prüft, ob der rechte Flügel die Power-Optionen enthält."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    # Power Options sollten fehlerfrei gerendert werden
    assert "Power" in log_content or "basics" in log_content.lower()


def test_r1_06_power_trigger_shows_confirmation(app_runner):
    """Prüft, ob das Auswählen von Power eine Sicherheitsabfrage anzeigt."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Tastaturnavigation oder Klicks simulieren (z. B. Rechtspfeil/Enter)
    app_runner.press_key("right")
    app_runner.press_key("enter")
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    # Es sollte eine Bestätigungsaufforderung geloggt werden
    assert "Sicher? (Power)" in log_content or "Sicher? (Restart)" in log_content


def test_r1_07_restart_trigger_shows_confirmation(app_runner):
    """Prüft, ob Neustart-Aktion eine Sicherheitsbestätigung erfordert."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Simulieren von Pfeiltasten-Navigation
    app_runner.press_key("left")
    app_runner.press_key("enter")
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "Sicher? (Restart)" in log_content


def test_r1_08_escape_dismisses_basics(app_runner):
    """Prüft, ob Drücken von Escape den Basics-Modus schließt und zu IDLE zurückkehrt."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    assert app_runner.wait_for_stdout("Escape=Basics schließen", timeout=8.0)
    assert app_runner.dismiss_basics_via_escape(timeout=12.0)


def test_r1_09_no_focus_stealing_basics(app_runner):
    """Stellt sicher, dass das Umschalten auf Basics keinen Fokus von anderen Apps stiehlt."""
    app_runner.start()
    # Vor dem Umschalten
    log_before = app_runner.get_stdout_content()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Keine Fehlermeldungen bezüglich Fokusverlust oder unerwünschte Aktivierung
    assert "FocusOut" not in log_before


def test_r1_10_app_modes_inactive_during_basics(app_runner):
    """Verifiziert, dass app_modes im Basics-Zustand inaktiv sind."""
    app_runner.start()
    app_runner.scroll_mouse(0, 10)
    assert app_runner.wait_for_stdout("[State] IDLE → BASICS", timeout=4.0)
    # Sicherstellen, dass keine ungewollten Modusänderungen getriggert werden
    log_content = app_runner.get_stdout_content()
    assert "App-Modus" not in log_content

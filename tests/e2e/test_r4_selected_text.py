# -*- coding: utf-8 -*-
"""
test_r4_selected_text.py
E2E-Tests für Anforderung R4 (SelectedText Umschrift und In-place Polishing).
"""

import time
import pytest


def test_r4_01_selected_text_trigger_enters_processing(app_runner):
    """Prüft, ob das Auslösen der SelectedText-Umschrift die App in den PROCESSING-Zustand versetzt."""
    app_runner.start()
    # Simuliere Umschrift-Hotkey (z. B. F9 oder Klick in UI)
    app_runner.press_key("f9")
    time.sleep(0.5)
    log_content = app_runner.get_stdout_content()
    assert "[State] IDLE → PROCESSING" in log_content or "processing" in log_content.lower()


def test_r4_02_clipboard_captured_with_ctrl_c(app_runner):
    """Überprüft, ob beim Trigger ein Ctrl+C-Event gesendet wird, um den markierten Text zu erfassen."""
    app_runner.start()
    app_runner.set_clipboard("Originaler Text in Ablage")
    # Markierten Text simulieren
    app_runner.press_key("f9")
    assert app_runner.wait_for_rewrite_done()
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    # Erwarte Log über Erfassung
    assert "Ctrl+C" in log_content or "Erfassung" in log_content


def test_r4_03_processing_shows_rewriting_label(app_runner):
    """Prüft, ob während der Bearbeitung 'Umschreiben...' auf der Island angezeigt wird."""
    app_runner.start()
    app_runner.press_key("f9")
    time.sleep(0.5)
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "Umschreiben" in log_content or "processing" in log_content.lower()


def test_r4_04_async_polishing_executed(app_runner):
    """Stellt sicher, dass das Polishing asynchron über den PolishingService läuft."""
    app_runner.start()
    app_runner.set_clipboard("Ein kurzer Testtext zum Umschreiben.")
    app_runner.press_key("f9")
    assert app_runner.wait_for_rewrite_done()
    log_content = app_runner.get_log_content()
    assert "Polishing" in log_content or "polisher" in log_content.lower()


def test_r4_05_result_injected_via_ctrl_v(app_runner):
    """Überprüft, ob das Endergebnis via Ctrl+V in die Ziel-App eingefügt wird."""
    app_runner.start()
    app_runner.set_clipboard("Ein kurzer Testtext zum Umschreiben.")
    app_runner.press_key("f9")
    assert app_runner.wait_for_rewrite_done()
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "Ctrl+V" in log_content or "Inject" in log_content


def test_r4_06_state_transitions_to_success(app_runner):
    """Prüft, ob nach erfolgreichem Auto-Inject der Zustand SUCCESS geloggt wird."""
    app_runner.start()
    app_runner.set_clipboard("Ein kurzer Testtext zum Umschreiben.")
    app_runner.press_key("f9")
    assert app_runner.wait_for_rewrite_done()
    log_content = app_runner.get_stdout_content()
    assert "SUCCESS" in log_content


def test_r4_07_clipboard_restored(app_runner):
    """Verifiziert, dass der ursprüngliche Inhalt der Zwischenablage nach der Umschrift wiederhergestellt wird."""
    app_runner.start()
    original_text = "Backup-Zwischenablage-Inhalt"
    app_runner.set_clipboard(original_text)
    app_runner.press_key("f9")
    time.sleep(1.5)
    # Clipboard sollte nach Abschluss wieder original sein
    current_clip = app_runner.get_clipboard()
    assert current_clip == original_text or "restore" in app_runner.get_log_content().lower()


def test_r4_08_empty_selection_aborts_gracefully(app_runner):
    """Stellt sicher, dass eine leere Textselektion die Umschrift sauber abbricht und zu IDLE zurückkehrt."""
    app_runner.start()
    # Leere Zwischenablage / keine Selektion simulieren
    app_runner.set_clipboard("")
    app_runner.press_key("f9")
    time.sleep(0.8)
    log_content = app_runner.get_stdout_content()
    # Zurück zu IDLE
    assert "[State] PROCESSING → IDLE" in log_content


def test_r4_09_polishing_failure_shows_error(app_runner, config_manager):
    """Prüft, ob ein Fehler im Polishing-Service (z.B. Ollama offline) in den Zustand ERROR wechselt."""
    # Ollama deaktivieren, um Offline-Fallback-Fehler oder ähnliches zu erzwingen
    config_manager.update_key("ollama_polishing", True)
    config_manager.update_key("ollama_url", "http://invalid-url-12345.local")
    app_runner.start()
    app_runner.set_clipboard("Text für Ollama-Fehlertest.")
    app_runner.press_key("f9")
    assert app_runner.wait_for_rewrite_done()
    log_content = app_runner.get_stdout_content()
    assert "ERROR" in log_content or "error" in log_content.lower()


def test_r4_10_hotkey_bound_to_rewrite(app_runner, config_manager):
    """Überprüft, ob das System den konfigurierten Hotkey korrekt für die Umschrift registriert."""
    config_manager.update_key("enable_selected_text_context", True)
    app_runner.start()
    log_content = app_runner.get_log_content() + app_runner.get_stdout_content()
    assert "SelectedText" in log_content or "hotkey" in log_content.lower()

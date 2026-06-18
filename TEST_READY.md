# SurepriseAi – TEST_READY.md

Diese Datei dokumentiert die E2E-Testabdeckung für SurepriseAi. Die Testsuite wurde vollständig unter `tests/e2e/` implementiert und ist bereit für die Ausführung gegen die Anwendung.

## Testabdeckung Zusammenfassung

| Feature / Bereich | Anzahl Testfälle | Tier-Klassifizierung | Status |
|---|---|---|---|
| Basics Mausrad & Layout (R1) | 10 | Tier 1 & Tier 2 | READY |
| Audio & Mic Steuerungen (R2) | 10 | Tier 1 & Tier 2 | READY |
| Siri HSL Waveform (R3) | 10 | Tier 1 & Tier 2 | READY |
| SelectedText Umschrift (R4) | 10 | Tier 1 & Tier 2 | READY |
| Windows 11 Acrylic/Mica (R5) | 10 | Tier 1 & Tier 2 | READY |
| Cross-Feature Kombinationen | 5 | Tier 3 | READY |
| Real-World Workloads | 5 | Tier 4 | READY |
| Adversarial Hardening (R2–R5) | 20 | Tier 5 | READY |
| **Gesamt E2E** | **60** | Tier 1–4 | **60/60 PASS** |
| **Gesamt inkl. Tier 5** | **80** | - | **READY** |

## Tier-5 Challenger-Tests (in-process)

White-Box-Grenzfalltests unter `tests/` (kein Subprozess, schnell):

| Datei | Bereich | Tests |
|---|---|---|
| `tests/test_challenger_m2.py` | R1 Mausrad & Power | 7 |
| `tests/test_challenger_audio.py` | R2 Mute/Device | 6 |
| `tests/test_challenger_waveform.py` | R3 HSL-Waveform | 6 |
| `tests/test_challenger_rewrite.py` | R4 SelectedText | 4 |
| `tests/test_challenger_backdrop.py` | R5 Win32 Backdrop | 4 |

```powershell
.\venv\Scripts\pytest tests/test_challenger_*.py -q
```

## Test-Dateien

Die E2E-Testsuite befindet sich im Verzeichnis `tests/e2e/` und besteht aus folgenden Dateien:

1. `tests/e2e/conftest.py`: Fixtures zum Sichern/Wiederherstellen von `config.json`, Hilfsklasse `AppRunner` zum Starten/Stoppen der App als Subprozess, Steuern von Maus/Tastatur via pynput, Verwalten der Zwischenablage via pyperclip und Auslesen des Logs.
2. `tests/e2e/test_r1_basics.py`: 10 Tests für R1 (Scroll-Geste, Layout-Symmetrie, Escape, Fokus, etc.).
3. `tests/e2e/test_r2_audio.py`: 10 Tests für R2 (Mute-Logik, zyklischer Device-Wechsel, dynamic Level-Indikator).
4. `tests/e2e/test_r3_waveform.py`: 10 Tests für R3 (Waveform-Anzeige, 60 FPS, RMS-Amplitude, HSL-Gradients).
5. `tests/e2e/test_r4_selected_text.py`: 10 Tests für R4 (Erfassung via Ctrl+C, PROCESSING-Status, Polieren, Auto-Inject via Ctrl+V, SUCCESS-Status).
6. `tests/e2e/test_r5_backdrop.py`: 10 Tests für R5 (ctypes Aufrufe für Mica/Acrylic, Fallback auf CSS).
7. `tests/e2e/test_combinations.py`: 5 Tests für Tier 3 (Cross-Feature Kombinationen).
8. `tests/e2e/test_workloads.py`: 5 Tests für Tier 4 (Real-World Workloads).

## Ausführung der Tests

Die Tests können über den Python-Interpreter der virtuellen Umgebung ausgeführt werden:

```powershell
.\venv\Scripts\pytest tests/e2e/
```

*Hinweis:* E2E-Läufe dauern wegen Whisper-Modell-Load mehrere Minuten. Einzeltests isoliert ausführen. Nach jedem Test wartet die Fixture 2s, damit der pynput-Global-Hook unter Windows freigegeben wird. Bei hängenden `run.py`-Prozessen vor dem Lauf: `taskkill /F /IM python.exe`.

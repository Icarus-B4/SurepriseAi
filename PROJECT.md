# Project: SurepriseAi Modernisierung & Erweiterung

## Architecture
SurepriseAi ist eine Windows-Desktop-Anwendung (PyQt6) für intelligentes Voice-Dictation und Text-Polishing mit einer Dynamic-Island-Benutzeroberfläche.
- **Frontend**: PyQt6-Widgets (`DynamicIslandWindow`, `ExpandedPillWidget`, `WaveformWidget`, `SettingsPanel`).
- **Controller**: `AppController` vermittelt Signale und Events zwischen UI und Backends.
- **Backend-Services**:
  - `AudioService`: Nimmt Audio über das Mikrofon (sounddevice) auf.
  - `SelectedTextService`: Liest markierten Text via Clipboard-Interaktionen (Ctrl+C).
  - `PolishingService`: Poliert Text per Ollama (asynchron) oder lokalem Offline-Fallback (instant/synchron).
  - `TranscriptionPipeline`: Orchestriert den Diktat-Workflow (Aufnahme -> Transkription -> Polishing -> Clipboard-Einfügen).

## Code Layout
Die Struktur der Quellcodedateien im `src/`-Verzeichnis:
- `src/main.py`: App-Einstiegspunkt
- `src/app.py`: Anwendungs-Klasse
- `src/services/`:
  - `app_controller.py`: Event-Handling und Signalkopplung
  - `audio_service.py`: Audioaufnahme
  - `selected_text_service.py`: Erfassung von selektiertem Text
  - `polishing_service.py`: Text-Polishing mit Ollama / Fallbacks
  - `transcription_pipeline.py`: Workflow-Orchestrierung
  - `clipboard_service.py`: Windows-Clipboard und Tastatur-Simulation
  - `config_service.py`: Konfigurationsverwaltung
  - `text_postprocessor.py`: Developer-Syntax + Deutsch-Engine
  - `developer_syntax.py`: camelCase / snake_case aus gesprochenem Text
  - `german_text_engine.py`: Sie/Du, Zahlen, Währung
  - `correction_learning_service.py`: Lernen aus Nutzerkorrekturen
  - `app_mode_service.py`: App-Erkennung und Stil-Mapping
- `src/ui/`:
  - `dynamic_island.py`: Hauptfenster-Klasse
  - `island_states.py`: Zustands-Enums und Übergänge
  - `island_pill.py`: Statuspillen-Visualisierung
  - `expanded_pill_widget.py`: Ausgeklappte Pill mit Stil-Chips
  - `waveform_widget.py`: Wellenform-Visualisierung (für Siri HSL Waveform)
  - `settings_panel.py`: Konfiguration und Verlauf
- `src/utils/`:
  - `windows_accent.py`: Akzentfarbe laden
  - `windows_overlay.py`: Win32-Fensterflags setzen

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Test Suite | Entwicklung der Testsuite für Tiers 1-4, Veröffentlichung von `TEST_READY.md` | None | DONE |
| 2 | Basics Mausrad & Layout | R1: Scroll-Geste (Idle <-> Basics) und symmetrischer Basics-Modus (Rechts: Power, Links: Audio-Placeholder) | None | DONE |
| 3 | Audio & Mic Steuerungen | R2: Mute-Logik, zyklischer Device-Wechsel, dynamic Audio-Level-Indikator links in Basics | M2 | DONE |
| 4 | Siri HSL Waveform | R3: Neuer Siri/Eloquent-Stil Kurvenzeichner in `waveform_widget.py` mit 60 FPS | None | DONE |
| 5 | SelectedText Umschrift | R4: In-place SelectedTextKit (Erfassung, Status PROCESSING, Polieren, Auto-Inject, SUCCESS) | None | DONE |
| 6 | Windows 11 Acrylic/Mica | R5: Win32-API-Aufrufe über ctypes für echtes Mica/Acryl mit CSS-Fallback | None | DONE |
| 7 | Final integration & Hardening | Phase 1: Bestehen aller E2E Tests (Tiers 1-4); Phase 2: Adversarial Hardening (Tier 5) | M1, M2, M3, M4, M5, M6 | DONE |
| 8 | Differenzierung & Premium-Features | Diff-Ansicht, App-Modes, Correction Learning, Live-Transkription in Expanded, Insights-Dashboard, Developer Mode, Hybrid-Pipeline, Deutsch-Engine | M7 | DONE |

## Differentiation Features (M8)

| Feature | Module | Beschreibung |
|---------|--------|--------------|
| Vertrauens-Diff | `success_widget`, `text_compare_slider`, `diff_helper` | Auto-Expand + Diff-Badge nach Polishing |
| App-Modes | `app_mode_service` | Foreground-App → Stil (Slack, Outlook, IDE …) |
| Correction Learning | `correction_learning_service` | Lernt Wort-Ersetzungen aus manuellen Korrekturen |
| Live-Transkription | `expanded_pill_widget`, `live_transcript_html` | Klick auf Pill während Aufnahme → LIVE-Ansicht |
| Insights | `insights_dialog`, `usage_stats` | Streak, Top-Apps, 7-Tage-Serie in Settings |
| Developer Mode | `developer_syntax`, `style_definitions` | camelCase/snake_case per Sprache + Developer-Chip |
| Hybrid Polishing | `transcription_pipeline`, `polishing_service` | Instant inject + optional Deep-Ollama-Upgrade |
| Deutsch-Engine | `german_text_engine`, `text_postprocessor` | Sie/Du, Zahlen, Euro, Datumsformat |

## Interface Contracts

### Basics Navigation
- Mausrad-Events in `DynamicIslandWindow` triggern Zustandswechsel über `IslandStateMachine`:
  - Wheel Up im IDLE-Zustand -> transition to `IslandState.BASICS`
  - Wheel Down im BASICS-Zustand -> transition to `IslandState.IDLE`
- Basics-Layout:
  - Linker Flügel: `BasicsAudioWidget` (Mute-Button, Source-Select, Level-Indicator)
  - Rechter Flügel: Bestehende Power-Optionen (Ausschalten, Neustart, Energiesparmodus)

### Audio & Mikrofon-Steuerung
- `AudioService.set_muted(muted: bool)`: Setzt Stummschaltung. Wenn stummgeschaltet, überschreibt der Recording-Callback alle gelesenen Frames mit Nullen.
- `AudioService.is_muted() -> bool`: Liefert aktuellen Stummschaltungsstatus.
- `AudioService.next_input_device()`: Wechselt zyklisch zum nächsten verfügbaren Input-Gerät, aktualisiert `config.json` über `ConfigService` unter `"recording_device"`, und sendet ein Signal zur Anzeige eines Overlays in der Island.
- `AudioService.level_changed(level: float)`: Signalisiert Lautstärkepegel (RMS) für den LED-Balken.

### Siri HSL Waveform
- `WaveformWidget` zeichnet mehrere animierte Sinus- oder Bezier-Kurven mit HSL-Gradient, basierend auf dem `rms`-Pegel.

### SelectedTextKit Umschreibung
- `SelectedTextService.capture_and_rewrite(style: str)`:
  - Führt Clipboard-Capture (Ctrl+C) aus.
  - Setzt Island-Zustand auf `PROCESSING` mit Anzeige "Umschreiben...".
  - Führt Polishing asynchron via `PolishingService` aus.
  - Fügt Resultat über Clipboard/Auto-Inject (Ctrl+V) ein.
  - Setzt Island-Zustand auf `SUCCESS` ("Umschrift eingefügt") und kehrt zu `IDLE` zurück.

### Acrylic/Mica Glow
- `windows_backdrop.py` stellt `set_backdrop_type(hwnd, backdrop_type)` bereit.
  - `backdrop_type`: 2 (Mica), 3 (Acrylic).

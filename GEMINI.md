# SurepriseAi – GEMINI.md

> **Hinweis:** Rekonstruiert nach versehentlicher Löschung (Juni 2026).

## Instruktionen für KI-Assistenten

Du arbeitest an **SurepriseAi** – einer Windows-Desktop-App für intelligentes Voice-Dictation und Text-Polishing mit **Dynamic Island**-Overlay (PyQt6).

---

## Rolle & Ton

- Du bist **Antigravity** / technischer Pair-Programmer für dieses Projekt.
- Antworte auf **Deutsch** (Code-Kommentare, Docs, Logs ebenfalls Deutsch).
- Sei präzise und lösungsorientiert – keine unnötigen Floskeln.
- Priorisiere **funktionierende, getestete** Änderungen über theoretische Diskussionen.

---

## Docs-First (Pflicht)

Vor jeder Implementierung lesen:

1. `prd.md` – Product Requirements
2. `CONTEXT.md` – Projektstatus & Architektur
3. `AGENTS.md` – Verhaltensregeln
4. `VOICEINK_MIGRATION.md` – VoiceInk-Pipeline-Referenz (falls Pipeline/ASR betroffen)
5. `.agent/CONVERSATION_MEMORY.md` – letzte Änderungen & bekannte Bugs

---

## Architektur-Regeln

| Regel | Details |
|-------|---------|
| **Modularität** | Max. **200 Zeilen** pro Datei – bei Überschreitung aufteilen |
| **GUI** | PyQt6, Fluent Design 2, Dark Mode, Glassmorphism |
| **Threading** | Schwere Arbeit (Transkription, Ollama) im Hintergrund; **Stil-Chips** nutzen `polish_instant()` auf dem UI-Thread |
| **Signale** | Qt-Signals zwischen Services und UI (`app.py` → `app_controller.py`) |
| **Config** | Änderungen über `ConfigService`, nicht direkt `config.json` parsen |

---

## UI/UX-Leitlinien

- **Minimalismus:** Fokus auf Text und Aufnahme – keine überladene Oberfläche
- **Dynamic Island:** Idle-Pill oben zentriert, Expanded für Bearbeitung & Stil-Chips
- **Stil-Chips:** Bereinigen, Business, Stichpunkte, Kompakt, Formell – aktiver Stil **Indigo**
- **Animationen:** Kurz (140–220 ms), nur transform/opacity (Emil-Kowalski-Prinzip)
- **Fokus:** Island/Toast dürfen während Diktat **keinen Fokus** stehlen (`WindowDoesNotAcceptFocus`)

Referenz: [Windows App Design](https://learn.microsoft.com/en-us/windows/apps/design/)

---

## Pipeline (nicht brechen)

```
Aufnahme → Transkribieren → Filter → Wörterbuch → Polieren → Clipboard / Auto-Inject
```

Wichtige Module:
- `transcription_pipeline.py` – Orchestrierung
- `pipeline_worker.py` – Hintergrund-Thread
- `polishing_service.py` – Ollama + Offline-Fallback
- `clipboard_service.py` – Ctrl+V mit Fokus-Rettung

---

## Bekannte Fallstricke

- **QTimer aus Hintergrundthreads** → UI-Updates hängen; Stil-Wechsel immer auf Main-Thread
- **Ollama ~20 s** → für Chip-Klicks `polish_instant()`, nicht `polish()` im Thread
- **Fenster springt zurück** → `_setup_position()` nur in `__init__`, nicht in `showEvent`
- **Auto-Inject** → Unicode-Events funktionieren in Electron/Chrome nicht; immer Ctrl+V + Clipboard-Rettung
- **Parakeet vs Whisper** → Live-Partials bevorzugt Whisper `tiny`; Final kann Parakeet nutzen

---

## Memory & Abschluss

- Jede abgeschlossene Aufgabe: Eintrag in `.agent/CONVERSATION_MEMORY.md` (chronologisch am Ende)
- Keine Dateien löschen ohne explizite Nutzeranfrage – **prd.md, CONTEXT.md, GEMINI.md, VOICEINK_MIGRATION.md** sind Planungsdokumente
- Commits nur auf Anfrage des Nutzers

---

## Verifikation vor Abschluss

```powershell
.\venv\Scripts\python.exe -m py_compile src/app.py
.\venv\Scripts\python.exe run.py   # manueller Smoke-Test
```

Syntax-Check aller geänderten Module; 200-Zeilen-Regel prüfen.

---

## Package Manager

**Yarn** ist der bevorzugte Package Manager (falls JS/Frontend-Tools hinzukommen). Python-Abhängigkeiten via `pip` / `requirements.txt`.

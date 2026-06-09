# SurepriseAi – CONTEXT.md

> **Hinweis:** Rekonstruiert nach versehentlicher Löschung (Juni 2026). Stand basiert auf `.agent/CONVERSATION_MEMORY.md` und dem aktuellen Code.

## Aktueller Projektstatus

**SurepriseAi** ist eine funktionsfähige **Windows-Desktop-App** (PyQt6) für Voice-Dictation mit **Dynamic Island**, Live-Transkription, lokalem ASR und KI-Polishing.

**Status:** Alpha – Kernfeatures implementiert, UI iterativ verfeinert.

---

## Erreichte Meilensteine

### Foundation & Intelligence
- Modulare Python-Architektur (`src/services/`, `src/ui/`, `src/utils/`)
- Transkriptions-Pipeline: Aufnahme → Transkribieren → Filter → Wörterbuch → Polieren → Clipboard/Inject
- **Parakeet V3** (sherpa-onnx) + **Whisper** (faster-whisper, `tiny` für Live-Partials)
- **Ollama-Polishing** mit Offline-Fallback (`polish_instant` für Chip-Umschaltung)
- Globaler Hotkey **F8** (pynput), Push-to-Talk / Toggle

### UI – Dynamic Island (PyQt6)
- Rahmenloses, transparentes Overlay (Win32 Always-on-Top, DWM-Blur)
- Zustände: Idle, Recording, Processing, Expanded, Basics
- Live-Toast-Fenster für Echtzeit-Transkription
- Expanded: Textfeld, WPM/Wort-Statistiken, 5 Stil-Chips (Indigo-Aktiv)
- Settings-Panel mit Glassmorphism (`settings_styles.py`)
- Drag-Griff zum Verschieben, ✕ für Reset zur Startposition

### System-Integration
- **System-Tray** (Diktat, Stile, Einstellungen, Beenden)
- **Auto-Inject** via Ctrl+V mit Clipboard-Rettung & Fokus-Rettung (`AttachThreadInput`)
- **File Transcription** per Drag & Drop (MP3, WAV, MP4, …)
- **Basics Control Hub** (Power, Restart, Sleep) mit Sicherheits-Bestätigung
- Fokus-Sperre: Island/Toast akzeptieren keinen Fokus während Diktat

### Personalisierung
- Personal Vocabulary & Word Replacements
- Sprachauswahl & Englisch-Übersetzung (Whisper)
- `config.json` mit typsicherem `ConfigService`

---

## Technologie-Stack

| Schicht | Technologie |
|---------|-------------|
| **Runtime** | Python 3.11+ |
| **GUI** | PyQt6 (Dynamic Island, Tray, Settings, Toast) |
| **Audio** | sounddevice, numpy |
| **ASR** | faster-whisper, sherpa-onnx (Parakeet) |
| **Polishing** | Ollama HTTP API + lokaler Regex-Fallback |
| **System** | Win32 API (Overlay, SendInput, Fokus, Systemaktionen) |
| **Input** | pynput (Hotkeys), pyperclip |

---

## Projektstruktur (Kurz)

```
SurepriseAi/
├── run.py
├── config.json              # lokal (nicht im Git)
├── config.example.json
├── prd.md                   # Product Requirements
├── GEMINI.md                # KI-Anweisungen
├── VOICEINK_MIGRATION.md      # VoiceInk-Referenz
├── AGENTS.md
├── src/
│   ├── app.py               # QApplication + Signals
│   ├── main.py
│   ├── services/            # Pipeline, Audio, Transcription, Polishing, …
│   └── ui/                  # Dynamic Island, Widgets, Settings, Tray
├── models/                  # ML-Modelle (gitignored)
└── .agent/CONVERSATION_MEMORY.md
```

---

## Bekannte Einschränkungen

- Nur **Windows** (Win32-Overlay, Auto-Typing)
- Ollama-Polishing nach Diktat kann Sekunden dauern; Chips nutzen schnellen Offline-Pfad
- Einige UI-Module > 200 Zeilen (Refactoring ausstehend)
- Kein paralleler CI-Lauf für macOS/Linux (Windows-only App)

---

## Nächste mögliche Ziele

- [x] Eloquent Phase 1–3 (Diff-Animation, Chips, Historie, App-Modi, Mini-FAB, …)
- [x] Settings-UI für Erscheinungsbild & App-Modi
- [x] Windows-Akzent live (periodischer Refresh)
- [x] Screen-Context / OCR (Windows-OCR, optional)
- [x] Markierter Text als Kontext (SelectedTextKit)
- [x] Historien-Export (TXT / MD / SRT)
- [x] YouTube/URL-Transkription (yt-dlp)
- [x] Installer (PyInstaller + Inno Setup) & Auto-Update (GitHub Releases)
- [x] CI/CD (GitHub Actions: Smoke-Test + Release-Build)

---

## Start

```powershell
cd c:\Users\ed\Webdesign\webstark.org\SurepriseAi
.\venv\Scripts\python.exe run.py
```

---

## Referenzen

- **PRD:** `prd.md`
- **VoiceInk-Migration:** `VOICEINK_MIGRATION.md`
- **Entwicklungschronik:** `.agent/CONVERSATION_MEMORY.md`
- **Design:** [Microsoft Fluent / Windows App Design](https://learn.microsoft.com/en-us/windows/apps/design/)

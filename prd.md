# SurepriseAi – Product Requirements Document (PRD)

> **Hinweis:** Diese Datei wurde nach versehentlicher Löschung aus Projekt-Memory, Transkripten und dem implementierten Stand rekonstruiert (Juni 2026).

## 1. Vision

**SurepriseAi** ist ein **Windows-Desktop-Diktier-Assistent** – ein „Eloquent Clone“ für Windows: sprechen, lokal transkribieren, KI-gestützt polieren und den Text direkt in die aktive Anwendung einfügen.

Kernprinzip: **Minimalismus** – das Interface konzentriert sich auf den **Text** und einen **zentralen Aufnahme-Button** (bzw. die Dynamic Island als schwebendes Overlay). Keine überladene Desktop-App.

---

## 2. Zielgruppe

- Wissensarbeiter, Entwickler, Autoren auf **Windows 10/11**
- Nutzer, die **lokale** Spracherkennung bevorzugen (Datenschutz, Offline)
- Optional: Nutzer mit **Ollama** für erweitertes Text-Polishing

---

## 3. Kern-Features (Muss)

### 3.1 Voice Dictation

| Anforderung | Beschreibung |
|-------------|--------------|
| Globaler Hotkey | Standard **F8**, Push-to-Talk oder Toggle konfigurierbar |
| Aufnahme | Mikrofon-Aufnahme im Hintergrund, non-blocking |
| Live-Transkription | Echtzeit-Anzeige des gesprochenen Textes während der Aufnahme |
| Finale Transkription | Nach Stopp: vollständige Verarbeitung der Aufnahme |

### 3.2 Transkriptions-Engines

| Engine | Technologie | Standard |
|--------|-------------|----------|
| **Parakeet V3** | sherpa-onnx (lokal) | Empfohlen |
| **Whisper** | faster-whisper (lokal) | Fallback / Partial-Live |

- Sprachauswahl: `auto`, `de`, `en`, …
- Option: **Übersetzung ins Englische** via Whisper `task="translate"`

### 3.3 Text-Polishing

| Anforderung | Beschreibung |
|-------------|--------------|
| Ollama-Integration | Optional, Standard-Modell `gemma2:2b` |
| Offline-Fallback | Regelbasierte Stil-Umformung wenn Ollama nicht erreichbar |
| **Re-Polishing** | Stil nach Diktat jederzeit änderbar |
| Pipeline | Transkribieren → Filter → Wörterbuch → Polieren → Ausgabe |

### 3.4 Stil-Chips (5 Stile)

Direktwahl ohne Kontextmenü – aktiver Stil **Indigo** hervorgehoben:

| Chip | Stil-Key | Wirkung |
|------|----------|---------|
| Bereinigen | `casual` | Füllwörter entfernen, glätten |
| Business | `professional` | Sachlicher Ton |
| Stichpunkte | `bullet_points` | Aufzählung mit `•` |
| Kompakt | `concise` | Kürzen |
| Formell | `formal` | Höfliche Sprache |

Stil muss **vor und nach** der Aufnahme wählbar sein (Tray, Expanded, Chips).

### 3.5 Dynamic Island (UI)

| Zustand | Verhalten |
|---------|-----------|
| **Idle** | Schmale Pill oben zentriert, Hover-Einblendung |
| **Recording** | Wellenform, Aufnahme-Indikator |
| **Processing** | Verarbeitungs-Animation |
| **Expanded** | Textfeld, Statistiken (Wörter, WPM), Stil-Chips, Kopieren |
| **Basics** | Systemsteuerung (Power, Restart, Sleep) per Scroll/Pfeiltasten |

- Verschiebbar per Drag-Griff
- ✕ schließt Expanded und setzt Position zurück
- Drag & Drop: Audio/Video-Dateien transkribieren

### 3.6 Ausgabe & Integration

- **Auto-Copy** in Zwischenablage (optional)
- **Auto-Inject** per Ctrl+V in aktive Anwendung (mit Clipboard-Rettung)
- Fokus-Sperre: Island/Toast stehlen keinen Fokus während Diktat
- **System-Tray**: Diktat, Stile, Einstellungen, Beenden

### 3.7 Personalisierung

- **Personal Vocabulary**: Eigennamen / Fachbegriffe für bessere Erkennung
- **Word Replacements**: `original=>replacement`-Paare
- Einstellungs-Panel: Engine, Modell, Hotkey, Sprache, Theme, Ollama

---

## 4. UI/UX Design-Vorgaben

Referenz: [Windows App Design Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/) / **Fluent Design 2**

| Bereich | Vorgabe |
|---------|---------|
| **Design System** | Minimalistisch, luftig, modern |
| **Dynamic Color** | Windows-Akzentfarbe oder sanfte Pastelltöne |
| **Typografie** | Inter / Segoe UI – maximale Lesbarkeit des polierten Textes |
| **Visuelle Rückmeldung** | Übergang Rohtext → Poliertext durch subtile Animationen (Einblenden, Diff-Markierung) – Eloquent-ähnlich |
| **Dark Mode** | Hochwertiges Dark / Light / System-Theme |
| **Animationen** | Emil-Kowalski-Prinzipien: 140–220 ms, nur transform + opacity |
| **Glassmorphism** | Settings-Panel mit transparentem Hintergrund, DWM-Blur |

---

## 5. Nicht-Ziele (Out of Scope)

- macOS / iOS / Linux (Windows-only)
- Cloud-only Transkription als Pflicht
- Vollständige VoiceInk 1:1-Portierung (siehe `VOICEINK_MIGRATION.md`)
- Menüleisten-Notch-UI wie auf MacBook

---

## 6. Technische Rahmenbedingungen

| Aspekt | Vorgabe |
|--------|---------|
| Sprache | Python 3.11+ |
| GUI | **PyQt6** (rahmenlos, transparent, Always-on-Top) |
| Modularität | Dateien ≤ 200 Zeilen |
| Dokumentation | Deutsch (Code-Kommentare, Docs, Logs) |
| Config | `config.json` (lokal, nicht im Git) |

---

## 7. Erfolgskriterien

- [x] Diktat starten/stoppen per F8
- [x] Live-Transkription mit niedriger Latenz
- [x] 5 Stil-Chips mit sofortigem Re-Polishing
- [x] Dynamic Island mit Expanded-Ansicht
- [x] Auto-Inject in Chrome, VS Code, Notepad, Terminal
- [x] System-Tray-Steuerung
- [x] File Transcription per Drag & Drop
- [x] Personal Vocabulary & Word Replacements
- [ ] Vollständige Fluent Dynamic-Color-Integration (teilweise)
- [ ] Polish-Animation im Eloquent-Stil (Flet-Phase geplant, PyQt6 variiert)

---

## 8. Referenzdokumente

- `CONTEXT.md` – Projektstatus & Meilensteine
- `GEMINI.md` – KI-Assistenten-Anweisungen
- `VOICEINK_MIGRATION.md` – VoiceInk-Architektur-Übernahme
- `AGENTS.md` – Cursor/Antigravity-Regeln
- `.agent/CONVERSATION_MEMORY.md` – Entwicklungschronik

# SurepriseAi

[![CI](https://github.com/Icarus-B4/SurepriseAi/actions/workflows/ci.yml/badge.svg)](https://github.com/Icarus-B4/SurepriseAi/actions/workflows/ci.yml)
[![Release](https://github.com/Icarus-B4/SurepriseAi/actions/workflows/release.yml/badge.svg)](https://github.com/Icarus-B4/SurepriseAi/actions/workflows/release.yml)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Plattform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Alpha-FF6B35?style=flat-square)
![License](https://img.shields.io/badge/Lizenz-MIT-blue?style=flat-square)

**SurepriseAi** ist eine Windows-Desktop-App für intelligentes Voice-Dictation mit **Dynamic Island**-Overlay, Live-Transkription und KI-Text-Polishing – inspiriert von modernen Diktier-Tools, vollständig lokal auf deinem Rechner.

---

## Installation (für Nutzer)

1. **`SurepriseAi-Setup.exe`** von [GitHub Releases](https://github.com/Icarus-B4/SurepriseAi/releases/latest) herunterladen
2. Doppelklick → Setup-Assistent (Deutsch) durchlaufen
3. Optional: Desktop-Verknüpfung, Autostart mit Windows
4. Nach der Installation: **Tray-Icon** unten rechts → **F8** zum Diktieren

Kein Python nötig – der Installer enthält alles. Einstellungen liegen unter `%APPDATA%\SurepriseAi\`.

---

## Features

| Feature | Beschreibung |
|---------|--------------|
| **Dynamic Island** | Schwebendes Overlay oben am Bildschirm – Idle, Aufnahme, Verarbeitung, Ergebnis |
| **Live-Transkription** | Echtzeit-Anzeige des gesprochenen Textes während der Aufnahme |
| **KI-Polishing** | Bereinigung und Stil-Umformung via **Ollama** (optional) oder schnellem Offline-Fallback |
| **5 Stil-Chips** | Bereinigen · Business · Stichpunkte · Kompakt · Formell – sofort umschaltbar |
| **Whisper & Parakeet** | Lokale Spracherkennung (`faster-whisper` oder `sherpa-onnx`) |
| **Auto-Typing** | Fertiger Text wird optional direkt in die aktive Anwendung eingefügt |
| **System-Tray** | Steuerung im Hintergrund: Diktat, Stil, Einstellungen |
| **Datei-Import** | Audio/Video per Drag & Drop auf die Island transkribieren |
| **URL-Import** | YouTube, Vimeo, SoundCloud & Co. per Tray, Dialog oder Drag & Drop (yt-dlp) |
| **Kontext-Polishing** | Markierter Text + optional OCR für bessere Ollama-Korrektur |
| **Historien-Export** | Diktate als TXT, Markdown oder SRT exportieren |

---

## Screenshots

> Die App erscheint als dunkle, halbtransparente **Pill** oben zentriert und expandiert nach dem Diktat zur Vollansicht mit Statistiken, Textfeld und Stil-Chips.

---

## Voraussetzungen

- **Windows 10/11**
- **Python 3.11+**
- Mikrofon
- *(Optional)* [Ollama](https://ollama.com/) für erweitertes KI-Polishing
- *(Optional)* Parakeet-Modell unter `models/` (siehe unten)

---

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/Icarus-B4/SurepriseAi.git
cd SurepriseAi
```

### 2. Virtuelle Umgebung erstellen

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Konfiguration anlegen

```powershell
copy config.example.json config.json
```

Passe `config.json` nach Bedarf an (Hotkey, Sprache, Whisper-Modell, Ollama-URL).

### 4. *(Optional)* Whisper-Modell

Beim ersten Start lädt `faster-whisper` automatisch das konfigurierte Modell (Standard: `tiny`).

### 5. *(Optional)* Parakeet-Modell

Für `transcription_engine: "parakeet"` das Modell in `models/` ablegen:

```
models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/
```

### 6. *(Optional)* Ollama

```bash
ollama pull gemma2:2b
ollama serve
```

---

## App starten

```powershell
.\venv\Scripts\python.exe run.py
```

Die **Dynamic Island** erscheint oben mittig (beim Hover sichtbar). Ein Tray-Icon bleibt im Hintergrund aktiv.

---

## Bedienungsanleitung

### Schnellstart – Diktat

1. **F8** drücken und halten *(Push-to-Talk)* oder kurz drücken *(Toggle – je nach Einstellung)*
2. Sprechen – der Text erscheint live im Toast-Fenster
3. **F8** loslassen / erneut drücken → Verarbeitung startet
4. Die **Expanded-Ansicht** öffnet sich mit bereinigtem Text, Wörtern & WPM

### Stil wechseln

Nach dem Diktat (oder vor dem nächsten) einen **Stil-Chip** anklicken:

| Chip | Wirkung |
|------|---------|
| **Bereinigen** | Füllwörter entfernen, Satz glätten |
| **Business** | Sachlicher, professioneller Ton |
| **Stichpunkte** | Aufzählung mit `•` |
| **Kompakt** | Auf das Wesentliche kürzen |
| **Formell** | Höfliche, formelle Sprache |

Der aktive Stil wird **indigo** hervorgehoben. Die Änderung erfolgt **sofort** (Offline-Fallback).

### Island verschieben & zurücksetzen

- **⠿ Griff** (rechts in der Pill / oben rechts in Expanded): Fenster per Drag verschieben
- **✕ Schließen**: Expanded schließen und Island zurück an die **Startposition oben zentriert**

### Weitere Bedienung

| Aktion | Steuerung |
|--------|-----------|
| Island öffnen (Expanded) | Linksklick auf die Pill |
| Einstellungen | Doppelklick auf die Pill **oder** Tray → Einstellungen |
| Diktat starten/stoppen | **F8** oder Tray → Diktat |
| Text kopieren | Kopieren-Icon im Textfeld |
| Audio-Datei transkribieren | MP3/WAV/MP4 per Drag & Drop auf die Island |
| Video-/Audio-URL transkribieren | Tray → **URL transkribieren…**, 🔗 in Expanded oder URL per Drag & Drop |
| Diktat exportieren | Tray → Diktat-Verlauf → Eintrag wählen → **Exportieren…** (TXT/MD/SRT) |
| Kontext für Polishing | Text in Ziel-App markieren, dann F8 – Ollama nutzt Markierung automatisch |
| Island ein-/ausblenden | Doppelklick auf Tray-Icon |
| Basics-Modus (Power/Restart/Sleep) | Mausrad auf der Idle-Pill |

### System-Tray

Rechtsklick auf das Tray-Icon:

- Diktat starten / stoppen
- Polishing-Stil wählen
- **URL transkribieren…** (YouTube, Vimeo, …)
- Einstellungen
- **Nach Updates suchen…** (GitHub Releases)
- Beenden

---

### Installer lokal bauen (Entwickler)

**Engine:** [NSIS 3](https://nsis.sourceforge.io/) – dieselbe Technologie wie [Hermes Desktop](https://github.com/NousResearch/hermes-agent/tree/main/apps/desktop) (`electron-builder` → NSIS auf Windows).

```powershell
# Doppelklick oder:
.\Erstelle-Installer.bat

# Oder manuell (lädt NSIS bei Bedarf nach .tools/):
powershell -ExecutionPolicy Bypass -File .\build\build.ps1 -Installer
```

Ergebnis: **`dist\SurepriseAi-Setup.exe`** (~140 MB) – an Endnutzer weitergeben.

Der Wizard entspricht Hermes (`oneClick: false`, Installationsordner wählbar, Benutzer-Installation):
- Willkommen → Lizenz → Zielordner → Optionen → Installation → Fertig
- Optional: Desktop-Verknüpfung, Autostart mit Windows
- Deinstallation über „Apps & Features“

---

- Beim Start wird optional nach GitHub-Releases gesucht (`check_updates_on_startup`)
- Tray → **Nach Updates suchen…**
- Bei neuem Release wird der Installer nach `Downloads\` geladen

Release auf GitHub anlegen mit Tag `v0.1.1` und Asset `SurepriseAi-Setup.exe`.

---

## CI/CD (GitHub Actions)

| Workflow | Trigger | Aufgabe |
|----------|---------|---------|
| **CI** | Push/PR auf `main` | Smoke-Test + `py_compile` aller Module |
| **Release** | Git-Tag `v*` (z. B. `v0.1.10`) | PyInstaller + NSIS → `SurepriseAi-Setup.exe` als Release-Asset |

### Ersten Release veröffentlichen

```bash
# Version in src/version.py prüfen (z. B. 0.1.0)
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions baut automatisch den Installer und lädt `dist/SurepriseAi-Setup.exe` als Release-Asset hoch. Die Auto-Update-Funktion in der App erkennt neuere Tags über die GitHub-API.

Lokal testen:

```powershell
python build/ci_smoke_test.py
powershell -ExecutionPolicy Bypass -File .\build\build.ps1 -Installer
```

---

## Konfiguration (`config.json`)

| Schlüssel | Beschreibung | Standard |
|-----------|--------------|----------|
| `global_hotkey` | Aufnahme-Hotkey | `f8` |
| `push_to_talk` | `true` = halten, `false` = Toggle | `true` |
| `transcription_engine` | `whisper` oder `parakeet` | `whisper` |
| `whisper_model_size` | `tiny`, `base`, `small` | `tiny` |
| `transcription_language` | `auto`, `de`, `en`, … | `auto` |
| `selected_style` | Standard-Stil nach Diktat | `casual` |
| `ollama_polishing` | KI-Polishing via Ollama | `true` |
| `ollama_url` | Ollama-API | `http://localhost:11434` |
| `auto_copy_to_clipboard` | Text automatisch kopieren | `true` |
| `auto_inject_text` | Text per Ctrl+V einfügen | `true` |

Vorlage: [`config.example.json`](config.example.json)

---

## Projektstruktur

```
SurepriseAi/
├── run.py                 # Startskript
├── config.example.json    # Konfigurationsvorlage
├── requirements.txt       # Python-Abhängigkeiten
├── src/
│   ├── app.py             # Qt-Hauptanwendung
│   ├── main.py            # Einstiegspunkt
│   ├── services/          # Audio, Transkription, Polishing, Pipeline
│   ├── ui/                # Dynamic Island, Widgets, Einstellungen
│   └── utils/             # Text-Cleaner, Win32-Overlay
├── models/                # ML-Modelle (nicht im Git)
└── AGENTS.md              # Hinweise für KI-Entwickler
```

---

## Entwicklung

```powershell
# CI-Smoke-Test (wie GitHub Actions)
python build/ci_smoke_test.py

# Syntax prüfen
.\venv\Scripts\python.exe -m py_compile src/app.py

# Abhängigkeiten aktualisieren
pip install -r requirements.txt
```

Code-Kommentare und Agent-Dokumentation sind auf **Deutsch**.

---

## Bekannte Einschränkungen

- Nur **Windows** (Win32-Overlay, Auto-Typing via SendInput)
- Ollama-Polishing nach dem Diktat kann einige Sekunden dauern; **Chip-Umschaltung** nutzt bewusst den schnellen Offline-Pfad
- Whisper-Modell `small`/`medium` ist genauer, aber langsamer als `tiny`

---

## Lizenz

MIT – siehe [LICENSE](LICENSE).

---

## Danksagung

Inspiriert von modernen Voice-Dictation-Tools und Fluent Design / Dynamic Island UI-Patterns.

# SurepriseAi

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Plattform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Alpha-FF6B35?style=flat-square)
![License](https://img.shields.io/badge/Lizenz-MIT-blue?style=flat-square)

**SurepriseAi** ist eine Windows-Desktop-App für intelligentes Voice-Dictation mit **Dynamic Island**-Overlay, Live-Transkription und KI-Text-Polishing – inspiriert von modernen Diktier-Tools, vollständig lokal auf deinem Rechner.

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
git clone https://github.com/DEIN-USER/SurepriseAi.git
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
| Island ein-/ausblenden | Doppelklick auf Tray-Icon |
| Basics-Modus (Power/Restart/Sleep) | Mausrad auf der Idle-Pill |

### System-Tray

Rechtsklick auf das Tray-Icon:

- Diktat starten / stoppen
- Polishing-Stil wählen
- Einstellungen
- Beenden

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

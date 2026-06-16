# VoiceInk → SurepriseAi (Windows) Migrationsplan

Referenz: [Beingpax/VoiceInk](https://github.com/Beingpax/VoiceInk) (geklont nach `_reference/VoiceInk`)

## Fazit: Keine 1:1-Migration möglich

VoiceInk ist **keine iOS-App**, sondern eine **native macOS Swift/SwiftUI-App** (99,7 % Swift).
Eine direkte Portierung nach Windows ist technisch unmöglich — der gesamte UI- und OS-Layer ist Apple-spezifisch.

## Was übernommen wurde (Architektur-Migration)

| VoiceInk (macOS) | SurepriseAi (Windows) | Status |
|------------------|----------------------|--------|
| `TranscriptionPipeline.swift` | `src/services/transcription_pipeline.py` | ✅ |
| `TranscriptionOutputFilter.swift` | `src/services/transcription_output_filter.py` | ✅ |
| `WordReplacementService.swift` | `src/services/word_replacement_service.py` | ✅ |
| Parakeet via FluidAudio (CoreML) | Parakeet via sherpa-onnx | ✅ |
| whisper.cpp | faster-whisper + sherpa fallback | ✅ |
| AIEnhancement (Ollama optional) | `polishing_service.py` + lokaler Fallback | ✅ |
| Global Shortcuts (CGEvent) | — | 🔲 geplant |
| SelectedTextKit / Paste | Markierter Text via Ctrl+C + Export TXT/MD/SRT | ✅ |
| Screen Context / OCR | `screen_context_service.py` + Windows OCR | ✅ |
| Modes pro App | `app_mode_service.py` | ✅ |

## Pipeline (wie VoiceInk)

```
Aufnahme → Transkribieren → Filter → Wörterbuch → Polieren → Zwischenablage
```

## Noch nicht portiert (macOS-only)

- Menüleisten-App / Notch-UI
- ScreenCaptureKit + Vision OCR
- Accessibility Text-Injection in fremde Apps
- FluidAudio CoreML (ersetzt durch sherpa-onnx auf Windows)

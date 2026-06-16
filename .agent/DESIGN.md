# SurepriseAi – Design System

Leitfaden für die **PyQt6-Desktop-App** (Windows). Vor neuen UI-Komponenten,
Overlays oder QSS-Stilen lesen. Grundregel: **Tokens statt Literale, eine Quelle
pro Anliegen, flach statt verschachtelt.**

**Single Source of Truth:** `src/ui/design_tokens.py`  
**QSS für Einstellungen:** `src/ui/settings_styles.py`  
**Windows-Akzent:** `src/ui/accent_theme.py`

---

## Prinzipien

1. **Fluent Design 2, Dark Mode.** Dunkle Oberflächen, dezente Hairlines, eine
   Akzentfarbe (Indigo oder Windows-System-Akzent).
2. **Dynamic Island als Herzstück.** Alle Zustände (Idle, Recording, Processing,
   Success, Expanded, Basics) teilen dieselben Tokens und Animationszeiten.
3. **Tokens, keine Hex-Literale.** Farben, Abstände und Größen aus
   `Colors`, `Spacing`, `Typography`, `IslandSize`, `AnimationTokens`.
4. **Modular & unter 200 Zeilen.** UI-Logik in eigene Module auslagern
   (`settings_styles.py`, `island_shimmer_indicator.py`, …).
5. **Deutsch in der UI.** Nutzer-sichtbare Texte auf Deutsch; Code-Kommentare
   und Docs ebenfalls.

---

## Farben (`Colors`)

| Token | Hex / Wert | Verwendung |
| --- | --- | --- |
| `ISLAND_BG_HEX` / `ISLAND_BG_ALPHA` | `#0D0D0F` / 90 % | Dynamic Island, Toast |
| `SURFACE_HEX` | `#1A1A1E` | Tray-Menü, sekundäre Flächen |
| `SURFACE_ELEVATED` | `#242428` | Erhöhte Ebenen |
| `TEXT_PRIMARY_HEX` | `#F5F5F7` | Haupttext, Titel |
| `TEXT_SECONDARY_HEX` | `#8E8E93` | Labels, Tray, Sektionen |
| `TEXT_TERTIARY_HEX` | `#48484A` | Hinweise, Platzhalter |
| `ACCENT_HEX` | `#6366F1` (oder Windows) | Fokus, Shimmer, aktive Chips |
| `ACCENT_BRIGHT_HEX` | `#818CF8` | Hover, Glow, Shimmer-Peak |
| `ACCENT_DARK_HEX` | `#4F46E5` | Hover auf Buttons, Dropdown-Auswahl |
| `RECORDING_RED_HEX` | `#FF453A` | Aufnahme, Fehler-Toast |
| `SUCCESS_GREEN_HEX` | `#30D158` | Erfolg, Kopiert |
| `PROCESSING_BLUE_HEX` | `#64D2FF` | Verarbeitung, Spinner |
| `BORDER_HEX` | `rgba(255,255,255,0.08)` | Pill-Rahmen, Inputs |
| `BORDER_SUBTLE_HEX` | `rgba(255,255,255,0.04)` | Dezente Trenner |

**Windows-Akzent:** Wenn `use_windows_accent` aktiv ist, überschreibt
`accent_theme.apply_accent_from_config()` die drei `ACCENT_*`-Werte zur Laufzeit.
Neue Komponenten müssen `Colors.ACCENT_HEX` referenzieren, nie hardcoded Indigo.

---

## Typografie (`Typography`)

| Stufe | px | Einsatz |
| --- | --- | --- |
| `TINY` | 10 | Sektionstitel, Privacy-Badge, Live-Titel |
| `SMALL` | 12 | Pill-Text, Tray, Checkboxen |
| `BODY` | 14 | Standard-Fließtext |
| `MEDIUM` | 16 | Dialog-Titel (Einstellungen) |
| `LARGE` | 18 | — |
| `TITLE` | 22 | — |

Schriftfamilie: `Segoe UI Variable Display, Segoe UI, sans-serif`  
Icons/Symbole: `FluentIcons.FONT_FAMILY` oder Unicode-Glyphen aus `FluentIcons`.

```python
label.setFont(Typography.get_font(Typography.SMALL, bold=True))
```

---

## Abstände (`Spacing`) – 8px-Grid

| Token | px |
| --- | --- |
| `XS` | 4 |
| `SM` | 8 |
| `MD` | 16 |
| `LG` | 24 |
| `XL` | 32 |

Island-Innenabstand: `ISLAND_PADDING_H = 16`, `ISLAND_PADDING_V = 8`.

---

## Dynamic Island (`IslandSize`)

### Zustände & Abmessungen

| Zustand | Breite × Höhe | Radius | Widget |
| --- | --- | --- | --- |
| **Idle** | 290 × 44 | Pill (h/2) | `island_pill.py` – Uhrzeit, Mic, Drag |
| **Presence** | 118 × 11 | Kapsel | `island_shimmer_indicator.py` – Shimmer |
| **Recording** | 360 × 56 | Pill | Waveform + Timer |
| **Processing** | 300 × 48 | Pill | Spinner + Label |
| **Success** | 400 × 50 | Pill | Checkmark + Preview |
| **Expanded** | 620 × 348 | 16 px | `expanded_pill_widget.py` – Transkript |
| **Basics** | 290 × 44 | Pill | Quick Controls (Power/Restart/Sleep) |

Trägerfenster: `WINDOW_WIDTH` × `WINDOW_HEIGHT` (muss Expanded umschließen).

### Verhalten

- **Idle/Basics:** Presence-Bar immer sichtbar; Hover oben mittig → volle Pill.
- **Aktive Zustände:** Pill volle Opacity, Shimmer aus.
- **Animation:** `AnimationTokens.NORMAL` (200 ms), Easing `OutBack` in
  `dynamic_island.py`.
- **Position:** Oben mittig (`y = screen.top + 10`), nach Drag bleibt Position.

### Shimmer (Presence-Bar)

- Wandernder Indigo-Weiß-Gradient, ~60 FPS.
- Größe nur über `PRESENCE_WIDTH`, `PRESENCE_HEIGHT`, `PRESENCE_TOP_Y` ändern.
- Bei geöffneten Einstellungen ausblenden (kein Durchscheinen).

---

## Oberflächen & Elevation

### Dynamic Island Pill

```python
# island_pill.py – QFrame#PillContainer
background: Colors.ISLAND_BG_ALPHA
border: 1px solid Colors.BORDER_HEX
border-radius: dynamisch (Pill vs. Expanded)
```

### Toast (`toast_notification.py`)

- Position: zentriert, `y = screen.top + 75` (unter der Island).
- Hintergrund: `rgba(13, 13, 15, 0.95)`, Radius 20 (Pill) / 12 (Live).
- Update-Toasts: `show_update()` – sticky, 10 s, grün.
- Fehler: `RECORDING_RED_HEX`, 6 s.

### Einstellungen (`settings_panel.py`)

- Größe: **440 × 680** px, `border-radius: 16`.
- **Kein DWM-Blur** auf dem HWND (verursacht eckige Artefakte).
- Undurchsichtiger Glas-Hintergrund (`settings_styles.GLASS_BG`).
- Abgerundete Maske via `QPainterPath` + `setMask()`.
- QSS zentral in `settings_styles.py` – `QLineEdit` und `QComboBox` getrennt.

### Dialoge (Historie, URL, Willkommen)

- Rahmenlos, `WindowStaysOnTopHint`, dunkler Hintergrund.
- Schatten: `QGraphicsDropShadowEffect` (blur ~28, offset 6).
- Zentriert auf dem Bildschirm.

---

## Steuerelemente (QSS-Muster)

| Element | Datei | Regeln |
| --- | --- | --- |
| Toggle-Schalter | `toggle_switch.py` | 32×18 px, Indigo `#6366F1`, weißer Daumen – fest, nicht Windows-Akzent |
| QLineEdit | `settings_styles.py` | Padding `9px 12px`, Radius 8, Fokus → Accent-Border |
| QComboBox | `settings_styles.py` | Extra rechts für Drop-Down (32 px) |
| QPushButton | `settings_styles.py` | `GLASS_ELEVATED`, Hover → `ACCENT_DARK` |
| Tray-Menü | `tray_icon.py` | `SURFACE_HEX`, Border, Radius 6 |
| Stil-Chips | `expanded_pill_widget.py` | Accent wenn aktiv |

Neue Inputs: Stil aus `settings_styles.py` wiederverwenden, nicht inline QSS.

---

## Bewegung (`AnimationTokens`)

| Token | ms | Einsatz |
| --- | --- | --- |
| `FAST` | 140 | Opacity-Fade Island, Hover |
| `NORMAL` | 200 | State-Wechsel Pill-Größe |
| `SLOW` | 300 | — |
| `SUCCESS_DISPLAY_MS` | 2500 | Erfolgs-Anzeige vor Idle |

- **Emil-Kowalski-Prinzip:** Kurz, funktional, kein Dekor ohne Zweck.
- **Settle-Pulse:** Indigo-Glow beim Wechsel Recording → Processing (`play_settle_pulse`).
- **Waveform:** 25 ms Timer (~40 FPS), `WAVEFORM_STAGGER_MS = 20`.
- **Shimmer:** 16 ms Timer, Phase += 0.012.

`QPropertyAnimation.finished`: nur `SingleShotConnection` (Toast-Crash vermeiden).

---

## Windows-Integration

| Feature | Modul |
| --- | --- |
| Always-on-Top Overlay | `windows_overlay.py` |
| System-Akzentfarbe | `windows_accent.py` + `accent_theme.py` |
| Tray-Icon | `tray_icon.py` – minimalistische Kapsel, Indigo |
| Silent Update | `update_installer.py` – NSIS `/S` |

---

## Komponenten-Karte

```
src/ui/
├── design_tokens.py      ← Farben, Größen, Animation (HIER starten)
├── settings_styles.py    ← QSS Einstellungen
├── toggle_switch.py      ← Kompakte Toggle-Rows (Einstellungen)
├── dynamic_island.py     ← Trägerfenster, Hover, State-Animation
├── island_pill.py        ← Pill-Zustände
├── island_shimmer_indicator.py  ← Presence-Bar
├── expanded_pill_widget.py      ← Transkript + Stil-Chips
├── toast_notification.py        ← Status-Toasts
├── settings_panel.py            ← Einstellungs-Dialog
├── tray_icon.py                 ← System-Tray
├── mini_fab.py                  ← Optionaler schwebender Mic-Button
└── accent_theme.py              ← Dynamic Color
```

---

## Checkliste vor neuen UI-Änderungen

- [ ] Farben/Abstände aus `design_tokens.py` – keine neuen Hex-Werte in Widgets?
- [ ] QSS in dedizierter `*_styles.py` statt inline in Widgets?
- [ ] Datei bleibt unter 200 Zeilen (sonst Modul auslagern)?
- [ ] Island-Zustand über `IslandState` + `dynamic_island._on_state_changed`?
- [ ] Toast/Tray für wichtige Nutzer-Feedback (nicht nur Console)?
- [ ] Einstellungs-Dialog: keine DWM-Blur, Mask-Radius 16?
- [ ] Nutzer-Texte auf Deutsch?
- [ ] `AnimationTokens` statt magic numbers für Timer/Dauer?

---

## Referenzen

- Fluent Design 2: https://fluent2.microsoft.design/
- Emil Kowalski (Motion): https://emilkowal.ski/ui/animation
- Projekt-Kontext: `AGENTS.md`, `CONTEXT.md`, `prd.md`

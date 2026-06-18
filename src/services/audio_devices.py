"""
audio_devices.py
Hilfsfunktionen zur Abfrage und Auswahl von Audio-Eingabegeräten.
"""

import numpy as np

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

from src.services.config_service import config

SAMPLE_RATE = 16000


def list_input_devices() -> list[dict]:
    """Gibt alle verfügbaren Eingabegeräte mit Kanälen > 0 zurück."""
    if not SOUNDDEVICE_AVAILABLE:
        return []
    try:
        devices = sd.query_devices()
        return [
            {
                "id": i,
                "name": d["name"],
                "channels": d["max_input_channels"],
                "default_samplerate": int(d.get("default_samplerate") or 0),
            }
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]
    except Exception as e:
        print(f"[Audio] Fehler beim Abrufen der Geräte: {e}")
        return []


def resolve_input_device_id(device: str | int | None) -> int | None:
    """Löst Gerätenamen in eine eindeutige sounddevice-ID auf."""
    if device in (None, "", "default"):
        return None
    try:
        return int(device)
    except (TypeError, ValueError):
        pass
    devices = list_input_devices()
    if not devices:
        return None
    exact = [d for d in devices if d["name"] == device]
    if exact:
        return exact[-1]["id"]
    needle = str(device).lower()
    partial = [d for d in devices if needle in d["name"].lower()]
    if partial:
        return partial[-1]["id"]
    return None


def supported_input_sample_rates(device: int | None) -> list[int]:
    """Liefert probierte Abtastraten – bevorzugt 16 kHz, sonst Geräte-Default."""
    if not SOUNDDEVICE_AVAILABLE:
        return [SAMPLE_RATE]

    rates: list[int] = [SAMPLE_RATE]
    try:
        info = sd.query_devices(device, "input")
        default_sr = int(info.get("default_samplerate") or 0)
        if default_sr > 0 and default_sr not in rates:
            rates.append(default_sr)
    except Exception:
        pass

    for rate in (48000, 44100, 32000, 22050, 8000):
        if rate not in rates:
            rates.append(rate)

    supported: list[int] = []
    for rate in rates:
        try:
            sd.check_input_settings(
                device=device,
                channels=1,
                dtype="float32",
                samplerate=rate,
            )
            supported.append(rate)
        except Exception:
            continue
    return supported or [SAMPLE_RATE]


def resample_audio(
    audio: np.ndarray,
    src_rate: int,
    dst_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Konvertiert Mono-Float32-Audio auf die Zielrate (linear)."""
    flat = np.asarray(audio, dtype=np.float32).flatten()
    if flat.size == 0 or src_rate <= 0 or dst_rate <= 0 or src_rate == dst_rate:
        return flat
    new_len = max(1, int(round(flat.size * dst_rate / float(src_rate))))
    x_old = np.linspace(0.0, 1.0, flat.size, endpoint=False)
    x_new = np.linspace(0.0, 1.0, new_len, endpoint=False)
    return np.interp(x_new, x_old, flat).astype(np.float32)


def input_device_display_name(device_key: str | int | None) -> str:
    """Liefert einen lesbaren Gerätenamen für Config-Werte (ID, Name oder default)."""
    if device_key in (None, "", "default"):
        return "Standard-Mikrofon"
    for d in list_input_devices():
        if str(d["id"]) == str(device_key) or d["name"] == device_key:
            return d["name"]
    return str(device_key)


def get_next_input_device() -> str:
    """Ermittelt das nächste Eingabegerät zyklisch und aktualisiert die Config.

    Returns:
        Lesbarer Gerätename für UI/Toast (Config speichert ID oder "default").
    """
    devices = list_input_devices()
    if not devices:
        return "Standard-Mikrofon"

    device_names = [d["name"] for d in devices]
    options = ["default"] + device_names
    current = config.get_str("recording_device", "default")

    try:
        idx = options.index(current)
    except ValueError:
        for i, d in enumerate(devices):
            if str(d["id"]) == current or d["name"] == current:
                idx = i + 1
                break
        else:
            idx = 0

    next_option = options[(idx + 1) % len(options)]
    next_key = "default"
    if next_option != "default":
        for d in devices:
            if d["name"] == next_option:
                next_key = str(d["id"])
                break
    config.set("recording_device", next_key)
    config.save()
    display = input_device_display_name(next_key)
    print(f"[Audio] Device gewechselt: {display} (id={next_key})")
    return display

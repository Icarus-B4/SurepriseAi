# -*- mode: python ; coding: utf-8 -*-
# PyInstaller-Spec für SurepriseAi (Windows, onedir)
import sys
from pathlib import Path

import certifi

ROOT = Path(SPECPATH).resolve().parent
SRC = ROOT / "src"
_ICON = ROOT / "build" / "assets" / "app_icon.ico"
_ICON_DATAS = []
if (ROOT / "App_icon.png").is_file():
    _ICON_DATAS.append((str(ROOT / "App_icon.png"), "."))
if _ICON.is_file():
    _ICON_DATAS.append((str(_ICON), "."))

try:
    import PyQt6

    _PYQT6_ROOT = Path(PyQt6.__file__).resolve().parent
    _QT_MULTIMEDIA_PLUGINS = _PYQT6_ROOT / "Qt6" / "plugins" / "multimedia"
except Exception:
    _QT_MULTIMEDIA_PLUGINS = None

_EXTRA_DATAS = []
if _QT_MULTIMEDIA_PLUGINS and _QT_MULTIMEDIA_PLUGINS.is_dir():
    _EXTRA_DATAS.append(
        (str(_QT_MULTIMEDIA_PLUGINS), "PyQt6/Qt6/plugins/multimedia")
    )

block_cipher = None

a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "config.example.json"), "."),
        (str(ROOT / "LICENSE"), "."),
        (str(ROOT / "sounds"), "sounds"),
        (certifi.where(), "certifi"),
        *_ICON_DATAS,
        *_EXTRA_DATAS,
    ],
    hiddenimports=[
        "PyQt6.sip",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtMultimedia",
        "sounddevice",
        "numpy",
        "pyperclip",
        "pynput",
        "pynput.keyboard",
        "faster_whisper",
        "ctranslate2",
        "sherpa_onnx",
        "winocr",
        "PIL",
        "PIL.ImageGrab",
        "yt_dlp",
        "certifi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SurepriseAi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_ICON) if _ICON.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SurepriseAi",
)

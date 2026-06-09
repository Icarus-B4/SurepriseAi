# -*- mode: python ; coding: utf-8 -*-
# PyInstaller-Spec für SurepriseAi (Windows, onedir)
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
SRC = ROOT / "src"
_ICON = ROOT / "build" / "assets" / "app_icon.ico"

block_cipher = None

a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "config.example.json"), "."),
        (str(ROOT / "LICENSE"), "."),
    ],
    hiddenimports=[
        "PyQt6.sip",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
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

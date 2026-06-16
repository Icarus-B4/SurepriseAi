"""
generate_installer_assets.py
Erzeugt app_icon.ico aus App_icon.png (falls vorhanden) und Wizard-Grafiken.
"""

import shutil
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Pillow fehlt: pip install Pillow")

BUILD_DIR = Path(__file__).resolve().parent
ROOT = BUILD_DIR.parent
ASSETS = BUILD_DIR / "assets"
SOURCE_PNG = ROOT / "App_icon.png"
ASSETS.mkdir(parents=True, exist_ok=True)

# SurepriseAi Design-Tokens (Fallback-Icon)
BG = (13, 13, 15)
SURFACE = (26, 26, 30)
ACCENT = (99, 102, 241)
ACCENT_BRIGHT = (129, 140, 248)
TEXT = (245, 245, 247)
TEXT_MUTED = (161, 161, 170)
ACCENT_DARK = (79, 70, 229)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_gradient(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(BG[0] + ACCENT_DARK[0] * t * 0.35)
        g = int(BG[1] + ACCENT_DARK[1] * t * 0.35)
        b = int(BG[2] + ACCENT_DARK[2] * t * 0.35)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def create_wizard_large() -> None:
    """NSIS Sidebar: 164 × 314 px BMP."""
    w, h = 164, 314
    if SOURCE_PNG.is_file():
        src = Image.open(SOURCE_PNG).convert("RGBA")
        img = Image.new("RGB", (w, h), BG)
        thumb = src.resize((w - 24, w - 24), Image.Resampling.LANCZOS)
        img.paste(thumb, (12, 24), thumb)
        draw = ImageDraw.Draw(img)
        title = _font(17, bold=True)
        sub = _font(10)
        draw.text((12, 200), "SurepriseAi", font=title, fill=TEXT)
        draw.text((12, 224), "Voice Dictation", font=sub, fill=TEXT_MUTED)
        img.save(ASSETS / "wizard_large.bmp", "BMP")
        return

    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    _draw_gradient(draw, w, h)
    cx, cy = w // 2, 118
    draw.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=ACCENT)
    draw.ellipse([cx - 14, cy - 22, cx + 14, cy + 8], fill=TEXT)
    draw.rectangle([cx - 5, cy + 8, cx + 5, cy + 18], fill=TEXT)
    title = _font(17, bold=True)
    sub = _font(10)
    draw.text((12, 200), "SurepriseAi", font=title, fill=TEXT)
    draw.text((12, 224), "Voice Dictation", font=sub, fill=TEXT_MUTED)
    draw.text((12, 242), "Lokal · Windows", font=sub, fill=ACCENT_BRIGHT)
    img.save(ASSETS / "wizard_large.bmp", "BMP")


def create_wizard_small() -> None:
    """NSIS Kopfzeile: 55 × 55 px BMP."""
    size = 55
    if SOURCE_PNG.is_file():
        src = Image.open(SOURCE_PNG).convert("RGBA")
        thumb = src.resize((size, size), Image.Resampling.LANCZOS)
        thumb.save(ASSETS / "wizard_small.bmp", "BMP")
        return

    img = Image.new("RGB", (size, size), SURFACE)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, size - 3, size - 3], radius=10, fill=ACCENT)
    cx = size // 2
    draw.ellipse([cx - 10, cx - 16, cx + 10, cx + 2], fill=TEXT)
    draw.rectangle([cx - 4, cx + 2, cx + 4, cx + 10], fill=TEXT)
    img.save(ASSETS / "wizard_small.bmp", "BMP")


def _synthetic_icon_images(sizes: list[int]) -> list[Image.Image]:
    """sizes muss absteigend sein (größte zuerst)."""
    images: list[Image.Image] = []
    for s in sizes:
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pad = max(1, s // 16)
        draw.rounded_rectangle(
            [pad, pad, s - pad - 1, s - pad - 1],
            radius=max(2, s // 5),
            fill=ACCENT + (255,),
        )
        cx = s // 2
        mic_h = max(2, s // 4)
        mic_w = max(2, s // 6)
        draw.ellipse(
            [cx - mic_w, cx - mic_h - 1, cx + mic_w, cx + 1],
            fill=TEXT + (255,),
        )
        draw.rectangle(
            [cx - mic_w // 2, cx + 1, cx + mic_w // 2, cx + mic_h],
            fill=TEXT + (255,),
        )
        images.append(img)
    return images


def create_app_icon() -> None:
    """Mehrgrößen-ICO für Setup und EXE – aus App_icon.png wenn vorhanden."""
    # Größte Auflösung zuerst – Pillow nutzt images[0] als Primärframe für Windows/NSIS.
    sizes = [256, 128, 64, 48, 32, 24, 16]
    images: list[Image.Image]

    if SOURCE_PNG.is_file():
        src = Image.open(SOURCE_PNG).convert("RGBA")
        images = [
            src.resize((s, s), Image.Resampling.LANCZOS)
            for s in sizes
        ]
        print(f"[Installer] Icon aus {SOURCE_PNG.name} ({sizes[0]}–{sizes[-1]} px)")
    else:
        images = _synthetic_icon_images(sizes)
        print("[Installer] App_icon.png fehlt – Fallback-Icon generiert")

    ico_path = ASSETS / "app_icon.ico"
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(im.width, im.height) for im in images],
        append_images=images[1:],
    )
    if ico_path.stat().st_size < 10_000:
        raise SystemExit(
            f"ICO zu klein ({ico_path.stat().st_size} B) – Mehrgrößen-Export fehlgeschlagen."
        )
    shutil.copy2(ico_path, ASSETS / "surepriseAi.ico")


def main() -> None:
    create_wizard_large()
    create_wizard_small()
    create_app_icon()
    print(f"[Installer] Assets erzeugt in {ASSETS}")


if __name__ == "__main__":
    main()

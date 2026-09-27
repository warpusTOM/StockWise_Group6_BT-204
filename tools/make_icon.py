"""Generate the StockWise app icon (assets/icon.ico) with Pillow.

    python tools/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "icon.ico"


def make_icon(path: Path) -> None:
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # rounded-square background (brand blue)
    d.rounded_rectangle([8, 8, size - 8, size - 8], radius=48, fill="#1f6aa5")
    # ascending stock bars
    for x0, y0, x1, y1 in [(56, 150, 96, 200), (106, 120, 146, 200), (156, 90, 196, 200)]:
        d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill="white")
    # trend arrow
    d.line([(60, 130), (110, 100), (160, 70), (200, 44)], fill="#7fe08c", width=14, joint="curve")
    d.polygon([(200, 44), (172, 42), (196, 72)], fill="#7fe08c")

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"icon written -> {path}")


if __name__ == "__main__":
    make_icon(OUT)

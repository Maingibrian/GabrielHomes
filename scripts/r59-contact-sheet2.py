#!/usr/bin/env python3
"""r59: contact sheet of house+apartment pools (minus used house-04)."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

MEDIA = Path("/home/z/my-project/gabriel-homes/media/demo-photos")
files = sorted(MEDIA.glob("house/*.jpg")) + sorted(MEDIA.glob("apartment/*.jpg"))
files = [f for f in files if f.name != "house-04.jpg"]

TILE, COLS = 300, 5
rows = (len(files) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * TILE, rows * (TILE + 26)), "#222")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf", 20)
except OSError:
    font = ImageFont.load_default()

for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    im.thumbnail((TILE, TILE))
    x = (i % COLS) * TILE + (TILE - im.width) // 2
    y = (i // COLS) * (TILE + 26) + 26
    sheet.paste(im, (x, y))
    draw.text(((i % COLS) * TILE + 6, (i // COLS) * (TILE + 26) + 2),
              f"{i+1}: {f.parent.name}/{f.name}", fill="#fff", font=font)

sheet.save("/tmp/pool-sheet2.jpg", quality=72)
print("tiles:", len(files), "->", sheet.size)

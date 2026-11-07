#!/usr/bin/env python3
"""r59: numbered contact sheet of house+interior pools for VLM picking."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

MEDIA = Path("/home/z/my-project/gabriel-homes/media/demo-photos")
files = sorted(MEDIA.glob("house/*.jpg")) + sorted(MEDIA.glob("interior/*.jpg"))

TILE = 300
COLS = 5
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
    label = f"{i+1}: {f.parent.name}/{f.name}"
    draw.text(((i % COLS) * TILE + 6, (i // COLS) * (TILE + 26) + 2),
              label, fill="#fff", font=font)

sheet.save("/tmp/pool-sheet.jpg", quality=72)
print("tiles:", len(files), "->", sheet.size)

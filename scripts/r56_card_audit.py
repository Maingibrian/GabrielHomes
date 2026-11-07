#!/usr/bin/env python3
"""r56 — audit the ~10 visible card images for baked-in text/watermarks."""
from PIL import Image, ImageDraw
from pathlib import Path
import json

GH = Path("/home/z/my-project/gabriel-homes")
raw = json.load(open("/tmp/render/card-imgs.json"))
if isinstance(raw, str):
    raw = json.loads(raw)
urls = sorted(set(raw))
names = [u.split("/")[-1] for u in urls]
print(f"{len(names)} unique card images")

TH, LABEL_H, COLS = 300, 18, 5
rows = (len(names) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * TH, rows * (TH + LABEL_H) + 26), (18, 18, 18))
d = ImageDraw.Draw(sheet)
d.text((8, 6), "VISIBLE CARD IMAGES (home page)", fill=(255, 210, 120))
for i, name in enumerate(names):
    f = GH / "media" / "property-images" / "2026" / "11" / name
    try:
        im = Image.open(f).convert("RGB")
    except Exception as e:
        print("MISSING", name, e)
        continue
    im.thumbnail((TH - 6, TH - 6))
    x = (i % COLS) * TH + 3
    y = (i // COLS) * (TH + LABEL_H) + 26
    sheet.paste(im, (x, y))
    d.text((x + 4, y + TH - LABEL_H), name[:34], fill=(255, 255, 150))
sheet.save("/tmp/render/r56-card-audit.png", optimize=True)
print("sheet saved", sheet.size)

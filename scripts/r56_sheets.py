#!/usr/bin/env python3
"""r56 — labeled contact sheets for hero/about image selection."""
from PIL import Image, ImageDraw
from pathlib import Path

GH = Path("/home/z/my-project/gabriel-homes")
OUT = Path("/home/z/my-project/download/preview-screenshots")
TH = 230
LABEL_H = 16
COLS = 6

def sheet(files, title, dest):
    rows = (len(files) + COLS - 1) // COLS
    w = COLS * TH
    h = rows * (TH + LABEL_H) + 28
    img = Image.new("RGB", (w, h), (18, 18, 18))
    d = ImageDraw.Draw(img)
    d.text((8, 6), title, fill=(255, 210, 120))
    for i, f in enumerate(files):
        try:
            im = Image.open(f).convert("RGB")
        except Exception:
            continue
        im.thumbnail((TH - 6, TH - 6))
        x = (i % COLS) * TH + 3
        y = (i // COLS) * (TH + LABEL_H) + 28
        img.paste(im, (x, y))
        d.text((x + 4, y + TH - LABEL_H), f.name[:26], fill=(255, 255, 150))
    img.save(OUT / dest, optimize=True)
    print(dest, img.size, f"{len(files)} files")

real = GH / "static" / "img" / "real"
media = GH / "media" / "demo-photos"

# sheet 1: current hero slides + real-0X about photos
sheet(sorted(real.glob("hero-slide-*.webp")) + sorted(real.glob("real-*.jpg")),
      "CURRENT ASSETS: hero-slide-*.webp (live hero) + real-*.jpg (about page)",
      "r56-sheet-current.png")

# sheet 2: house pool (exteriors)
sheet(sorted(media.glob("house/*.jpg")),
      "POOL: house (exterior candidates)",
      "r56-sheet-house.png")

# sheet 3: interior + apartment pools (room candidates)
sheet(sorted(media.glob("interior/*.jpg")) + sorted(media.glob("apartment/*.jpg")),
      "POOL: interior + apartment (room candidates)",
      "r56-sheet-rooms.png")

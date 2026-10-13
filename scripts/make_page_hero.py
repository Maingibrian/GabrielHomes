#!/usr/bin/env python3
"""Build static/img/real/page-hero.jpg from a REAL listing photo.

Replaces the AI-generated cliff-villa render (hero-bg.jpg) that the user
kept calling out as "not a real image". Source: real-01-kitchen-island.jpg
(bright open-plan interior, not used by the home slideshow).

Output: 1600x900 centre-crop, quality 85 — wide enough for the .page-hero
background at any viewport, small enough to stay lean in update zips.
"""
from PIL import Image
from pathlib import Path

SRC = Path("/home/z/my-project/gabriel_homes/static/img/real/real-01-kitchen-island.jpg")
OUT = Path("/home/z/my-project/gabriel_homes/static/img/real/page-hero.jpg")

TARGET_W, TARGET_H = 1600, 900  # 16:9-ish wide crop

img = Image.open(SRC).convert("RGB")
w, h = img.size
print(f"source: {w}x{h}")

# Centre-crop to target aspect, then resize.
target_ar = TARGET_W / TARGET_H
ar = w / h
if ar > target_ar:  # too wide -> trim sides
    new_w = int(h * target_ar)
    x0 = (w - new_w) // 2
    box = (x0, 0, x0 + new_w, h)
else:  # too tall -> trim top/bottom (bias slightly up to keep ceiling space)
    new_h = int(w / target_ar)
    y0 = max(0, int((h - new_h) * 0.40))
    box = (0, y0, w, y0 + new_h)

img = img.crop(box).resize((TARGET_W, TARGET_H), Image.LANCZOS)
img.save(OUT, "JPEG", quality=85, optimize=True, progressive=True)
print(f"wrote {OUT}: {TARGET_W}x{TARGET_H}, {OUT.stat().st_size/1024:.0f} KB")

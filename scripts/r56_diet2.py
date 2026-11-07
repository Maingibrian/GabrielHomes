#!/usr/bin/env python3
"""r56 diet round 2 — fit under 4,191,687 with headroom."""
from PIL import Image
from pathlib import Path

GH = Path("/home/z/my-project/gabriel-homes")
REAL = GH / "static" / "img" / "real"
POOL = GH / "media" / "demo-photos"
BASELINE = 4_191_687

def load(src):
    return Image.open(src).convert("RGB")

def save_webp(src, dest, width, q):
    im = load(src); im.thumbnail((width, width), Image.LANCZOS)
    im.save(REAL / dest, "WEBP", quality=q, method=6)
    return (REAL / dest).stat().st_size

def save_jpg(src, dest, width, q):
    im = load(src); im.thumbnail((width, width), Image.LANCZOS)
    im.save(REAL / dest, "JPEG", quality=q, optimize=True, progressive=True)
    return (REAL / dest).stat().st_size

jobs = [
    # (kind, src, dest, width, q)
    ("webp", POOL / "house/house-13.jpg", "hero-slide-1.webp", 1300, 64),
    ("webp", POOL / "house/house-03.jpg", "hero-slide-2.webp", 1300, 64),
    ("webp", POOL / "interior/interior-22.jpg", "hero-slide-3.webp", 1100, 66),
    ("webp", POOL / "apartment/apartment-11.jpg", "hero-slide-4.webp", 1200, 64),
    ("jpg",  POOL / "house/house-13.jpg", "hero-poster.jpg", 1150, 64),
    ("jpg",  POOL / "house/house-20.jpg", "real-06-living-terrace.jpg", 950, 70),
    ("jpg",  POOL / "house/house-15.jpg", "real-09-golden-hour.jpg", 850, 70),
    ("jpg",  POOL / "apartment/apartment-18.jpg", "real-10-sea-light.jpg", 850, 70),
    ("jpg",  POOL / "interior/interior-05.jpg", "real-11-slow-mornings.jpg", 850, 70),
    # existing large assets, lightly dieted (never displayed at full res)
    ("jpg",  REAL / "real-08-aerial.jpg", "real-08-aerial.jpg", 1100, 64),
    ("jpg",  REAL / "cta-balcony.jpg", "cta-balcony.jpg", 1100, 68),
    ("jpg",  REAL / "page-hero.jpg", "page-hero.jpg", 1100, 68),
    ("jpg",  REAL / "real-05-dining.jpg", "real-05-dining.jpg", 1100, 70),
]
for kind, src, dest, w, q in jobs:
    fn = save_webp if kind == "webp" else save_jpg
    n = fn(src, dest, w, q)
    print(f"{dest:26s} {n:>7,} bytes  (w={w} q={q})")

total = sum(p.stat().st_size for p in (GH / "static").rglob("*")
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif"))
delta = BASELINE - total
print(f"\nTOTAL {total:,} / baseline {BASELINE:,}  "
      f"({'UNDER by %.0f KB' % (delta / 1024) if delta >= 0 else 'OVER by %.0f KB' % (-delta / 1024)})")

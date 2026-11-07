#!/usr/bin/env python3
"""r56 pass 2 — final image swaps (vision-driven):
  real-06-living-terrace.jpg <- interior-23 (single bright restful room;
      the house-20 pick was a mismatched day/dusk diptych)
  page-hero.jpg              <- house-03 (sunlit white arches; the old
      dim interior contributed no coastal identity on every page-hero)
Budget-checked against F3 (4,191,687).
"""
from PIL import Image
from pathlib import Path

GH = Path("/home/z/my-project/gabriel-homes")
REAL = GH / "static" / "img" / "real"
POOL = GH / "media" / "demo-photos"
BASELINE = 4_191_687

def save_jpg(src, dest, width, q):
    im = Image.open(src).convert("RGB")
    im.thumbnail((width, width), Image.LANCZOS)
    im.save(REAL / dest, "JPEG", quality=q, optimize=True, progressive=True)
    return (REAL / dest).stat().st_size

n = save_jpg(POOL / "interior/interior-23.jpg", "real-06-living-terrace.jpg", 950, 70)
print(f"real-06-living-terrace.jpg  {n:,} bytes")
n = save_jpg(POOL / "house/house-03.jpg", "page-hero.jpg", 1100, 70)
print(f"page-hero.jpg               {n:,} bytes")

total = sum(p.stat().st_size for p in (GH / "static").rglob("*")
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif"))
delta = BASELINE - total
print(f"TOTAL {total:,} / baseline {BASELINE:,}  "
      f"({'UNDER by %.0f KB' % (delta / 1024) if delta >= 0 else 'OVER by %.0f KB' % (-delta / 1024)})")

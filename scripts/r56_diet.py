#!/usr/bin/env python3
"""r56 — image diet: fit the new sunlit set under the F3 ratchet
(IMAGE_BYTES_BASELINE = 4_191_687; every file <= 250KB).

Displays (device-pixel aware):
  hero slides   ~1440x810 CSS fullscreen -> 1400px webp
  hero-poster   video poster only        -> 1280px jpg
  real-06       story figure col <=520px -> 1000px jpg
  real-09/10/11 CTA strip <=454px device -> 900px jpg
  real-08       fallback bento bg        -> 1280px jpg (was 244KB)
"""
from PIL import Image
from pathlib import Path

GH = Path("/home/z/my-project/gabriel-homes")
REAL = GH / "static" / "img" / "real"
BASELINE = 4_191_687

def load(src):
    return Image.open(src).convert("RGB")

def save_webp(im, dest, width, q):
    im = im.copy(); im.thumbnail((width, width), Image.LANCZOS)
    im.save(dest, "WEBP", quality=q, method=6)
    return dest.stat().st_size

def save_jpg(im, dest, width, q):
    im = im.copy(); im.thumbnail((width, width), Image.LANCZOS)
    im.save(dest, "JPEG", quality=q, optimize=True, progressive=True)
    return dest.stat().st_size

# hero slides (re-encode from the pool originals, warm grade kept simple)
POOL = GH / "media" / "demo-photos"
jobs_webp = [  # (pool file, dest, width, quality)
    ("house/house-13.jpg", "hero-slide-1.webp", 1400, 70),
    ("house/house-03.jpg", "hero-slide-2.webp", 1400, 70),
    ("interior/interior-22.jpg", "hero-slide-3.webp", 1200, 72),
    ("apartment/apartment-11.jpg", "hero-slide-4.webp", 1300, 70),
]
for src, dest, w, q in jobs_webp:
    n = save_webp(load(POOL / src), REAL / dest, w, q)
    print(f"{dest:26s} {n:>7,} bytes  (w={w} q={q})")

# poster from slide-1
n = save_jpg(load(POOL / "house/house-13.jpg"), REAL / "hero-poster.jpg", 1280, 68)
print(f"{'hero-poster.jpg':26s} {n:>7,} bytes")

# about photos
jobs_jpg = [
    ("house/house-20.jpg", "real-06-living-terrace.jpg", 1000, 72),
    ("house/house-15.jpg", "real-09-golden-hour.jpg", 900, 72),
    ("apartment/apartment-18.jpg", "real-10-sea-light.jpg", 900, 74),
    ("interior/interior-05.jpg", "real-11-slow-mornings.jpg", 900, 74),
    (REAL / "real-08-aerial.jpg", "real-08-aerial.jpg", 1280, 70),  # re-encode own
]
for src, dest, w, q in jobs_jpg:
    src_path = src if isinstance(src, Path) else POOL / src
    n = save_jpg(load(src_path), REAL / dest, w, q)
    print(f"{dest:26s} {n:>7,} bytes  (w={w} q={q})")

total = sum(p.stat().st_size for p in (GH / "static").rglob("*")
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif"))
print(f"\nTOTAL {total:,} / baseline {BASELINE:,}  "
      f"({'UNDER by %d KB' % ((BASELINE - total) // 1024) if total <= BASELINE else 'OVER by %d KB' % ((total - BASELINE) // 1024)})")

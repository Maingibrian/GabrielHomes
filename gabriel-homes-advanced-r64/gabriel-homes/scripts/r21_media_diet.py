"""r21 — F3 media diet conversions.

1. Search market-filter cards (green-apartments, mombasa-villa,
   pool-villa-night): downscale 1600px -> 900px wide, convert to WebP q82,
   delete the JPGs (search.html is updated to .webp separately).
2. Home hero slides 1-4 (1920x1080): WebP q85 at native size (full-bleed
   LCP art), delete the JPGs (home.html updated separately).
3. Seed-source stock images (nyali-apartment, ocean-bedroom): re-encode
   JPEG q82 downscaled (1600->1200 w / 2400->1800 h) — format kept because
   seed_demo.py / seed_mombasa_showcase.py copy these files into listing
   media at seed time (documented, D-LOOP-21b).
Prints the post-diet exact byte total for the ratchet constant.
"""
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
IMG = REPO / "static" / "img"


def to_webp(src: Path, dst: Path, max_w: int, quality: int):
    im = Image.open(src).convert("RGB")
    if im.width > max_w:
        h = round(im.height * max_w / im.width)
        im = im.resize((max_w, h), Image.LANCZOS)
    im.save(dst, "WEBP", quality=quality, method=6)
    print(f"  webp {src.name} {src.stat().st_size//1024}KB -> "
          f"{dst.name} {dst.stat().st_size//1024}KB ({im.width}x{im.height})")


def reencode_jpg(src: Path, max_w: int, quality: int):
    im = Image.open(src).convert("RGB")
    if im.width > max_w:
        h = round(im.height * max_w / im.width)
        im = im.resize((max_w, h), Image.LANCZOS)
    im.save(src, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"  jpg  {src.name} re-encoded -> {src.stat().st_size//1024}KB "
          f"({im.width}x{im.height})")


print("1. market-filter cards -> WebP 900w q82")
for name in ("green-apartments", "mombasa-villa", "pool-villa-night"):
    src = IMG / "stock" / f"{name}.jpg"
    dst = IMG / "stock" / f"{name}.webp"
    to_webp(src, dst, 900, 82)

print("2. hero slides -> WebP q85 native")
for n in (1, 2, 3, 4):
    src = IMG / "real" / f"hero-slide-{n}.jpg"
    dst = IMG / "real" / f"hero-slide-{n}.webp"
    to_webp(src, dst, 1920, 85)

print("3. seed sources re-encoded (format kept)")
reencode_jpg(IMG / "stock" / "nyali-apartment.jpg", 1200, 82)
reencode_jpg(IMG / "stock" / "ocean-bedroom.jpg", 1200, 82)

print("4. delete converted-away JPGs")
for name in ("green-apartments", "mombasa-villa", "pool-villa-night"):
    (IMG / "stock" / f"{name}.jpg").unlink()
    print(f"  deleted stock/{name}.jpg")
for n in (1, 2, 3, 4):
    (IMG / "real" / f"hero-slide-{n}.jpg").unlink()
    print(f"  deleted real/hero-slide-{n}.jpg")

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
total = sum(p.stat().st_size for p in (REPO / "static").rglob("*")
            if p.suffix.lower() in IMG_EXTS and p.is_file())
print(f"\nPOST-DIET EXACT BYTES: {total}")
big = [(p.stat().st_size, p) for p in (REPO / "static").rglob("*")
       if p.suffix.lower() in IMG_EXTS and p.stat().st_size > 250 * 1024]
print("offenders >250KB remaining:", big or "none")

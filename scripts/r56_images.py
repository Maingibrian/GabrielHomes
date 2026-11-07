#!/usr/bin/env python3
"""r56 — install the sunlit coastal image set (vision-curated picks).

Hero:    house-13 (Swahili villa+pool) -> hero-slide-1.webp
         house-03 (sunlit white arches) -> hero-slide-2.webp
         interior-22 (vaulted daylight) -> hero-slide-3.webp
         apartment-11 (living->sea)     -> hero-slide-4.webp
Poster:  slide-1 -> hero-poster.jpg
About:   house-20 (veranda seating)     -> real-06-living-terrace.jpg (overwrite)
         house-15 (cream villa golden)  -> real-09-golden-hour.jpg
         apartment-18 (airy wood living)-> real-10-sea-light.jpg
         interior-05 (sunlit bedroom)   -> real-11-slow-mornings.jpg
"""
from PIL import Image, ImageEnhance
from pathlib import Path

GH = Path("/home/z/my-project/gabriel-homes")
POOL = GH / "media" / "demo-photos"
REAL = GH / "static" / "img" / "real"

def warm(im, sat=1.04, bright=1.03):
    """Gentle shared coastal grade: slightly warm, slightly brighter."""
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Brightness(im).enhance(bright)
    return im

def crop_to(im, ratio):
    w, h = im.size
    target = ratio
    if w / h > target:  # too wide
        nw = int(h * target)
        x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = int(w / target)
    y = max(0, int((h - nh) * 0.42))  # bias toward upper-middle (horizons)
    return im.crop((0, y, w, y + nh))

def save_hero(src, dest_webp, poster=False):
    im = Image.open(src).convert("RGB")
    im = crop_to(im, 16 / 9)
    im.thumbnail((1920, 1920), Image.LANCZOS)
    im = warm(im)
    im.save(REAL / dest_webp, "WEBP", quality=78, method=6)
    if poster:
        im.save(REAL / "hero-poster.jpg", "JPEG", quality=82, optimize=True)
    print(f"{dest_webp}  <- {src.name}  {im.size}")

def save_room(src, dest, ratio=3 / 2, width=1200):
    im = Image.open(src).convert("RGB")
    im = crop_to(im, ratio)
    im.thumbnail((width, width), Image.LANCZOS)
    im = warm(im)
    im.save(REAL / dest, "JPEG", quality=82, optimize=True)
    print(f"{dest}  <- {src.name}  {im.size}")

# hero slides + poster
save_hero(POOL / "house" / "house-13.jpg", "hero-slide-1.webp", poster=True)
save_hero(POOL / "house" / "house-03.jpg", "hero-slide-2.webp")
save_hero(POOL / "interior" / "interior-22.jpg", "hero-slide-3.webp")
save_hero(POOL / "apartment" / "apartment-11.jpg", "hero-slide-4.webp")

# about story figure (overwrite — a veranda IS a living terrace, name stays honest)
save_room(POOL / "house" / "house-20.jpg", "real-06-living-terrace.jpg")

# about CTA strip
save_room(POOL / "house" / "house-15.jpg", "real-09-golden-hour.jpg")
save_room(POOL / "apartment" / "apartment-18.jpg", "real-10-sea-light.jpg")
save_room(POOL / "interior" / "interior-05.jpg", "real-11-slow-mornings.jpg")

"""Build the home-page hero slideshow slides from the real home photos.

Picks the four strongest frames of the owner's Nyali beachfront set
(kitchen island, evening dining, living terrace, bright living room —
per docs/HOME-REDESIGN.md §2.1), center-crops each to 16:9 and renders
1920x1080 JPEGs (LANCZOS upscale + gentle sharpen, q82) into
static/img/real/hero-slide-NN.jpg.

Excluded on purpose: real-08 (construction-site aerial), real-07 (raw
concrete slab over the balcony), real-04 (blank wall behind bed).

Idempotent — safe to re-run; output overwrites in place.
"""
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "static" / "img" / "real"
OUT = SRC

# (source file, output name, focus bias 0..1 for vertical crop center)
PICKS = [
    ("real-01-kitchen-island.jpg", "hero-slide-1.jpg", 0.5),
    ("real-06-living-terrace.jpg", "hero-slide-2.jpg", 0.55),
    ("real-05-dining.jpg", "hero-slide-3.jpg", 0.5),
    ("real-02-living.jpg", "hero-slide-4.jpg", 0.5),
]

TARGET_W, TARGET_H = 1920, 1080
QUALITY = 82
# Every slide sits under the same dark scrim, so bright interiors must be
# pulled down to a common exposure or white-heavy frames (terrace/living)
# wash out the headline. 0.47 mean luminance keeps the photo clearly
# visible while the cream headline keeps >4.5:1 contrast.
TARGET_MEAN_LUM = 0.47
MIN_BRIGHTEN = 0.75  # never brighten beyond this (keeps mood)


def make(src_path: Path, out_path: Path, focus: float) -> None:
    im = Image.open(src_path).convert("RGB")
    w, h = im.size

    # Center-crop to 16:9 with a vertical focus bias.
    target_ratio = TARGET_W / TARGET_H
    if w / h > target_ratio:  # too wide -> trim sides
        new_w = int(h * target_ratio)
        x0 = (w - new_w) // 2
        box = (x0, 0, x0 + new_w, h)
    else:  # too tall -> trim top/bottom around focus
        new_h = int(w / target_ratio)
        cy = int(h * focus)
        y0 = max(0, min(h - new_h, cy - new_h // 2))
        box = (0, y0, w, y0 + new_h)
    im = im.crop(box)

    # Upscale to 1920 wide (sources are 1200x800) + gentle sharpen.
    im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=48, threshold=2))

    # Normalize exposure so all four frames sit under the scrim equally.
    lum = ImageStat.Stat(im.convert("L")).mean[0] / 255.0
    factor = TARGET_MEAN_LUM / lum if lum > 0 else 1.0
    if factor < 1.0:
        factor = max(factor, 0.62)  # never crush darker than 0.62x
        im = ImageEnhance.Brightness(im).enhance(factor)
        im = ImageEnhance.Contrast(im).enhance(1.04)  # win back some pop
    elif factor > 1.0:
        im = ImageEnhance.Brightness(im).enhance(min(factor, 1.0 / MIN_BRIGHTEN))

    im.save(out_path, format="JPEG", quality=QUALITY, optimize=True,
            progressive=True)
    kb = out_path.stat().st_size // 1024
    print(f"  {out_path.name}  {kb} KB  (mean lum {lum:.2f} -> x{factor:.2f})")


def main() -> None:
    print("Building hero slideshow slides:")
    for src_name, out_name, focus in PICKS:
        make(SRC / src_name, OUT / out_name, focus)
    total = sum((OUT / n).stat().st_size for _, n, _ in PICKS)
    print(f"Total: {total // 1024} KB for 4 slides")


if __name__ == "__main__":
    main()

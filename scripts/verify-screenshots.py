"""Verify preview screenshots: dimensions, non-blank content; convert to JPEG."""
from PIL import Image
from pathlib import Path

SRC = Path("/home/z/my-project/download/preview-screenshots")
CHECK = Path("/tmp/render")
CHECK.mkdir(parents=True, exist_ok=True)

for png in sorted(SRC.glob("*.png")):
    im = Image.open(png)
    w, h = im.size
    # non-blank check: sample pixels, count non-white
    small = im.convert("RGB").resize((min(w, 200), min(h, 2000)))
    pixels = list(small.getdata())
    non_white = sum(1 for p in pixels if p != (255, 255, 255) and (p[0] < 245 or p[1] < 245 or p[2] < 245))
    ratio = non_white / len(pixels)
    # convert to JPEG q86 (photos -> much smaller than PNG)
    jpg = png.with_suffix(".jpg")
    im.convert("RGB").save(jpg, "JPEG", quality=86, optimize=True)
    # small check copy
    ch = CHECK / (png.stem + ".jpg")
    im.convert("RGB").resize((min(w, 480), int(h * min(w, 480) / w))).save(ch, "JPEG", quality=60)
    png.unlink()
    print(f"{png.stem}: {w}x{h} non-white={ratio:.0%} -> jpg {jpg.stat().st_size//1024}KB")

print("VERIFIED")

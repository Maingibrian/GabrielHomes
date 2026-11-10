"""Generate a placeholder hero background for the home page.

Phase 2 ships with a Pillow-generated warm architectural gradient
placeholder. Phase 6 (per WORK.md §10.7) replaces this with the owner's
own photography.
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "hero-bg.jpg"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 2400, 1600

# Warm sunset gradient (cream -> clay -> brown -> espresso)
stops = [
    (0.0,  (250, 248, 244)),   # cream
    (0.35, (214, 174, 138)),   # warm sand
    (0.6,  (166, 106, 77)),    # clay
    (0.85, (90, 64, 50)),      # brown
    (1.0,  (42, 33, 28)),      # espresso
]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def color_at(t):
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1:
            local = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return lerp(c0, c1, local)
    return stops[-1][1]


img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)
# Vertical gradient
for y in range(H):
    draw.line([(0, y), (W, y)], fill=color_at(y / H))

# Add a soft "sun" highlight
cx, cy, r = int(W * 0.78), int(H * 0.42), int(W * 0.18)
for ry in range(-r, r):
    yy = cy + ry
    if yy < 0 or yy >= H:
        continue
    half = int((r * r - ry * ry) ** 0.5)
    for rx in range(-half, half):
        xx = cx + rx
        if 0 <= xx < W:
            d = (rx * rx + ry * ry) ** 0.5 / r
            falloff = max(0.0, 1.0 - d) ** 2
            base = img.getpixel((xx, yy))
            new = tuple(min(255, int(base[i] + (255 - base[i]) * falloff * 0.35)) for i in range(3))
            img.putpixel((xx, yy), new)

# Architectural silhouette: a simple building horizon along the bottom third
buildings = [
    (0.00, 0.78, 0.05),
    (0.05, 0.82, 0.04),
    (0.09, 0.74, 0.06),
    (0.15, 0.86, 0.05),
    (0.20, 0.78, 0.08),
    (0.28, 0.84, 0.05),
    (0.33, 0.76, 0.07),
    (0.40, 0.88, 0.06),
    (0.46, 0.80, 0.05),
    (0.51, 0.86, 0.04),
    (0.55, 0.78, 0.06),
    (0.61, 0.82, 0.05),
    (0.66, 0.76, 0.07),
    (0.73, 0.84, 0.05),
    (0.78, 0.80, 0.06),
    (0.84, 0.86, 0.05),
    (0.89, 0.78, 0.07),
    (0.96, 0.82, 0.04),
]
for x0, y0, w in buildings:
    x1 = x0 + w
    px0 = int(x0 * W)
    px1 = int(x1 * W)
    py0 = int(y0 * H)
    py1 = H
    draw.rectangle([(px0, py0), (px1, py1)], fill=(42, 33, 28))

img.save(OUT, format="JPEG", quality=82, optimize=True)
print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")

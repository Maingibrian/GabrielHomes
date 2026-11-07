#!/usr/bin/env python3
"""r56 — WCAG contrast probe for the hero headline over the new bright slides.

Crops the title region from the full-page screenshot (1440px viewport),
separates cream text pixels from background photo+scrim pixels, and
computes the contrast ratio against the WORST (brightest) background
band the text sits on (95th percentile of background luminance).
"""
from PIL import Image
from pathlib import Path

SHOT = Path("/home/z/my-project/download/preview-screenshots/r56-after-home-desktop.png")
# title rect from the DOM probe: left=118, top=209, w=727, h=85 (1440x900)
# pad vertically a little to catch the full glyph height + local bg
im = Image.open(SHOT).convert("RGB")
crop = im.crop((110, 200, 860, 300))
px = list(crop.getdata())

def rel_lum(c):
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c[0]), ch(c[1]), ch(c[2]))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

lums = [rel_lum(c) for c in px]
# text pixels: brightest cluster (cream ~0.9+); background: the rest
text_lums = sorted([l for l in lums if l > 0.55])
bg_lums = sorted([l for l in lums if l <= 0.55])

L_text = text_lums[len(text_lums) // 2] if text_lums else 0.95
# worst-case background: 95th percentile (brightest band under text)
p95 = bg_lums[int(len(bg_lums) * 0.95)] if bg_lums else 0
p50 = bg_lums[len(bg_lums) // 2] if bg_lums else 0

def ratio(a, b):
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)

print(f"text pixels: {len(text_lums):,}  bg pixels: {len(bg_lums):,}")
print(f"text median luminance : {L_text:.3f}")
print(f"bg median luminance   : {p50:.3f}  -> contrast {ratio(L_text, p50):.2f}:1")
print(f"bg p95 (worst band)   : {p95:.3f}  -> contrast {ratio(L_text, p95):.2f}:1")

# where does the worst band sit? scan columns
w, h = crop.size
col_p95 = []
for x in range(0, w, 10):
    col = [rel_lum(crop.getpixel((x, y))) for y in range(0, h, 4)]
    col = sorted([l for l in col if l <= 0.55]) or [0]
    col_p95.append((x + 110, col[int(len(col) * 0.95)]))
worst = sorted(col_p95, key=lambda t: -t[1])[:5]
print("brightest columns (x, lum):", [(x, round(l, 2)) for x, l in worst])

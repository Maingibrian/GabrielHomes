"""r24 — process the owner-supplied founder portrait (Gabriel Omulu).

Source: /home/z/my-project/upload/pasted_image_1793887773280.png
        (1145x1374 studio portrait, owner upload 2026-11-05)
Output: static/img/real/founder-portrait.webp — 240x240 square,
        WebP q85, must stay under 250KB (F3 diet contract).

Crop: square 1145x1145 from y=40 (keeps headroom + face + suit chest,
drops the lower torso) then downscale to 240x240.
"""
from pathlib import Path

from PIL import Image

SRC = Path("/home/z/my-project/upload/pasted_image_1793887773280.png")
DST = Path(__file__).resolve().parents[1] / "static" / "img" / "real" / "founder-portrait.webp"

im = Image.open(SRC).convert("RGB")
W, H = im.size  # 1145 x 1374
side = min(W, H)          # 1145
top = 40                  # headroom; face + chest inside 40..1185
im = im.crop((0, top, side, top + side))
im = im.resize((240, 240), Image.LANCZOS)
DST.parent.mkdir(parents=True, exist_ok=True)
im.save(DST, "WEBP", quality=85, method=6)

size = DST.stat().st_size
print(f"wrote {DST} — {size} bytes ({size/1024:.1f} KB)")
assert size <= 250 * 1024, f"portrait exceeds the 250KB F3 budget: {size}"
print("PORTRAIT-OK")

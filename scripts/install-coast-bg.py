#!/usr/bin/env python3
"""r59: install the Swahili-coast dhow background for the home-nearby
section. Recompresses the verified candidate to 1600w progressive JPEG."""
from PIL import Image

SRC = "/tmp/coast/a.jpg"
DST = "/home/z/my-project/gabriel-homes/static/img/real/coast-dhow.jpg"

im = Image.open(SRC).convert("RGB")
w, h = im.size
target_w = 1600
if w > target_w:
    im = im.resize((target_w, round(h * target_w / w)), Image.LANCZOS)
im.save(DST, "JPEG", quality=82, optimize=True, progressive=True)

out = Image.open(DST)
import os
print(f"installed {DST}: {out.size[0]}x{out.size[1]}, "
      f"{os.path.getsize(DST) // 1024} KB")

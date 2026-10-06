#!/usr/bin/env python3
"""verify_pools.py — build LARGE contact sheets from the PROCESSED pool files
(media/demo-photos) so watermarks that survived cropping can be spotted and
blacklisted."""
import os, sys
from PIL import Image, ImageDraw, ImageFont

POOL = "/home/z/my-project/gabriel_homes/media/demo-photos"
OUT = "/home/z/my-project/scripts/design-audit"
TH = 420          # big thumbs — watermarks show up at this size
COLS = 5
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)

files = []
for d in sorted(os.listdir(POOL)):
    pdir = os.path.join(POOL, d)
    if not os.path.isdir(pdir):
        continue
    for f in sorted(os.listdir(pdir)):
        if f.endswith(".jpg"):
            files.append(f"{d}/{f[:-4]}")

rows = (len(files) + COLS - 1) // COLS
per_sheet = COLS * 5  # 5 rows per sheet
for s in range(0, len(files), per_sheet):
    chunk = files[s:s + per_sheet]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * TH, rows * (TH + 34)), (244, 240, 234))
    dr = ImageDraw.Draw(sheet)
    for j, name in enumerate(chunk):
        im = Image.open(f"{POOL}/{name}.jpg")
        im.thumbnail((TH - 8, TH - 8))
        x = (j % COLS) * TH; y = (j // COLS) * (TH + 34)
        sheet.paste(im, (x + 4, y + 4))
        dr.text((x + 8, y + TH + 6), name, fill=(25, 20, 16), font=font)
    out = f"{OUT}/pool-check-{s // per_sheet}.png"
    sheet.save(out)
    print("sheet:", out, len(chunk), "images")

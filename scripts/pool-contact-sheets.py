#!/usr/bin/env python3
"""Build contact sheets of media/demo-photos pools for watermark inspection."""
from PIL import Image
from pathlib import Path

MEDIA = Path("/home/z/my-project/gabriel-homes/media/demo-photos")
OUT = Path("/home/z/my-project/download/preview-screenshots")
TH = 220  # thumbnail size

pools = sorted(p for p in MEDIA.iterdir() if p.is_dir())
for pool in pools:
    files = sorted(pool.glob("*.jpg"))
    cols = 6
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TH, rows * TH + 24), (24, 24, 24))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    d.text((8, 6), f"POOL: {pool.name} ({len(files)})", fill=(255, 210, 120))
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        im.thumbnail((TH - 8, TH - 8))
        x = (i % cols) * TH + 4
        y = (i // cols) * TH + 24 + 4
        sheet.paste(im, (x, y))
    dest = OUT / f"r54-pool-{pool.name}.png"
    sheet.save(dest, optimize=True)
    print(dest.name, sheet.size)

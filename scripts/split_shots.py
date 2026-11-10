#!/usr/bin/env python3
"""Split full-page screenshots into readable sections."""
from PIL import Image
import os

SHOTS = '/tmp/shots'
OUT = '/tmp/shots/sections'
os.makedirs(OUT, exist_ok=True)

TARGET_W = 900  # readable width

for name in ['about-full.png', 'home-full.png', 'listings-full.png']:
    img = Image.open(os.path.join(SHOTS, name))
    w, h = img.size
    scale = TARGET_W / w
    new_w, new_h = TARGET_W, int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # split into chunks of ~1400px tall
    chunk_h = 1400
    n_chunks = (new_h + chunk_h - 1) // chunk_h
    base = name.replace('-full.png', '')
    for i in range(n_chunks):
        top = i * chunk_h
        bottom = min((i + 1) * chunk_h, new_h)
        crop = img.crop((0, top, new_w, bottom))
        out_path = os.path.join(OUT, f'{base}-{i+1:02d}.png')
        crop.save(out_path, optimize=True)
        print(f'{out_path}: {crop.size}')

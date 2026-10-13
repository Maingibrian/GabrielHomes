#!/usr/bin/env python3
"""Convert generated agent portraits (PNG) to optimized JPEG static assets.

Output: gabriel_homes/static/img/agents/<slug>.jpg — 864x1152 kept (card
background resolution), quality 85. These ship in the update zip; an
agency without a portrait falls back to the monogram chip.
"""
from pathlib import Path
from PIL import Image

SRC = Path("/tmp/agent-faces")
OUT = Path("/home/z/my-project/gabriel_homes/static/img/agents")
OUT.mkdir(parents=True, exist_ok=True)

for png in sorted(SRC.glob("*.png")):
    img = Image.open(png).convert("RGB")
    dest = OUT / (png.stem + ".jpg")
    img.save(dest, "JPEG", quality=85, optimize=True, progressive=True)
    print(f"{dest.name}: {img.size[0]}x{img.size[1]}, {dest.stat().st_size/1024:.0f} KB")

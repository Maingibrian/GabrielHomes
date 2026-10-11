#!/usr/bin/env python3
"""Task 17 — process the owner's real media (Harmony Nyali, Mombasa).

Curates the 30 WhatsApp photos + walkthrough video into optimized front-page
assets:
  static/img/real/hero-poster.jpg   — video poster / no-JS hero fallback
  static/img/real/cta-balcony.jpg   — CTA section background
  static/img/real/real-0X-*.jpg     — 8-shot gallery strip
  static/video/hero-loop.mp4        — 14 s living-room segment, silent, loopable
All 31 originals are archived to media/real-photos/ (untracked, restorable
via bootstrap).
"""
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image

SRC = Path("/home/z/my-project/scripts/real-assets/extracted")
GH = Path("/home/z/my-project/gabriel_homes")
IMG_OUT = GH / "static" / "img" / "real"
VID_OUT = GH / "static" / "video"
ARCHIVE = GH / "media" / "real-photos"

W = "WhatsApp Image 2026-10-07 at "

PICKS = [  # (source filename, output name, max width)
    (f"{W}18.54.56 (1).jpeg", "hero-poster.jpg", 1600),
    (f"{W}18.54.54.jpeg", "cta-balcony.jpg", 1600),
    (f"{W}18.54.53.jpeg", "real-01-kitchen-island.jpg", 1200),      #06 kitchen island
    (f"{W}18.54.59 (1).jpeg", "real-02-living.jpg", 1200),          #22 L-sofa living
    (f"{W}18.54.57 (1).jpeg", "real-03-bedroom-garden.jpg", 1200),  #17 bedroom garden
    (f"{W}18.54.55.jpeg", "real-04-bedroom-sea.jpg", 1200),         #12 bedroom blue
    (f"{W}18.54.57 (2).jpeg", "real-05-dining.jpg", 1200),          #18 dining plates
    (f"{W}18.54.54 (2).jpeg", "real-06-living-terrace.jpg", 1200),  #08 living-to-terrace
    (f"{W}18.54.51.jpeg", "real-07-balcony.jpg", 1200),             #02 balcony sofas
    (f"{W}18.54.53 (1).jpeg", "real-08-aerial.jpg", 1200),          #05 aerial
]

VIDEO_SRC = SRC / "WhatsApp Video 2026-10-07 at 18.55.00.mp4"


def optimize(src: Path, dst: Path, max_w: int, quality: int = 82) -> None:
    im = Image.open(src).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    kb = dst.stat().st_size / 1024
    print(f"  {dst.name:32s} {im.width}x{im.height}  {kb:6.0f} KB")


def main() -> None:
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    VID_OUT.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    print("== photos ==")
    for name, out, max_w in PICKS:
        optimize(SRC / name, IMG_OUT / out, max_w)

    print("== hero video loop (0.5-14.5 s, silent, faststart) ==")
    dst_video = VID_OUT / "hero-loop.mp4"
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", "0.5", "-to", "14.5", "-i", str(VIDEO_SRC),
         "-an", "-c:v", "libx264", "-crf", "27", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", str(dst_video)],
        check=True, timeout=240,
    )
    print(f"  hero-loop.mp4  {dst_video.stat().st_size / 1e6:.2f} MB")

    print("== archive originals -> media/real-photos/ ==")
    n = 0
    for f in sorted(SRC.iterdir()):
        dst = ARCHIVE / f.name
        if not dst.exists():
            shutil.copy2(f, dst)
            n += 1
    print(f"  {n} new files archived ({len(list(ARCHIVE.iterdir()))} total)")


if __name__ == "__main__":
    main()

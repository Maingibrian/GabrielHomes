#!/usr/bin/env python3
"""Append extra stock photos to pools, continuing numbering, skipping any
that fail download or re-encode. Then print pool totals."""
import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

MEDIA = Path("/home/z/my-project/gabriel-homes/media/demo-photos")
SRC = Path("/tmp/imgsearch")
MAX_W, QUALITY, MIN_W = 1400, 80, 500


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def reencode(data: bytes) -> tuple[bytes, int, int]:
    img = Image.open(io.BytesIO(data))
    img.load()
    w, h = img.size
    if w < MIN_W and h < MIN_W:
        raise ValueError(f"too small {w}x{h}")
    if img.mode != "RGB":
        img = img.convert("RGB")
    if w > MAX_W:
        img = img.resize((MAX_W, round(h * MAX_W / w)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
    return buf.getvalue(), img.width, img.height


added = 0
for urls_file in sorted(SRC.glob("extra-*.urls")):
    pool = urls_file.stem.replace("extra-", "")
    dest_dir = MEDIA / pool
    existing = sorted(dest_dir.glob(f"{pool}-*.jpg"))
    n = max((int(p.stem.split("-")[-1]) for p in existing), default=0)
    for url in urls_file.read_text().split():
        try:
            jpeg, w, h = reencode(fetch(url))
        except Exception as exc:  # noqa: BLE001
            print(f"  skip {pool} {url[-14:]}: {exc}")
            continue
        n += 1
        (dest_dir / f"{pool}-{n:02d}.jpg").write_bytes(jpeg)
        added += 1
        print(f"  {pool}-{n:02d}.jpg  {len(jpeg)//1024}KB {w}x{h}")

print(f"added {added}")
for p in sorted(MEDIA.iterdir()):
    if p.is_dir():
        print(p.name, len(list(p.glob('*.jpg'))))

#!/usr/bin/env python3
"""Install real stock photos into the Gabriel Homes demo-photo pools.

Reads URL lists from /tmp/imgsearch/*.urls, downloads each (OSS-hosted,
guaranteed reachable), re-encodes with Pillow (max 1400px wide, JPEG q80,
EXIF stripped) and writes them to:

    gabriel-homes/media/demo-photos/<pool>/<pool>-NN.jpg

The seeder (apps/listings/management/commands/seed_demo.py) then uses
these pools for every bulk listing instead of the Pillow gradient art.
Pool mapping follows DEMO_TYPE_POOL + the interior pool.
"""
from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

SRC = Path("/tmp/imgsearch")
MEDIA = Path("/home/z/my-project/gabriel-homes/media/demo-photos")

# urls-file -> pool directory
POOLS = {
    "house-a": "house",
    "house-b": "house",
    "house-c": "house",
    "apartment-a": "apartment",
    "apartment-b": "apartment",
    "interior-a": "interior",
    "interior-b": "interior",
    "land": "land",
    "office": "office",
    "shops": "shops",
    "warehouse": "warehouse",
}

MAX_W = 1400
QUALITY = 80
MIN_W = 500  # reject tiny thumbnails


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def reencode(data: bytes) -> tuple[bytes, str, int, int]:
    img = Image.open(io.BytesIO(data))
    img.load()
    w, h = img.size
    if w < MIN_W and h < MIN_W:
        raise ValueError(f"too small {w}x{h}")
    if img.mode != "RGB":
        img = img.convert("RGB")
    if w > MAX_W:
        nh = round(h * MAX_W / w)
        img = img.resize((MAX_W, nh), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
    orientation = "landscape" if img.width >= img.height else "portrait"
    return buf.getvalue(), orientation, img.width, img.height


def main() -> int:
    MEDIA.mkdir(parents=True, exist_ok=True)
    counters: dict[str, int] = {}
    total_bytes = 0
    failures = []
    for stem, pool in POOLS.items():
        urls_file = SRC / f"{stem}.urls"
        if not urls_file.exists():
            failures.append(f"{stem}: missing urls file")
            continue
        for url in urls_file.read_text().split():
            try:
                raw = fetch(url)
                jpeg, orientation, w, h = reencode(raw)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{stem} {url[-16:]}: {exc}")
                continue
            counters[pool] = counters.get(pool, 0) + 1
            n = counters[pool]
            dest = MEDIA / pool / f"{pool}-{n:02d}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(jpeg)
            total_bytes += len(jpeg)
            print(f"{dest.relative_to(MEDIA)}  {len(jpeg)//1024}KB  {w}x{h} {orientation}")
    print(f"\ninstalled {sum(counters.values())} photos, {total_bytes//1024}KB total")
    print("pool counts:", counters)
    if failures:
        print("failures:")
        for f in failures:
            print(" -", f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

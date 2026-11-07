#!/usr/bin/env python3
"""Install the replacement batch (r57) into the demo-photo pools.

Reads the r57 *.urls files (land-b, office-b, shops-b, warehouse-b,
apartment-c, interior-c), downloads + re-encodes exactly like
scripts/install-stock-pools.py, and writes files into the pool dirs
continuing the numbering AFTER the highest existing index, so kept
photos keep their names (DB rows stay valid).
"""
import io
import json
import urllib.request
from pathlib import Path

from PIL import Image

SRC = Path("/tmp/imgsearch")
MEDIA = Path("/home/z/my-project/gabriel-homes/media/demo-photos")

NEW = {
    "land-b": "land",
    "office-b": "office",
    "shops-b": "shops",
    "warehouse-b": "warehouse",
    "apartment-c": "apartment",
    "interior-c": "interior",
}
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
        nh = round(h * MAX_W / w)
        img = img.resize((MAX_W, nh), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
    return buf.getvalue(), img.width, img.height


def next_free(pool_dir: Path, pool: str) -> int:
    n = 0
    for f in pool_dir.glob(f"{pool}-*.jpg"):
        try:
            n = max(n, int(f.stem.split("-")[1]))
        except ValueError:
            pass
    return n


def main() -> int:
    installed, failures = [], []
    for stem, pool in NEW.items():
        raw = SRC / f"{stem}.raw"
        text = raw.read_text()
        start = text.find("{")
        data = json.loads(text[start:])
        urls = [r.get("original_url") for r in data.get("results", []) if r.get("original_url")]
        pool_dir = MEDIA / pool
        pool_dir.mkdir(parents=True, exist_ok=True)
        n = next_free(pool_dir, pool)
        for url in urls:
            try:
                jpeg, w, h = reencode(fetch(url))
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{stem} {url[-16:]}: {exc}")
                continue
            n += 1
            dest = pool_dir / f"{pool}-{n:02d}.jpg"
            dest.write_bytes(jpeg)
            installed.append((dest.relative_to(MEDIA), len(jpeg) // 1024, f"{w}x{h}"))
    for rel, kb, dims in installed:
        print(f"{rel}  {kb}KB  {dims}")
    print(f"\ninstalled {len(installed)} replacement photos")
    print("failures:", failures if failures else "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

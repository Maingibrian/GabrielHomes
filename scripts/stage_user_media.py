#!/usr/bin/env python3
"""stage_user_media.py — copy the owner's real listing media (WhatsApp export)
into gabriel_homes/media/real-listing-src/ with clean, sortable names.

Photos  -> real-01.jpg, real-02.jpg, ...   (sorted by WhatsApp timestamp name)
Video   -> real-tour.mp4

Run once before `manage.py import_real_listing`.
"""
import re
import shutil
from pathlib import Path

SRC = Path("/home/z/my-project/scripts/user-media")
DST = Path("/home/z/my-project/gabriel_homes/media/real-listing-src")


def sort_key(p: Path):
    m = re.search(r"at (\d+)\.(\d+)\.(\d+)(?: \((\d+)\))?", p.name)
    if m:
        h, mi, s, idx = m.group(1), m.group(2), m.group(3), m.group(4) or "0"
        return (int(h), int(mi), int(s), int(idx))
    return (99, 0, 0, 0)


def main():
    DST.mkdir(parents=True, exist_ok=True)
    photos = sorted(
        [p for p in SRC.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}],
        key=sort_key,
    )
    videos = sorted([p for p in SRC.iterdir() if p.suffix.lower() == ".mp4"])

    for old in DST.iterdir():
        old.unlink()

    for i, p in enumerate(photos, 1):
        shutil.copyfile(p, DST / f"real-{i:02d}.jpg")
    for p in videos:
        shutil.copyfile(p, DST / "real-tour.mp4")

    print(f"staged {len(photos)} photos + {len(videos)} video -> {DST}")


if __name__ == "__main__":
    main()

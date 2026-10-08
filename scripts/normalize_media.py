#!/usr/bin/env python3
"""Phase 0 media normalization for gabriel_homes.

Moves the stray project-root property-images/ folder (287 files) into
media/property-images/ with content-aware dedupe:
  - target missing          -> move
  - target exists, same md5 -> drop root copy (true duplicate)
  - target exists, differs  -> move as <stem>_from-root<ext> (no data loss)
Verifies every copied file byte-for-byte before removing the source dir.

Also restores media/demo-photos/ (74 files) from the shipped one-click zip,
so seed_demo regenerates real photography instead of Pillow placeholder art.
"""
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

BASE = Path("/home/z/my-project/gabriel_homes")
ROOT_IMGS = BASE / "property-images"
MEDIA_IMGS = BASE / "media" / "property-images"
ZIP = Path("/home/z/my-project/download/gabriel-homes-oneclick.zip")
DEMO_POOL = BASE / "media" / "demo-photos"


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    moved = dup_dropped = renamed = 0
    files = sorted(p for p in ROOT_IMGS.rglob("*") if p.is_file())
    print(f"source files in {ROOT_IMGS.name}/: {len(files)}")

    for src in files:
        rel = src.relative_to(ROOT_IMGS)
        dst = MEDIA_IMGS / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            if md5(src) == md5(dst):
                dup_dropped += 1
                src.unlink()
                continue
            dst = dst.with_name(f"{dst.stem}_from-root{dst.suffix}")
            if dst.exists() and md5(src) == md5(dst):
                dup_dropped += 1
                src.unlink()
                continue
            renamed += 1
        shutil.copy2(src, dst)
        if md5(src) != md5(dst):
            print(f"FATAL: verify failed {src} -> {dst}", file=sys.stderr)
            return 1
        src.unlink()
        moved += 1

    leftover_files = [p for p in ROOT_IMGS.rglob("*") if p.is_file()]
    if leftover_files:
        print(f"WARNING: {ROOT_IMGS} still has files after move:", file=sys.stderr)
        for p in leftover_files:
            print("   leftover:", p, file=sys.stderr)
        return 1
    shutil.rmtree(ROOT_IMGS)
    print(f"merged: moved={moved} dup-dropped={dup_dropped} renamed-on-conflict={renamed}")
    print(f"removed stray dir {ROOT_IMGS}")

    # restore demo-photos pool from the shipped zip
    if not DEMO_POOL.exists():
        restored = 0
        with zipfile.ZipFile(ZIP) as z:
            for name in z.namelist():
                if "/media/demo-photos/" not in name or name.endswith("/"):
                    continue
                rel = name.split("/media/demo-photos/", 1)[1]
                dst = DEMO_POOL / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(z.read(name))
                restored += 1
        print(f"restored demo-photos pool: {restored} files -> {DEMO_POOL}")
    else:
        n = sum(1 for p in DEMO_POOL.rglob("*") if p.is_file())
        print(f"demo-photos pool already present: {n} files (skipped restore)")

    total = sum(1 for p in MEDIA_IMGS.rglob("*") if p.is_file())
    print(f"media/property-images now holds {total} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""r54: wipe the Pillow gradient-art cards out of bulk demo listings.

The media/demo-photos pools were lost in a workspace recycle, so a reseed
fell back to _cover_image() gradient art. This script re-installs the pool
photos onto every bulk PropertyImage IN PLACE (same filename, same DB row —
URLs stay stable) using the exact digest logic seed_demo._demo_photo uses,
so a fresh seed and this repair converge on identical photos.

Curated listings (is_featured + curated title set from seed_demo) keep
their real img/stock covers — untouched.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.listings.models import Property, PropertyImage  # noqa: E402

DEMO_TYPE_POOL = {
    "flats-apartments": "apartment", "houses": "house", "townhouses": "house",
    "maisonettes": "house", "bungalows": "house", "villas": "house",
    "land": "land", "commercial-property": "office", "offices": "office",
    "shops": "shops", "warehouses": "warehouse",
}

MEDIA = Path(django.conf.settings.MEDIA_ROOT)


def pool_files(pool: str) -> list[Path]:
    base = MEDIA / "demo-photos" / pool
    return sorted(base.glob("*.jpg")) if base.is_dir() else []


def pick(caption: str, pool: str) -> Path | None:
    files = pool_files(pool)
    if not files:
        return None
    digest = int(hashlib.md5(caption.encode("utf-8")).hexdigest(), 16)
    return files[digest % len(files)]


def main() -> int:
    pools = {p: len(pool_files(p)) for p in set(DEMO_TYPE_POOL.values()) | {"interior"}}
    print("pools:", pools)
    if not all(pools.values()):
        print("FATAL: a pool is empty"); return 1

    bulk = Property.objects.filter(is_demo=True).exclude(title__regex=r".*#\d{3}$")
    curated_slugs = set(bulk.values_list("slug", flat=True))
    print(f"curated (untouched): {len(curated_slugs)}")

    qs = Property.objects.filter(is_demo=True, title__regex=r".*#\d{3}$")
    replaced, healed = 0, 0
    for prop in qs:
        for pi in prop.images.all().order_by("position"):
            caption = pi.caption or prop.title
            pool = "interior" if not pi.is_cover else DEMO_TYPE_POOL.get(
                prop.property_type.slug_plural, "house")
            src = pick(caption, pool)
            if src is None:
                print(f"  !! no pool photo for {caption!r}"); continue
            dest = Path(pi.image.path)
            data = src.read_bytes()
            if dest.exists():
                dest.write_bytes(data)
                replaced += 1
            else:
                # heal a missing file: create under the same upload path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                healed += 1
    print(f"replaced {replaced} image files in place, healed {healed} missing")

    # report any bulk listing still without a cover
    no_cover = [p.title for p in qs if not p.images.filter(is_cover=True).exists()]
    print("bulk listings without cover:", len(no_cover), no_cover[:5])
    return 0


if __name__ == "__main__":
    sys.exit(main())

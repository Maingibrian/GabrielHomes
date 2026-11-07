"""Replace Pillow gradient-card images with real pool photos (r56).

The owner reported "the cards are back in place of the images": a seeded
DB can still carry the seeder's Pillow gradient covers (small JPEGs with
the listing title drawn on) when the demo-photo pools were absent at seed
time — or when the DB was re-seeded after a workspace recycle.

This script walks every PropertyImage, detects gradient-card files by
size (< 45 KB — real pool photos re-encode well above that), and
OVERWRITES the file content at the exact referenced path with a real
photo from the matching demo-photos pool (path unchanged, so every URL,
cache entry and DB row stays valid). Run AFTER scripts/
install-stock-pools.py has populated the pools.

Usage:
    .venv/bin/python scripts/replace_gradient_cards.py [--dry-run]

Exits 0 with a report; never touches files >= 45 KB or missing paths.
"""
import os
import sys

import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.conf import settings  # noqa: E402

from apps.listings.management.commands.seed_demo import DEMO_TYPE_POOL  # noqa: E402
from apps.listings.models import PropertyImage  # noqa: E402

from PIL import Image  # noqa: E402

GRADIENT_MAX_BYTES = 45 * 1024  # pool photos re-encode far above this


def pool_for(image_row) -> str:
    prop = getattr(image_row, "property", None)
    if prop is None:
        return "house"
    slug = prop.property_type.slug_plural if prop.property_type else ""
    return DEMO_TYPE_POOL.get(slug, "house")


def main() -> int:
    dry = "--dry-run" in sys.argv
    media = os.path.join(settings.MEDIA_ROOT, "demo-photos")

    pools = {}
    for name in sorted(os.listdir(media)) if os.path.isdir(media) else []:
        d = os.path.join(media, name)
        if os.path.isdir(d):
            pools[name] = sorted(
                f for f in os.listdir(d) if f.lower().endswith(".jpg"))

    if not pools:
        print("no demo-photos pools found — run install-stock-pools first")
        return 1

    replaced, kept = [], 0
    counters = {}
    for row in PropertyImage.objects.select_related(
            "property", "property__property_type").all():
        path = row.image.path
        if not os.path.exists(path):
            continue
        if os.path.getsize(path) >= GRADIENT_MAX_BYTES:
            kept += 1
            continue
        pool = pool_for(row)
        if pool not in pools or not pools[pool]:
            pool = next(iter(pools))
        idx = counters.get(pool, 0)
        counters[pool] = idx + 1
        src = os.path.join(media, pool, pools[pool][idx % len(pools[pool])])
        if dry:
            replaced.append((os.path.basename(path), src, "dry-run"))
            continue
        im = Image.open(src).convert("RGB")
        im.thumbnail((1200, 1200), Image.LANCZOS)
        im.save(path, "JPEG", quality=80, optimize=True, progressive=True)
        replaced.append((os.path.basename(path), os.path.basename(src),
                         f"{os.path.getsize(path):,}B"))

    print(f"real photos kept: {kept}")
    print(f"gradient cards replaced: {len(replaced)}")
    for name, src, note in replaced:
        print(f"  {name}  <-  {src}  ({note})")
    if dry:
        print("(dry run — nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Task 17 — put the owner's real Harmony Nyali photos on the flagship listing.

The sandbox wipes the runtime layer (db + media) between messages, so this
runs from bootstrap_env.sh after every re-seed. Idempotent: skips if the
flagship listing already carries harmony-nyali media.

What it does:
  1. Pick the first featured published property (lowest id).
  2. Copy the 10 curated real photos into media/property-images/.
  3. Replace that property's image rows (real photo set, ordered, first = cover).
  4. Clear the home featured-fragment cache so the grid re-renders immediately.
"""
import os
import shutil
import sys
from pathlib import Path

import django

sys.path.insert(0, "/home/z/my-project/gabriel_homes")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.core.cache import cache  # noqa: E402

from apps.listings.models import Property, PropertyImage  # noqa: E402

SRC = Path("/home/z/my-project/gabriel_homes/static/img/real")
MARKER = "harmony-nyali"

# archive filename -> (order, caption)
PHOTOS = [
    ("hero-poster.jpg", 1, "Open-plan living room"),
    ("real-01-kitchen-island.jpg", 2, "Kitchen and dining"),
    ("real-02-living.jpg", 3, "Living room"),
    ("real-03-bedroom-garden.jpg", 4, "Bedroom"),
    ("real-04-bedroom-sea.jpg", 5, "Second bedroom"),
    ("real-05-dining.jpg", 6, "Dining room"),
    ("real-06-living-terrace.jpg", 7, "Indoor-outdoor flow"),
    ("real-07-balcony.jpg", 8, "Balcony"),
    ("real-08-aerial.jpg", 9, "Build progress — aerial"),
    ("cta-balcony.jpg", 10, "Glass-edge balcony"),
]


def main() -> None:
    # Replicate core.views.home's featured queryset exactly (same ordering,
    # same [:6] slice) so we upgrade the card the homepage actually shows first.
    prop = (
        Property.objects.published()
        .filter(is_featured=True)
        .select_related("property_type", "location__parent__parent", "agent__user")
        .prefetch_related("images")
        .first()
    )
    if prop is None:
        print("  no featured published property — run seed_demo first")
        return

    dest_dir = Path("media/property-images/2026/10")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Re-runnable: drop previous harmony-nyali rows (content may have been
    # re-curated under the same filenames), keep any original demo rows gone.
    PropertyImage.objects.filter(property=prop).delete()
    made = 0
    for i, (fname, position, caption) in enumerate(PHOTOS):
        src = SRC / fname
        if not src.exists():
            print(f"  missing source photo: {fname} — run process_real_assets.py")
            continue
        stem = Path(fname).stem
        dst = dest_dir / f"{MARKER}-{stem}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        PropertyImage.objects.create(
            property=prop,
            image=str(dst.relative_to("media")),
            caption=caption,
            position=position,
            is_cover=(i == 0),
        )
        made += 1

    cache.delete("home:featured_listings")
    print(f"  listing #{prop.id} '{prop.title}' now shows {made} real Harmony Nyali photos")


if __name__ == "__main__":
    main()

"""C1 — list media files that no DB row references.

Scans MEDIA_ROOT (media/) and the legacy property-images/ directory for
files that are NOT referenced by any Property.cover_image,
PropertyImage.image, or AgencyProfile.photo/logo row.

Output: a plain list, one path per line, plus a summary to stderr.
Nothing is deleted by this script — per PLAN C1, files move to
../gabriel-media-archive/ only after the owner confirms (O2).

Usage:
    python scripts/list_unused_media.py                # human output
    python scripts/list_unused_media.py --json         # machine-readable
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def referenced_paths() -> set[str]:
    """All media paths referenced from the database, normalized relative
    to the repo root (e.g. 'media/demo-photos/x.jpg',
    'property-images/y.jpg')."""
    import django

    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()

    from apps.agents.models import AgencyProfile
    from apps.listings.models import Property, PropertyImage

    refs: set[str] = set()

    def add_rel(value: str) -> None:
        """A stored FileField name is relative to MEDIA_ROOT; register it
        under both layouts so either storage convention matches."""
        if not value:
            return
        refs.add(str(Path("media") / value))
        refs.add(str(Path("property-images") / value))
        refs.add(value)

    # Images live on PropertyImage (Property has no cover field — the
    # cover is the first PropertyImage by position, see listing templates).
    for value in PropertyImage.objects.exclude(image="").values_list(
        "image", flat=True
    ):
        add_rel(value)

    for profile in AgencyProfile.objects.all():
        for f in (getattr(profile, "logo", None), getattr(profile, "photo", None)):
            if f and getattr(f, "name", None):
                add_rel(f.name)

    return refs


def on_disk() -> set[str]:
    """Every file under media/ and property-images/, repo-relative."""
    files: set[str] = set()
    for root in ("media", "property-images"):
        base = REPO / root
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file():
                    files.add(str(p.relative_to(REPO)))
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    refs = referenced_paths()
    disk = on_disk()
    unused = sorted(disk - refs)
    referenced_on_disk = sorted(disk & refs)

    if args.json:
        print(json.dumps({
            "unused": unused,
            "referenced_on_disk": referenced_on_disk,
            "totals": {
                "on_disk": len(disk),
                "referenced": len(referenced_on_disk),
                "unused": len(unused),
            },
        }, indent=2))
        return 0

    for u in unused:
        print(u)
    print(
        f"\n{len(unused)} unused of {len(disk)} files "
        f"({len(referenced_on_disk)} referenced).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

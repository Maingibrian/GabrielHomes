#!/usr/bin/env python
"""Re-assign agency portraits (AgencyProfile.logo) from the demo-photos pool.

The workspace restore sometimes wipes media/agency-logos/ and nulls the DB
references; this restores them without touching anything else. Idempotent.
"""
import os
import sys
import django

os.chdir("/home/z/my-project/gabriel_homes")
sys.path.insert(0, ".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.core.files.base import ContentFile  # noqa: E402
from apps.agents.models import AgencyProfile  # noqa: E402

POOL = "/home/z/my-project/gabriel_homes/media/demo-photos/portraits"
# Fallback: raw photo library (resize on the fly)
LIB = "/home/z/my-project/scripts/design-audit/photo-library"
ORDER = ["men2-01", "men-03", "men-05", "men-06", "women-04", "women2-03"]


def src_bytes(i: int) -> bytes:
    pool_file = os.path.join(POOL, f"portrait-{i + 1:02d}.jpg")
    if os.path.exists(pool_file):
        return open(pool_file, "rb").read()
    lib_file = os.path.join(LIB, f"{ORDER[i % len(ORDER)]}.jpg")
    return open(lib_file, "rb").read()


def main() -> None:
    agencies = list(AgencyProfile.objects.all())
    if not agencies:
        print("no agencies found")
        return
    for i, agency in enumerate(agencies):
        data = src_bytes(i)
        name = f"{agency.slug or agency.name}-portrait.jpg"
        agency.logo.save(name, ContentFile(data), save=True)
        ok = agency.logo and agency.logo.storage.exists(agency.logo.name)
        print(f"  {agency.name} -> {agency.logo.name} (file exists: {ok})")
    print(f"assigned {len(agencies)} portraits")


def override() -> bool:
    """`--file <path> <agency-name-substring>` assigns one specific image."""
    args = sys.argv[1:]
    if len(args) >= 3 and args[0] == "--file":
        data = open(args[1], "rb").read()
        needle = args[2].lower()
        for a in AgencyProfile.objects.all():
            if needle in a.name.lower():
                a.logo.save(f"{a.slug}-custom.jpg", ContentFile(data), save=True)
                print(f"  override: {a.name} -> {a.logo.name}")
                return True
        print(f"no agency matches '{args[2]}'")
        return True
    return False


if __name__ == "__main__":
    if not override():
        main()

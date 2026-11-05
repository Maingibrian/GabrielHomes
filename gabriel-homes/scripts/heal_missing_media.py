"""Heal missing media files referenced by the dev DB.

The shipped zip's property-images/ tree is missing some Pillow-generated
demo photos (random-hash names created on the owner's machine). This script
finds EVERY model FileField whose file is missing on disk and, for images,
writes the project's own seed_demo cover-art JPEG at the exact referenced
path — the same fallback the seeder itself uses. Missing non-image files
are reported, not invented.
"""
import os
import sys

import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.apps import apps  # noqa: E402
from django.db import models  # noqa: E402

from apps.listings.management.commands.seed_demo import _cover_image  # noqa: E402


def field_caption(instance, field_name):
    for attr in ("caption", "title", "name", "slug"):
        v = getattr(instance, attr, None)
        if v:
            return str(v)
    return instance._meta.label


def main():
    healed, missing_other = [], []
    for model in apps.get_models():
        file_fields = [f for f in model._meta.concrete_fields
                       if isinstance(f, models.FileField)]
        if not file_fields:
            continue
        qs = model._default_manager.all()
        for obj in qs:
            for f in file_fields:
                v = getattr(obj, f.name)
                if not v or not v.name:
                    continue
                rel = v.name
                if os.path.exists(rel):
                    continue
                is_image = isinstance(f, models.ImageField) or \
                    os.path.splitext(rel)[1].lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}
                if is_image:
                    os.makedirs(os.path.dirname(rel) or ".", exist_ok=True)
                    art = _cover_image(field_caption(obj, f.name))
                    with open(rel, "wb") as fh:
                        fh.write(art.read())
                    healed.append((model._meta.label, rel))
                else:
                    missing_other.append((model._meta.label, rel))
    print(f"healed images: {len(healed)}")
    for label, rel in sorted(healed):
        print(f"  {label}: {rel}")
    print(f"missing non-image files (left alone): {len(missing_other)}")
    for label, rel in sorted(missing_other):
        print(f"  {label}: {rel}")


if __name__ == "__main__":
    main()

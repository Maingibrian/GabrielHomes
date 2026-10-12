#!/usr/bin/env python3
"""Purge dead media: move unreferenced files under media/ to the archive.

Rules:
  - Recompute DB FileField references live (so the just-bound video counts).
  - NEVER touch media/demo-photos/** (seed pools for fresh installs)
    or media/property-videos/** (tour video, now bound to flagship).
  - Everything else unreferenced -> moved to
    /home/z/my-project/archive/media-orphans/<same relative path>
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/gabriel_homes")
ARCHIVE = Path("/home/z/my-project/archive/media-orphans")
KEEP_PREFIXES = ("media/demo-photos/", "media/property-videos/")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
sys.path.insert(0, str(REPO))

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.db import models as djm  # noqa: E402


def db_refs() -> set[str]:
    refs: set[str] = set()
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, (djm.FileField, djm.ImageField)):
                vals = (
                    model._default_manager.exclude(**{field.name: ""})
                    .values_list(field.name, flat=True)
                    .distinct()
                )
                for v in vals:
                    if v:
                        refs.add(v)
                        refs.add(f"media/{v}")
                        refs.add(f"property-images/{v}")
    return refs


def main() -> int:
    refs = db_refs()
    moved = 0
    freed = 0
    for p in sorted((REPO / "media").rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO).as_posix()
        if rel.startswith(KEEP_PREFIXES):
            continue
        if rel in refs:
            continue
        dest = ARCHIVE / Path(rel).relative_to("media")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest))
        moved += 1
        freed += p.stat().st_size if not dest.exists() else 0
        print(f"  moved  {rel}")
    print(f"\n{moved} files moved to {ARCHIVE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""r24 — build the owner zip: full tree minus orphans.

media/property-images/ holds 10,256 files accumulated across seed/test
cycles; the shipped db.sqlite3 references only 125. Ship those 125
(fresh seeding re-copies from static/ anyway) plus everything else
outside the noise dirs. Keeps the zip ~60MB instead of 365MB.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/z/my-project")
TREE = ROOT / "gabriel-homes"
sys.path.insert(0, str(TREE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django  # noqa: E402

django.setup()
from apps.listings.models import PropertyImage  # noqa: E402

OUT = ROOT / "download" / "gabriel-homes-full-2026-11-05-r24.zip"

referenced = {str(p) for p in PropertyImage.objects.values_list("image", flat=True)}
print("DB-referenced media files:", len(referenced))

EXCLUDE_DIRS = {".venv", "__pycache__", "staticfiles", ".pytest_cache",
                "audit-screens", "node_modules", ".git"}

files = []
for path in TREE.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if any(p in EXCLUDE_DIRS for p in parts):
        continue
    if parts[1] == "media" and len(parts) > 2 and parts[2] == "property-images":
        # only the files the shipped DB actually references
        media_rel = "/".join(parts[2:])
        if media_rel not in referenced:
            continue
    if path.suffix == ".pyc":
        continue
    files.append(str(rel))

print("files to zip:", len(files))

if OUT.exists():
    OUT.unlink()
listfile = ROOT / "scripts" / "r24_zip_list.txt"
listfile.write_text("\n".join(files), encoding="utf-8")
subprocess.run(["zip", "-q", str(OUT), "-@", ], stdin=open(listfile, "rb"),
               cwd=ROOT, check=True)
listfile.unlink()
print(f"zip: {OUT} — {OUT.stat().st_size/1024/1024:.1f} MB")
print("ZIP-OK")

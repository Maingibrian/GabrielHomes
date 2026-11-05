"""Rebuild the full Gabriel Homes deliverable zip (post-r20).

Policy (parity with the previous delivery, download/gabriel-homes-full-2026-11-05.zip):
- whole tree under /home/z/my-project/gabriel-homes/ (incl. db.sqlite3, .env
  [dev-only, no credentials], .env.example, launcher scripts, LOOP/, docs/)
- EXCLUDE: __pycache__/, .pytest_cache/, *.pyc, *.log (runtime logs)
- media: include every file that was in the previous zip; for files created
  after it (media/property-images/2026/11/*), include only if DB-referenced
  (none are) — i.e. drop the 457 new orphans, keep the older set untouched.
"""
import sqlite3
import zipfile
from pathlib import Path

TREE = Path("/home/z/my-project/gabriel-homes")
OLD_ZIP = Path("/home/z/my-project/download/gabriel-homes-full-2026-11-05.zip")
OUT = Path("/home/z/my-project/download/gabriel-homes-full-2026-11-05-r20.zip")

# media files present in the previous delivery (relative to tree root)
with zipfile.ZipFile(OLD_ZIP) as zf:
    prev = {n[len("gabriel-homes/"):] for n in zf.namelist()
            if n.startswith("gabriel-homes/media/") and not n.endswith("/")}

# DB-referenced media (all FileField-ish values), for safety
con = sqlite3.connect(TREE / "db.sqlite3")
refs = set()
for (table,) in con.execute(
        "select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
    cols = [r[1] for r in con.execute(f'pragma table_info("{table}")')]
    for col in cols:
        for (val,) in con.execute(
                f'select "{col}" from "{table}" where "{col}" is not null '
                f"and \"{col}\" != ''"):
            if isinstance(val, str) and (val.startswith("property-images/")
                                         or val.startswith("property-videos/")
                                         or val.startswith("media/")):
                p = val[len("media/"):] if val.startswith("media/") else val
                refs.add(p)

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "node_modules", ".git"}
EXCLUDE_SUFFIX = (".pyc", ".log")

files, skipped_new_orphans = [], 0
for p in sorted(TREE.rglob("*")):
    if p.is_dir():
        continue
    rel = p.relative_to(TREE).as_posix()
    if any(part in EXCLUDE_DIRS for part in Path(rel).parts):
        continue
    if rel.endswith(EXCLUDE_SUFFIX):
        continue
    if rel.startswith("media/"):
        if rel in prev or rel in refs:
            files.append(rel)
        elif rel not in prev:
            # created after the previous zip: keep only if DB-referenced
            if rel in refs:
                files.append(rel)
            else:
                skipped_new_orphans += 1
        continue
    files.append(rel)

print(f"files to zip: {len(files)}  (skipped new unreferenced media: {skipped_new_orphans})")
print(f"db-referenced media: {len(refs)}, of which missing from disk: "
      f"{sum(1 for r in refs if not (TREE / r).exists())}")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for rel in files:
        zf.write(TREE / rel, f"gabriel-homes/{rel}")

print(f"wrote {OUT} ({OUT.stat().st_size / 1_048_576:.1f} MB)")

# verification pass
with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    assert len(names) == len(files)
    must_have = [
        "gabriel-homes/db.sqlite3",
        "gabriel-homes/.env.example",
        "gabriel-homes/START-GABRIEL-HOMES.sh",
        "gabriel-homes/RUN-ME-FIRST.txt",
        "gabriel-homes/apps/core/tests/test_h1_home_order.py",
        "gabriel-homes/apps/core/tests/test_h3_mobile_bento.py",
        "gabriel-homes/apps/core/tests/test_f1_token_integrity.py",
        "gabriel-homes/static/css/home.css",
        "gabriel-homes/scripts/r20_e3_h3_audit.py",
        "gabriel-homes/LOOP/audit-screens/r20-e3-h3-mobile-rail.png",
        "gabriel-homes/LOOP/STATE.md",
    ]
    for m in must_have:
        assert m in names, f"MISSING {m}"
    assert not any("__pycache__" in n or n.endswith(".pyc") or n.endswith(".log")
                   for n in names), "cache/log leaked into zip"
    home = zf.read("gabriel-homes/templates/core/home.html").decode()
    assert 'id="hero"' in home and 'id="bento"' in home, "home.html not r18 build"
    print("verify: all must-have files present, r18 home structure confirmed, "
          f"zip entries {len(names)}")

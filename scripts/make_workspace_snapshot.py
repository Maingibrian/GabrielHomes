#!/usr/bin/env python3
"""Build a downloadable snapshot of the whole workspace (zipfile stdlib build).

Excludes platform infra + secrets + git internals; everything else included
so the owner can browse the real workspace files locally.
"""
import os
import sys
import zipfile

ROOT = "/home/z/my-project"
OUT = os.path.join(ROOT, "download", "gabriel-workspace-snapshot.zip")

SKIP_DIRS = {".git", "node_modules", "skills", ".venv", "__pycache__",
             "tool-results", "download", "upload"}
SKIP_FILES = {".env", "cookies.txt", "gabriel-workspace-snapshot.zip",
              "server.log", "db.sqlite3"}


def skip(name: str, is_dir: bool) -> bool:
    if is_dir:
        return name in SKIP_DIRS
    if name in SKIP_FILES:
        return True
    # Loop 4 (H2): drop the real secret file but KEEP .env.example — the old
    # `name.startswith(".env")` glob silently removed it from every export.
    return name.endswith((".pyc", ".pyo")) or (
        name == ".env" or (name.startswith(".env.") and name != ".env.example"))


count = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not skip(d, True)]
        for f in files:
            if skip(f, False):
                continue
            full = os.path.join(base, f)
            rel = os.path.relpath(full, ROOT)  # archive roots at gabriel_homes/, scripts/ ... (check_export layout)
            try:
                z.write(full, rel)
                count += 1
            except OSError as e:
                print(f"skip (unreadable): {rel}: {e}")

# -- Loop 4 (H2): verify dotfile-critical content BEFORE declaring success.
REQUIRED = [
    "gabriel_homes/.env.example",
    "gabriel_homes/.gitignore",
    "gabriel_homes/docs/STATUS.md",
    "gabriel_homes/docs/AGENT-BRIEF.md",
    "gabriel_homes/manage.py",
]
with zipfile.ZipFile(OUT) as z:
    names = set(z.namelist())
missing = [r for r in REQUIRED if r not in names]
if missing:
    print("ABORT: export would drop required files: " + ", ".join(missing))
    sys.exit(1)
print("export check: all 5 required files present (dotfiles included)")

print(f"archived {count} files -> {OUT}")
print(f"size: {os.path.getsize(OUT) / 1e6:.1f} MB")

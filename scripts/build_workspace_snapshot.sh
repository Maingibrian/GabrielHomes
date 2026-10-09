#!/usr/bin/env bash
# =============================================================================
# build_workspace_snapshot.sh — H2: build the WORKSPACE export zip with the
# dotfiles KEPT (this is the script whose absence let dotfile-less exports
# ship silently — .env.example / .gitignore / .git were missing from every
# earlier snapshot).
#
# Usage:   bash scripts/build_workspace_snapshot.sh [out.zip]
# Default: /home/z/my-project/download/gabriel-workspace-snapshot.zip
#
# Layout: zip root = workspace root, so entries look like
#   gabriel_homes/manage.py, gabriel_homes/.env.example, scripts/preview_site/...
#
# KEPT : gabriel_homes/ (all dotfiles), scripts/preview_site/, scripts/launcher/
# DROPPED: .git/, db.sqlite3, .env (real), *.log, *.pyc, __pycache__, .venv,
#          download/, upload/, node_modules/, media/ (heavy binaries),
#          test caches, staging/ziptest scratch dirs
# Note: the one-click DELIVERABLE zip (build_package.sh) intentionally ships
# the seeded demo db; THIS snapshot is the workspace export and must not.
# Always follow with: bash scripts/check_export.sh <out.zip>
# =============================================================================
set -euo pipefail

OUT="${1:-/home/z/my-project/download/gabriel-workspace-snapshot.zip}"

python3 - "$OUT" <<'PYEOF'
import os
import sys
import zipfile
from pathlib import Path

out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
WS = Path("/home/z/my-project")

include_dirs = [
    WS / "gabriel_homes",
    WS / "scripts" / "preview_site",
    WS / "scripts" / "launcher",
]
prune_dirs = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".idea", ".vscode",
    "download", "upload", "node_modules", "media", "staticfiles",
    "htmlcov", "design-reference", "gabriel_extract", "ziptest", "ziptest-gate",
    "stage", "shots", "browsertest", "design-audit", "property-images",
}
drop_files = {
    "db.sqlite3", ".env", ".coverage", ".DS_Store", "cookies.txt",
    "server.log", "preview_server.log",
}
drop_suffixes = (".pyc", ".pyo", ".log", ".sqlite3-journal", ".sqlite3-wal", ".sqlite3-shm")

count = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for base in include_dirs:
        if not base.exists():
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in prune_dirs)
            for name in sorted(files):
                if name in drop_files or name.endswith(drop_suffixes):
                    continue
                p = Path(root) / name
                arcname = p.relative_to(WS).as_posix()
                z.write(p, arcname)
                count += 1

print(f"snapshot: {count} files -> {out}")
PYEOF

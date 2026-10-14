#!/usr/bin/env bash
# SESSION-END BACKUP (rule 5 of WORK.md).
#   1. git bundle  = full history, the ONLY artifact that survives a sandbox
#      rollback (the user downloads it; REBUILD.md step 1 restores from it).
#   2. DB snapshot = rollback also wipes SQLite (stats showed 0 once); the
#      backup lets REBUILD.md step 2 restore the seeded database as-is.
#   3. Both are copied into scripts/preview_site/files/ so the user can
#      download them from the :3000 delivery page with one click.
# Safe to re-run; overwrites the previous backup (fixed names, no versions).
set -euo pipefail
cd "$(dirname "$0")/.."

BUNDLE=download/gabriel-homes.bundle
DBSRC=gabriel_homes/db.sqlite3
DBDST=download/gabriel-homes-db-backup.sqlite3
FILES=scripts/preview_site/files

echo "== git bundle (full history) =="
git bundle create "$BUNDLE" --all
git bundle verify "$BUNDLE" 2>&1 | tail -1
ls -lh "$BUNDLE" | awk '{print "  " $5 "  " $NF}'

echo "== db snapshot =="
if [ -f "$DBSRC" ]; then
  cp -f "$DBSRC" "$DBDST"
  ls -lh "$DBDST" | awk '{print "  " $5 "  " $NF}'
else
  echo "  WARN: $DBSRC not found - skipping db backup" >&2
fi

echo "== publish to :3000 delivery tree =="
mkdir -p "$FILES"
cp -f "$BUNDLE" "$FILES/"
[ -f "$DBDST" ] && cp -f "$DBDST" "$FILES/"
echo "DONE - tell the user to download gabriel-homes.bundle"
echo "(and the db backup) from the :3000 page after every session."

#!/usr/bin/env bash
# SESSION-END BACKUP (rule 5 of WORK.md).
#   1. git bundle  = full history, the ONLY artifact that survives a sandbox
#      rollback (the user downloads it; REBUILD.md step 1 restores from it).
#   2. DB snapshot = rollback also wipes SQLite (stats showed 0 once); the
#      backup lets REBUILD.md step 2 restore the seeded database as-is.
#      It is published as a .zip because the :3000 server hard-denies *.sqlite3.
#   3. Both are copied into scripts/preview_site/files/ so the user can
#      download them from the :3000 delivery page with one click.
# Safe to re-run; overwrites the previous backup (fixed names, no versions).
set -euo pipefail
cd "$(dirname "$0")/.."

BUNDLE=download/gabriel-homes.bundle
DBSRC=gabriel_homes/db.sqlite3
DBDST=download/gabriel-homes-db-backup.sqlite3
DBZST=download/gabriel-homes-db-backup.zip
FILES=scripts/preview_site/files

echo "== git bundle (full history) =="
git bundle create "$BUNDLE" --all
git bundle verify "$BUNDLE" 2>&1 | tail -1
ls -lh "$BUNDLE" | awk '{print "  " $5 "  " $NF}'

echo "== db snapshot =="
if [ -f "$DBSRC" ]; then
  cp -f "$DBSRC" "$DBDST"
  ( cd download && rm -f gabriel-homes-db-backup.zip && python3 -m zipfile -c gabriel-homes-db-backup.zip gabriel-homes-db-backup.sqlite3 )
  ls -lh "$DBZST" | awk '{print "  " $5 "  " $NF}'
else
  echo "  WARN: $DBSRC not found - skipping db backup" >&2
fi

echo "== publish to :3000 delivery tree =="
mkdir -p "$FILES"
cp -f "$BUNDLE" "$FILES/"
[ -f "$DBZST" ] && cp -f "$DBZST" "$FILES/"
echo "DONE - tell the user to download gabriel-homes.bundle"
echo "(and the db backup zip) from the :3000 page after every session."

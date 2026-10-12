#!/usr/bin/env bash
# Build a rootless Gabriel Homes UPDATE zip (code only — no db/media/venv/.env).
# Result: /home/z/my-project/download/gabriel-homes-update-YYYY-MM-DD.zip
set -euo pipefail

GH=/home/z/my-project/gabriel_homes
OUT_DIR=/home/z/my-project/download
DATE=$(date +%F)
OUT="$OUT_DIR/gabriel-homes-update-$DATE.zip"
STAGE=$(mktemp -d)

cd "$GH"
rsync -a \
  --exclude '.venv/' \
  --exclude 'media/' \
  --exclude 'db.sqlite3' \
  --exclude 'staticfiles/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'nohup.out' \
  --exclude '.pytest_cache/' \
  --exclude '.coverage' \
  --exclude 'htmlcov/' \
  --exclude 'docs/shots/' \
  --exclude 'property-images/' \
  "$GH/" "$STAGE/gabriel-homes/"

mkdir -p "$OUT_DIR"
rm -f "$OUT"
cd "$STAGE"
zip -rq "$OUT" gabriel-homes -x '*/.git/*'
rm -rf "$STAGE"

echo "== built: $OUT =="
ls -la "$OUT"
echo "== sanity: rootless + no db/media =="
unzip -l "$OUT" | grep -Eq '(^| )gabriel-homes/manage\.py$' && echo "manage.py at top: OK"
unzip -l "$OUT" | grep -Eq 'db\.sqlite3|media/|\.venv/|\.env$' && echo "FATAL: forbidden file in zip" || echo "no db/media/venv/.env: OK"
unzip -l "$OUT" | tail -2

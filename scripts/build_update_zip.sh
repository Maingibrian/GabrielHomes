#!/usr/bin/env bash
# Build gabriel-homes-update-<date>.zip — a ROOTLESS, CODE-ONLY overlay zip.
#
#   unzip -o gabriel-homes-update-*.zip -d <existing-install-dir>
#       (or just run UPDATE-WEBSITE.sh which is bundled inside)
#
# Applying it over an existing install updates code/templates/static while
# keeping db.sqlite3, media/ and .venv completely untouched. New users should
# take the full one-click zip instead.
set -euo pipefail
WS=/home/z/my-project
SRC="$WS/gabriel_homes"
OUT="$WS/download/gabriel-homes-update-$(date +%F).zip"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

rsync -a --delete \
    --exclude '__pycache__/' --exclude '*.pyc' \
    --exclude '.venv/' --exclude 'db.sqlite3' \
    --exclude 'media/' --exclude '.env' \
    --exclude '.pytest_cache/' --exclude 'staticfiles/' \
    --exclude 'WORK.md' --exclude 'preview_bridge.log' \
    "$SRC/" "$STAGE/"
chmod +x "$STAGE/UPDATE-WEBSITE.sh" "$STAGE/scripts/ensure-runtime.sh"

: > "$STAGE/UPDATE-README.txt"
cat >> "$STAGE/UPDATE-README.txt" <<'EOF'
GABRIEL HOMES — UPDATE PACKAGE (code only)
==========================================
You should already have a working install (from gabriel-homes-oneclick.zip).

Easiest way to apply this update:

    1. Put this zip in ~/Downloads (or anywhere).
    2. Open a terminal IN YOUR EXISTING gabriel-homes FOLDER and run:

           ./UPDATE-WEBSITE.sh

    (it auto-finds the newest update zip, or pass one explicitly:
     ./UPDATE-WEBSITE.sh /path/to/gabriel-homes-update-YYYY-MM-DD.zip)

Manual equivalent (same result):

    unzip -o gabriel-homes-update-YYYY-MM-DD.zip -d /path/to/gabriel-homes
    cd /path/to/gabriel-homes && .venv/bin/python manage.py migrate --noinput

Your database, photos, videos and settings are never touched.
EOF

# zip -qr on an existing archive only ADDS/UPDATES entries (never removes) —
# stale files from earlier builds would survive. Always start fresh.
rm -f "$OUT"
( cd "$STAGE" && zip -qr "$OUT" . )
ls -la "$OUT"

echo "--- integrity checks (capture listing ONCE, no unzip|grep races) ---"
ZIP_LISTING="$(unzip -l "$OUT")"
fail=0
for bad_re in '(^| )db\.sqlite3$' '(^| )\.env$' ' \.venv/' ' media/' '__pycache__' 'preview_bridge\.log'; do
    if grep -qE "$bad_re" <<<"$ZIP_LISTING"; then
        echo "FATAL: forbidden entry matches $bad_re in $OUT" >&2; fail=1
    fi
done
for good in 'manage.py' 'apps/listings/models.py' 'config/settings/base.py' \
            'templates/base.html' 'static/css/home.css' 'UPDATE-WEBSITE.sh' \
            'UPDATE-README.txt' '.env.example' 'scripts/ensure-runtime.sh'; do
    grep -qF "$good" <<<"$ZIP_LISTING" || { echo "FATAL: $good missing from $OUT" >&2; fail=1; }
done
[ "$fail" = 0 ] || exit 1
echo "OK: $OUT ($(echo "$ZIP_LISTING" | grep -cE 'inflating|^[ 0-9]+ [0-9]{2}' || true) entries, $(du -h "$OUT" | cut -f1))"

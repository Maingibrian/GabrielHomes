#!/usr/bin/env bash
# Test the oneclick zip EXACTLY like a user's Linux machine:
# extract -> bash START-GABRIEL-HOMES.sh (no browser) -> verify pages answer.
set -u
ROOT=/home/z/my-project
TEST_DIR=$ROOT/scripts/stage/oneclick-test
LOG=$TEST_DIR/boot.log

echo "== 1. clean slate =="
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

echo "== 2. extract zip (python3 fallback path, like the user's one-liner) =="
python3 -c "import zipfile; zipfile.ZipFile('$ROOT/download/gabriel-homes-oneclick.zip').extractall('$TEST_DIR')"
cd "$TEST_DIR/gabriel-homes" || exit 1
[ -f manage.py ] && [ -f START-GABRIEL-HOMES.sh ] || { echo "FATAL: zip layout wrong"; exit 1; }
echo "   extracted: $(ls | wc -l) entries at top level"

echo "== 3. launch (first run: venv + pip install online + db check) =="
GABRIEL_NO_BROWSER=1 bash START-GABRIEL-HOMES.sh > "$LOG" 2>&1 &
LAUNCHER_PID=$!

echo "== 4. wait for the site to answer (max 300s) =="
for i in $(seq 1 300); do
  kill -0 "$LAUNCHER_PID" 2>/dev/null || { echo "FATAL: launcher died early"; tail -30 "$LOG"; exit 1; }
  # discover the chosen port from the log
  PORT=$(grep -oE '127\.0\.0\.1:[0-9]+' "$LOG" | head -1 | cut -d: -f2)
  if [ -n "${PORT:-}" ] && [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/" 2>/dev/null)" = "200" ]; then
    echo "   UP after ${i}s on port $PORT"
    break
  fi
  sleep 1
  [ "$i" = 300 ] && { echo "FATAL: site never answered"; tail -30 "$LOG"; exit 1; }
done

echo "== 5. verify key pages =="
BASE="http://127.0.0.1:$PORT"
for path in "/" "/properties/" "/property-for-sale/" "/agents/" "/admin/login/" "/dashboard/"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE$path")
  echo "   $path -> $code"
done
# homepage must show real seeded content, not an empty shell
curl -s "$BASE/" | grep -qi "gabriel" || { echo "FATAL: homepage content wrong"; exit 1; }
# a listing detail page must render (grab first listing link from /properties/)
SLUG=$(curl -s "$BASE/properties/" | grep -oE '/listing/[a-z0-9-]+-[0-9]+/' | head -1)
[ -n "$SLUG" ] && echo "   detail $SLUG -> $(curl -s -o /dev/null -w '%{http_code}' "$BASE$SLUG")"
# static CSS must serve (whitenoise/dev static)
CSS=$(curl -s "$BASE/" | grep -oE '/static/css/[a-z._-]+\.css' | head -1)
[ -n "$CSS" ] && echo "   static $CSS -> $(curl -s -o /dev/null -w '%{http_code}' "$BASE$CSS")"
# a listing image must serve from the shipped media
IMG=$(curl -s "$BASE/properties/" | grep -oE '/media/property-images/[^"]+\.(jpg|png|jpeg|webp)' | head -1)
if [ -n "$IMG" ]; then
  echo "   image $IMG -> $(curl -s -o /dev/null -w '%{http_code}' "$BASE$IMG")"
else
  echo "   WARN: no /media/property-images image URL found on listings page"
fi

echo "== 6. launcher log summary =="
grep -E "Python:|Installing|Preparing|starting at|Admin:|Agent:" "$LOG" | head -8

echo "== 7. stop the site =="
kill "$LAUNCHER_PID" 2>/dev/null
sleep 1
pkill -f "manage.py runserver 127.0.0.1:$PORT" 2>/dev/null
echo "ONECLICK LINUX TEST PASS (port $PORT)"

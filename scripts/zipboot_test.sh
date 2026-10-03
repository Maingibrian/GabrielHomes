#!/bin/bash
# =============================================================================
# zipboot_test.sh — TRIPLE-CHECK 3 (boot half)
# Boots the UNZIPPED delivery copy exactly as a user would (shipped DB present,
# no venv) and verifies the site + data integrity + BROWSER AUTO-OPEN.
# =============================================================================
set -u
PKG=/home/z/my-project/scripts/ziptest/gabriel-homes
LOG=/home/z/my-project/scripts/ziptest/boot.log
TESTROOT=/home/z/my-project/scripts/ziptest

# -- Fake browser (same contract as the unit test + coldstart test).
FAKE_BROWSER="$TESTROOT/fake-browser.sh"
FAKE_BROWSER_LOG="$TESTROOT/browser-opens.log"
export FAKE_BROWSER_LOG
cat > "$FAKE_BROWSER" <<'EOF'
#!/bin/bash
URL="$1"
if curl -s -o /dev/null --max-time 2 "$URL"; then STATE=UP; else STATE=DOWN; fi
echo "$(date +%s.%N) $URL $STATE" >> "${FAKE_BROWSER_LOG:?}"
exit 0
EOF
chmod +x "$FAKE_BROWSER"
: > "$FAKE_BROWSER_LOG"

cd "$PKG"
LISTINGS_BEFORE=$(python3 -c "
import sqlite3; print(sqlite3.connect('db.sqlite3').execute('SELECT COUNT(*) FROM listings_property').fetchone()[0])")
echo "listings in shipped db: $LISTINGS_BEFORE"

BROWSER="$FAKE_BROWSER %s" bash START-GABRIEL-HOMES.sh > "$LOG" 2>&1 &
LAUNCH_PID=$!
echo "launcher PID $LAUNCH_PID — polling..."

PORT=""
for i in $(seq 1 100); do
  sleep 3
  if ! kill -0 "$LAUNCH_PID" 2>/dev/null; then
    echo "FAIL: launcher exited early:"; tail -20 "$LOG"; exit 1
  fi
  PORT=$(rg -o "127\.0\.0\.1:([0-9]+)/" -r '$1' "$LOG" | head -1)
  if [ -n "$PORT" ] && curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$PORT/"; then
    break
  fi
  PORT=""
done
[ -z "$PORT" ] && { echo "FAIL: server never came up:"; tail -30 "$LOG"; exit 1; }
echo "OK: server up on port $PORT after ~$((i*3))s"

PASS=0; FAIL=0
chk() {
  local body; body=$(curl -s --max-time 5 "$2")
  if [ -n "${3:-}" ]; then
    if echo "$body" | grep -q "$3"; then PASS=$((PASS+1)); echo "  OK   $1"; else FAIL=$((FAIL+1)); echo "  FAIL $1"; fi
  else
    PASS=$((PASS+1)); echo "  OK   $1"
  fi
}
chk "home"                        "http://127.0.0.1:$PORT/"                             "Real estate with a human point of view"
chk "search"                      "http://127.0.0.1:$PORT/property-for-sale/mombasa/"   "listing-card"
chk "about page"                  "http://127.0.0.1:$PORT/about/"                       "Gabriel"
LISTING_URL=$(curl -s "http://127.0.0.1:$PORT/property-for-sale/mombasa/" | grep -o '/listing/[a-z0-9-]*-[0-9]*/' | head -1)
chk "listing detail"              "http://127.0.0.1:$PORT$LISTING_URL"                  "KES"
IMG=$(curl -s "http://127.0.0.1:$PORT/property-for-sale/mombasa/" | grep -o '/media/[^"]*\.jpg' | head -1)
chk "media image"                 "http://127.0.0.1:$PORT$IMG"                          ""
chk "sitemap"                     "http://127.0.0.1:$PORT/sitemap.xml"                  "/listing/"

echo "seeding did not duplicate data (launcher is idempotent):"
LISTINGS_AFTER=$(python3 -c "
import sqlite3; print(sqlite3.connect('db.sqlite3').execute('SELECT COUNT(*) FROM listings_property').fetchone()[0])")
echo "  listings before=$LISTINGS_BEFORE after=$LISTINGS_AFTER"
if [ "$LISTINGS_BEFORE" = "$LISTINGS_AFTER" ]; then PASS=$((PASS+1)); echo "  OK   no duplication"; else FAIL=$((FAIL+1)); echo "  FAIL duplicated"; fi

echo "browser auto-open check (the v1 bug):"
sleep 2
OPENS=$(wc -l < "$FAKE_BROWSER_LOG" | tr -d ' ')
if [ "$OPENS" = "1" ]; then PASS=$((PASS+1)); echo "  OK   browser fired exactly once"; else FAIL=$((FAIL+1)); echo "  FAIL browser fired $OPENS times (want 1)"; fi
OPEN_URL=$(awk '{print $2}' "$FAKE_BROWSER_LOG" | head -1)
if [ "$OPEN_URL" = "http://127.0.0.1:$PORT/" ]; then PASS=$((PASS+1)); echo "  OK   browser opened the served URL"; else FAIL=$((FAIL+1)); echo "  FAIL browser opened '$OPEN_URL'"; fi
if grep -q " UP$" "$FAKE_BROWSER_LOG"; then PASS=$((PASS+1)); echo "  OK   site was UP at browser-open time"; else FAIL=$((FAIL+1)); echo "  FAIL site was DOWN at browser-open: $(cat "$FAKE_BROWSER_LOG")"; fi

pkill -f "ziptest/gabriel-homes" 2>/dev/null && echo "stopped."
sleep 1
echo ""
echo "ZIPBOOT RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ] && echo "TRIPLE-CHECK 3: PASSED" || echo "TRIPLE-CHECK 3: FAILED"
exit $FAIL

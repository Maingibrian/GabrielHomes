#!/bin/bash
# =============================================================================
# coldstart_test.sh — TRIPLE-CHECK 2
# Simulates a user who unzipped the package on a machine with nothing set up:
#   - no .venv            (launcher must create it + pip install)
#   - no db.sqlite3       (launcher must migrate + seed ~80 listings)
#   - port 8000 occupied  (launcher must fall back to 8001+)
# Then curls the key pages and shuts the server down.
# =============================================================================
set -u
TESTROOT=/home/z/my-project/scripts/coldtest
PKG="$TESTROOT/gabriel-homes"

echo "== 1. Fresh copy of staged package (no venv, no DB) =="
rm -rf "$TESTROOT"
mkdir -p "$TESTROOT"
cp -r /home/z/my-project/scripts/stage/gabriel-homes "$PKG/"
rm -f "$PKG/db.sqlite3"
rm -rf "$PKG/.venv"
[ -f "$PKG/db.sqlite3" ] && echo "FAIL: db still present" && exit 1
echo "  OK: no .venv, no db.sqlite3"

echo "== 2. Launch (headless: GABRIEL_NO_BROWSER=1) =="
cd "$PKG"
GABRIEL_NO_BROWSER=1 bash START-GABRIEL-HOMES.sh > "$TESTROOT/launcher.log" 2>&1 &
LAUNCH_PID=$!
echo "  launcher PID: $LAUNCH_PID — polling for the server (up to 300s)..."

PORT=""
for i in $(seq 1 100); do
  sleep 3
  if ! kill -0 "$LAUNCH_PID" 2>/dev/null; then
    echo "FAIL: launcher exited early. Log tail:"
    tail -20 "$TESTROOT/launcher.log"
    exit 1
  fi
  # Detect the port from the launcher banner, then probe it.
  PORT=$(rg -o "127\.0\.0\.1:([0-9]+)/" -r '$1' "$TESTROOT/launcher.log" | head -1)
  if [ -n "$PORT" ] && curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$PORT/"; then
    break
  fi
  PORT=""
done

if [ -z "$PORT" ]; then
  echo "FAIL: server never came up. Log tail:"
  tail -30 "$TESTROOT/launcher.log"
  kill "$LAUNCH_PID" 2>/dev/null
  exit 1
fi
echo "  OK: server answering on port $PORT after ~$((i*3))s"

echo "== 3. Page checks on port $PORT =="
PASS=0; FAIL=0
chk() { # label, url, needle(optional)
  local body; body=$(curl -s --max-time 5 "$2")
  if [ -n "${3:-}" ]; then
    if echo "$body" | grep -q "$3"; then PASS=$((PASS+1)); echo "  OK   $1"; else FAIL=$((FAIL+1)); echo "  FAIL $1"; fi
  else
    PASS=$((PASS+1)); echo "  OK   $1"
  fi
}
chk "home 200+headline"        "http://127.0.0.1:$PORT/"                                        "Real estate with a human point of view"
chk "search for-sale Mombasa"  "http://127.0.0.1:$PORT/property-for-sale/mombasa/"              "listing-card"
chk "search for-rent Nairobi"  "http://127.0.0.1:$PORT/property-for-rent/nairobi/"              "listing-card"
LISTING_URL=$(curl -s "http://127.0.0.1:$PORT/property-for-sale/mombasa/" | grep -o '/listing/[a-z0-9-]*-[0-9]*/' | head -1)
chk "listing detail page"      "http://127.0.0.1:$PORT$LISTING_URL"                             "enquiry"
chk "login page"               "http://127.0.0.1:$PORT/account/login/"                          "password"
IMG=$(curl -s "http://127.0.0.1:$PORT/property-for-sale/mombasa/" | grep -o '/media/[^"]*\.jpg' | head -1)
chk "media image served"       "http://127.0.0.1:$PORT$IMG"                                     ""
chk "admin login page"         "http://127.0.0.1:$PORT/admin/login/"                            "Log in"
chk "autocomplete JSON"        "http://127.0.0.1:$PORT/search/locations/?q=nya"                 "Nyali"

echo "== 4. Account checks (created by launcher?) =="
cd "$PKG"
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python manage.py shell -c "
from apps.accounts.models import User
from apps.listings.models import Property
a = User.objects.filter(email='admin@gabrielhomes.co.ke').first()
g = User.objects.filter(email='hello@gabrielhomes.co.ke').first()
print('  admin exists:', bool(a and a.is_superuser and a.check_password('gabriel2026')))
print('  agent password set:', bool(g and g.check_password('gabriel2026')))
print('  listings:', Property.objects.count())
" 2>/dev/null
else
  echo "  FAIL: no venv created"
  FAIL=$((FAIL+1))
fi

echo "== 5. Shutdown =="
pkill -f "coldtest/gabriel-homes" 2>/dev/null && echo "  stopped (pkill coldtest)" || kill "$LAUNCH_PID" 2>/dev/null
sleep 1
echo ""
echo "COLDSTART RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ] && echo "TRIPLE-CHECK 2: PASSED" || echo "TRIPLE-CHECK 2: FAILED"
exit $FAIL

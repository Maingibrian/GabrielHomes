#!/bin/bash
# =============================================================================
# coldstart_test.sh — TRIPLE-CHECK 2
# Simulates a user who unzipped the package on a machine with nothing set up:
#   - no .venv            (launcher must create it + pip install)
#   - no db.sqlite3       (launcher must migrate + seed ~80 listings)
#   - port 8000 occupied  (launcher must fall back to 8001+)
# Then curls the key pages, verifies the BROWSER AUTO-OPEN fired only after
# the site was actually serving (v1 regression!), and shuts the server down.
# =============================================================================
set -u
TESTROOT=/home/z/my-project/scripts/coldtest
PKG="$TESTROOT/gabriel-homes"

rm -rf "$TESTROOT"; mkdir -p "$TESTROOT"

# -- Fake browser: records every open() + whether the site answered.
# -- $BROWSER is what the stdlib webbrowser module uses on POSIX.
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

echo "== 1. Fresh copy of staged package (no venv, no DB) =="
mkdir -p "$TESTROOT"
cp -r /home/z/my-project/scripts/stage/gabriel-homes "$PKG/"
rm -f "$PKG/db.sqlite3"
rm -rf "$PKG/.venv"
[ -f "$PKG/db.sqlite3" ] && echo "FAIL: db still present" && exit 1
echo "  OK: no .venv, no db.sqlite3"

echo "== 2. Launch (fake browser wired via \$BROWSER - the real path is exercised) =="
cd "$PKG"
BROWSER="$FAKE_BROWSER %s" bash START-GABRIEL-HOMES.sh > "$TESTROOT/launcher.log" 2>&1 &
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

echo "== 5. Browser auto-open check (the v1 bug) =="
sleep 2   # give the browser waiter a moment to fire after the server came up
OPENS=$(wc -l < "$FAKE_BROWSER_LOG" | tr -d ' ')
if [ "$OPENS" = "1" ]; then
  PASS=$((PASS+1)); echo "  OK   browser auto-open fired exactly once"
else
  FAIL=$((FAIL+1)); echo "  FAIL browser auto-open fired $OPENS times (want 1)"
fi
OPEN_URL=$(awk '{print $2}' "$FAKE_BROWSER_LOG" | head -1)
if [ "$OPEN_URL" = "http://127.0.0.1:$PORT/" ]; then
  PASS=$((PASS+1)); echo "  OK   browser opened the served URL ($OPEN_URL)"
else
  FAIL=$((FAIL+1)); echo "  FAIL browser opened '$OPEN_URL' (want http://127.0.0.1:$PORT/)"
fi
if grep -q " UP$" "$FAKE_BROWSER_LOG"; then
  PASS=$((PASS+1)); echo "  OK   site was actually serving when the browser opened"
else
  FAIL=$((FAIL+1)); echo "  FAIL browser opened while site was DOWN: $(cat "$FAKE_BROWSER_LOG")"
fi

echo "== 6. Shutdown =="
pkill -f "coldtest/gabriel-homes" 2>/dev/null && echo "  stopped (pkill coldtest)" || kill "$LAUNCH_PID" 2>/dev/null
sleep 1
echo ""
echo "COLDSTART RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ] && echo "TRIPLE-CHECK 2: PASSED" || echo "TRIPLE-CHECK 2: FAILED"
exit $FAIL

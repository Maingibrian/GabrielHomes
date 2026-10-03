#!/bin/bash
# =============================================================================
# browser_helper_test.sh — verifies scripts/open_browser_when_ready.py
#
# Regression test for the v1 bug: launchers opened the browser BEFORE the
# server listened (users got ERR_CONNECTION_REFUSED / nothing at all).
#
# Cases:
#   A. Server comes up 2s AFTER the helper starts  -> browser fires, and
#      only AFTER the server was actually reachable (race is dead).
#   B. Server never comes up                       -> loud URL warning, exit 0.
#   C. GABRIEL_NO_BROWSER=1                        -> immediate exit, no open.
#   D. No browser available at all                 -> loud manual-URL warning.
# =============================================================================
set -u
T=/home/z/my-project/scripts/browsertest
HELPER=/home/z/my-project/gabriel_homes/scripts/open_browser_when_ready.py
PY=/home/z/my-project/gabriel_homes/.venv/bin/python
[ -x "$PY" ] || PY="$(command -v python3)"

rm -rf "$T"; mkdir -p "$T"

# Fake browser: the harness points $BROWSER at it; it logs every URL it
# gets AND whether the site actually answered at the moment of opening -
# the exact user-facing guarantee the v1 bug violated.
cat > "$T/fake-browser.sh" <<'EOF'
#!/bin/bash
URL="$1"
if curl -s -o /dev/null --max-time 2 "$URL"; then STATE=UP; else STATE=DOWN; fi
echo "$(date +%s.%N) $URL $STATE" >> "${FAKE_BROWSER_LOG:?}"
exit 0
EOF
chmod +x "$T/fake-browser.sh"

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "  OK   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }

# ------------------------------------------------------------------ Case A --
echo "== A. browser fires only after the server is really up =="
PORT_A=8771
FAKE_BROWSER_LOG="$T/a.log"; export FAKE_BROWSER_LOG
: > "$FAKE_BROWSER_LOG"
# Server starts 2 seconds LATER than the helper - the old code opened the
# browser instantly; the helper must wait for the server instead.
( sleep 2 && exec python3 -m http.server "$PORT_A" --bind 127.0.0.1 ) >/dev/null 2>&1 &
SRV_A=$!
python3 -c "import time; print(time.time())" > "$T/helper_started_at"
BROWSER="$T/fake-browser.sh %s" "$PY" "$HELPER" "$PORT_A" > "$T/a.out" 2>&1 &
HELPER_A=$!
wait "$HELPER_A" || true
kill "$SRV_A" 2>/dev/null

HITS=$(wc -l < "$FAKE_BROWSER_LOG" | tr -d ' ')
[ "$HITS" = "1" ] && ok "browser opened exactly once" || bad "browser opened $HITS times (want 1)"
grep -q "http://127.0.0.1:$PORT_A/" "$FAKE_BROWSER_LOG" \
  && ok "fake browser received the correct URL" || bad "wrong/missing URL: $(cat "$FAKE_BROWSER_LOG")"
grep -q " UP$" "$FAKE_BROWSER_LOG" \
  && ok "site was actually serving at the moment the browser opened" \
  || bad "browser opened while site was DOWN: $(cat "$FAKE_BROWSER_LOG")"
OPENED_AT=$(cut -d' ' -f1 "$FAKE_BROWSER_LOG" | head -1)
STARTED_AT=$(cat "$T/helper_started_at")
WAITED=$(python3 -c "print(f'{float('$OPENED_AT') - float('$STARTED_AT'):.1f}')")
LATE_OK=$(python3 -c "print(1 if float('$OPENED_AT') - float('$STARTED_AT') >= 2.0 else 0)")
[ "$LATE_OK" = "1" ] && ok "waited ${WAITED}s for the late server (v1 bug opened at ~0s)" \
                      || bad "opened after only ${WAITED}s - race still present"
grep -q "Browser opened" "$T/a.out" && ok "helper logged success" || bad "no success log: $(cat "$T/a.out")"

# ------------------------------------------------------------------ Case B --
echo "== B. server never comes up -> loud warning, still exit 0 =="
: > "$FAKE_BROWSER_LOG"
BROWSER="$T/fake-browser.sh %s" "$PY" "$HELPER" 8772 > "$T/b.out" 2>&1
RC_B=$?
grep -q "did not respond" "$T/b.out" && ok "timeout warning printed" || bad "no timeout warning: $(cat "$T/b.out")"
grep -q "http://127.0.0.1:8772/" "$T/b.out" && ok "warning contains the URL" || bad "URL missing from warning"
[ -s "$FAKE_BROWSER_LOG" ] && bad "browser must NOT fire on timeout" || ok "browser not fired on timeout"
[ "$RC_B" = "0" ] && ok "exit code 0 (non-fatal)" || bad "exit code $RC_B"

# ------------------------------------------------------------------ Case C --
echo "== C. GABRIEL_NO_BROWSER=1 -> no-op =="
PORT_C=8773
python3 -m http.server "$PORT_C" --bind 127.0.0.1 >/dev/null 2>&1 &
SRV_C=$!
sleep 0.5
: > "$FAKE_BROWSER_LOG"
BROWSER="$T/fake-browser.sh %s" GABRIEL_NO_BROWSER=1 "$PY" "$HELPER" "$PORT_C" > "$T/c.out" 2>&1
RC_C=$?
[ -s "$FAKE_BROWSER_LOG" ] && bad "browser fired despite GABRIEL_NO_BROWSER" || ok "browser not fired"
[ "$RC_C" = "0" ] && ok "exit code 0" || bad "exit code $RC_C"
kill "$SRV_C" 2>/dev/null

# ------------------------------------------------------------------ Case D --
echo "== D. no browser available -> loud manual-URL message =="
PORT_D=8774
python3 -m http.server "$PORT_D" --bind 127.0.0.1 >/dev/null 2>&1 &
SRV_D=$!
sleep 0.5
env -u BROWSER -u DISPLAY "$PY" "$HELPER" "$PORT_D" > "$T/d.out" 2>&1
RC_D=$?
grep -q "COULD NOT OPEN A BROWSER" "$T/d.out" && ok "manual-open warning printed" || bad "no manual-open warning: $(cat "$T/d.out")"
grep -q "http://127.0.0.1:$PORT_D/" "$T/d.out" && ok "warning contains URL" || bad "URL missing"
[ "$RC_D" = "0" ] && ok "exit code 0" || bad "exit code $RC_D"
kill "$SRV_D" 2>/dev/null

echo ""
echo "BROWSER-HELPER RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ] && echo "BROWSER PATH: VERIFIED" || echo "BROWSER PATH: FAILED"
exit "$FAIL"

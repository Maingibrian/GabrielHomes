#!/bin/bash
# =============================================================================
# verify_v3_zip.sh — final delivery gate run against the SHIPPED zip itself.
# 1. Extract launchers from the zip and re-run every build gate on THEM.
# 2. Fresh-unzip the whole zip; assert structure (no junk, exec bits, CRLF/LF).
# 3. Hand off to zipboot_test.sh (boots the extracted copy, browser checks).
# 4. Run browser_helper_test.sh (unit harness for the browser path).
# =============================================================================
set -uo pipefail

ZIP=/home/z/my-project/download/gabriel-homes-oneclick.zip
WORK=/home/z/my-project/scripts/ziptest
GATE=/home/z/my-project/scripts/ziptest-gate
SCRIPTS=/home/z/my-project/scripts

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "  OK   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }

echo "== 1. Gates on the SHIPPED launchers (extracted from the zip) =="
rm -rf "$GATE"; mkdir -p "$GATE"
unzip -q "$ZIP" 'gabriel-homes/START-GABRIEL-HOMES.bat' \
                 'gabriel-homes/START-GABRIEL-HOMES.sh' \
                 'gabriel-homes/STOP-WEBSITE.bat' \
                 'gabriel-homes/RUN-ME-FIRST.txt' \
                 'gabriel-homes/scripts/open_browser_when_ready.py' -d "$GATE"
GBP="$GATE/gabriel-homes"

python3 - "$GBP" <<'PYEOF'
rc = 0
import re, sys
from pathlib import Path
pkg = Path(sys.argv[1])

helper = pkg / "scripts" / "open_browser_when_ready.py"
assert helper.is_file(), "browser helper missing"
sh  = (pkg / "START-GABRIEL-HOMES.sh").read_text()
bat = (pkg / "START-GABRIEL-HOMES.bat").read_text()
assert "open_browser_when_ready.py" in sh, "sh does not call browser helper"
assert "open_browser_when_ready.py" in bat, "bat does not call browser helper"
assert "sleep 2" not in sh, "sh still uses racy fixed sleep"
assert 'start "" "http://' not in bat, "bat opens browser before server"
# v3 UNC handling must be present in the SHIPPED bat
assert 'SRCDIR:~0,2' in bat, "bat has no UNC detection"
assert '\\\\' in bat, "bat has no UNC backslash test"  # two literal backslashes
assert "robocopy" in bat and "LOCALAPPDATA" in bat, "bat has no copy-to-local logic"
assert bat.count("zip window") >= 1, "guard message missing"
# block-paren audit (the v1/v2 Windows-killer bug class)
def strip_quotes(line): return re.sub(r'"[^"]*"', "Q", line)
depth = 0; violations = []
for n, raw in enumerate(bat.splitlines(), 1):
    code = strip_quotes(raw).strip()
    if not code or code.lower().startswith("rem"):
        if depth > 0:
            no_esc = re.sub(r"\^\)", "", strip_quotes(raw).strip())
            if ")" in no_esc:
                violations.append(f"line {n}: unquoted ')' inside block")
        continue
    body = strip_quotes(raw); stripped = body.strip()
    cmd = stripped.split()[0].lower() if stripped.split() else ""
    if cmd == "echo" and depth > 0:
        no_esc = re.sub(r"\^\)", "", stripped)
        if ")" in no_esc.rstrip(">").rstrip():
            violations.append(f"line {n}: unquoted ')' in echo inside block")
    if stripped.endswith("("): depth += 1
    if stripped.startswith(")"): depth -= 1
if depth != 0: violations.append(f"unbalanced blocks: depth {depth}")
assert not violations, "BAT BLOCK-PAREN BUGS: " + "; ".join(violations)
print("     (helper present, browser chain intact, UNC handling present, paren audit clean)")
PYEOF
PYRC=$?
[ $PYRC -eq 0 ] && ok "static gates on shipped .bat/.sh (browser chain, UNC, paren-audit)" || bad "static gates on shipped launchers (rc=$PYRC)"

# CRLF / LF encoding of shipped files
file "$GBP/START-GABRIEL-HOMES.bat" | grep -q CRLF && ok "shipped .bat is CRLF" || bad "shipped .bat is not CRLF"
file "$GBP/START-GABRIEL-HOMES.sh"  | grep -q CRLF && bad "shipped .sh has CRLF (must be LF)" || ok "shipped .sh is LF"
grep -qi "network drive" "$GBP/RUN-ME-FIRST.txt" && ok "RUN-ME documents network-drive behaviour" || bad "RUN-ME missing network-drive docs"

echo "== 2. Fresh unzip + structure =="
rm -rf "$WORK"; mkdir -p "$WORK"
unzip -q "$ZIP" -d "$WORK"
JUNK=$(cd "$WORK" && find . \( -name '__pycache__' -o -name '.venv' -o -name '*.pyc' -o -name '.pytest_cache' -o -name 'staticfiles' \) | wc -l)
[ "$JUNK" = "0" ] && ok "0 junk entries in zip" || bad "$JUNK junk entries in zip"
for f in gabriel-homes/START-GABRIEL-HOMES.bat gabriel-homes/START-GABRIEL-HOMES.sh gabriel-homes/STOP-WEBSITE.bat gabriel-homes/RUN-ME-FIRST.txt gabriel-homes/manage.py gabriel-homes/db.sqlite3 gabriel-homes/scripts/open_browser_when_ready.py gabriel-homes/scripts/find_free_port.py gabriel-homes/scripts/setup_accounts.py gabriel-homes/requirements.txt; do
  [ -e "$WORK/$f" ] && ok "present: $f" || bad "MISSING: $f"
done
[ -x "$WORK/gabriel-homes/START-GABRIEL-HOMES.sh" ] && ok ".sh is executable" || bad ".sh not executable"

echo "== 3. Boot the shipped copy exactly as a user would =="
if bash "$SCRIPTS/zipboot_test.sh"; then ok "zipboot e2e (server+data+browser)"; else bad "zipboot e2e"; fi

echo "== 4. Browser-helper unit harness =="
if bash "$SCRIPTS/browser_helper_test.sh" > /tmp/bh.log 2>&1; then ok "browser-helper harness (14 checks)"; tail -2 /tmp/bh.log; else bad "browser-helper harness"; tail -15 /tmp/bh.log; fi

echo ""
echo "=================================================="
echo "V3 FINAL DELIVERY GATE: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ] && echo "RESULT: CLEARED FOR DELIVERY" || echo "RESULT: DO NOT DELIVER"
exit $FAIL

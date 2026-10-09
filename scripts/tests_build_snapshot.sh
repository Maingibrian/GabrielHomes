#!/usr/bin/env bash
# =============================================================================
# tests_build_snapshot.sh — H4 regression test for build_workspace_snapshot.sh.
#
# Builds a disposable FAKE workspace in /tmp, plants leaks (db.sqlite3,
# download/, upload/, scripts/server.log, .git/) and a marker file, then runs
# the real builder with:
#   - WS_ROOT pointing at the fake workspace (override must be honored)
#   - an explicit output path as argument 1
#
# Asserts:
#   1. builder exit code 0
#   2. reported "snapshot: N files" equals the zip's own entry count
#   3. zip contains the marker + gabriel_homes/.env.example + docs/STATUS.md
#   4. zip contains none of: db.sqlite3, download/, upload/, scripts/server.log, .git/
#
# Run:  bash scripts/tests_build_snapshot.sh   (exit 0 = GREEN)
# The produced zip is kept at /tmp/h4test-snapshot.zip for check_export.sh.
# =============================================================================
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILDER="$REPO_ROOT/scripts/build_workspace_snapshot.sh"
T="/tmp/h4test-ws.$$"
OUT="/tmp/h4test-snapshot.zip"
rm -rf "$T" "$OUT"
trap 'rm -rf "$T"' EXIT

# ---------------------------------------------------------- fake workspace
WS="$T/ws"
mkdir -p "$WS/gabriel_homes/docs" "$WS/scripts/preview_site" "$WS/download" "$WS/upload" "$WS/.git"
: > "$WS/gabriel_homes/.env.example"
: > "$WS/gabriel_homes/.gitignore"
: > "$WS/gabriel_homes/manage.py"
: > "$WS/gabriel_homes/H4MARKER.txt"          # proves WS_ROOT override is honored
: > "$WS/gabriel_homes/docs/STATUS.md"
: > "$WS/gabriel_homes/docs/AGENT-BRIEF.md"
: > "$WS/gabriel_homes/db.sqlite3"            # planted leak — must be excluded
: > "$WS/scripts/server.log"                  # planted leak — must be excluded
: > "$WS/scripts/preview_site/index.html"
: > "$WS/download/leak.zip"                   # planted leak — must be excluded
: > "$WS/upload/leak.txt"                     # planted leak — must be excluded
: > "$WS/.git/config"                         # planted leak — must be excluded

fails=0
ok()   { printf 'ok:   %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*"; fails=$((fails+1)); }

# ---------------------------------------------------------------- run it
if WS_ROOT="$WS" bash "$BUILDER" "$OUT" > "$T/build.log" 2>&1; then
  ok "builder exited 0"
else
  fail "builder exited non-zero"
  tail -5 "$T/build.log"
fi

[ -f "$OUT" ] || { fail "no zip produced at $OUT"; exit 1; }

# --------------------------------------------- 1. reported count == zip count
entries="$(unzip -Z1 "$OUT" | grep -vc '/$')"
reported="$(sed -n 's/^snapshot: \([0-9][0-9]*\) files.*/\1/p' "$T/build.log" | tail -1)"
if [ -n "$reported" ] && [ "$reported" -eq "$entries" ]; then
  ok "reported count ($reported) == zip entry count ($entries)"
else
  fail "reported count '${reported:-<none>}' != zip entry count ($entries)"
fi

# --------------------------------------------------------- 2. required content
for need in gabriel_homes/H4MARKER.txt gabriel_homes/.env.example gabriel_homes/docs/STATUS.md; do
  if unzip -Z1 "$OUT" | grep -Fxq "$need"; then
    ok "zip contains $need"
  else
    fail "zip missing $need (WS_ROOT override honored? dotfiles kept?)"
  fi
done

# --------------------------------------------------------- 3. forbidden content
for bad in '(^|/)db\.sqlite3$' '(^|/)download/' '(^|/)upload/' '(^|/)scripts/server\.log$' '(^|/)\.git/'; do
  hits="$(unzip -Z1 "$OUT" | grep -E "$bad" | head -3)"
  if [ -z "$hits" ]; then
    ok "no entries matching $bad"
  else
    fail "forbidden entries matching $bad: $hits"
  fi
done

echo "----"
if [ "$fails" -eq 0 ]; then
  echo "H4 TEST: GREEN — all assertions passed (zip kept at $OUT)"
  exit 0
else
  echo "H4 TEST: RED — $fails assertion group(s) failed"
  exit 1
fi

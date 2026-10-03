#!/bin/bash
# =============================================================================
# build_package.sh — build the one-click Gabriel Homes zip for delivery.
#
# Steps:
#   0. Hygiene-clean the source demo DB (test inquiries, stale sessions)
#   1. Stage the project (rsync, excluding dev-only artefacts)
#   2. Add the one-click launchers (sh/command/bat), RUN-ME guide
#   3. Fix line endings: .bat -> CRLF, unix scripts -> LF; chmod +x
#   4. Zip into /home/z/my-project/download/gabriel-homes-oneclick.zip
# =============================================================================
set -euo pipefail

SRC=/home/z/my-project/gabriel_homes
STAGE=/home/z/my-project/scripts/stage
PKG="$STAGE/gabriel-homes"
LAUNCH=/home/z/my-project/scripts/launcher
OUT=/home/z/my-project/download/gabriel-homes-oneclick.zip
VPY="$SRC/.venv/bin/python"

# -- Self-heal: the dev venv may be missing (fresh checkout/cleanup).
if [ ! -x "$VPY" ]; then
  echo "   .venv missing -> recreating it (one time)..."
  python3 -m venv "$SRC/.venv"
  "$VPY" -m pip install --quiet --disable-pip-version-check -r "$SRC/requirements.txt"
  touch "$SRC/.venv/.deps_ok"
fi

# -- Self-heal: the demo DB must ship pre-seeded; rebuild if absent.
if [ ! -f "$SRC/db.sqlite3" ]; then
  echo "   db.sqlite3 missing -> migrating + seeding a fresh demo DB..."
  (cd "$SRC" && "$VPY" manage.py migrate --noinput >/dev/null \
     && "$VPY" manage.py seed_demo >/dev/null \
     && "$VPY" manage.py shell < scripts/setup_accounts.py >/dev/null)
fi

echo "== 0. DB hygiene on source =="
cd "$SRC"
"$VPY" manage.py shell -c "
from apps.inquiries.models import Inquiry
from django.contrib.sessions.models import Session
from apps.listings.models import Property
n1, _ = Inquiry.objects.filter(email__regex=r'@(test|spam)\.com$').delete()
n2, _ = Session.objects.all().delete()
n3, _ = Property.objects.filter(title__startswith='Agent Test ').delete()
print(f'  removed inquiries: {n1}, sessions: {n2}, test listings: {n3}')
" 2>/dev/null

echo "== 1. Stage project =="
rm -rf "$STAGE"
mkdir -p "$STAGE"
rsync -a \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude 'htmlcov/' \
  --exclude '.coverage' \
  --exclude 'staticfiles/' \
  --exclude '.DS_Store' \
  --exclude '*.sqlite3-journal' \
  --exclude '*.sqlite3-wal' \
  --exclude '*.sqlite3-shm' \
  "$SRC/" "$PKG/"

echo "== 2. Add launchers + guide =="
cp "$LAUNCH/START-GABRIEL-HOMES.sh"      "$PKG/START-GABRIEL-HOMES.sh"
cp "$LAUNCH/START-GABRIEL-HOMES.sh"      "$PKG/START-GABRIEL-HOMES.command"
cp "$LAUNCH/START-GABRIEL-HOMES.bat"     "$PKG/START-GABRIEL-HOMES.bat"
cp "$LAUNCH/STOP-WEBSITE.sh"             "$PKG/STOP-WEBSITE.sh"
cp "$LAUNCH/STOP-WEBSITE.sh"             "$PKG/STOP-WEBSITE.command"
cp "$LAUNCH/STOP-WEBSITE.bat"            "$PKG/STOP-WEBSITE.bat"
cp "$LAUNCH/RUN-ME-FIRST.txt"            "$PKG/RUN-ME-FIRST.txt"

echo "== 3. Line endings + exec bits =="
# Windows launchers must be CRLF; unix launchers must be LF.
python3 - <<'PYEOF'
import re
from pathlib import Path

pkg = Path("/home/z/my-project/scripts/stage/gabriel-homes")
for name in ("START-GABRIEL-HOMES.bat", "STOP-WEBSITE.bat"):
    p = pkg / name
    text = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    p.write_bytes(text)
    print(f"  CRLF: {name} ({len(text)} bytes)")
for name in ("START-GABRIEL-HOMES.sh", "START-GABRIEL-HOMES.command",
             "STOP-WEBSITE.sh", "STOP-WEBSITE.command"):
    p = pkg / name
    text = p.read_bytes().replace(b"\r\n", b"\n")
    p.write_bytes(text)
    print(f"  LF:   {name} ({len(text)} bytes)")

# -- Sanity gates: the browser-opening chain must be intact in the staged
# -- package, or the v1 'browser never opened' bug ships again.
helper = pkg / "scripts" / "open_browser_when_ready.py"
assert helper.is_file(), "browser helper missing from staged package"
sh = (pkg / "START-GABRIEL-HOMES.sh").read_text()
bat = (pkg / "START-GABRIEL-HOMES.bat").read_text()
assert "open_browser_when_ready.py" in sh, "sh launcher does not call the browser helper"
assert "open_browser_when_ready.py" in bat, "bat launcher does not call the browser helper"
assert "sleep 2" not in sh, "sh launcher still uses the racy fixed sleep"
assert 'start "" "http://' not in bat, "bat launcher still opens the browser before the server starts"
print("  sanity: browser-open chain present in staged launchers")
PYEOF
chmod +x "$PKG/START-GABRIEL-HOMES.sh" "$PKG/START-GABRIEL-HOMES.command" \
         "$PKG/STOP-WEBSITE.sh" "$PKG/STOP-WEBSITE.command"

echo "== 4. Zip =="
mkdir -p /home/z/my-project/download
rm -f "$OUT"
(cd "$STAGE" && zip -rq "$OUT" gabriel-homes)
ls -lh "$OUT"
echo "== Package built: $OUT =="

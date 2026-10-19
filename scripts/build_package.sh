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
if [ ! -f "$SRC/db.sqlite3" ] || [ ! -s "$SRC/db.sqlite3" ]; then
  echo "   db.sqlite3 missing/empty -> migrating + seeding a fresh demo DB..."
  (cd "$SRC" && "$VPY" manage.py migrate --noinput >/dev/null \
     && "$VPY" manage.py seed_demo >/dev/null \
     && "$VPY" manage.py import_real_listing >/dev/null \
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
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude 'htmlcov/' \
  --exclude '.coverage' \
  --exclude 'staticfiles/' \
  --exclude '/wheels/' \
  --exclude '.DS_Store' \
  --exclude 'preview_bridge.log' \
  --exclude 'media/real-listing-src/' \
  --exclude '/property-images/' \
  --exclude 'docs/shots/' \
  --exclude 'docs/a11y/' \
  --exclude '/design-reference/' \
  --exclude 'runserver.log' \
  --exclude '*.sqlite3-journal' \
  --exclude '*.sqlite3-wal' \
  --exclude '*.sqlite3-shm' \
  "$SRC/" "$PKG/"

# -- H2 dotfile guarantee: these files are part of the deliverable (setup and
# -- repo hygiene for the buyer); if staging ever drops dotfiles again, fail
# -- here instead of shipping a broken zip.
echo "== 1b. Dotfile guarantee =="
for f in .env.example .gitignore docs/STATUS.md docs/AGENT-BRIEF.md manage.py; do
  if [ ! -f "$PKG/$f" ]; then
    echo "FATAL: $f missing from staged package (dotfiles dropped in staging?)" >&2
    exit 1
  fi
done
echo "  dotfiles present in package: .env.example .gitignore docs/STATUS.md docs/AGENT-BRIEF.md"

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
bat_names = ("START-GABRIEL-HOMES.bat", "STOP-WEBSITE.bat", "UPDATE-WEBSITE.bat")
for name in bat_names:
    p = pkg / name
    if not p.is_file():
        continue  # launcher bats are copied in step 2; UPDATE lives in the tree
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

# -- .bat block-paren audit: in cmd, an UNQUOTED ')' inside an echo/rem line
# -- that sits within an if/for (...) block terminates the block early and
# -- aborts or corrupts the script. This exact bug class broke the v1+v2
# -- Windows launchers (script died at 'Creating virtual environment (.venv)').
# -- We have no Windows box in CI, so enforce it statically.
import re

def strip_quotes(line: str) -> str:
    return re.sub(r'"[^"]*"', "Q", line)

depth = 0
violations = []
for n, raw in enumerate(bat.splitlines(), 1):
    code = strip_quotes(raw).strip()
    if not code or code.lower().startswith("rem"):
        # rem lines still break blocks on ')', so audit their text when inside blocks
        if depth > 0:
            no_esc = re.sub(r"\^\)", "", strip_quotes(raw).strip())
            if ")" in no_esc:
                violations.append(f"line {n}: unquoted ')' inside block: {raw.strip()[:70]}")
        continue
    body = strip_quotes(raw)
    stripped = body.strip()
    cmd = stripped.split()[0].lower() if stripped.split() else ""
    if cmd == "echo" and depth > 0:
        # any unquoted ')' that is not an escaped '^)' and not the line's
        # trailing block-terminator is forbidden inside a block
        no_esc = re.sub(r"\^\)", "", stripped)
        if ")" in no_esc.rstrip(">").rstrip():
            violations.append(f"line {n}: unquoted ')' in echo inside block: {raw.strip()[:70]}")
    # block-depth tracking (quoted text already neutralised)
    if stripped.endswith("("):
        depth += 1
    if stripped.startswith(")"):
        depth -= 1
if depth != 0:
    violations.append(f"unbalanced blocks: final depth {depth}")
assert not violations, "BAT BLOCK-PAREN BUGS:\n" + "\n".join(violations)
print("  sanity: .bat block-paren audit clean")
PYEOF
chmod +x "$PKG/START-GABRIEL-HOMES.sh" "$PKG/START-GABRIEL-HOMES.command" \
         "$PKG/STOP-WEBSITE.sh" "$PKG/STOP-WEBSITE.command"

echo "== 4. Zip =="
# Build stamp so the user can verify WHICH build they extracted (releases
# share one zip filename; a stale download is invisible otherwise).
GIT_SHA="$(git -C /home/z/my-project rev-parse --short HEAD 2>/dev/null || echo unknown)"
cat > "$PKG/BUILD-INFO.txt" <<STAMP
Gabriel Homes — package build stamp
  built (UTC) : $(date -u '+%Y-%m-%d %H:%M')
  release     : ${RELEASE_TAG:-dev}
  git commit  : $GIT_SHA
  bento patch : r16 (owner bento-shift.patch applied verbatim)
Check the zip you downloaded matches the md5 shown on the delivery page,
and that THIS file exists at the top of your extracted gabriel-homes folder.
STAMP
mkdir -p /home/z/my-project/download
rm -f "$OUT"
# zip by directory NAME (not by glob): 'zip -rq out *' would silently drop
# every dotfile at the staging root — the H2 bug class.
(cd "$STAGE" && zip -rq "$OUT" gabriel-homes)
# post-zip proof the dotfiles made it into the archive.
# Capture the listing ONCE, then grep the captured text. An
# 'unzip -l | grep -q' pipeline is racy under 'set -o pipefail':
# grep -q exits at the first match, unzip gets SIGPIPE (exit 141),
# and the check reports a false FATAL on a perfectly good zip.
ZIP_LISTING="$(unzip -l "$OUT")"
for f in gabriel-homes/.env.example gabriel-homes/.gitignore gabriel-homes/docs/STATUS.md; do
  grep -q " $f\$" <<<"$ZIP_LISTING" || { echo "FATAL: $f missing from $OUT" >&2; exit 1; }
done
echo "  zip verified: .env.example/.gitignore/docs present in archive"
ls -lh "$OUT"
echo "== Package built: $OUT =="

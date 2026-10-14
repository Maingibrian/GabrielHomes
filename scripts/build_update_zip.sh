#!/usr/bin/env bash
# Build a rootless Gabriel Homes UPDATE zip (code only — no db/media/venv/.env).
# "Rootless" = manage.py sits at the TOP of the archive, so the update can be
# extracted straight over an existing install (both UPDATE-WEBSITE.sh and
# UPDATE-WEBSITE.bat rely on that contract).
# Result: /home/z/my-project/download/gabriel-homes-update-YYYY-MM-DD.zip
set -euo pipefail

GH=/home/z/my-project/gabriel_homes
OUT_DIR=/home/z/my-project/download
DATE=$(date +%F)
UPDATE_TAG="${UPDATE_TAG:-}"
OUT="$OUT_DIR/gabriel-homes-update-$DATE${UPDATE_TAG:+-$UPDATE_TAG}.zip"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

# The update zip MUST carry the Windows wheels: the user's corporate network
# can block pypi.org, and the updaters repair a broken .venv OFFLINE from
# wheels/ (see UPDATE-WEBSITE.bat STEP 6 / START-GABRIEL-HOMES.bat deps ladder).
# Refresh them with scripts/vendor_wheels.sh whenever requirements.txt changes.
if [ ! -e "$GH/requirements.txt" -o "$GH/requirements.txt" -nt "$GH/wheels" ]; then
  echo "WARNING: requirements.txt is newer than wheels/ - run scripts/vendor_wheels.sh" >&2
fi
ls "$GH"/wheels/*.whl >/dev/null 2>&1 || {
  echo "FATAL: gabriel_homes/wheels/ has no wheels - run scripts/vendor_wheels.sh first" >&2
  exit 1
}
for pat in 'django-.*\.whl' 'pillow-.*\.whl' 'psycopg_binary-.*\.whl'; do
  ls "$GH/wheels" | grep -Eiq "$pat" || { echo "FATAL: $pat wheel missing from wheels/" >&2; exit 1; }
done
echo "  wheels: $(ls "$GH"/wheels/*.whl | wc -l) files, $(du -sh "$GH/wheels" | cut -f1)"

cd "$GH"
# Rootless staging: rsync DIRECTLY into $STAGE (no gabriel-homes/ wrapper).
rsync -a \
  --exclude '.venv/' \
  --exclude 'media/' \
  --exclude 'db.sqlite3' \
  --exclude 'staticfiles/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'nohup.out' \
  --exclude '*.log' \
  --exclude '.pytest_cache/' \
  --exclude '.coverage' \
  --exclude 'htmlcov/' \
  --exclude 'docs/shots/' \
  --exclude 'property-images/' \
  --exclude 'static/video/' \
  --exclude '*.sqlite3-journal' \
  --exclude '*.sqlite3-wal' \
  --exclude '*.sqlite3-shm' \
  --exclude '.DS_Store' \
  "$GH/" "$STAGE/"

echo "== line endings: .bat -> CRLF =="
# Launcher bats must ride along with every update: otherwise a site
# installed from an old oneclick keeps its OLD launcher forever (the
# updater would never refresh it). Staged from the single source of
# truth in scripts/launcher/.
cp /home/z/my-project/scripts/launcher/START-GABRIEL-HOMES.bat "$STAGE/"
cp /home/z/my-project/scripts/launcher/STOP-WEBSITE.bat "$STAGE/"
python3 - "$STAGE" <<'PYEOF'
import sys
from pathlib import Path

stage = Path(sys.argv[1])
bats = sorted(stage.rglob("*.bat"))
if not bats:
    raise SystemExit("FATAL: no .bat files staged")
for p in bats:
    text = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    p.write_bytes(text)
    print(f"  CRLF: {p.relative_to(stage)} ({len(text)} bytes)")

# .bat block-paren audit: an UNQUOTED ')' inside an echo/rem line that sits
# within an if/for (...) block terminates the block early and corrupts the
# script. Same audit as build_package.sh — we have no Windows box in CI.
import re

def strip_quotes(line: str) -> str:
    return re.sub(r'"[^"]*"', "Q", line)

for p in bats:
    depth = 0
    violations = []
    for n, raw in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        code = strip_quotes(raw).strip()
        if not code or code.lower().startswith("rem"):
            if depth > 0:
                no_esc = re.sub(r"\^\)", "", strip_quotes(raw).strip())
                if ")" in no_esc:
                    violations.append(f"line {n}: unquoted ')' inside block: {raw.strip()[:70]}")
            continue
        body = strip_quotes(raw)
        stripped = body.strip()
        cmd = stripped.split()[0].lower() if stripped.split() else ""
        if cmd == "echo" and depth > 0:
            no_esc = re.sub(r"\^\)", "", stripped)
            if ")" in no_esc.rstrip(">").rstrip():
                violations.append(f"line {n}: unquoted ')' in echo inside block: {raw.strip()[:70]}")
        if stripped.endswith("("):
            depth += 1
        if stripped.startswith(")"):
            depth -= 1
    if depth != 0:
        violations.append(f"unbalanced blocks: final depth {depth}")
    assert not violations, f"{p.name} BLOCK-PAREN BUGS:\n" + "\n".join(violations)
    print(f"  audit: {p.name} block-paren clean")
PYEOF

echo "== sanity checks =="
if [ -f "$STAGE/gabriel-homes/manage.py" ]; then
  echo "FATAL: zip is WRAPPED (gabriel-homes/ prefix) - the updaters need a ROOTLESS zip" >&2
  exit 1
fi
for f in manage.py UPDATE-WEBSITE.sh UPDATE-WEBSITE.bat START-GABRIEL-HOMES.bat STOP-WEBSITE.bat requirements.txt templates apps config static scripts; do
  [ -e "$STAGE/$f" ] || { echo "FATAL: $f missing from staged update" >&2; exit 1; }
done
grep -q $'\r' "$STAGE/UPDATE-WEBSITE.bat" || { echo "FATAL: UPDATE-WEBSITE.bat is not CRLF" >&2; exit 1; }
echo "  staged tree: rootless + all updaters present + bat is CRLF"

mkdir -p "$OUT_DIR"
rm -f "$OUT"
(cd "$STAGE" && zip -rq "$OUT" . -x '*/.git/*' -x '.git/*')

echo "== built: $OUT =="
ls -la "$OUT"
ZIP_LISTING="$(unzip -l "$OUT")"
if ! echo "$ZIP_LISTING" | grep -Eq '(^| )manage\.py$'; then
  echo "FATAL: manage.py is not at the top of the zip (layout changed?)" >&2
  exit 1
fi
echo "  manage.py at top: OK"
if ! echo "$ZIP_LISTING" | grep -Eq '(^| )UPDATE-WEBSITE\.bat$'; then
  echo "FATAL: UPDATE-WEBSITE.bat missing from the zip top level" >&2
  exit 1
fi
echo "  UPDATE-WEBSITE.bat at top: OK"
if echo "$ZIP_LISTING" | grep -Eq 'db\.sqlite3|/media/|\.venv/| \.env$'; then
  echo "FATAL: forbidden file (db/media/venv/.env) inside the zip" >&2
  exit 1
fi
echo "  no db/media/venv/.env: OK"
echo "$ZIP_LISTING" | tail -2

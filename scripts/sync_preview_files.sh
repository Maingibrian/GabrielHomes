#!/usr/bin/env bash
# Sync the user-facing delivery artifacts into scripts/preview_site/files/
# (the tree served by the locked :3000 preview server) and BYTE-VERIFY them.
#
# Incident this guards against (2026-10-14): a raw `cp` of the repo's
# UPDATE-WEBSITE.bat shipped it with Unix (LF-only) line endings; CMD
# misparses ( ... ) blocks in LF-only batch files and the user's updater
# died with "'.' is not recognized". Every .bat here MUST be CRLF-only.
set -euo pipefail

ROOT=/home/z/my-project
GH=$ROOT/gabriel_homes
DST=$ROOT/scripts/preview_site/files
SRC_ZIP=$(ls -t "$ROOT"/download/gabriel-homes-update-*.zip 2>/dev/null | head -1)

[ -n "$SRC_ZIP" ] || { echo "FATAL: no download/gabriel-homes-update-*.zip found - run build_update_zip.sh first" >&2; exit 1; }
[ -f "$GH/UPDATE-WEBSITE.bat" ] || { echo "FATAL: $GH/UPDATE-WEBSITE.bat missing" >&2; exit 1; }

mkdir -p "$DST"

echo "== copy zip: $(basename "$SRC_ZIP") =="
cp -f "$SRC_ZIP" "$DST/"

echo "== copy bat (CRLF-enforced) =="
python3 - "$GH/UPDATE-WEBSITE.bat" "$DST/UPDATE-WEBSITE.bat" <<'PYEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
data = open(src, "rb").read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
open(dst, "wb").write(data)
print(f"  wrote {dst} ({len(data)} bytes, CRLF)")
PYEOF

echo "== copy evidence shots =="
for f in about-hero.png about-agents.png about-mobile.png; do
    [ -f "$GH/docs/shots/$f" ] && cp -f "$GH/docs/shots/$f" "$DST/" && echo "  from docs/shots: $f" || true
done

echo "== byte verification =="
python3 - "$DST" "$SRC_ZIP" <<'PYEOF'
import sys, zipfile
from pathlib import Path

dst = Path(sys.argv[1])
src_zip = Path(sys.argv[2])
fails = []

# 1. every .bat in the delivery tree must be CRLF-only
for bat in dst.rglob("*.bat"):
    rb = bat.read_bytes()
    bare_lf = rb.count(b"\n") - rb.count(b"\r\n")
    if bare_lf:
        fails.append(f"{bat.name}: {bare_lf} bare-LF line(s) - LF batch files break CMD")
    else:
        print(f"  OK {bat.name}: CRLF-only ({len(rb)} bytes)")

# 2. the delivered zip must exist, be rootless, and contain a CRLF bat
zp = dst / src_zip.name
if not zp.exists():
    fails.append("zip missing from delivery tree")
else:
    z = zipfile.ZipFile(zp)
    names = z.namelist()
    if "manage.py" not in names:
        fails.append("zip is not rootless (manage.py not at top)")
    if "UPDATE-WEBSITE.bat" not in names:
        fails.append("zip has no UPDATE-WEBSITE.bat")
    else:
        rb = z.read("UPDATE-WEBSITE.bat")
        bare_lf = rb.count(b"\n") - rb.count(b"\r\n")
        if bare_lf:
            fails.append(f"zip's UPDATE-WEBSITE.bat has {bare_lf} bare-LF line(s)")
        else:
            print(f"  OK zip bat: CRLF-only ({len(rb)} bytes)")
    print(f"  OK zip: {src_zip.name} - {len(names)} files, {zp.stat().st_size} bytes")

# 3. evidence shots present
for f in ("about-hero.png", "about-agents.png", "about-mobile.png"):
    p = dst / f
    if p.exists():
        print(f"  OK {f}: {p.stat().st_size} bytes")
    else:
        print(f"  WARN {f}: not found (page will show a broken image)")

if fails:
    print("\nFATAL: delivery verification failed:")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("\nDELIVERY SYNC OK")
PYEOF

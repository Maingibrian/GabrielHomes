#!/usr/bin/env bash
# =============================================================================
# split_package.sh — split the oneclick zip into ~14 MB parts + rejoin tools.
#
# Why: 60+ MB single downloads over the preview proxy keep failing for the
# owner. 14 MB parts survive flaky links (retry one part, not the whole zip).
# The rejoin tools are dependency-free: cmd's `copy /b` on Windows, `cat` on
# macOS/Linux, plus Windows 10+ ships tar.exe which can extract the zip.
# =============================================================================
set -euo pipefail

SRC=/home/z/my-project/download/gabriel-homes-oneclick.zip
OUT=/home/z/my-project/scripts/preview_site/files/parts
PART_MB=14

[ -f "$SRC" ] || { echo "FATAL: $SRC missing - run build_package.sh first" >&2; exit 1; }

rm -rf "$OUT"
mkdir -p "$OUT"

echo "== splitting $(basename "$SRC") into ${PART_MB} MB parts =="
# -d numeric suffixes, zero padded so alphabetical order == byte order
split -b "${PART_MB}M" -d -a 2 "$SRC" "$OUT/gabriel-homes-oneclick.part-"
n=$(find "$OUT" -name 'gabriel-homes-oneclick.part-*' | wc -l)
for f in "$OUT"/gabriel-homes-oneclick.part-*; do
  mv "$f" "$f-of-$n.bin"
done
echo "  $n parts written"

# -- byte-verify: reassemble in a temp dir and compare hashes --
SRC_MD5=$(md5sum "$SRC" | cut -d' ' -f1)
JOIN_MD5=$(cat "$OUT"/gabriel-homes-oneclick.part-*.bin | md5sum | cut -d' ' -f1)
if [ "$SRC_MD5" != "$JOIN_MD5" ]; then
  echo "FATAL: parts do not reassemble to the original (md5 mismatch)" >&2
  exit 1
fi
echo "  rejoin md5 verified: $SRC_MD5"

# -- checksums file for the owner's own verification --
{
  echo "# MD5 of the reassembled gabriel-homes-oneclick.zip"
  echo "# After rejoining, check: the zip's MD5 must be the value below."
  echo "$SRC_MD5  gabriel-homes-oneclick.zip"
} > "$OUT/MD5-CHECK.txt"

# -- Windows rejoin (CRLF is enforced below) --
cat > "$OUT/REJOIN-WINDOWS.bat" <<'EOF'
@echo off
setlocal
title Gabriel Homes - package rejoin
echo ============================================
echo  Gabriel Homes - rejoin the downloaded parts
echo ============================================
echo.
set ZIP=gabriel-homes-oneclick.zip
if exist "%ZIP%" (
  echo A %ZIP% already exists here. Delete it first if you want to rebuild it.
  pause
  exit /b 1
)
echo Step 1/2: joining the parts back into one zip...
copy /b /y "gabriel-homes-oneclick.part-*.bin" "%ZIP%" >nul
if errorlevel 1 (
  echo.
  echo FAILED: could not join the parts. Make sure ALL part files
  echo AND this .bat are in the same folder, then run it again.
  pause
  exit /b 1
)
echo           done.
echo.
echo Step 2/2: extracting the website...
tar -xf "%ZIP%"
if errorlevel 1 (
  echo tar.exe extract failed - right-click %ZIP% and choose
  echo "Extract All", then open the gabriel-homes folder.
  pause
  exit /b 1
)
echo.
echo ============================================================
echo  DONE. Your website is in the "gabriel-homes" folder.
echo  Next: open that folder and double-click
echo        START-GABRIEL-HOMES.bat
echo  The site opens in your browser automatically.
echo ============================================================
pause
EOF

# -- macOS / Linux rejoin --
cat > "$OUT/REJOIN-MAC-LINUX.sh" <<'EOF'
#!/bin/sh
# Gabriel Homes - rejoin the downloaded parts, then extract.
set -e
ZIP=gabriel-homes-oneclick.zip
echo "== Gabriel Homes - rejoin the downloaded parts =="
if [ -f "$ZIP" ]; then
  echo "A $ZIP already exists here. Delete it first if you want to rebuild it."
  exit 1
fi
echo "Step 1/2: joining the parts..."
cat gabriel-homes-oneclick.part-*.bin > "$ZIP"
echo "          done."
if command -v md5sum >/dev/null 2>&1; then
  echo "Step 1b: verifying checksum..."
  if md5sum -c MD5-CHECK.txt >/dev/null 2>&1; then
    echo "          checksum OK"
  else
    echo "          WARNING: checksum mismatch - a part is incomplete."
    echo "          Delete the failed part, download it again, rerun."
    exit 1
  fi
fi
echo "Step 2/2: extracting the website..."
unzip -o -q "$ZIP"
echo ""
echo "DONE. Your website is in the 'gabriel-homes' folder."
echo "Next:  cd gabriel-homes && bash START-GABRIEL-HOMES.sh"
EOF

# -- line endings + exec bits: .bat must be CRLF, .sh must be LF + executable --
python3 - "$OUT" <<'PYEOF'
import sys
from pathlib import Path
out = Path(sys.argv[1])
bat = out / "REJOIN-WINDOWS.bat"
data = bat.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
bat.write_bytes(data)
bare = data.count(b"\n") - data.count(b"\r\n")
assert bare == 0, f"REJOIN-WINDOWS.bat has {bare} bare-LF lines"
print(f"  REJOIN-WINDOWS.bat: CRLF-only ({len(data)} bytes)")
sh = out / "REJOIN-MAC-LINUX.sh"
data = sh.read_bytes().replace(b"\r\n", b"\n")
sh.write_bytes(data)
sh.chmod(0o755)
print(f"  REJOIN-MAC-LINUX.sh: LF-only ({len(data)} bytes, +x)")
PYEOF

echo "== parts ready in $OUT =="
ls -lh "$OUT" | awk '{print "  " $9 "  " $5}'

#!/usr/bin/env bash
# Repair stub (<1KB) media files in media/property-images/real/ and
# media/property-videos/real/ by re-copying from media/real-listing-src/.
# Idempotent: only touches files that are actually broken.
set -euo pipefail
GH=/home/z/my-project/gabriel_homes
SRC="$GH/media/real-listing-src"
REAL_IMG="$GH/media/property-images/real"
REAL_VID="$GH/media/property-videos/real"

fixed=0
for f in "$REAL_IMG"/nyali-real-*.jpg; do
  [ -f "$f" ] || continue
  size=$(stat -c%s "$f")
  if [ "$size" -lt 1024 ]; then
    base=$(basename "$f" | sed 's/^nyali-//')   # nyali-real-01.jpg -> real-01.jpg
    if [ -f "$SRC/$base" ]; then
      cp "$SRC/$base" "$f"
      echo "fixed image: $(basename "$f") ($size B -> $(stat -c%s "$f") B)"
      fixed=$((fixed+1))
    else
      echo "WARN: no source for $base" >&2
    fi
  fi
done

vid="$REAL_VID/nyali-real-tour.mp4"
if [ -f "$vid" ] && [ "$(stat -c%s "$vid")" -lt 1024 ] && [ -f "$SRC/real-tour.mp4" ]; then
  cp "$SRC/real-tour.mp4" "$vid"
  echo "fixed video: nyali-real-tour.mp4 -> $(stat -c%s "$vid") B"
  fixed=$((fixed+1))
fi

echo "--- post-fix: files under 1KB remaining in real/ dirs ---"
find "$REAL_IMG" "$REAL_VID" -type f -size -1024c | wc -l
echo "--- smallest 3 real images now ---"
ls -laS "$REAL_IMG" | tail -4
echo "fixed=$fixed"

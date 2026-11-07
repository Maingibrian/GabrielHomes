#!/usr/bin/env bash
# Fetch online stock photos via z-ai image-search (stdout capture — the CLI's
# -o flag is broken in this version). Serial with one retry each.
set -u
OUT=/tmp/imgsearch
mkdir -p "$OUT"

run () {  # $1=stem $2=query $3=count
  local attempt=1
  while [ "$attempt" -le 2 ]; do
    z-ai image-search -q "$2" --count "$3" --gl us --no-rank \
      > "$OUT/$1.raw" 2>/dev/null
    if [ -s "$OUT/$1.raw" ] && grep -q '"success": true' "$OUT/$1.raw"; then
      echo "[ok] $1 (attempt $attempt)"
      return 0
    fi
    attempt=$((attempt+1))
    sleep 3
  done
  echo "[FAIL] $1"
}

run house-a      "modern tropical villa exterior with palm trees and swimming pool" 10
run house-b      "white swahili style house with courtyard garden coastal Kenya" 10
run house-c      "beachfront family home exterior tropical east africa coast" 10
run apartment-a  "modern apartment building exterior in coastal african city" 10
run apartment-b  "bright modern apartment living room with ocean view balcony" 10
run interior-a   "cozy modern bedroom interior with warm natural light" 10
run interior-b   "modern kitchen with wooden island and dining area interior" 10
run land         "vacant land plot with palm trees tropical coastline" 8
run office       "modern office interior workspace with desks and large windows" 8
run shops        "small retail shop storefront on a sunny tropical street" 8
run warehouse    "empty warehouse interior industrial storage space daylight" 8

# --- extract JSON + urls ----------------------------------------------------
python3 - <<'PY'
import json, pathlib, re
out = pathlib.Path("/tmp/imgsearch")
total = 0
for f in sorted(out.glob("*.raw")):
    text = f.read_text(errors="replace")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        print(f"{f.stem}: NO JSON"); continue
    try:
        data = json.loads(m.group(0))
    except Exception as exc:
        print(f"{f.stem}: bad json {exc}"); continue
    if not data.get("success"):
        print(f"{f.stem}: search failed -> {data.get('error')}"); continue
    urls = [r["original_url"] for r in data.get("results", []) if r.get("original_url")]
    (out / f"{f.stem}.urls").write_text("\n".join(urls) + ("\n" if urls else ""))
    total += len(urls)
    print(f"{f.stem}: {len(urls)} urls")
print("TOTAL:", total)
PY

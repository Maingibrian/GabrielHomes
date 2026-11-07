#!/usr/bin/env bash
# Fetch REPLACEMENT stock photos for the flagged/watermarked pool entries.
# Serial, stdout capture, one retry. Writes /tmp/imgsearch/extra-<pool>.urls.
set -u
OUT=/tmp/imgsearch
mkdir -p "$OUT"

run () {  # $1=pool(extra name) $2=query $3=count
  local attempt=1
  while [ "$attempt" -le 3 ]; do
    z-ai image-search -q "$2" --count "$3" --gl us --no-rank \
      > "$OUT/$1.raw" 2>/dev/null
    if [ -s "$OUT/$1.raw" ] && grep -q '"success": true' "$OUT/$1.raw"; then
      echo "[ok] $1 (attempt $attempt)"; return 0
    fi
    attempt=$((attempt+1)); sleep 3
  done
  echo "[FAIL] $1"
}

run extra-house      "luxury beach house exterior with garden and palms daytime" 8
run extra-apartment  "modern residential apartment building facade balconies" 10
run extra-interior   "scandinavian style living room interior bright and airy" 8
run extra-land       "green field empty plot of land for development aerial" 6
run extra-office     "coworking office space interior modern bright" 5
run extra-shops      "shop storefront exterior with awning street level" 6
run extra-warehouse  "logistics warehouse exterior large industrial building" 5

python3 - <<'PY'
import json, pathlib, re
out = pathlib.Path("/tmp/imgsearch")
for f in sorted(out.glob("extra-*.raw")):
    text = f.read_text(errors="replace")
    m = re.search(r"\{.*\}", text, re.S)
    if not m: print(f.stem, "NO JSON"); continue
    data = json.loads(m.group(0))
    if not data.get("success"):
        print(f.stem, "failed:", data.get("error")); continue
    urls = [r["original_url"] for r in data.get("results", []) if r.get("original_url")]
    pool = f.stem.replace("extra-", "")
    (out / f"extra-{pool}.urls").write_text("\n".join(urls) + ("\n" if urls else ""))
    print(pool, len(urls), "urls")
PY

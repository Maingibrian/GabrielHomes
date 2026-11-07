#!/usr/bin/env bash
# Rebuild /tmp/imgsearch/*.urls after a sandbox recycle wiped them.
# NOTE: this z-ai CLI build ignores -o, so stdout is captured and the JSON
# block is stripped of its emoji preamble by the python step.
set -u
mkdir -p /tmp/imgsearch
cd /tmp/imgsearch

search() { # stem query count
  local stem="$1" q="$2" n="$3"
  if [ -s "/tmp/imgsearch/${stem}.json" ]; then
    echo "[skip] ${stem}"; return
  fi
  z-ai image-search -q "$q" -c "$n" --gl us --no-rank \
    > "/tmp/imgsearch/${stem}.raw" 2>/dev/null
  if grep -q '"success"' "/tmp/imgsearch/${stem}.raw" 2>/dev/null; then
    echo "[ok] ${stem}"
  else
    echo "[FAIL] ${stem} ($(wc -c < /tmp/imgsearch/${stem}.raw 2>/dev/null || echo 0) bytes)"
  fi
}

# ---- batch 1 ----
search house-a "modern white coastal villa with palm trees and a pool, bright sunny day" 6 &
search house-b "tropical family house exterior with a lush green garden in Kenya" 6 &
search house-c "swahili style house with white walls and wooden doors in daylight" 6 &
wait
# ---- batch 2 ----
search apartment-a "modern apartment building exterior with balconies in bright daylight" 6 &
search apartment-b "bright airy apartment living room with large windows and plants" 6 &
search interior-a "sunlit living room interior with warm natural light and cozy furniture" 7 &
wait
# ---- batch 3 ----
search interior-b "coastal style bedroom with white linen and soft morning light" 7 &
search office "small bright office interior with a wooden desk near a window" 5 &
search shops "retail shop storefront on a sunny street" 5 &
wait
# ---- batch 4 ----
search warehouse "empty warehouse interior with clean concrete floor" 5 &
wait

echo "---- extracting urls ----"
/home/z/my-project/.venv/bin/python - <<'PY'
import json
from pathlib import Path

src = Path("/tmp/imgsearch")
stems = ["house-a","house-b","house-c","apartment-a","apartment-b",
         "interior-a","interior-b","land","office","shops","warehouse"]
# land.json never got written by -o in the earlier probe; keep its raw too.
total = 0
for stem in stems:
    raw = src / f"{stem}.raw"
    if not raw.exists():
        print(f"{stem}: NO RAW"); continue
    text = raw.read_text()
    start = text.find("{")
    if start < 0:
        print(f"{stem}: NO JSON BLOCK"); continue
    try:
        data = json.loads(text[start:])
    except Exception as e:
        print(f"{stem}: BAD JSON {e}"); continue
    urls = [r.get("original_url","") for r in data.get("results",[]) if r.get("original_url")]
    (src / f"{stem}.urls").write_text("\n".join(urls) + ("\n" if urls else ""))
    print(f"{stem}: {len(urls)} urls")
    total += len(urls)
print(f"TOTAL: {total}")
PY

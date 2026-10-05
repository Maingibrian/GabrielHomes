#!/bin/bash
# fetch_demo_photos.sh — batch 3: portraits + coast hero
set -u
OUT=/home/z/my-project/scripts/design-audit/search-json
mkdir -p "$OUT"
z-ai image-search -q "professional headshot portrait african businessman in suit smiling" -c 6 --gl us -o "$OUT/men.json"
z-ai image-search -q "professional headshot portrait african businesswoman blazer smiling" -c 5 --gl us -o "$OUT/women.json"
z-ai image-search -q "diani beach kenya white sand palm trees turquoise ocean" -c 5 --gl us --no-rank -o "$OUT/coast.json"
z-ai image-search -q "mombasa kenya coastal city skyline ocean" -c 4 --gl us --no-rank -o "$OUT/city.json"
echo BATCH-C-DONE

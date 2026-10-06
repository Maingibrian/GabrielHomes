#!/bin/bash
# fetch_demo_photos.sh — batch 2: interiors
set -u
OUT=/home/z/my-project/scripts/design-audit/search-json
mkdir -p "$OUT"
z-ai image-search -q "bright modern living room interior with large windows" -c 6 --gl us --no-rank -o "$OUT/living.json"
z-ai image-search -q "modern kitchen interior wooden cabinets marble" -c 4 --gl us --no-rank -o "$OUT/kitchen.json"
z-ai image-search -q "cozy bedroom interior warm tones hotel" -c 4 --gl us --no-rank -o "$OUT/bedroom.json"
z-ai image-search -q "modern office space interior wooden desks" -c 3 --gl us --no-rank -o "$OUT/office.json"
z-ai image-search -q "tropical garden with palm trees and stone pathway" -c 4 --gl us --no-rank -o "$OUT/garden.json"
echo BATCH-B-DONE

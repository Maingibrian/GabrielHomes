#!/bin/bash
# fetch_demo_photos.sh — batch 1: property exteriors
set -u
OUT=/home/z/my-project/scripts/design-audit/search-json
mkdir -p "$OUT"
z-ai image-search -q "modern tropical villa exterior with swimming pool at golden hour" -c 6 --gl us --no-rank -o "$OUT/villa.json"
z-ai image-search -q "white beach house exterior with palm trees" -c 5 --gl us --no-rank -o "$OUT/beachhouse.json"
z-ai image-search -q "modern apartment building exterior residential balconies" -c 5 --gl us --no-rank -o "$OUT/apartment.json"
z-ai image-search -q "contemporary townhouse exterior facade" -c 4 --gl us --no-rank -o "$OUT/townhouse.json"
z-ai image-search -q "luxury house exterior with garden and driveway" -c 5 --gl us --no-rank -o "$OUT/luxhouse.json"
echo BATCH-A-DONE

#!/bin/bash
set -u
OUT=/home/z/my-project/scripts/design-audit/search-json
z-ai image-search -q "confident young african professional woman studio portrait plain background" -c 6 --gl us -o "$OUT/women2.json"
z-ai image-search -q "smiling african man corporate portrait office background" -c 6 --gl us -o "$OUT/men2.json"
echo PORTRAITS2-DONE

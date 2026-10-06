#!/bin/bash
set -u
OUT=/home/z/my-project/scripts/design-audit/search-json
z-ai image-search -q "modern residential apartment complex exterior blue sky balconies" -c 6 --gl us -o "$OUT/apartment2.json"
z-ai image-search -q "row of small shop storefronts exterior street" -c 6 --gl us -o "$OUT/shops.json"
z-ai image-search -q "modern warehouse industrial building exterior" -c 5 --gl us -o "$OUT/warehouse.json"
z-ai image-search -q "modern glass office building exterior low rise" -c 5 --gl us -o "$OUT/officebld.json"
echo EXTRA-DONE

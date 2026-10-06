#!/bin/bash
# fetch_photos_retry.sh <group> — group in {a1,a2,a3}
set -u
OUT=/home/z/my-project/scripts/design-audit/search-json
mkdir -p "$OUT"
G="$1"
if [ "$G" = a1 ]; then
  z-ai image-search -q "modern tropical villa exterior with swimming pool at golden hour" -c 6 --gl us -o "$OUT/villa.json"
  z-ai image-search -q "white beach house exterior with palm trees" -c 5 --gl us -o "$OUT/beachhouse.json"
  z-ai image-search -q "modern apartment building exterior residential balconies" -c 5 --gl us -o "$OUT/apartment.json"
  z-ai image-search -q "contemporary townhouse exterior facade" -c 4 --gl us -o "$OUT/townhouse.json"
elif [ "$G" = a2 ]; then
  z-ai image-search -q "luxury house exterior with garden and driveway" -c 5 --gl us -o "$OUT/luxhouse.json"
  z-ai image-search -q "bright modern living room interior with large windows" -c 6 --gl us -o "$OUT/living.json"
  z-ai image-search -q "modern kitchen interior wooden cabinets marble" -c 4 --gl us -o "$OUT/kitchen.json"
  z-ai image-search -q "cozy bedroom interior warm tones hotel" -c 4 --gl us -o "$OUT/bedroom.json"
else
  z-ai image-search -q "modern office space interior wooden desks" -c 3 --gl us -o "$OUT/office.json"
  z-ai image-search -q "tropical garden with palm trees and stone pathway" -c 4 --gl us -o "$OUT/garden.json"
  z-ai image-search -q "diani beach kenya white sand palm trees turquoise ocean" -c 5 --gl us -o "$OUT/coast.json"
  z-ai image-search -q "mombasa kenya coastal city skyline ocean" -c 4 --gl us -o "$OUT/city.json"
fi
echo "GROUP-$G-DONE"

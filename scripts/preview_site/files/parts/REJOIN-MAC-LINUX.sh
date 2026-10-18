#!/bin/sh
# Gabriel Homes - rejoin the downloaded parts, then extract.
set -e
ZIP=gabriel-homes-oneclick.zip
echo "== Gabriel Homes - rejoin the downloaded parts =="
if [ -f "$ZIP" ]; then
  echo "A $ZIP already exists here. Delete it first if you want to rebuild it."
  exit 1
fi
echo "Step 1/2: joining the parts..."
cat gabriel-homes-oneclick.part-*.bin > "$ZIP"
echo "          done."
if command -v md5sum >/dev/null 2>&1; then
  echo "Step 1b: verifying checksum..."
  if md5sum -c MD5-CHECK.txt >/dev/null 2>&1; then
    echo "          checksum OK"
  else
    echo "          WARNING: checksum mismatch - a part is incomplete."
    echo "          Delete the failed part, download it again, rerun."
    exit 1
  fi
fi
echo "Step 2/2: extracting the website..."
unzip -o -q "$ZIP"
echo ""
echo "DONE. Your website is in the 'gabriel-homes' folder."
echo "Next:  cd gabriel-homes && bash START-GABRIEL-HOMES.sh"

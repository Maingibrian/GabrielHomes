#!/usr/bin/env bash
# Vendor Windows wheels for the offline self-repair ladder.
# The update zip carries wheels/ so the updaters can fix a broken .venv
# with NO internet (corporate networks often block pypi.org).
# Downloads win_amd64 CPython wheels for every supported Python (3.10-3.13).
set -euo pipefail

GH=/home/z/my-project/gabriel_homes
cd "$GH"
mkdir -p wheels

for PYVER in 3.10 3.11 3.12 3.13; do
  echo "== downloading wheels for CPython $PYVER =="
  python3 -m pip download \
    --only-binary=:all: \
    --platform win_amd64 \
    --implementation cp \
    --python-version "$PYVER" \
    -r requirements.txt \
    -d wheels \
    --quiet --disable-pip-version-check
done

echo "== wheels vendored: $(ls wheels/*.whl | wc -l) files, $(du -sh wheels | cut -f1) =="
# Sanity: the packages that MUST be present for the site to run.
for pat in 'django-.*\.whl' 'pillow-.*\.whl' 'psycopg_binary-.*\.whl' 'whitenoise-.*\.whl'; do
  ls wheels | grep -Eiq "$pat" || { echo "FATAL: $pat wheel missing" >&2; exit 1; }
done
echo "WHEELS OK"

#!/usr/bin/env bash
# Gabriel Homes — one-shot environment bootstrap.
# The sandbox wipes the runtime layer (.venv, db, media) between messages;
# this script restores it deterministically. Idempotent: safe to re-run.
set -euo pipefail
GH=/home/z/my-project/gabriel_homes
cd "$GH"

echo "== 1/6 virtualenv =="
if [ ! -x .venv/bin/python ]; then python3.12 -m venv .venv; fi
.venv/bin/pip install --quiet -r requirements.txt
.venv/bin/python -c "import django; print('   Django', django.get_version())"

echo "== 2/6 media (from oneclick zip) =="
if [ ! -d media/demo-photos ]; then
  mkdir -p media
  python3 - << 'PY'
import zipfile
z = zipfile.ZipFile('/home/z/my-project/download/gabriel-homes-oneclick.zip')
names = [n for n in z.namelist() if n.startswith('gabriel-homes/media/')]
z.extractall('/tmp/gh_media_boot', members=names)
import shutil
src = '/tmp/gh_media_boot/gabriel-homes/media'
for item in os.listdir(src) if False else __import__('os').listdir(src):
    dst = f'media/{item}'
    if not __import__('os').path.exists(dst):
        shutil.move(f'{src}/{item}', dst)
print('   media restored')
PY
else
  echo "   media present, skipped"
fi

echo "== 3/6 database =="
if [ ! -f db.sqlite3 ]; then .venv/bin/python manage.py migrate --noinput | tail -1; else echo "   db present, skipped"; fi

echo "== 4/6 demo seed =="
COUNT=$(.venv/bin/python manage.py shell -c "
from apps.listings.models import Property
print(Property.objects.filter(status='published').count())" 2>/dev/null | tail -1 || echo 0)
if [ "$COUNT" != "80" ]; then
  .venv/bin/python manage.py seed_demo --clear | tail -1
else
  echo "   80 listings present, skipped"
fi

echo "== 5/6 demo accounts =="
.venv/bin/python manage.py shell < scripts/setup_accounts.py 2>&1 | tail -1

echo "== 6/6 real front media (Task 17) =="
if [ -f /home/z/my-project/scripts/apply_real_media.py ]; then
  .venv/bin/python /home/z/my-project/scripts/apply_real_media.py || true
fi

echo "BOOTSTRAP OK"

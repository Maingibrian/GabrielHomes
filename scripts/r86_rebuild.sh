#!/bin/sh
# r86 rebuild after sandbox recycle: venv, .env, migrate, seed, launch.
set -eu
cd /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes

# 1. runtime (venv + requirements + migrate)
sh scripts/ensure-runtime.sh

# 2. .env with BOTH public gateway hosts (r84 lesson: .fcapp.run needed)
printf 'EXTRA_ALLOWED_HOSTS=.space-z.ai,.fcapp.run\nCSRF_TRUSTED_ORIGINS=https://*.space-z.ai,https://*.fcapp.run\n' > .env

# 3. psycopg (prod-settings tests import it; binary wheel)
.venv/bin/pip install -q "psycopg[binary]==3.2.13" || echo "[rebuild] psycopg install failed (non-fatal for preview)"

# 4. seed pipeline (r84 order) — real-listing-src staged from static/img/real
mkdir -p media/real-listing-src
cp -n static/img/real/*.jpg media/real-listing-src/ 2>/dev/null || true
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py seed_mombasa_showcase
.venv/bin/python manage.py import_real_listing

# 5. launch daemon + bridge
python3 /home/z/my-project/scripts/launch_preview.py
sleep 6
curl -s -o /dev/null -w "bridge /: %{http_code}\n" http://127.0.0.1:3000/ || true
curl -s -o /dev/null -w "bridge /properties/: %{http_code}\n" http://127.0.0.1:3000/properties/ || true
.venv/bin/python - <<'EOF'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()
from apps.listings.models import Property
pub = Property.objects.published() if hasattr(Property.objects, "published") else Property.objects.filter(status="published")
print("published:", pub.count())
EOF
echo "[rebuild] DONE"

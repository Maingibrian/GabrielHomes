#!/bin/bash
# Full self-healing bootstrap for the Gabriel Homes sandbox preview.
#
# The workspace sandbox recycles between chat messages and drops gitignored
# files: .env, db.sqlite3, media/* (except demo-photos), and the Python venv's
# project packages. This script restores ALL of it and starts the server:
#
#   browser -> preview panel -> tunnel (fcapp.run) -> gateway :81
#           -> preview bridge :3000 -> Django runserver :8000
#
# Safe to run repeatedly; every step is idempotent.
set -u

PROJ=/home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes
PY=/home/z/.venv/bin/python3
PIP=/home/z/.venv/bin/pip
LOG=/tmp/gabriel-runserver.log

cd "$PROJ"

echo "=== 1. Python deps ==="
if ! $PY -c "import django" 2>/dev/null; then
    $PIP install -r requirements.txt
else
    echo "django present — skipping install"
fi

echo "=== 2. .env ==="
if [ ! -f .env ]; then
    cat > .env <<'EOF'
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=django-insecure-change-me-to-a-long-random-string-of-at-least-50-characters
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=
TRUST_X_REAL_IP=False
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=hello@gabrielhomes.co.ke
OWNER_EMAIL=
MEDIA_URL=/media/
STATIC_URL=/static/
SITE_DOMAIN=http://localhost:8000
GABRIEL_PREVIEW_BRIDGE=1
EXTRA_ALLOWED_HOSTS=.space-z.ai,.fcapp.run
CSRF_TRUSTED_ORIGINS=https://*.space-z.ai,https://*.fcapp.run
EOF
    echo ".env recreated"
else
    echo ".env present"
fi

echo "=== 3. Migrations ==="
$PY manage.py migrate --noinput | tail -2

echo "=== 4. Seed (only if DB is empty) ==="
LISTINGS=$($PY manage.py shell -c "from apps.listings.models import Property; print(Property.objects.count())" 2>/dev/null | tail -1)
if [ "${LISTINGS:-0}" = "0" ]; then
    echo "empty DB — seeding 80 demo listings with photos"
    $PY manage.py seed_demo --target 80
    echo "replacing any gradient cards with real pool photos"
    $PY scripts/replace_gradient_cards.py || true
else
    echo "DB already has $LISTINGS listings — skipping seed"
fi

echo "=== 5. Start server (detached) ==="
pkill -f "manage.py runserver" 2>/dev/null
sleep 1
setsid nohup $PY manage.py runserver 0.0.0.0:8000 \
  > "$LOG" 2>&1 < /dev/null &
sleep 7

pgrep -af "manage.py runserver" | head -2 || { echo "RUNSERVER FAILED — log:"; tail -20 "$LOG"; exit 1; }
ss -tln 2>/dev/null | rg "3000|8000" || { echo "PORTS NOT BOUND — log:"; tail -20 "$LOG"; exit 1; }

echo "=== 6. Gateway smoke test ==="
curl -s -o /dev/null -m 10 -w "home via :81 -> %{http_code}\n" \
  -H "Host: ws-dfdddd-bbead-uabvrzfhdv.cn-hongkong-vpc.fcapp.run" \
  http://127.0.0.1:81/

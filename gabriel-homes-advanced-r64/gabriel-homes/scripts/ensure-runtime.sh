#!/usr/bin/env sh
# Runtime self-heal for the workspace auto dev server and fresh checkouts.
# Ensures: .venv exists (requirements installed), .env exists, schema migrated.
# Safe to run any number of times; skips work that is already done.
set -eu
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
    echo "[ensure-runtime] creating .venv and installing requirements..."
    python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
fi

if [ ! -f .env ]; then
    echo "[ensure-runtime] writing default .env..."
    printf 'EXTRA_ALLOWED_HOSTS=.space-z.ai\nCSRF_TRUSTED_ORIGINS=https://*.space-z.ai\n' > .env
fi

.venv/bin/python manage.py migrate --noinput
echo "[ensure-runtime] ok"

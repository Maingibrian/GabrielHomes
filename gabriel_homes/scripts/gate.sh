#!/usr/bin/env bash
# gate.sh — quality gate for Gabriel Homes (docs/PLAN.md task F3).
# Runs every check in order; exits non-zero on the first failure.
# Stages G-CDN / G-STATIC / G-COV are enabled by flipping the flags below
# as their enabling tasks (S10 / S6 / V1) land.
set -u

cd "$(dirname "$0")/.."

ENABLE_G_CDN=0     # enabled after S10
ENABLE_G_STATIC=1  # enabled after S6
ENABLE_G_COV=0     # enabled after V1

PY="${PYTHON:-.venv/bin/python}"
FAIL=0

# helper: run a command, stream its output, keep its exit code
run_checked() {
  local label="$1"; shift
  echo "==> $label"
  local out rc
  out="$("$@" 2>&1)"
  rc=$?
  [ -n "${TAIL_LINES:-}" ] && printf '%s\n' "$out" | tail -"$TAIL_LINES"
  if [ $rc -ne 0 ]; then
    echo "GATE FAIL: $label"
    exit 1
  fi
}

# 1. Django system check
run_checked "check" "$PY" manage.py check

# 2. No missing migrations
run_checked "makemigrations --check" "$PY" manage.py makemigrations --check --dry-run

# 3. Full test suite
TAIL_LINES=5
run_checked "pytest" "$PY" -m pytest -q
unset TAIL_LINES

# 4. G-DEPLOY: prod settings deploy check with a real-length secret
TAIL_LINES=3
run_checked "G-DEPLOY check --deploy" env \
  DJANGO_SETTINGS_MODULE=config.settings.prod \
  SECRET_KEY="$(python3 -c "import secrets;print(secrets.token_urlsafe(60))")" \
  ALLOWED_HOSTS=example.com \
  DATABASE_URL=postgres://u:p@localhost:5432/x \
  "$PY" manage.py check --deploy
unset TAIL_LINES

# 5. G-SAFE: no unlisted |safe in templates
echo "==> G-SAFE |safe allowlist"
if grep -rn "|safe" templates/ | grep -v -F -f scripts/safe_allowlist.txt; then
  echo "GATE FAIL: unallowlisted |safe usage found"
  exit 1
fi

# 6. G-CDN: no third-party CDN hosts in templates/static (enabled after S10)
if [ "$ENABLE_G_CDN" = "1" ]; then
  echo "==> G-CDN third-party hosts"
  if grep -rn -E "unpkg\.com|cdn\.jsdelivr\.net|framerusercontent\.com" templates/ static/ 2>/dev/null; then
    echo "GATE FAIL: third-party CDN reference found"
    exit 1
  fi
fi

# 7. G-STATIC: collectstatic under prod settings (enabled after S6)
if [ "$ENABLE_G_STATIC" = "1" ]; then
  echo "==> G-STATIC collectstatic (prod)"
  _TMP_STATIC="$(mktemp -d)"
  if ! env \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    SECRET_KEY="$(python3 -c "import secrets;print(secrets.token_urlsafe(60))")" \
    ALLOWED_HOSTS=example.com \
    DATABASE_URL=postgres://u:p@localhost:5432/x \
    STATIC_ROOT="$_TMP_STATIC" \
    "$PY" manage.py collectstatic --noinput --verbosity 0; then
    echo "GATE FAIL: collectstatic"
    rm -rf "$_TMP_STATIC"
    exit 1
  fi
  _HASHED="$(find "$_TMP_STATIC" -type f -name "*[0-9a-f][0-9a-f]*.*" | head -1)"
  if [ -z "$_HASHED" ]; then
    echo "GATE FAIL: no hashed filenames in STATIC_ROOT"
    rm -rf "$_TMP_STATIC"
    exit 1
  fi
  rm -rf "$_TMP_STATIC"
fi

# 8. G-COV: coverage >= 80% on the three core apps (enabled after V1)
if [ "$ENABLE_G_COV" = "1" ]; then
  echo "==> G-COV coverage 80"
  run_checked "coverage" "$PY" -m pytest -q \
    --cov=apps/listings --cov=apps/agents --cov=apps/inquiries \
    --cov-fail-under=80
fi

echo "GATE GREEN"
exit 0

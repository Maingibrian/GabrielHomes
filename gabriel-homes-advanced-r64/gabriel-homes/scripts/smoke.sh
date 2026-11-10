#!/usr/bin/env bash
# smoke.sh — portable smoke check for Gabriel Homes (docs/PLAN.md task R2).
#
# Usage:
#   BASE_URL=https://gabrielhomes.co.ke bash scripts/smoke.sh
#   BASE_URL=http://127.0.0.1:8000 bash scripts/smoke.sh
#
# Expects:
#   - 200 for public pages (incl. /healthz/)
#   - 302 for /dashboard/ and /admin/ when NOT logged in
#   - 404 for an unknown listing slug
# Exits non-zero on any mismatch. No dependencies beyond bash + curl.
set -u

BASE_URL="${BASE_URL:-}"
if [ -z "$BASE_URL" ]; then
  echo "Usage: BASE_URL=<site-root> bash scripts/smoke.sh"
  echo "  e.g. BASE_URL=http://127.0.0.1:8000 bash scripts/smoke.sh"
  exit 2
fi
BASE_URL="${BASE_URL%/}"

PASS=0
FAIL=0
FAILURES=""

check() {
  # check <expected-status> <path>
  local want="$1" path="$2" got
  got="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$BASE_URL$path")"
  if [ "$got" = "$want" ]; then
    PASS=$((PASS + 1))
    printf '  ok   %s %s\n' "$want" "$path"
  else
    FAIL=$((FAIL + 1))
    FAILURES="$FAILURES  FAIL $path -> got $got, want $want"$'\n'
    printf '  FAIL %s -> got %s\n' "$path" "$got"
  fi
}

echo "Smoke check against $BASE_URL"

# --- public pages: 200 -----------------------------------------------------
for p in \
  / \
  /flats-apartments-for-sale/mombasa/ \
  /houses-for-rent/nairobi/ \
  /agents/ \
  /about/ \
  /sitemap.xml \
  /robots.txt \
  /account/login/ \
  /healthz/
do
  check 200 "$p"
done

# --- auth-gated: 302 when not logged in ------------------------------------
check 302 /dashboard/
check 302 /admin/

# --- unknown listing: 404 ---------------------------------------------------
check 404 /listing/not-a-real-listing-99999/

echo
echo "PASS: $PASS  FAIL: $FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "$FAILURES"
  exit 1
fi
exit 0

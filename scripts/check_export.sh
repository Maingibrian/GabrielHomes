#!/usr/bin/env bash
# =============================================================================
# check_export.sh — H2: validate an export zip BEFORE it leaves the building.
#
# Usage:   bash scripts/check_export.sh <path-to.zip>
# Exit 0 = export is complete and clean. Exit 1 = violations (listed).
#
# REQUIRED inside the zip (missing any one -> FAIL):
#   gabriel_homes/.env.example
#   gabriel_homes/.gitignore
#   gabriel_homes/docs/STATUS.md
#   gabriel_homes/docs/AGENT-BRIEF.md
#   gabriel_homes/manage.py
#
# FORBIDDEN inside the zip (any hit -> FAIL):
#   db.sqlite3 (anywhere), download/*, upload/*, scripts/server.log
#
# Listing is done with unzip (names only via -Z1, same tool as `unzip -l`).
# =============================================================================
set -u

ZIP="${1:-}"
if [ -z "$ZIP" ] || [ ! -f "$ZIP" ]; then
  echo "FAIL: usage: check_export.sh <zip>  ('${ZIP:-<none>}' is not a file)"
  exit 1
fi
if ! command -v unzip >/dev/null 2>&1; then
  echo "FAIL: unzip is not installed; cannot inspect $ZIP"
  exit 1
fi

# One entry per line (paths have no newlines in this project)
LIST="$(mktemp)"
unzip -Z1 "$ZIP" > "$LIST" 2>/dev/null
if [ ! -s "$LIST" ]; then
  echo "FAIL: could not list $ZIP (corrupt or empty archive)"
  rm -f "$LIST"
  exit 1
fi

status=0

echo "-- required files --"
for f in \
  "gabriel_homes/.env.example" \
  "gabriel_homes/.gitignore" \
  "gabriel_homes/docs/STATUS.md" \
  "gabriel_homes/docs/AGENT-BRIEF.md" \
  "gabriel_homes/manage.py"
do
  if grep -Fxq "$f" "$LIST"; then
    echo "   ok      $f"
  else
    echo "   MISSING $f"
    status=1
  fi
done

echo "-- forbidden content --"
for pat in "(^|/)db\.sqlite3$" "(^|/)download/" "(^|/)upload/" "(^|/)scripts/server\.log$"; do
  hits="$(grep -E "$pat" "$LIST" | head -5)"
  if [ -n "$hits" ]; then
    echo "   FORBIDDEN entries matching $pat:"
    printf '%s\n' "$hits" | sed 's/^/      /'
    status=1
  else
    echo "   ok      none matching $pat"
  fi
done

rm -f "$LIST"
if [ "$status" -eq 0 ]; then
  echo "EXPORT OK: $ZIP carries the dotfiles and nothing forbidden"
else
  echo "EXPORT FAILED: see MISSING/FORBIDDEN lines above for $ZIP"
fi
exit "$status"

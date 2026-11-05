#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Gabriel Homes — stop the local website (Linux + macOS)
# Kills whatever is listening on ports 8000-8010 (the launcher's range).
# ---------------------------------------------------------------------------
cd "$(dirname "$0")" || exit 1

echo "Stopping Gabriel Homes website..."
found=0

if command -v lsof >/dev/null 2>&1; then
  for p in $(seq 8000 8010); do
    pids="$(lsof -ti tcp:"$p" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
      # shellcheck disable=SC2086
      if echo "$pids" | xargs kill 2>/dev/null; then
        found=1
        echo "  Stopped process(es) on port $p"
      fi
    fi
  done
fi

if [ "$found" = "0" ]; then
  if pkill -f "manage.py runserver" 2>/dev/null; then
    found=1
  fi
fi

if [ "$found" = "1" ]; then
  echo "Done. The website is stopped."
else
  echo "Nothing appears to be running."
fi

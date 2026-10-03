#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Gabriel Homes — one-click website launcher (Linux: .sh / macOS: .command) [v2]
#
# What it does:
#   1. Finds (or helps install) Python 3.10+
#   2. Creates a .venv and installs dependencies (first run only, needs internet)
#   3. Migrates + seeds ~80 demo listings (skipped automatically if data exists)
#   4. Ensures demo accounts (admin + agent) exist
#   5. Picks a free port (8000-8010), waits until the site answers,
#      THEN opens your browser, and keeps the site running here
#
# Stop: close this window, or run STOP-WEBSITE(.sh/.bat)
# Set GABRIEL_NO_BROWSER=1 to skip auto-opening the browser.
# ---------------------------------------------------------------------------
set -u
cd "$(dirname "$0")" || exit 1

# -- Guard: the script needs the whole project next to it.
if [ ! -f "manage.py" ]; then
  echo "  ERROR: manage.py not found next to this script."
  echo "  Please extract the WHOLE zip into a folder first, then run"
  echo "  this script from inside the extracted gabriel-homes folder."
  exit 1
fi

BOLD=""; NC=""
if [ -t 1 ]; then BOLD=$'\033[1m'; NC=$'\033[0m'; fi
hr() { printf -- "--------------------------------------------------------------\n"; }

hr
printf "  %s Gabriel Homes — local website launcher %s\n" "$BOLD" "$NC"
hr

NO_BROWSER="${GABRIEL_NO_BROWSER:-0}"

# ------------------------------------------------------------- 1. python --
find_python() {
  for c in python3.12 python3.11 python3.13 python3.10 python3 python; do
    if command -v "$c" >/dev/null 2>&1; then
      if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        printf "%s" "$c"
        return 0
      fi
    fi
  done
  return 1
}

PY="$(find_python)"
if [ -z "${PY:-}" ]; then
  printf "  Python 3.10+ not found — trying to install it...\n"
  if [ "$(uname)" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
      brew install python@3.12 || true
    else
      printf "  Homebrew not found — installing Python manually is required.\n"
    fi
  else
    printf "  On Linux, install Python with your package manager, e.g.:\n"
    printf "    sudo apt install python3 python3-venv python3-pip\n"
  fi
  PY="$(find_python)"
  if [ -z "${PY:-}" ]; then
    printf "  Opening https://www.python.org/downloads/\n"
    printf "  Install Python 3.12, then start this file again.\n"
    ( open "https://www.python.org/downloads/" 2>/dev/null \
      || xdg-open "https://www.python.org/downloads/" 2>/dev/null ) || true
    exit 1
  fi
fi
printf "  Python:   %s (%s)\n" "$($PY --version 2>&1)" "$PY"

# ---------------------------------------------------------------- 2. venv --
if [ ! -x ".venv/bin/python" ]; then
  printf "  Creating virtual environment (.venv) — one time only...\n"
  "$PY" -m venv .venv || { printf "  ERROR: could not create .venv\n"; exit 1; }
fi
VPY=".venv/bin/python"

# --------------------------------------------------------- 3. dependencies --
if [ ! -f ".venv/.deps_ok" ] || [ "requirements.txt" -nt ".venv/.deps_ok" ]; then
  printf "  Installing dependencies (first run needs internet, 1-3 min)...\n"
  "$VPY" -m pip install --quiet --disable-pip-version-check -r requirements.txt \
    || { printf "  ERROR: pip install failed — check your internet connection.\n"; exit 1; }
  touch .venv/.deps_ok
else
  printf "  Dependencies: OK\n"
fi

# ------------------------------------------------------ 4. database setup --
printf "  Preparing database...\n"
"$VPY" manage.py migrate --noinput >/dev/null \
  || { printf "  ERROR: database migration failed.\n"; exit 1; }
"$VPY" manage.py seed_demo \
  || { printf "  ERROR: demo data seeding failed.\n"; exit 1; }

# --------------------------------------------------------- 5. demo accounts --
"$VPY" manage.py shell < scripts/setup_accounts.py \
  || { printf "  ERROR: account setup failed.\n"; exit 1; }

# ------------------------------------------------------------- 6. port -----
PORT="$("$VPY" scripts/find_free_port.py)"
if [ "${PORT:-0}" = "0" ]; then
  printf "  ERROR: ports 8000-8010 are all in use. Close some apps and retry.\n"
  exit 1
fi
URL="http://127.0.0.1:${PORT}/"

# ------------------------------------------------------------- 7. go -------
printf "\n"
hr
printf "  Gabriel Homes is starting at:  %s%s%s\n" "$BOLD" "$URL" "$NC"
printf "  Website:   %s\n" "$URL"
printf "  Admin:     http://127.0.0.1:%s/admin/     (admin@gabrielhomes.co.ke / gabriel2026)\n" "$PORT"
printf "  Agent:     http://127.0.0.1:%s/dashboard/  (hello@gabrielhomes.co.ke / gabriel2026)\n" "$PORT"
printf "  Stop:      close this window, or run STOP-WEBSITE\n"
printf "  Your browser will open as soon as the site is ready.\n"
hr
printf "\n"

# -- v2 fix: the browser used to open on a fixed 2-second guess, which
# -- raced the server (users got "This site can't be reached" or, on
# -- WSL/headless systems, nothing at all and silence about it).
# -- Now a waiter polls until the site answers, then opens the browser,
# -- with WSL-aware fallbacks and a loud message if it cannot.
if [ "$NO_BROWSER" != "1" ]; then
  "$VPY" scripts/open_browser_when_ready.py "$PORT" &
fi

exec "$VPY" manage.py runserver "0.0.0.0:${PORT}" --noreload

#!/usr/bin/env bash
# Watchdog: revive both servers if a sandbox wipe kills them.
# Runs one check+revive pass; schedule in a loop (or cron if it ever exists).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

port_up() { ss -tln 2>/dev/null | grep -q ":$1 "; }
changed=0

# Django :3011 (needs venv; if venv was wiped, rebuild it first)
if ! port_up 3011; then
  if [ ! -x gabriel_homes/.venv/bin/python ]; then
    ( cd gabriel_homes && python3 -m venv .venv \
      && .venv/bin/pip install -q -r requirements.txt ) >> scripts/watchdog.log 2>&1
  fi
  if [ ! -f gabriel_homes/db.sqlite3 ]; then
    ( cd gabriel_homes && .venv/bin/python manage.py migrate --noinput \
      && .venv/bin/python manage.py seed_demo ) >> scripts/watchdog.log 2>&1
  fi
  nohup python3 scripts/daemon_runserver.py >/dev/null 2>&1 &
  changed=1
fi

# Delivery :3000 (stdlib only)
if ! port_up 3000; then
  nohup python3 scripts/workspace_server.py \
    >"$ROOT/scripts/workspace-server.log" 2>&1 &
  changed=1
fi

if [ "$changed" = "1" ]; then
  echo "$(date '+%F %T') revived servers" >> scripts/watchdog.log
fi

#!/usr/bin/env bash
# Start both sandbox servers (idempotent - safe to re-run):
#   :3011  Django site   via scripts/daemon_runserver.py
#          (MUST be launched from the repo root with the system python3;
#           the daemon itself spawns gabriel_homes/.venv/bin/python)
#   :3000  delivery page via scripts/workspace_server.py
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

port_up() { ss -tln 2>/dev/null | grep -q ":$1 "; }

if port_up 3011; then
  echo ":3011 already up"
else
  echo "starting :3011 (Django daemon)..."
  python3 "$ROOT/scripts/daemon_runserver.py"
  sleep 2
fi

if port_up 3000; then
  echo ":3000 already up"
else
  echo "starting :3000 (delivery page)..."
  nohup python3 "$ROOT/scripts/workspace_server.py" \
    >"$ROOT/scripts/workspace-server.log" 2>&1 &
  sleep 1
fi

echo "-- health --"
curl -s -o /dev/null -w ':3011 Django      -> HTTP %{http_code}\n' http://127.0.0.1:3011/ \
  || echo ':3011 DOWN - check /tmp/runserver.log'
curl -s -o /dev/null -w ':3000 delivery  -> HTTP %{http_code}\n' \
  http://127.0.0.1:3000/scripts/preview_site/index.html \
  || echo ':3000 DOWN - check scripts/workspace-server.log'

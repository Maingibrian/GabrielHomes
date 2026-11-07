#!/usr/bin/env bash
# Gabriel Homes — sandbox live-preview restorer.
# Recreated 2026-11-07 after a workspace recycle wiped the previous script.
#
# What it does:
#   1. Ensures the sandbox .env exists (bridge flag + preview hosts).
#   2. Kills any stale runserver.
#   3. Starts runserver on 127.0.0.1:3011 (--noreload). The in-process
#      preview bridge (apps/core/preview_bridge.py) then binds 0.0.0.0:3000
#      and forwards to 3011 — the workspace caddy gateway (:81) expects
#      port 3000. NEVER bind runserver itself to 3000.
#   4. Waits for the bridge, then verifies the chain end to end.
set -u
PROJECT=/home/z/my-project/gabriel-homes
PY=/home/z/my-project/.venv/bin/python
cd "$PROJECT"

# --- 1. .env -------------------------------------------------------------
if [ ! -f .env ]; then
  printf 'GABRIEL_PREVIEW_BRIDGE=1\nEXTRA_ALLOWED_HOSTS=.space-z.ai,*\nCSRF_TRUSTED_ORIGINS=https://*.space-z.ai\n' > .env
  echo "[fix] .env recreated"
fi

# --- 2. stale processes ---------------------------------------------------
pkill -f "manage.py runserver" 2>/dev/null && sleep 2 || true

# --- 3. database (sqlite + demo data are gitignored; heal after recycle) --
if [ ! -f db.sqlite3 ]; then
  echo "[fix] db missing -> migrate + seed_demo"
  "$PY" manage.py migrate --noinput >/dev/null 2>&1
  "$PY" manage.py seed_demo --i-know-this-is-demo >/dev/null 2>&1
fi

# --- 4. start runserver ---------------------------------------------------
nohup "$PY" manage.py runserver 127.0.0.1:3011 --noreload > preview_runserver.log 2>&1 &
echo "[fix] runserver starting on 127.0.0.1:3011 (pid $!)"

# --- 5. wait for the bridge on :3000 --------------------------------------
up=""
for i in $(seq 1 60); do
  if (exec 3<>/dev/tcp/127.0.0.1/3000) 2>/dev/null; then up=1; break; fi
  sleep 0.5
done
if [ -z "$up" ]; then
  echo "[fix] ERROR: bridge never bound :3000 — see preview_bridge.log / preview_runserver.log"
  tail -5 preview_bridge.log 2>/dev/null
  tail -10 preview_runserver.log 2>/dev/null
  exit 1
fi
echo "[fix] bridge listening on 0.0.0.0:3000 -> 127.0.0.1:3011"

# --- 6. verify ------------------------------------------------------------
sleep 1
code() { curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$@"; }
R1=$(code http://127.0.0.1:3011/)
R2=$(code http://127.0.0.1:3000/)
R3=$(code http://127.0.0.1:3000/ -H "Host: preview.space-z.ai")
CSP=$(curl -s -D - -o /dev/null --max-time 15 http://127.0.0.1:3000/ \
      | tr -d '\r' | grep -i '^content-security-policy:' | head -1)
XFO=$(curl -s -D - -o /dev/null --max-time 15 http://127.0.0.1:3000/ \
      | tr -d '\r' | grep -i '^x-frame-options:' | head -1)
echo "[fix] runserver(3011): $R1 | bridge(3000): $R2 | bridge+preview-host: $R3"
echo "[fix] ${CSP:-<no CSP header>}"
echo "[fix] ${XFO:-<no X-Frame-Options header (exempted — iframe preview OK)>}"
case "$R1$R2$R3" in
  *200*200*200*) echo "[fix] PREVIEW STACK OK" ;;
  *) echo "[fix] WARN: unexpected status codes — check logs" ;;
esac

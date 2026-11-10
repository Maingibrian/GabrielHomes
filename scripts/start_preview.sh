#!/bin/bash
# Start the Gabriel Homes Django dev server + preview bridge so the workspace
# preview panel (browser -> gateway :81 -> bridge :3000 -> runserver :8000)
# can reach the site.
#
# setsid is essential: background processes are reaped when the launching
# bash invocation ends, unless they are detached into their own session.
set -u

cd /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes

pkill -f "manage.py runserver" 2>/dev/null
sleep 1

setsid nohup /home/z/.venv/bin/python3 manage.py runserver 0.0.0.0:8000 \
  > /tmp/gabriel-runserver.log 2>&1 < /dev/null &

sleep 7

echo "=== processes ==="
pgrep -af "manage.py runserver" | head -3 || echo "RUNSERVER NOT RUNNING"
echo "=== ports ==="
ss -tln 2>/dev/null | rg "3000|8000" || echo "PORTS NOT BOUND"
echo "=== gateway smoke test ==="
curl -s -o /dev/null -w "home via :81 -> %{http_code}\n" \
  -H "Host: ws-dfdddd-bbead-uabvrzfhdv.cn-hongkong-vpc.fcapp.run" \
  http://127.0.0.1:81/

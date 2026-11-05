#!/usr/bin/env bash
# Gabriel Homes — capture full-page preview screenshots of the running site.
# Server + browser must live within this single invocation (sandbox kills
# user processes between tool calls).
set -u
BASE=http://127.0.0.1:3000
OUT=/home/z/my-project/download/preview-screenshots
mkdir -p "$OUT"

# 1. Start Django dev server
cd /home/z/my-project/gabriel-homes || exit 1
/home/z/my-project/.venv/bin/python manage.py runserver 0.0.0.0:3000 --noreload >/tmp/django-preview.log 2>&1 &
DJANGO_PID=$!
for i in $(seq 1 20); do
  curl -s -o /dev/null --max-time 2 "$BASE/healthz/" && break
  sleep 1
done
echo "server-up pid=$DJANGO_PID"

shot () { # shot <name> <url> [desktop|mobile]
  local name="$1" url="$2" mode="${3:-desktop}"
  if [ "$mode" = "mobile" ]; then
    agent-browser set viewport 390 844 >/dev/null
  else
    agent-browser set viewport 1440 900 >/dev/null
  fi
  agent-browser open "$BASE$url" >/dev/null
  agent-browser wait --load networkidle >/dev/null 2>&1
  # scroll pass to trigger lazy-loaded images, then back to top
  agent-browser eval "window.scrollTo(0, document.body.scrollHeight)" >/dev/null 2>&1
  sleep 1
  agent-browser eval "window.scrollTo(0, 0)" >/dev/null 2>&1
  sleep 1
  agent-browser screenshot "$OUT/$name.png" --full >/dev/null
  local size
  size=$(stat -c%s "$OUT/$name.png" 2>/dev/null || echo 0)
  echo "$name.png  ${size} bytes  <- $url"
}

shot 01-home-desktop        /
shot 02-properties-browse   /properties/
shot 03-houses-rent-mombasa /houses-for-rent/mombasa/
shot 04-listing-detail      /listing/4br-maisonette-in-limuru-45/
shot 05-about               /about/
shot 06-contact             /contact/
shot 07-home-mobile         / mobile

agent-browser close >/dev/null 2>&1
kill "$DJANGO_PID" 2>/dev/null
echo "DONE"

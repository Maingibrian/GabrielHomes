#!/usr/bin/env bash
# r56 diagnosis captures — about + home, desktop + mobile, viewport shots.
set -u
BASE=http://127.0.0.1:3000
OUT=/home/z/my-project/download/preview-screenshots
mkdir -p "$OUT"

# make sure the bridge stack is alive (idempotent)
if ! curl -s -o /dev/null --max-time 3 "$BASE/healthz/"; then
  bash /home/z/my-project/scripts/fix-preview-bridge.sh >/dev/null 2>&1
  sleep 2
fi

agent-browser set media reduced-motion=no-preference >/dev/null 2>&1

shot () { # shot <name> <url> [desktop|mobile]
  local name="$1" url="$2" mode="${3:-desktop}"
  if [ "$mode" = "mobile" ]; then
    agent-browser set viewport 390 844 >/dev/null
  else
    agent-browser set viewport 1440 900 >/dev/null
  fi
  agent-browser open "$BASE$url" >/dev/null
  agent-browser wait --load networkidle >/dev/null 2>&1
  agent-browser eval "window.scrollTo(0, document.body.scrollHeight)" >/dev/null 2>&1
  sleep 1
  agent-browser eval "window.scrollTo(0, 0)" >/dev/null 2>&1
  sleep 1
  agent-browser screenshot "$OUT/r56-$name.png" --full >/dev/null
  local size
  size=$(stat -c%s "$OUT/r56-$name.png" 2>/dev/null || echo 0)
  echo "r56-$name.png  ${size} bytes  <- $url ($mode)"
}

shot about-desktop  /about/
shot about-mobile   /about/  mobile
shot home-desktop   /
shot home-mobile    /        mobile

agent-browser close >/dev/null 2>&1
echo "DONE"

#!/usr/bin/env bash
# r56 final capture — with a slow step-scroll so mid-page lazy images
# paint into the full-page bitmap (the previous full-page shots blanked
# the mid-page story figure — screenshot artifact, not a page defect).
set -u
bash /home/z/my-project/scripts/fix-preview-bridge.sh >/dev/null 2>&1
sleep 2
BASE=http://127.0.0.1:3000
OUT=/home/z/my-project/download/preview-screenshots
agent-browser set media reduced-motion=no-preference >/dev/null 2>&1

slowpass () {  # step-scroll the page so observers + lazy images fire
  agent-browser eval "
    (async () => {
      const h = document.body.scrollHeight;
      for (let y = 0; y <= h; y += 400) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
      await new Promise(r => setTimeout(r, 500));
      window.scrollTo(0, 0);
      await new Promise(r => setTimeout(r, 400));
    })()" >/dev/null 2>&1
  sleep 1
}

shot () {
  local name="$1" url="$2" mode="${3:-desktop}"
  if [ "$mode" = "mobile" ]; then
    agent-browser set viewport 390 844 >/dev/null
  else
    agent-browser set viewport 1440 900 >/dev/null
  fi
  agent-browser open "$BASE$url" >/dev/null
  agent-browser wait --load networkidle >/dev/null 2>&1
  slowpass
  agent-browser screenshot "$OUT/r56-final-$name.png" --full >/dev/null
  echo "r56-final-$name.png  $(stat -c%s "$OUT/r56-final-$name.png") bytes"
}

shot about-desktop /about/
shot about-mobile  /about/  mobile
shot home-desktop  /

agent-browser close >/dev/null 2>&1
echo DONE

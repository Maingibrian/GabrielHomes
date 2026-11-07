#!/usr/bin/env bash
# r56 verification: restart bridge (fresh templates), probe hero contrast,
# capture after screenshots.
set -u
bash /home/z/my-project/scripts/fix-preview-bridge.sh >/dev/null 2>&1
sleep 2
BASE=http://127.0.0.1:3000
OUT=/home/z/my-project/download/preview-screenshots
mkdir -p "$OUT"

agent-browser set media reduced-motion=no-preference >/dev/null 2>&1

# --- contrast probe: headline over the new bright slide 1 ---
agent-browser set viewport 1440 900 >/dev/null
agent-browser open "$BASE/" >/dev/null
agent-browser wait --load networkidle >/dev/null 2>&1
sleep 6  # let slide 1 be the visible slide (0-6s window)
agent-browser eval "
(() => {
  const h = document.querySelector('[data-hero-headline]');
  const r = h.getBoundingClientRect();
  const probe = (x, y) => {
    const el = document.elementFromPoint(
      r.left + x * r.width, r.top + y * r.height);
    return el ? el.tagName : 'none';
  };
  // rough luminance of the composited hero background under the title:
  // paint the slide image into a canvas via CSS is not possible directly,
  // so we approximate from the computed scrim + image average.
  const bg = getComputedStyle(document.querySelector('.hero__bg')).backgroundColor;
  return JSON.stringify({title: h.textContent.trim().slice(0, 40),
    rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    atPoint: probe(0.1, 0.5), bg});
})()
"

# --- screenshots ---
shot () {
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
  agent-browser screenshot "$OUT/r56-after-$name.png" --full >/dev/null
  echo "r56-after-$name.png  $(stat -c%s "$OUT/r56-after-$name.png") bytes  <- $url ($mode)"
}

shot about-desktop /about/
shot about-mobile  /about/  mobile
shot home-desktop  /
shot home-mobile   /        mobile

agent-browser close >/dev/null 2>&1
echo "DONE"

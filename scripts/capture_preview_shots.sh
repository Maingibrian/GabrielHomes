#!/usr/bin/env bash
# Capture v2: after each open, step-scroll the full page so IntersectionObserver
# reveals (motion.js) fire and lazy images load, then screenshot.
set -uo pipefail
OUT=/home/z/my-project/download/gabriel-homes-preview
GH=/home/z/my-project/gabriel_homes
AB=/usr/local/bin/agent-browser
BASE=http://127.0.0.1:3000
mkdir -p "$OUT"

cd "$GH"
.venv/bin/python manage.py runserver 0.0.0.0:3000 >/tmp/shot-server.log 2>&1 &
SRV=$!
up=0
for i in $(seq 1 30); do
    curl -sf -o /dev/null "$BASE/" && { up=1; break; }
    sleep 1
done
[ "$up" = 1 ] || { echo "FATAL: no server"; kill "$SRV" 2>/dev/null; exit 1; }
echo "server up"

VW=1440; VH=900
reveal() { # tall-viewport toggle fires IntersectionObserver for ALL sections,
           # then restore real viewport and step-scroll for lazy images
    "$AB" set viewport "$VW" 2600 >/dev/null 2>&1
    sleep 0.6
    "$AB" set viewport "$VW" "$VH" >/dev/null 2>&1
    "$AB" eval "(async () => { const h=document.body.scrollHeight; for(let y=0;y<=h;y+=700){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,120));} window.scrollTo(0,0); await new Promise(r=>setTimeout(r,400)); return 'ok'; })()" >/dev/null 2>&1
    sleep 1
}

shot() { # $1=path $2=outfile $3=settletime
    "$AB" open "$BASE$1" >/dev/null 2>&1 || { echo "OPEN-FAIL $1"; return 1; }
    sleep "${3:-2}"
    reveal
    "$AB" screenshot --full "$OUT/$2" >/dev/null 2>&1 \
        && echo "ok: $2" || echo "SHOT-FAIL $2"
}

# DOM sanity: does the agents directory actually contain agency cards?
"$AB" open "$BASE/agents/" >/dev/null 2>&1 && sleep 2
echo "--- DOM check on /agents/ ---"
"$AB" snapshot -c 2>/dev/null | grep -icE "coast|property|realty|homes|agency" || echo "no agency names found in DOM"

VW=1440; VH=900
$AB set viewport 1440 900 >/dev/null 2>&1
QUICK="${1:-full}"
if [ "$QUICK" = "quick" ]; then
    shot "/agents/"                   03-agents-bento-desktop.png 3
    shot "/listing/3br-bungalow-in-nyali-77/" 05-real-listing-desktop.png 4
else
shot "/"                          01-home-desktop.png        3
shot "/property-for-sale/"        02-search-desktop.png      3
shot "/agents/"                   03-agents-bento-desktop.png 3
shot "/agents/coast-property-co/" 04-agent-detail-desktop.png 3
shot "/listing/3br-bungalow-in-nyali-77/" 05-real-listing-desktop.png 4
shot "/about/"                    06-about-desktop.png       2
shot "/contact/"                  07-contact-desktop.png     2
VW=390; VH=844
$AB set viewport 390 844 >/dev/null 2>&1
shot "/"                          08-home-mobile.png         3
shot "/agents/"                   09-agents-mobile.png       3
shot "/listing/3br-bungalow-in-nyali-77/" 10-real-listing-mobile.png 4
fi

"$AB" close >/dev/null 2>&1
kill "$SRV" 2>/dev/null
echo "--- done ---"
ls -la "$OUT" | tail -11

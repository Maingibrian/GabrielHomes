#!/bin/bash
URL="$1"
if curl -s -o /dev/null --max-time 2 "$URL"; then STATE=UP; else STATE=DOWN; fi
echo "$(date +%s.%N) $URL $STATE" >> "${FAKE_BROWSER_LOG:?}"
exit 0

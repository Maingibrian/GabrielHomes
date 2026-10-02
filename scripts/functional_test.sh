#!/bin/bash
# Gabriel Homes — deep functional tests against the live dev server
BASE="http://127.0.0.1:8000"
JAR="/home/z/my-project/scripts/cookies.txt"
LOG="/home/z/my-project/scripts/server.log"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  OK   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL  $1  [$2]"; }
assert_contains() { # label, haystack_file, needle
  if grep -q "$3" "$2"; then ok "$1"; else bad "$1" "missing: $3"; fi
}
assert_not_contains() {
  if grep -q "$3" "$2"; then bad "$1" "unexpected: $3"; else ok "$1"; fi
}

rm -f "$JAR"
cd /home/z/my-project/gabriel_homes

echo "=== 0. Prep agent password (test harness) ==="
.venv/bin/python manage.py shell -c "
from apps.accounts.models import User
u = User.objects.filter(is_agent=True).first()
u.set_password('TestPass123!')
u.save()
print('AGENT_EMAIL=' + u.email)
" 2>/dev/null > /home/z/my-project/scripts/agent_email.txt
AGENT_EMAIL=$(grep AGENT_EMAIL= /home/z/my-project/scripts/agent_email.txt | cut -d= -f2)
echo "Agent: $AGENT_EMAIL"

echo "=== 1. Anonymous visitor: search & detail content ==="
curl -s "$BASE/" > /tmp/home.html
assert_contains "Home renders headline" /tmp/home.html "Real estate with a human point of view"
assert_contains "Home hero search form present" /tmp/home.html "search"
assert_contains "Home featured listings section" /tmp/home.html "[001]"
assert_contains "Home stats counter" /tmp/home.html "data-count"
assert_contains "Home story section" /tmp/home.html "\[STORY\]"
assert_contains "Home numbers section" /tmp/home.html "\[NUMBERS\]"
assert_contains "Home agents section" /tmp/home.html "\[AGENTS\]"
assert_contains "Home philosophy section" /tmp/home.html "\[001-UNDERSTAND\]"
assert_contains "Home footer wordmark" /tmp/home.html "Homes"
assert_contains "Home links to search URLs" /tmp/home.html "flats-apartments-for-sale"

curl -s "$BASE/flats-apartments-for-sale/mombasa/" > /tmp/search.html
assert_contains "Search H1 generated" /tmp/search.html "Flats &amp; Apartments for Sale in Mombasa"
assert_contains "Search has listing cards" /tmp/search.html "listing-card"
assert_contains "Search canonical tag" /tmp/search.html 'rel="canonical"'

curl -s "$BASE/property-for-sale/mombasa/?sort=DROP%20TABLE" > /tmp/bogussort.html
if grep -qi "error\|Traceback\|Exception" /tmp/bogussort.html; then bad "Bogus sort handled" "error text in page"; else ok "Bogus sort handled safely"; fi

LISTING_URL=$(grep -o '/listing/[a-z0-9-]*-[0-9]*/' /tmp/search.html | head -1)
echo "  (listing url: $LISTING_URL)"
curl -s "$BASE$LISTING_URL" > /tmp/detail.html
assert_contains "Detail JSON-LD present" /tmp/detail.html 'application/ld+json'
assert_contains "Detail canonical" /tmp/detail.html 'rel="canonical"'
assert_contains "Detail OG tags" /tmp/detail.html 'property="og:title"'
assert_contains "Detail enquiry form" /tmp/detail.html "enquiry"
assert_contains "Detail WhatsApp link" /tmp/detail.html "wa.me"
assert_contains "Detail map div" /tmp/detail.html "leaflet"
assert_contains "Detail price present" /tmp/detail.html "KES"
CSRF_TOKEN=$(grep -o 'csrfmiddlewaretoken" value="[^"]*"' /tmp/detail.html | head -1 | sed 's/.*value="//;s/"$//')
CSRF_COOKIE=$(grep csrftoken "$JAR" | awk '{print $NF}')

echo "=== 2. Enquiry flow (HTMX) ==="
COUNT_BEFORE=$(.venv/bin/python manage.py shell -c "from apps.inquiries.models import Inquiry; print(Inquiry.objects.count())" 2>/dev/null | tail -1)
SLUG=$(echo "$LISTING_URL" | sed 's|/listing/||;s|/$||' | sed 's/-[0-9]*$//')
PK=$(echo "$LISTING_URL" | grep -o '[0-9]*' | tail -1)
curl -s -b "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -H "HX-Request: true" \
  -d "csrfmiddlewaretoken=$CSRF_TOKEN&name=Test Buyer&email=buyer@test.com&phone=+254700111222&message=Is this still available?&website=" \
  "$BASE/enquiry/$SLUG-$PK/" -o /tmp/enquiry_resp.html -w "%{http_code}" > /tmp/enquiry_code.txt
CODE=$(cat /tmp/enquiry_code.txt)
if [[ "$CODE" == "200" ]]; then ok "Enquiry POST returns 200"; else bad "Enquiry POST" "code $CODE"; fi
assert_contains "Enquiry success partial" /tmp/enquiry_resp.html "Thank"
COUNT_AFTER=$(.venv/bin/python manage.py shell -c "from apps.inquiries.models import Inquiry; print(Inquiry.objects.count())" 2>/dev/null | tail -1)
if [[ "$COUNT_AFTER" -gt "$COUNT_BEFORE" ]]; then ok "Inquiry row created ($COUNT_BEFORE -> $COUNT_AFTER)"; else bad "Inquiry row" "count unchanged"; fi
if grep -q "New enquiry" "$LOG"; then ok "Agent email sent (console backend)"; else bad "Agent email" "not in server log"; fi

echo "=== 3. Honeypot catches spam ==="
curl -s -b "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -H "HX-Request: true" \
  -d "csrfmiddlewaretoken=$CSRF_TOKEN&name=SpamBot&email=bot@spam.com&phone=123&message=buy now&website=http://spam.com" \
  "$BASE/enquiry/$SLUG-$PK/" -o /tmp/honeypot.html -w "%{http_code}" > /tmp/honeypot_code.txt
CODE=$(cat /tmp/honeypot_code.txt)
if [[ "$CODE" == "200" ]]; then ok "Honeypot returns fake success"; else bad "Honeypot" "code $CODE"; fi
SPAM_COUNT=$(.venv/bin/python manage.py shell -c "from apps.inquiries.models import Inquiry; print(Inquiry.objects.filter(honeypot__gt='').count())" 2>/dev/null | tail -1)
if [[ "$SPAM_COUNT" -ge 1 ]]; then ok "Spam inquiry saved with honeypot flag"; else bad "Spam inquiry" "not flagged"; fi

echo "=== 4. Enquiry rate limit (3/min per IP) ==="
for i in 1 2 3; do
  curl -s -b "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -H "HX-Request: true" \
    -d "csrfmiddlewaretoken=$CSRF_TOKEN&name=RL$i&email=rl$i@test.com&phone=1&message=hi&website=" \
    -o /dev/null "$BASE/enquiry/$SLUG-$PK/"
done
CODE=$(curl -s -b "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -H "HX-Request: true" \
  -d "csrfmiddlewaretoken=$CSRF_TOKEN&name=RL4&email=rl4@test.com&phone=1&message=hi&website=" \
  -o /tmp/ratelimit.html -w "%{http_code}" "$BASE/enquiry/$SLUG-$PK/")
if [[ "$CODE" == "429" ]]; then ok "4th enquiry rate-limited with 429"; else bad "Rate limit" "code $CODE (want 429)"; fi

echo "=== 5. Agent login + dashboard end-to-end ==="
curl -s -c "$JAR" "$BASE/account/login/" > /tmp/login.html
CSRF_TOKEN=$(grep -o 'csrfmiddlewaretoken" value="[^"]*"' /tmp/login.html | head -1 | sed 's/.*value="//;s/"$//')
CSRF_COOKIE=$(grep csrftoken "$JAR" | awk '{print $NF}')
curl -s -b "$JAR" -c "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -L \
  -d "csrfmiddlewaretoken=$CSRF_TOKEN&login=$AGENT_EMAIL&password=TestPass123!" \
  "$BASE/account/login/" -o /tmp/login_post.html -w "%{http_code}" > /tmp/login_code.txt
if grep -q "dashboard\|Sign Out\|Logout" /tmp/login_post.html; then ok "Agent login succeeds"; else bad "Agent login" "no dashboard marker"; fi

CODE=$(curl -s -b "$JAR" -o /tmp/dash.html -w "%{http_code}" "$BASE/dashboard/")
if [[ "$CODE" == "200" ]]; then ok "Dashboard 200 for agent"; else bad "Dashboard" "code $CODE"; fi
assert_contains "Dashboard shows listing table" /tmp/dash.html "listing"

echo "=== 6. Agent creates listing via dashboard ==="
curl -s -b "$JAR" "$BASE/dashboard/listings/new/" > /tmp/newform.html
CSRF_TOKEN=$(grep -o 'csrfmiddlewaretoken" value="[^"]*"' /tmp/newform.html | head -1 | sed 's/.*value="//;s/"$//')
CSRF_COOKIE=$(grep csrftoken "$JAR" | awk '{print $NF}')
LOC_ID=$(.venv/bin/python manage.py shell -c "from apps.locations.models import Location; print(Location.objects.filter(level='neighbourhood').first().id)" 2>/dev/null | tail -1)
PT_ID=$(.venv/bin/python manage.py shell -c "from apps.listings.models import PropertyType; print(PropertyType.objects.filter(slug_plural='flats-apartments').first().id)" 2>/dev/null | tail -1)
AM_ID=$(.venv/bin/python manage.py shell -c "from apps.listings.models import Amenity; print(Amenity.objects.first().id)" 2>/dev/null | tail -1)
curl -s -b "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -L \
  -d "csrfmiddlewaretoken=$CSRF_TOKEN&title=Agent Test Apartment Nyali&listing_type=sale&property_type=$PT_ID&location=$LOC_ID&price=12500000&price_period=total&bedrooms=3&bathrooms=2&furnishing=unfurnished&status=published&description=A test listing created by the E2E functional test.&amenities=$AM_ID" \
  "$BASE/dashboard/listings/new/" -o /tmp/create_resp.html -w "%{http_code}" > /tmp/create_code.txt
NEW_ID=$(.venv/bin/python manage.py shell -c "from apps.listings.models import Property; p=Property.objects.filter(title='Agent Test Apartment Nyali').first(); print(p.pk if p else 'MISSING')" 2>/dev/null | tail -1)
if [[ "$NEW_ID" != "MISSING" && -n "$NEW_ID" ]]; then ok "Listing created (id $NEW_ID)"; else bad "Listing create" "not in DB"; fi
CODE=$(curl -s -o /tmp/new_public.html -w "%{http_code}" "$BASE/listing/agent-test-apartment-nyali-$NEW_ID/")
if [[ "$CODE" == "200" ]]; then ok "New listing live on public site"; else bad "New listing public" "code $CODE"; fi

echo "=== 7. Permissions: agent A cannot edit agent B's listing ==="
OTHER_ID=$(.venv/bin/python manage.py shell -c "
from apps.listings.models import Property
from apps.accounts.models import User
me = User.objects.filter(is_agent=True).first()
others = Property.objects.exclude(agent__user=me).first()
print(others.pk)" 2>/dev/null | tail -1)
CODE=$(curl -s -b "$JAR" -o /tmp/perm.html -w "%{http_code}" "$BASE/dashboard/listings/$OTHER_ID/edit/")
if [[ "$CODE" == "404" ]]; then ok "Cross-agent edit blocked (404)"; else bad "Cross-agent edit" "code $CODE (want 404)"; fi

echo "=== 8. Save / unsave toggle ==="
curl -s -b "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -H "HX-Request: true" \
  -d "csrfmiddlewaretoken=$CSRF_TOKEN" \
  "$BASE/account/save/$NEW_ID/" -o /tmp/save1.html -w "%{http_code}" > /tmp/save_code.txt
assert_contains "Save ON partial" /tmp/save1.html "saved"
SAVED_COUNT=$(.venv/bin/python manage.py shell -c "from apps.accounts.models import SavedProperty; print(SavedProperty.objects.count())" 2>/dev/null | tail -1)
if [[ "$SAVED_COUNT" -ge 1 ]]; then ok "SavedProperty row created"; else bad "SavedProperty" "none"; fi
curl -s -b "$JAR" -H "X-CSRFToken: $CSRF_COOKIE" -H "HX-Request: true" \
  -d "csrfmiddlewaretoken=$CSRF_TOKEN" "$BASE/account/save/$NEW_ID/" -o /tmp/save2.html
SAVED_COUNT2=$(.venv/bin/python manage.py shell -c "from apps.accounts.models import SavedProperty; print(SavedProperty.objects.count())" 2>/dev/null | tail -1)
if [[ "$SAVED_COUNT2" -lt "$SAVED_COUNT" ]]; then ok "Toggle off removes row"; else bad "Toggle off" "count $SAVED_COUNT -> $SAVED_COUNT2"; fi

echo "=== 9. Saved list page ==="
CODE=$(curl -s -b "$JAR" -o /tmp/savedlist.html -w "%{http_code}" "$BASE/account/saved/")
if [[ "$CODE" == "200" ]]; then ok "Saved list 200"; else bad "Saved list" "code $CODE"; fi

echo "=== 10. Autocomplete endpoint ==="
curl -s "$BASE/search/locations/?q=nya" > /tmp/autocomplete.json
if .venv/bin/python -c "import json; d=json.load(open('/tmp/autocomplete.json')); assert isinstance(d, list) or 'results' in d; print(True)" 2>/dev/null | grep -q True; then
  ok "Autocomplete returns valid JSON"; else bad "Autocomplete" "invalid JSON: $(head -c 100 /tmp/autocomplete.json)"; fi

echo "=== 11. Sitemap & robots content ==="
curl -s "$BASE/sitemap.xml" > /tmp/sitemap.xml
assert_contains "Sitemap lists listing URLs" /tmp/sitemap.xml "/listing/"
assert_contains "Sitemap lists search URLs" /tmp/sitemap.xml "for-sale"
curl -s "$BASE/robots.txt" > /tmp/robots.txt
assert_contains "robots.txt disallows admin" /tmp/robots.txt "Disallow: /admin/"
assert_contains "robots.txt points to sitemap" /tmp/robots.txt "Sitemap:"

echo "=== 12. HTMX pagination partial ==="
curl -s -H "HX-Request: true" "$BASE/property-for-sale/mombasa/?page=2" > /tmp/page2.html
if grep -q "listing-card\|results" /tmp/page2.html; then ok "HTMX page 2 partial renders"; else bad "HTMX page 2" "empty partial"; fi

echo ""
echo "================================"
echo "FUNCTIONAL PASS: $PASS   FAIL: $FAIL"

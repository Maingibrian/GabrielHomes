#!/bin/bash
# Gabriel Homes — comprehensive URL smoke test
BASE="http://127.0.0.1:8000"
PASS=0; FAIL=0; FAILED_URLS=()

check() {
  local label="$1"; local url="$2"; local expect="${3:-200}"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$BASE$url")
  # follow one redirect if 301/302
  if [[ "$code" == "301" || "$code" == "302" ]]; then
    code=$(curl -s -L -o /dev/null -w "%{http_code}" --max-time 15 "$BASE$url")
  fi
  if [[ "$code" == "$expect" ]]; then
    PASS=$((PASS+1)); printf "  OK   %-3s  %s\n" "$code" "$label"
  else
    FAIL=$((FAIL+1)); FAILED_URLS+=("$label -> $url (got $code, want $expect)")
    printf "FAIL  %-3s  %s  %s\n" "$code" "$label" "$url"
  fi
}

# get a real listing slug-id and agency slug from the DB
LISTING=$(cd /home/z/my-project/gabriel_homes && .venv/bin/python manage.py shell -c "
from apps.listings.models import Property
p = Property.objects.published().first()
print(f'{p.slug}-{p.pk}')
" 2>/dev/null | tail -1)
AGENCY=$(cd /home/z/my-project/gabriel_homes && .venv/bin/python manage.py shell -c "
from apps.agents.models import AgencyProfile
print(AgencyProfile.objects.first().slug)
" 2>/dev/null | tail -1)
echo "Using listing: $LISTING | agency: $AGENCY"
echo "=== CORE PAGES ==="
check "Home"                        "/"
check "Styleguide"                  "/styleguide/"
check "About"                       "/about/"
check "Contact"                     "/contact/"
check "Privacy"                     "/privacy/"
check "Terms"                       "/terms/"
echo "=== SEARCH URLS (SEO map) ==="
check "Type-for-sale (no loc)"      "/flats-apartments-for-sale/"
check "Type-for-sale + loc"         "/flats-apartments-for-sale/mombasa/"
check "Type-for-rent + loc"         "/houses-for-rent/nairobi/"
check "All-for-sale + loc"          "/property-for-sale/mombasa/"
check "All-for-rent + loc"          "/property-for-rent/nairobi/"
check "Type-for-rent (no loc)"      "/houses-for-rent/"
check "All-for-sale (no loc)"       "/property-for-sale/"
check "All-for-rent (no loc)"       "/property-for-rent/"
check "Land for sale + loc"         "/land-for-sale/kiambu/"
check "Villas rent Diani(Kwale)"    "/villas-for-rent/diani/"
echo "=== SEARCH FILTERS (query params) ==="
check "min/max price"               "/flats-apartments-for-sale/mombasa/?min_price=5000000&max_price=20000000"
check "beds+baths"                  "/flats-apartments-for-sale/mombasa/?beds=2&baths=2"
check "furnishing"                  "/houses-for-rent/nairobi/?furnishing=furnished"
check "sort price_desc"             "/property-for-sale/mombasa/?sort=price_desc"
check "sort featured"               "/property-for-sale/mombasa/?sort=featured"
check "q free text"                 "/property-for-sale/mombasa/?q=Nyali"
check "page 2"                      "/property-for-sale/mombasa/?page=2"
check "amenities filter"            "/property-for-rent/nairobi/?amenities=1&amenities=2"
check "bogus sort whitelisted"      "/property-for-sale/mombasa/?sort=DROP%20TABLE"
check "page beyond range"           "/property-for-sale/mombasa/?page=999"
echo "=== LISTING DETAIL ==="
check "Listing detail"              "/listing/$LISTING/"
check "Listing JSON-LD present"     "/listing/$LISTING/"
echo "=== AGENTS ==="
check "Agent directory"             "/agents/"
check "Agent profile"               "/agents/$AGENCY/"
check "Agent search q"              "/agents/?q=mombasa"
echo "=== ACCOUNT ==="
check "Login"                       "/account/login/"
check "Signup"                      "/account/signup/"
check "Password reset"              "/account/password/reset/"
# NOTE: check() follows one redirect, so an anon 302 -> login page lands on 200.
check "Saved (anon -> login)"       "/account/saved/" "200"
echo "=== DASHBOARD (auth) ==="
check "Dashboard anon -> login"     "/dashboard/" "200"
echo "=== MISC / SEO ==="
check "robots.txt"                  "/robots.txt"
check "sitemap.xml"                 "/sitemap.xml"
check "favicon"                     "/favicon.ico"
echo "=== 404 HANDLING ==="
check "Bogus page -> 404"           "/this-page-does-not-exist/" "404"
check "Bogus listing -> 404"        "/listing/not-a-real-listing-99999/" "404"
check "Bogus location -> 404"       "/property-for-sale/not-a-place/" "404"
check "Bogus type -> 404"           "/not-a-type-for-sale/mombasa/" "404"
echo "=== ADMIN ==="
check "Admin login"                 "/admin/login/"
echo "=== HTMX ENDPOINTS ==="
check "Autocomplete"                "/search/locations/?q=Nya"
check "Results partial (htmx)"      "/property-for-sale/mombasa/?page=2" "200"
echo "=== STATIC / MEDIA ==="
check "tokens.css"                  "/static/css/tokens.css"
check "base.css"                    "/static/css/base.css"
check "components.css"              "/static/css/components.css"
check "home.css"                    "/static/css/home.css"
check "search.css"                  "/static/css/search.css"
check "detail.css"                  "/static/css/detail.css"
check "dashboard.css"               "/static/css/dashboard.css"
check "motion.js"                   "/static/js/motion.js"
check "Geist font"                  "/static/fonts/Geist-Variable.woff2"
check "Geist Mono font"             "/static/fonts/GeistMono-Variable.woff2"
check "hero-bg.jpg"                 "/static/img/hero-bg.jpg"
check "media image"                 "$(cd /home/z/my-project/gabriel_homes && .venv/bin/python manage.py shell -c "
from apps.listings.models import PropertyImage
print(PropertyImage.objects.first().image.url)
" 2>/dev/null | tail -1)"

echo ""
echo "================================"
echo "PASS: $PASS   FAIL: $FAIL"
for f in "${FAILED_URLS[@]}"; do echo "  FAILED: $f"; done

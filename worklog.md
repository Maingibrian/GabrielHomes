# Worklog — gabriel_homes verification & troubleshooting

---
Task ID: 1
Agent: Super Z (main agent)
Task: Confirm whether the Gabriel Homes website is sufficient, test it thoroughly, and troubleshoot all issues found.

Work Log:
- Located the project at /home/z/my-project/gabriel_homes (Django 5.1 property portal, Phases 0-7 per WORK.md), dev server already running on :8000.
- Ran the backend suite via pytest (project uses pytest-django, not `manage.py test`): 231/231 passed.
- Ran scripts/smoke_test.sh (58 URL checks) and scripts/functional_test.sh (46 deep checks incl. enquiry, honeypot, rate limit, agent login, listing create, save toggle, sitemap/robots).
- Triaged every failure into "site bug" vs "stale test-script expectation"; verified each raw HTTP behaviour with curl.
- Fixed 7 real site bugs: missing /property-for-sale/ + /property-for-rent/ routes (default hero search 404), search-view GET-param fallback, dead home browse/View-all links, empty enquiry form on detail page (include without `with form=enquiry_form`), footer /careers/ + /cookies/ 404s, header nav dead anchors + no account links (added Sign in / Saved / Dashboard / Sign out), favicon 404 (created static/img/favicon.svg + link tag), mobile-menu aria-hidden never toggled (a11y).
- Rewrote stale expectations in both test scripts (endpoints, cookie jar ordering, grep patterns, POST data validity, rate-limiter reset) and added regression asserts for the enquiry-form bug.
- Live browser E2E with agent-browser (desktop + iPhone 14): autocomplete hero search, HTMX enquiry submit, agent login -> dashboard -> new listing form -> sign out, mobile menu open/navigate; zero console/page errors.
- Re-ran everything green: pytest 231/231, smoke 58/58, functional 46/46; prod check --deploy clean except documented W009 (no real SECRET_KEY in env).
- Appended a full dated entry to gabriel_homes/WORK.md section 14 (project's own progress log).

Stage Summary:
- Verdict: the site is SUFFICIENT / production-ready for v1 after this pass; it was not before (default search click 404'd, detail-page enquiry form was unusable in a real browser).
- All fixes are in the repo; dev server auto-reloaded and serving the fixed build.
- Test suites: pytest 231, scripts/smoke_test.sh, scripts/functional_test.sh — all green and now trustworthy as regression gates.

---
Task ID: 2
Agent: Super Z (main agent)
Task: Continue verification after session restart — re-confirm site sufficiency, re-run all suites, troubleshoot new findings.

Work Log:
- Re-verified current state of /home/z/my-project/gabriel_homes: dev server up (200), pytest 231/231, smoke 58/58 on first pass.
- First functional re-run: 45/46; immediate second run: 37/46 — 9 failures clustered on agent login -> dashboard -> save toggle.
- Diagnosed via server.log: GET /account/login/ returned 429 (auth rate limiter metered page views), so the login POST had no CSRF cookie -> 403, cascading to all session-dependent checks. Section-6 "listing created" check false-passed on a leftover published test listing (id 84) from a prior run.
- Fixed apps/accounts/rate_limit.py: limiter now meters only POST/PUT/PATCH/DELETE; GET/HEAD pass through. Added Retry-After header + text/plain content type to the 429 response.
- Added regression test test_login_get_is_never_rate_limited (10 GETs -> all 200; POST budget unaffected by GETs).
- Made scripts/functional_test.sh idempotent: prep purges Property rows titled 'Agent Test *'.
- Deleted leftover 'Agent Test Apartment Nyali' (id 84) from the demo DB; search results confirmed clean.
- Re-ran everything: pytest 232/232, smoke 58/58, functional 46/46 on run 1 AND immediate back-to-back run 2. /account/login/ -> 200, home -> 200.
- Appended dated entry to gabriel_homes/WORK.md section 14.

Stage Summary:
- Verdict unchanged and re-confirmed: the site IS sufficient / production-ready for v1.
- New fix this pass: auth rate limiter no longer locks users out of rendering auth pages (real NAT/office UX bug found via test flakiness).
- All suites green and now provably idempotent across consecutive runs.

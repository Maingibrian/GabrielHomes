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

---
Task ID: 3
Agent: Super Z (main agent)
Task: Deliver the project as a one-click package — script the user can double-click to run the whole website. Plan first, triple-check before delivery.

Work Log:
- Read key configs: requirements.txt (pinned, Python 3.12), dev settings force SQLite + DEBUG, MEDIA_ROOT='' (CWD-relative -> launcher must cd to project root), seed_demo idempotent + Pillow covers (offline), UserManager.create_superuser(email, password), PyPI reachable.
- TRIPLE-CHECK 1: re-ran full suites on the fixed project — pytest 232/232, smoke 58/58, functional 46/46.
- Wrote launchers (scripts/launcher/): START-GABRIEL-HOMES.{sh,command,bat} + STOP-WEBSITE.{sh,command,bat} + RUN-ME-FIRST.txt. Shared logic: find/install Python 3.10+ (winget/brew fallback, download-page last resort), venv + pip install (marker-file .deps_ok), migrate, idempotent seed, demo accounts via project scripts/setup_accounts.py (admin@gabrielhomes.co.ke / hello@gabrielhomes.co.ke, both gabriel2026), free-port scan 8000-8010 via project scripts/find_free_port.py, auto-open browser (GABRIEL_NO_BROWSER=1 for headless runs), runserver --noreload in foreground. Windows .bat authored then CRLF-converted; unix scripts LF + chmod +x; for /f uses the call pattern for quoted paths.
- Added project helpers: scripts/find_free_port.py, scripts/setup_accounts.py.
- build_package.sh: DB hygiene (test inquiries/sessions/Agent Test listings deleted), rsync stage (excludes .venv/__pycache__/.pytest_cache/etc), adds launchers, fixes line endings, zips -> download/gabriel-homes-oneclick.zip (3.8M, 486 files, verified 0 junk entries).
- TRIPLE-CHECK 2 (cold start, scripts/coldstart_test.sh): fresh copy with NO venv and NO db -> launcher created venv, installed deps (~12s), migrated, seeded 80 listings + images, created accounts, port fallback 8001 (8000 busy), 8/8 page checks (home/search x2/detail/login/admin/media/autocomplete), no data duplication on re-run. PASSED.
- TRIPLE-CHECK 3 (delivery verification, scripts/zipboot_test.sh): unzipped the actual zip -> structure complete, 0 junk entries, .bat=CRLF ASCII, .sh=LF executable, exec bits preserved; booted with shipped db -> server in ~12s, 7/7 checks, seeding correctly skipped (80->80). PASSED.
- Cleaned test copies (coldtest/ziptest). Main dev server on :8000 still serving.

Stage Summary:
- Deliverable: /home/z/my-project/download/gabriel-homes-oneclick.zip (3.8 MB) — unzip anywhere, double-click START-GABRIEL-HOMES(.bat/.command/.sh) for your OS.
- Triple-checked: suites green pre-package; cold start green; delivered-zip boot green.
- Demo credentials documented in RUN-ME-FIRST.txt: admin@gabrielhomes.co.ke / gabriel2026 (admin), hello@gabrielhomes.co.ke / gabriel2026 (agent dashboard).

---
Task ID: 4
Agent: Super Z (main agent)
Task: Bug report from user — "it didn't open my browser". Re-assess the one-click package, find the root cause, fix it, re-verify 100%.

Work Log:
- Root-cause analysis of the v1 launchers (user ran the delivered zip; browser never opened usable site). Found 7 concrete defects:
  1. START-GABRIEL-HOMES.bat opened the browser BEFORE `runserver` bound the port -> browser fired into ERR_CONNECTION_REFUSED.
  2. .sh launcher used a fixed `sleep 2` guess -> same race on slow first boots.
  3. .sh swallowed every browser-open failure silently (`2>/dev/null || true`) — WSL/headless systems got nothing AND no message.
  4. No WSL-aware fallbacks (wslview / cmd.exe / explorer.exe) — xdg-open typically fails under WSL.
  5. Windows: a winget-installed Python is invisible in the running session (PATH not refreshed) -> script gave up before the browser stage.
  6. Windows: running the .bat from inside Explorer's zip preview extracts only that file to %TEMP% -> pip failed -> early exit, no browser.
  7. STOP-WEBSITE.bat used `!FOUND!` without EnableDelayedExpansion -> status messages never printed.
- META root cause (why previous "triple check" missed it): all three verification runs used GABRIEL_NO_BROWSER=1 — the browser path was NEVER executed before delivery.
- Fixes:
  - New gabriel_homes/scripts/open_browser_when_ready.py: polls the URL until HTTP is answered (45s budget), THEN opens the browser (webbrowser + per-OS fallbacks incl. WSL), prints a loud ASCII manual-URL banner if it cannot; honours GABRIEL_NO_BROWSER; non-fatal exit 0.
  - Rewrote START-GABRIEL-HOMES.bat (v2): extraction guard, winget PATH-refresh probe of standard install dirs, browser helper via `start /b`, runserver stays foreground.
  - Rewrote START-GABRIEL-HOMES.sh (v2): extraction guard, helper in background replaces racy sleep-2 subshell.
  - Fixed STOP-WEBSITE.bat delayed expansion; updated RUN-ME-FIRST.txt (extract-first warning, Gatekeeper, WSL note, "browser opens when site is ready", manual-URL troubleshooting).
- NEW regression harness scripts/browser_helper_test.sh (4 cases, 14 checks): late-starting server -> browser fires once, correct URL, site verifiably UP at open time, waited >=2s (v1 would fire at ~0s); timeout -> loud warning no open; GABRIEL_NO_BROWSER=1 -> no-op; no browser available -> loud manual-URL message. 14/14 PASS.
- Environment drift found + fixed: source .venv and db.sqlite3 had vanished -> restored db from the shipped zip, recreated .venv, made build_package.sh self-healing (recreates venv + reseeds db if missing) with zip-stage sanity gates (helper present, launchers call it, racy patterns absent).
- Upgraded coldstart_test.sh + zipboot_test.sh: fake browser wired via $BROWSER records every open + whether the site answered — the browser path is now exercised end-to-end in BOTH e2e tests.
- Re-verified: pytest 232/232; build sanity gates OK; TRIPLE-CHECK 2 cold start 11/11 (incl. browser fired once, correct URL, site UP); TRIPLE-CHECK 3 delivered-zip boot 10/10 (80->80 no duplication, browser checks green); zip integrity OK, .bat CRLF OK.
- Cleaned test copies; rebuilt /home/z/my-project/download/gabriel-homes-oneclick.zip (3.8 MB).

Stage Summary:
- The browser bug is fixed at the design level: the browser can no longer open before the site answers, failures are loud (never silent), and WSL/zip-viewer/winget-PATH traps are guarded.
- The exact failure the user hit is now a permanent regression gate: browser auto-open is asserted in the unit harness AND both e2e harnesses.
- Deliverable rebuilt and triple-verified: /home/z/my-project/download/gabriel-homes-oneclick.zip

---
Task ID: 5
Agent: Super Z (main agent)
Task: User hit "CMD does not support UNC paths" — corporate redirected Downloads (\\KT-DC2\FolderRedir$\...). Re-assess, fix, re-verify.

Work Log:
- Diagnosis: user DID extract the zip correctly; their Downloads folder is a network share. CMD cannot use a UNC path as CWD (silently falls back to C:\Windows), so the v2 guard misfired with the "zip window" message.
- DEEPER FIND via paren-audit grep: the v1 AND v2 .bat contained 3 unquoted ')' inside echo lines within if(...) blocks — in cmd this closes the block early. Consequences: v1/v2 died with a syntax error at "Creating virtual environment (.venv)" on EVERY first run (the true Windows-killer), and the pip-error branch paused+exited unconditionally. The UNC bug the user hit was just the first wall.
- v3 START-GABRIEL-HOMES.bat: absolute-path manage.py guard, UNC detection (%SRCDIR:~0,2%=="\\") -> robocopy the site to %LOCALAPPDATA%\GabrielHomes (excluding db.sqlite3/.venv/__pycache__, db copied only if absent so local data is never clobbered), then run from the local copy; all 3 paren bugs reworded; space-safe PYCMD storage (quoted %%P); delayed !LOCALAPPDATA! for the fallback path; runserver bound to 127.0.0.1 (avoids the Windows Firewall prompt on corporate machines). .sh switched to 127.0.0.1 too.
- NEW permanent gate in build_package.sh: static .bat block-paren auditor (tracks if/for block depth on quote-stripped lines; forbids unquoted ')' in echo/rem lines inside blocks; checks block balance). Self-tested: fixed .bat CLEAN; all 3 historical bugs CAUGHT by the scanner.
- Environment drift (Oct 5): source .venv + db.sqlite3 wiped again between sessions — build_package.sh self-heal recreated both automatically (recreated venv, migrate+seed 80 listings, setup accounts) exactly as designed on Oct 3.
- RUN-ME-FIRST.txt: documented the network-drive auto-copy behaviour (HOW TO START + TROUBLESHOOTING).
- Re-verified: browser-helper unit 14/14; cold start 11/11 (browser fired once, correct URL, site UP); delivered-zip boot 10/10 (80->80, browser green); zip integrity OK; UNC handling + CRLF confirmed inside the shipped .bat.
- Deliverable: /home/z/my-project/download/gabriel-homes-oneclick.zip (5.2 MB — larger because the reseeded DB regenerated fresh image files).

Stage Summary:
- Root cause of user's failure: corporate UNC Downloads folder + CMD's UNC limitation; fixed by automatic copy-to-local-disk in v3.
- Also found and killed the deeper Windows-killer (paren-in-echo breaking every first run) that v1 and v2 shipped with; a static scanner gate now prevents this bug class permanently.
- All suites green; browser path exercised end-to-end in unit + both e2e harnesses.

---
Task ID: 6
Agent: Super Z (main agent)
Task: Final independent verification of the SHIPPED v3 zip before telling the user "download and run".

Work Log:
- Confirmed zip mtime 2026-10-05 07:48 UTC (5.4 MB, 602 entries, integrity OK).
- Byte-verified the shipped START-GABRIEL-HOMES.bat against the v3 source (identical modulo CRLF; file(1) confirms "DOS batch file, ASCII text, with CRLF line terminators"); shipped .sh and open_browser_when_ready.py identical to sources.
- Wrote scripts/verify_v3_zip.sh: runs every build gate against the launchers EXTRACTED FROM THE ZIP (browser chain, UNC detection SRCDIR:~0,2 + robocopy + LOCALAPPDATA, block-paren audit, CRLF/LF, RUN-ME network-drive docs), fresh-unzips the artifact (0 junk entries, all 10 key files present, exec bits), then chains zipboot_test.sh and browser_helper_test.sh.
- Harness bugs found and fixed during gating (artifact was never wrong): Python backslash-escaping in the UNC assertion, case-sensitive grep for "network drive", pass/fail accounting that read $? after echo instead of after python.
- Results: static gates PASS; zipboot e2e PASS=10 FAIL=0 (server up ~9-12s, home/search/about/listing/media/sitemap green, 80->80 listings no duplication, browser fired exactly once at the served URL with site UP); browser-helper harness PASS=14 FAIL=0; STOP-WEBSITE.bat EnableDelayedExpansion fix confirmed in zip. FINAL: PASS=18 FAIL=0 -> CLEARED FOR DELIVERY.
- Cleaned ziptest/ziptest-gate scratch dirs.

Stage Summary:
- The exact zip in download/gabriel-homes-oneclick.zip is verified as-shipped, not as-sourced: UNC auto-copy logic, browser-when-ready chain, paren-audit cleanliness, encodings and boot behaviour all green on the artifact itself.

---
Task ID: 7
Agent: Super Z (main agent)
Task: Design overhaul — user verdict "the front page looks generic... give it style". Plan + implement + verify.

Work Log:
- AUDIT (before-screenshots desktop/mobile + code read): root cause of "generic" was NOT layout — it was (1) zero real photography: hero was a cartoon skyline JPEG, all 80 listing covers were flat Pillow-gradient rectangles, agency portraits were CSS gradient divs, founder portrait was a gradient block; (2) one font family (Geist) doing every job; (3) text-only cards; (4) cavernous flat dark sections.
- IMAGERY (the ~70% win): 6 image-search batches -> 95 downloaded, PIL-validated. Curated + cropped stock watermark strips (CROP_BOTTOM map). Built clean pools in media/demo-photos/{house,apartment,shops,warehouse,office,land,interior,portraits}. First assignment caught 6 images with DIAGONAL watermarks that survive bottom-crops (men-01/women-02/women-03 portraits, living-06/bedroom-02 interiors, garden-03 land, plus borderline apartment2-02/04, officebld-04) -> blacklisted after large-thumb pool audit (verify_pools.py), re-fetched 12 replacement portraits (men2/women2). Final: 80 covers overwritten IN PLACE (filename/DB stable, type-matched exteriors via md5(slug)), 33 interiors, 6 agency portraits via AgencyProfile.logo, hero (dusk cliff villa), CTA beach, founder portrait. Orphan media files deleted (6 old logos + portrait-07).
- seed_demo.py: added _demo_photo() — future reseeds prefer the bundled media/demo-photos pool (deterministic md5 pick, type-aware via DEMO_TYPE_POOL), Pillow art stays as offline fallback.
- TYPOGRAPHY: self-hosted Fraunces variable (normal+italic latin woff2, 144KB total) in static/fonts; tokens.css adds --font-display; base.css h1-h6 -> Fraunces 560 opsz60; hero/display/wordmark/story-quote tuned per-section (opsz 144 display sizes, italic clay accent on "human").
- CSS: components.css — warm-tinted shadow tokens (--shadow-card-hover), listing-card cover shade + 0.7s image zoom + 5px lift, value/principle cards get icon slot + hover lift, agent cards + portraits refined. home.css — hero overlay deepened, agents section radial clay/brown texture, CTA background photo + overlay, founder portrait real image with hover shadow.
- TEMPLATES: home.html hero title gets <em class="hero__accent">, founder portrait uses static/img/founder.jpg, 3 value cards get inline SVG line icons (people/eye/keys).
- BUGS FOUND DURING VERIFY: pytest caught my new SVGs missing aria-hidden (a11y gate works) -> fixed, 232/232. Dev server (--noreload) served stale templates -> restart fixed. Browser cache showed stale hero -> fresh session re-captured.
- VERIFICATION: pytest 232/232, smoke 58/58, functional 46/46 (run twice), before/after screenshots desktop + mobile viewport-scrolls (mobile hero/serif/search pill confirmed clean), zipboot e2e 10/10, browser-helper 14/14, delivery gate PASS=18 FAIL=0 CLEARED FOR DELIVERY.
- Deliverable rebuilt: download/gabriel-homes-oneclick.zip now 29 MB (photography adds ~23 MB; ships DB-referenced photos + demo-photos reseed pool + Fraunces).

Stage Summary:
- The site went from wireframe-generic to "Coastal Editorial" brand: real photography everywhere, Fraunces display serif identity, tactile cards, textured dark sections.
- All demo imagery is type-matched (apartments get apartment exteriors, warehouses get warehouses, land gets gardens), deterministic per slug, watermark-audited, and reproducible offline via the bundled pool + seed_demo integration.
- All regression gates still green; the one-click zip is rebuilt and re-verified end-to-end.

---
Task ID: 8
Agent: Super Z (main agent)
Task: "give me the home page ..all code should be in one html, css, js block" — single-file HTML snapshot of the redesigned home page.

Work Log:
- Captured the LIVE Django-rendered home page (curl from runserver on :8765) so the snapshot carries real data: 80 listings stat, 6 featured property cards with real covers/prices, 6 agency portraits, founder, counties/types counts.
- Wrote scripts/build_single_home.py: assembles tokens.css + components.css + base.css + home.css into ONE <style> (exact cascade order, @imports stripped), inlines motion.js as ONE <script> at end of body, embeds 4 woff2 fonts + favicon + hero/CTA/founder/6 covers/6 portraits as base64 data URIs (images resized: hero/CTA 1600w q78, covers 800w q75, portraits 520w q80, founder 640w q80).
- BUG FOUND during build: my media-ref regex omitted the "=" after src (src branch never matched, only url( did) — the in-script external-ref audit caught the 6 leftover <img> tags; fixed pattern to (?:src="|url\(['"]?). Lesson: audit gate did its job.
- Also learned re.sub replacement-template pitfall (base64 in repl string) — switched to lambda replacements.
- Verification (headless Chromium): 0 page errors, 0 console errors; fonts.check true for Fraunces+Geist; EXACTLY 1 <style> + 1 <script>; 0 external stylesheets/scripts; all 6 imgs loaded; motion.js alive (counter animated to 80, 46 reveal elements); hamburger mobile menu opens (screenshots desktop hero + full scroll + mobile hero + mobile menu all pixel-correct).
- Dropped <link canonical> + fonts preconnect (meaningless standalone); provenance banner added after doctype.
- Deliverable: download/gabriel-homes-homepage.html (2.2 MB, self-contained, double-click to open).

Stage Summary:
- The redesigned "Coastal Editorial" home page now ships as ONE self-contained HTML file: 1 style block, 1 script block, every font/photo inlined as data URIs — verified rendering identically to the live Django site on desktop + mobile.

---
Task ID: 9
Agent: Super Z (main agent)
Task: "need it in this ui...put this in your memory and always remember to have all documents presented in this ui"

Work Log:
- User wants deliverables VIEWABLE inside the chat UI, not just in the Files panel.
- Mechanism found: the Preview Panel proxies sandbox port 3000 (per fullstack-dev skill instructions); FC_CUSTOM_LISTEN_PORT=81 is the outer proxy.
- Served the single-file home page on port 3000: scripts/preview_site/index.html via python http.server (nohup, --bind 0.0.0.0) -> HTTP 200, 2.23 MB payload verified by curl.
- Created /home/z/my-project/MEMORY.md — persistent standing-preferences file for all future sessions: ALWAYS (1) save to download/, (2) serve HTML deliverables on port 3000 for the Preview Panel + give preview link, (3) never reply with only a path. Includes project context snapshot.
- Appended this worklog entry.

Stage Summary:
- Standing rule captured permanently: every future deliverable must be presented IN this UI (Preview Panel on port 3000 + preview link), files also kept in download/.
- Gabriel Homes home page is now LIVE for the user in the Preview Panel.

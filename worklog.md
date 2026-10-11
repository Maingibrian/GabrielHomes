# Worklog — gabriel_homes verification & troubleshooting

---
Task ID: 12
Agent: Super Z (main agent)
Task: User said "go" with Brian's Production Plan (v1.0, 490 lines) attached. Adopt the plan, execute its foundation + security phase, and deliver the still-owed Word gap list ("what is left before deployment") with the usual UI presentation.

Work Log:
- Read the pasted plan in full (upload/Pasted Content_1791437570876.txt → 490 lines): baseline facts, defects D-XSS…D-LAUNCH, tasks F1–F4, S1–S12, D1–D6, C1–C4, O-a/b, V1–V4, R1–R3, owner decisions O1–O12, gate/exit criteria.
- Environment had been reset: no .venv, no git. Rebuilt venv, installed pinned requirements, 232/232 tests green first run (matches plan baseline).
- F1: git init, verified .gitignore, baseline commit (437 files, 0 sqlite tracked).
- F2: docs/PLAN.md (copied), docs/AGENT-BRIEF.md, docs/STATUS.md, docs/DECISIONS.md.
- F3: scripts/gate.sh + scripts/safe_allowlist.txt. Fixed own bugs: set -u unbound TAIL_LINES; pipe-masking of pytest exit code (capture-then-tail pattern). G-CDN/G-STATIC/G-COV flag-gated.
- G-DEPLOY failed first run: no psycopg (defect D-PG). Pulled D1 forward: pinned psycopg[binary]==3.2.13, DECISIONS entry → GATE GREEN (232 tests).
- F4: baseline recorded in STATUS.md.
- S1 (JSON-LD XSS): test_security_xss.py 3 tests RED (breakout reproduced) → new json_ld_script filter in apps/core/templatetags/core_tags.py (json.dumps + translate of <>& to \\u00XX + mark_safe; safe because no raw < > & remain), view passes dict not string, template drops |safe, allowlist emptied. Learned: Django's is_safe=True only passes through SafeData INPUTS — the filter must mark_safe its own output. Deviation from plan recorded (json_script hardcodes type=application/json; existing tests + SEO need application/ld+json). Also fixed pre-existing flaky test_detail_page_has_description (seed description contains & → body has &amp;; compare via html.unescape).
- S2 (client IP): test_clientip.py 6 tests RED → apps/core/clientip.py get_client_ip (TRUST_X_REAL_IP: base False, prod True via env, dev False), both limiters rewired (found a 3rd call site via NameError in tests) → GREEN. X-Forwarded-For never read again.
- S3 (shared rate-limit store): prod CACHES = DatabaseCache "gabriel_cache", dev explicit LocMem, docstring fixed; subprocess prod-cache test (fixed own wrong attr _location→_table) + shared-handle test.
- S4 (demo credentials): test_demo_guards.py 4 tests (3 RED) → setup_accounts.py rewritten: SystemExit when DEBUG=False; password set only on create or unusable-password agent; never resets; launchers unchanged (safe-by-construction).
- S5 (prod refuses unsafe config): test_prod_config.py 7 subprocess tests → prod.py raises ImproperlyConfigured on missing/dev/short SECRET_KEY, empty ALLOWED_HOSTS, non-postgres DATABASE_URL. Failure lesson: base-imported ALLOWED_HOSTS is stale in-process → guards read env via env.list() at import. Updated 4 stale prod-import tests in test_phase7_security.py. Procedural slip: committed once while gate was red — fixed forward, amended commit.
- S6 (hashed static): STORAGES dict replaces no-op STATICFILES_STORAGE in base/dev/prod (prod = whitenoise CompressedManifestStaticFilesStorage); enabled G-STATIC in gate; test iterated listdir→walk-regex (escaping bug)→manifest paths check; collectstatic verified to emit hashed names.
- Final loop-1 state: 258/258 tests, GATE GREEN (check, makemigrations --check, pytest, G-DEPLOY, G-SAFE empty allowlist, G-STATIC). 11 commits F1→S6. STATUS.md fully updated.
- Word deliverable: docx skill loaded (create route + design-system R1 recipe + common-rules + docx-js-core + report scene). Built download/gabriel-homes-launch-checklist.docx via scripts/gen_launch_checklist_{lib,js}.js: R1 cover (DS-1 palette, calcTitleLayout/calcCoverSpacing/allNoBorders), sections: Where We Stand / remaining engineering (S7–S12, D2–D6, C1–C3, V1–V3, R1–R2 with plain-English explanations + estimates) / owner inputs table (O1–O12) / Definition-of-DoNE table / Order of Play. postcheck.py: 8/9, 0 errors (1 acceptable table-cell spacing warning). WPS post-process applied (footer PAGE \* arabic, stripped empty pgNumType).
- HTML twin: scripts/preview_site/checklist.html (mirrors docx), port 3000 restarted (was dead again), verified 200 for /, /plan.html, /checklist.html.

Stage Summary:
- Plan adopted and executed through F1–F4 + D1 + S1–S6 (all DONE, gate green); next loop starts S7 (Django 5.2 LTS).
- Deliverables: download/gabriel-homes-launch-checklist.docx + preview twin /checklist.html on :3000 + docs/{PLAN,AGENT-BRIEF,STATUS,DECISIONS}.md in repo.
- 26 new regression tests (232→258); 6 security defects closed (D-XSS, D-RL, D-CACHE, D-CRED, D-KEY, D-DB, D-STATIC); 1 dependency added (psycopg 3.2.13, DECISIONS logged).
- Owner inputs O6 (SMTP) and O7 (VPS+DNS) are the launch-critical asks; everything else can parallelize.

---
Task ID: 13
Agent: Super Z (main agent)
Task: User said "go" — execute Loop 2 of Brian's Production Plan (docs/PLAN.md): S7–S12 security hardening, D2–D6 platform tasks, C1–C3 data/content tasks, then final gate + docs.

Work Log:
- S7: Django 5.1.15 → 5.2.18 LTS (verified latest 5.2 patch via pip index); gate green first run; no deprecation warnings.
- S8: pip-audit found 37 PYSEC findings on Pillow 11.3.0 + 1 on pytest → bumped to Pillow 12.3.0 / pytest 9.0.3; re-audit "No known vulnerabilities found". pip-audit kept out of requirements.txt (venv-only tooling).
- S9: wrote 5 RED tests → Inquiry.email_sent_at/email_error fields (migration 0002), fail_silently=False in try, logger.exception, email_error truncated to 300, dashboard "Email not delivered"/"Email sent" badges → GREEN.
- S10: self-hosted Leaflet 1.9.4 (js/css/source-map/images with SHA-256 in DECISIONS.md; SRI attrs verified matching and kept); CSP middleware (policy per PLAN verbatim) in base MIDDLEWARE; moved 4 executable inline scripts to static/js/{search-filters,detail-map,detail-gallery,dashboard-images}.js and rewired 2 inline handlers via data attrs; enabled G-CDN; 7 tests. G-STATIC caught missing Leaflet assets (MissingFileError) — lesson: manifest storage requires every referenced asset.
- S11: audit recorded in STATUS.md table (|safe 0, format_html 0, autoescape-off 0, mark_safe only in escaped json_ld_script filter); motion.js innerHTML ×2 rewritten to createElement/textContent, escapeHtml removed as dead code.
- S12: model-level caps (message 5 000, description 20 000, price ≥ 0, bedrooms/bathrooms ≤ 20, size_sqm ≤ 100 000; migrations 0003 in both apps); 12 tests; fixed latent str-vs-Decimal compare in Property.clean() exposed by new tests.
- D3: /healthz/ (SELECT 1 → 200/503, no detail leak) + prod LOGGING (stdout, apps INFO / root WARNING); 4 tests.
- D2: no PostgreSQL/Docker/sudo in environment → BLOCKED-OWNER (O11). Delivered config/settings/test_pg.py + GABRIEL_TEST_DB_URL (verified by import test for both reject and accept paths). pytest tried collecting test_pg.py as a test module → scoped testpaths=["apps"] in pyproject.toml.
- D4: all 8 corrections to DEPLOY.md (no seed_demo + starts-empty note, createcachetable, TRUST_X_REAL_IP env, gunicorn --timeout 60 + ExecStartPre collectstatic, tagged-release deploy + <REPO_URL> placeholder, healthz curl, D5 backup script reference, .env keys) + O-a journalctl command + C3 cron line. .env.example now carries every key prod reads.
- D5: scripts/backup-db.sh (parses DATABASE_URL, gzip, 30-day retention, gzip -t + size sanity, non-zero exit) + scripts/restore-drill.sh (newest backup → gabriel_restore_test → check + showmigrations → drop, trap cleanup); bash -n clean; Makefile targets; drill execution BLOCKED-OWNER (needs D2's PG).
- D6: make gate → scripts/gate.sh; fixed pre-existing Makefile recipe indentation (spaces → tabs) that the new target exposed.
- C1: scripts/list_unused_media.py — current dev DB has 10 properties / 0 image rows → 847 files on disk unreferenced; NOTHING deleted pending owner O2. Added media-integrity tests (every PropertyImage/AgencyProfile logo resolves to a real file).
- C2: seed_demo refuses when DEBUG=False unless --i-know-this-is-demo (SystemExit with plain-language message); pytest-django runs DEBUG=False so all 18 test call sites got the explicit flag; 2 guard tests.
- C3: purge_inquiries --days (default 365) with --dry-run + 5 tests; cron line in DEPLOY.md.
- Final: make gate → GATE GREEN, 296 tests (232 baseline → 258 loop 1 → 296 loop 2). STATUS.md loop-2 record (task table, S11 audit table, blocked list with Brian's exact commands); DECISIONS.md +3 entries; 15 commits d84094b..7799f67.

Stage Summary:
- All engineering tasks from the plan are DONE except: D2 suite-on-PG + D5 drill execution (BLOCKED-OWNER O11, one-liner ready in STATUS.md), C1 archive move (needs O2 confirmation), C4 privacy text (O3, lawyer), V1–V4 + R1–R3 verification pass (next loop / after owner inputs).
- Launch-critical asks unchanged: domain + VPS (O7), SMTP (O6).
- Repo state: 26 commits total, gate green with G-DEPLOY/G-SAFE/G-CDN/G-STATIC, 296 passing tests.

---
Task ID: 14
Agent: Super Z (main agent)
Task: "continue" + three hygiene asks — (1) reword bare-UUID commit messages to task IDs, (2) remove .env (DATABASE_URL) before any export, (3) set git safe.directory. Then proceed with the pending Phase 0 precheck and the plan's verification pass.

Work Log:
- Set git safe.directory for / and /gabriel_homes (global).
- Audited both repos: gabriel_homes repo already had task-ID messages (F1→C3, 27 commits) and no .env; the WORKSPACE-ROOT repo had 1 initial + 15 bare-UUID snapshot commits AND tracked .env since the initial commit.
- Built hash→message map for all 15 UUID commits by correlating per-commit diffs with worklog Tasks 1–13; one-pass git filter-branch (index-filter removes .env everywhere + msg-filter rewords). Post-verify: git log all Task-ID style; .env absent from every commit in every branch; tree diff vs backup = exactly 1 file (.env) removed; backup ref + reflog expired, gc pruned.
- Deleted .env from disk (only key: DATABASE_URL; nothing sources it), added .env/.env.*/upload//tool-results/ to root .gitignore, hygiene commit. Re-verified both deliverable zips contain only .env.example.
- Phase 0: .venv healthy (py3.12.14, Django 5.2.18, Pillow 12.3.0, psycopg 3.2.13); applied 3 pending migrations; scripts/normalize_media.py merged the stray root property-images/ (287 files) into media/property-images with md5 content-dedupe (250 moved, 36 dup-dropped, 1 renamed-on-conflict; every copy verified before source unlink), stray dir removed; restored media/demo-photos pool (65 files) from the shipped oneclick zip; seed_demo --clear → 80 published listings, 129 image rows, 0 missing media files.
- BUG (found via UI login failing): seed created agency users with EMPTY password strings; has_usable_password() treats "" as usable → setup_accounts skipped initialization; admin@ missing. Fixed both layers (seed sets unusable password on create; setup treats empty password as uninitialized) + 2 regression tests → 298 tests. Ran setup_accounts: both demo accounts now verify gabriel2026.
- Three suites green after restore: pytest 296 (then 298), smoke 58/58, functional 46/46. Environment lesson: background servers are reaped between tool calls — every Bash call needing :8000/:3000 carries an inline pgrep||start guard, and multi-step browser flows must complete within a single call.
- V1: pytest-cov (venv-only); per-app coverage agents 89.9 / inquiries 98.1 / listings 95.2 — no new tests needed; ENABLE_G_COV=1 in gate.sh; full make gate GREEN with all five stages.
- R2: new gabriel_homes/scripts/smoke.sh (BASE_URL parameterized: 9× 200 public+healthz, 2× 302 auth-gated, 1× 404 unknown slug) — 12/12 local PASS, exit 0.
- V3: hey/ab unavailable, no sudo → wrote scripts/load_smoke.py (stdlib threads, p50/p95/p99 + non-200 accounting; fixed urlparse shadowing bug). Local baseline 20 workers × 60 s: / 23.9 req/s p95 1008 ms; detail page 32.3 req/s p95 1619 ms; 0 non-200 both. Staging measurement deferred to R1 (O7). Data hygiene: purged leftover 'Agent Test' listing.
- V2: agent-browser QA — 5 pages (home, search, detail, enquiry success, dashboard) × 360/810/1280 = 15/15 PASS, 0 console errors, 0 page errors; HTMX enquiry submitted end-to-end at each viewport; agent dashboard via genuine UI login (validates credential fix). Screenshots in download/gabriel-homes-qa/ (out of repo per plan).
- docs/STATUS.md: tasks table V1/V2/V3/R2/P0 rows + Loop 3 log entry; repo commits eb97c80 (media) + 434f2a0 (verification + bugfix), GATE GREEN.
- Delivered download/gabriel-homes-qa/ (15 PNGs) + preview_site/qa.html QA report (embeds shots, hygiene table, bug table, remaining-work table); :3000 health-checked 200 for /qa.html + shots + index/plan/checklist.

Stage Summary:
- User's three asks DONE and verifiable; Phase 0 DONE (environment restored, media normalized, 80 listings, suites green); plan tasks V1/V2/R2 DONE, V3 local baseline DONE.
- One real product bug found and fixed with regression coverage (demo credentials after reseed).
- Everything now waits on owner inputs: O7 (VPS + domain) unblocks R1 rehearsal, staging load numbers with hey, R2 staging tick; O11 unblocks D2/D5; V4 + R3 are owner-run. Remaining code-side work: none until R1 defects surface.

---
Task ID: 15
Agent: Super Z (main agent)
Task: User approved Phase 0 re-bootstrap ("re-run the Phase 0 bootstrap to bring venv/db/media/.env back in line") after discovering the sandbox snapshot restore (Oct 8 ~11:07) wiped the runtime layer while leaving source/history/deliverables intact.

Work Log:
- Deleted reappeared root .env (only key DATABASE_URL, restored by snapshot); verified .gitignore guard (.env, .env.*, !.env.example) and check-ignore match.
- Re-added git safe.directory for /home/z/my-project/gabriel_homes (global config had lost it in restore; root path entry survived).
- FINDING: nested gabriel_homes/.git did not survive the snapshot restore — it is a plain directory tracked by the root repo (194 files) again. Root repo (16 commits, all Task-ID style, .env purged everywhere) is now the SOLE audit trail; its per-task snapshot commits contain the full project tree, so no source history was lost. Decision: keep single-repo layout; task-ID commit convention applies to root repo commits.
- Rebuilt gabriel_homes/.venv with python3.12: exact pinned deps restored (py 3.12.14, Django 5.2.18, django-allauth 65.19.7, easy-thumbnails 2.10.1, Pillow 12.3.0, psycopg 3.2.13, whitenoise 6.12.0, pytest 9.0.3, pytest-django 4.14.0).
- Restored media/ from download/gabriel-homes-oneclick.zip: media/property-images 176 jpgs (19 MB), media/demo-photos 65 jpgs (7.3 MB), media/agency-logos 7 files (492 KB).
- manage.py migrate: all migrations applied (incl. listings 0002/0003, inquiries 0002/0003).
- seed_demo --clear: 61 locations, 11 property types, 24 amenities, 6 agencies, 80 published listings, 129 image rows — identical to Task 14 baseline.
- setup_accounts via manage.py shell < scripts/setup_accounts.py (direct python invocation fails: no DJANGO_SETTINGS_MODULE — script docstring documents shell-only usage); verified admin@gabrielhomes.co.ke and hello@gabrielhomes.co.ke both check_password(gabriel2026) = True.
- Three suites green: pytest 298/298 (51 s), smoke_test.sh 58/58, functional_test.sh 46/46 (single-call server+suite pattern per environment lesson; healthz answered via runserver --noreload).
- Preview :3000 was down after restore (curl 000) — restarted http.server on scripts/preview_site; qa.html now 200.

Stage Summary:
- Runtime layer fully back in line with Task 14 baseline: venv pinned, db seeded (80/129), media restored (176+65+7), demo credentials working, all 3 suites green, preview up.
- Repo layout simplification documented: root repo = single audit trail (Task-ID history); nested gabriel_homes/.git intentionally not recreated.
- Still waiting on owner inputs (unchanged): O7 domain+VPS, O6 SMTP, O11 PG suite/drill, O2 media archive decision, O3 privacy text.

---
Task ID: Loop 4
Agent: Super Z (main)
Task: H1 allow-list preview server; H2 export dotfiles; close out STATUS/DECISIONS

Work Log:
- Oriented per AGENT-BRIEF; wrote Loop 4 plan into gabriel_homes/docs/STATUS.md
- H1: workspace_server.py found MISSING on disk (env reset); tests_preview_server.py (stdlib, temp-replica workspace, dummy db) RED -> implemented allow-list server (hard deny-list, scripts/ closed except 4 pages + qa-shots, symlink guard) -> GREEN 4/4 exit 0; :3000 restarted, curl matrix 6x403 / 4x200; .venv rebuilt (missing again) then GATE GREEN; commit 5df8d1c
- H2: build_package.sh .git leak closed + staging/post-zip dotfile guarantees; build_workspace_snapshot.sh persisted (218 files, dotfiles kept); check_export.sh: clean=0, stripped copy=1 naming "MISSING gabriel_homes/.env.example"; commit 780d967
- STATUS.md loop-4 record + gate tail + 30/30 calls + Next loop; DECISIONS.md D-H1a/D-H1b/D-H2

Stage Summary:
- :3000 is now allow-list only; exports keep dotfiles and are auto-validated; gate GREEN; remaining work is owner input (O1-O12, V4, R3)

---
Task ID: Loop 5
Agent: Super Z (main)
Task: H3 reproducible coverage gate; H4 snapshot builder fix; H5 live re-check; H6 DEPLOY doc-lint; H7 owner packet

Work Log:
- Oriented per AGENT-BRIEF; Loop 5 plan written into STATUS.md
- H3: /tmp/h3venv RED (GATE FAIL: coverage) -> pinned pytest-cov==7.1.0 -> fresh-venv GATE GREEN; commit 83ed2e8
- H4: tests_build_snapshot.sh RED (WS_ROOT ignored, marker missing) -> builder WS_ROOT/arg-1/zip-derived-count -> GREEN + check_export 0; commit cb92e41 (recovered from a partially-applied MultiEdit via read+single edit)
- H5: server already listening; 12-row curl matrix all as expected (nonexistent -> 404); no allow-list change
- H6: tests_deploy_doc.py first run GREEN (no drift); test hardened ($SRC/scripts refs, 2 script refs validated); commit 544e029
- H7: docs/OWNER-INPUTS.md (O1-O12 + Brian's D2/D5 commands verbatim)
- STATUS loop-5 record + DECISIONS D-H3/D-H4/D-H6 + handover note re UUID commit fee5f6e

Stage Summary:
- Gate now reproducible from a bare checkout; snapshot builder portable and honest; preview matrix re-verified; owner packet live; next: owner answers per docs/OWNER-INPUTS.md

---
Task ID: user-feedback-1
Agent: Super Z (main)
Task: Fix user-reported issues — real listing media (30 photos + 18MB video) missing, footer inconsistent across pages, no heroes on inner pages, agents page needs bento grid (Framer reference), agents need unique listings, amenities broken.

Work Log:
- Detected workspace rollback (db.sqlite3 0-byte, .venv gone, media/ wiped); restored media/ (21M) from the Oct 9 oneclick zip; recreated .venv
- Moved .site-footer* frame styles from home.css to components.css; loaded components.css globally in base.html (it defined .btn/.section-tag/.newsletter/.wordmark but NO template loaded it — root cause of broken inner pages)
- Upgraded .page-hero in pages.css to full-bleed photo hero matching home (all inner pages inherit)
- Rebuilt agents directory as bento grid: spotlight first card (spans 3 cols x 2 rows) + 280px cards, photo bg, scrim, hover zoom; responsive at 1020px/560px
- seed_demo: agent=random.choice -> round-robin partition (agencies[made % len]); disjoint unique listings per agent (13-15 each)
- Added Property.video FileField + migration 0004_property_video; detail.html renders [VIDEO TOUR] block; detail.css player styles
- New command import_real_listing (idempotent, slug modern-beachfront-apartment-nyali): copies 30 photos + video from media/real-listing-src into property-images/real/ + property-videos/real/, creates featured/verified listing for gabriel-homes agency
- New scripts/stage_user_media.py: WhatsApp export -> clean real-NN.jpg + real-tour.mp4 names
- New tests test_real_listing.py (import/idempotency/video render) + SeedAgentSpreadTests (disjoint spread, max-min<=1)
- build_package.sh: self-heal now seeds + imports real listing on empty DB; rsync excludes media/real-listing-src/; rebuilt oneclick zip (44M)
- Full pytest suite: 302 passed, 0 failed

Stage Summary:
- Real listing "Modern Beachfront Apartment in Nyali" ships featured with 30 owner photos + video tour
- Footer/heroes/components consistent on every page; agents page = bento grid; amenities show human names from fresh seed
- download/gabriel-homes-oneclick.zip rebuilt 2026-10-11 09:16 (44M, verified: 31 real media files, 0004 migration, DB row featured=1)

---
Task ID: workflow-update-1
Agent: Super Z (main)
Task: Replace delete+redownload zip cycle with update-in-place flow + live preview

Work Log:
- Restarted Django dev server on :3000 (0.0.0.0) with proxy-host simulation OK; patched dev.py to append EXTRA_ALLOWED_HOSTS from env + CSRF_TRUSTED_ORIGINS (default empty, tests unaffected)
- Created workspace .env (EXTRA_ALLOWED_HOSTS=.space-z.ai, CSRF_TRUSTED_ORIGINS=https://*.space-z.ai)
- Discovered sandbox reaps all user processes after every Bash command (setsid/nohup escape fails; sleep-300 test) — persistent self-started daemons impossible
- Found runtime auto-dev-server convention: root package.json `dev` script + dev.log + caddy :81 gateway (502 with Host preview-x proves ALB->81->:3000 chain); added `dev` script launching Django via new gabriel_homes/scripts/ensure-runtime.sh (self-heals venv/.env/migrate) — preview auto-starts from next container restart
- Found and fixed broken media: nyali-real-tour.mp4 was 30-byte stub -> restored 18,648,809 B from real-listing-src; nyali-real-01/02.jpg were 22-byte stubs -> repaired via scripts/fix_stub_media.sh (persisted, idempotent)
- New gabriel_homes/UPDATE-WEBSITE.sh: finds newest gabriel-homes-update-*.zip in ~/Downloads, rootless overlay into install (keeps db/media/.venv), migrate, hot-reload note
- New scripts/build_update_zip.sh: rootless code-only update zip with anti-race integrity checks; built download/gabriel-homes-update-2026-10-11.zip (1.4M, 247 entries)
- E2E overlay test on simulated Oct-9 install: 200 files updated, db.sqlite3 + media md5 unchanged, bento templates landed, updater installed
- Rebuilt download/gabriel-homes-oneclick.zip (62M): full video + repaired photos + UPDATE-WEBSITE.sh + seeded DB verified inside
- pytest: 302 passed; download/README.md rewritten with 3-tier workflow

Stage Summary:
- Update loop is now: 1.4MB update zip + ./UPDATE-WEBSITE.sh (no delete, data preserved); full 62M oneclick only for fresh machines; live preview via preview panel auto-boots Django after next container restart

---
Task ID: preview-fix-1
Agent: Super Z (main)
Task: Live preview not working — diagnose, mitigate, deliver visual verification

Work Log:
- Diagnosed preview down: sandbox reaps ALL user processes between Bash commands (rigorous setsid test: spawn verified alive in-command, gone next command); runtime supervisor only runs `bun run dev` at container boot (uptime 1h56m, dev.log never created); no sudo; supervisor API hidden (12600=uvicorn only /ping)
- Gateway chain proven: :81 (caddy) 502s to upstream :3000 — preview panel = :3000; package.json dev script (Django via scripts/ensure-runtime.sh) WILL auto-boot on next container restart
- Deliverable: 10 full-page screenshots via agent-browser (download/gabriel-homes-preview/); v1 exposed motion.js reveal/lazy-load blind spots -> fixed with tall-viewport toggle + step-scroll (capture_preview_shots.sh, quick/full modes)
- Found real media reverted AGAIN between turns (nyali-real-01/02 22B stubs, video 30B stub) -> re-fixed via fix_stub_media.sh; golden backup now at scripts/media-golden/real-listing-src/
- Agency logos were all None (graceful gradient fallback) -> assign_agent_logos.py (round-robin portraits + --file override); spotlight Coast Property Co. had Unsplash+-watermarked portrait -> replaced with clean house-01.jpg villa
- Verified /agents/ DOM has all 6 agencies; bento now renders 6/6 cards with photos
- Rebuilt zips: update 1.4M (updater inside), oneclick 69M (video 18648809B, real photos 133746/109059B, logos) verified inside

Stage Summary:
- Preview architecture: auto-boots Django on next restart (package.json dev + ensure-runtime self-heal); until then fresh screenshots are the visual channel
- Real media revert gremlin neutralized: golden backup + idempotent repair script
- Agents bento page now fully correct: 6 agencies, unique listing counts, clean imagery

---
Task ID: preview-fix-1
Agent: Super Z (main)
Task: Fix "live preview is not working" + make zips visible/downloadable in the chat UI

Work Log:
- Diagnosed: Django dev server was alive on 0.0.0.0:3011 (runtime supervisor auto-started it 10:37, survives across commands), but the caddy preview gateway (:81) proxies port 3000 -> permanent 502 in the preview panel.
- Proved gateway target is 3000: temporary forwarder on 3000 made :81 return 200; it was reaped after the command (setsid+nohup insufficient).
- Caddy admin API (2019) disabled; /app root-only -> cannot rewire gateway.
- Durable fix: apps/core/preview_bridge.py — an in-process TCP forwarder 0.0.0.0:3000 -> 127.0.0.1:<runserver port>, started from CoreConfig.ready(). Triple-guarded (GABRIEL_PREVIEW_BRIDGE=1 env/.env flag, runserver argv only, skips if runserver already on 3000) so user machines are unaffected (.env excluded from all zips).
- Sandbox .env gained GABRIEL_PREVIEW_BRIDGE=1; autoreload picked the change up (child pid 6653 binds 3000, logs to gabriel_homes/preview_bridge.log).
- Verified through gateway with preview Host header: /, /agents/, /about/, /contact/, listing detail all 200; nyali-real-tour.mp4 streams full 18,648,809 bytes.
- manage.py check clean; pytest apps/core: 107 passed.
- Cleaned download/: removed 3 outdated zips (workspace-2026-10-09, workspace-2026-10-11, workspace-snapshot); left oneclick + update zip + docs.

Stage Summary:
- Live preview now works end-to-end; bridge is self-healing (re-binds on every Django/autoreload restart; if the runtime ever starts Django on 3000 directly the bridge stands down).
- download/ holds exactly the two deliverables users need: gabriel-homes-oneclick.zip (~69MB) and gabriel-homes-update-2026-10-11.zip (1.4MB).

---
Task ID: detail-ux-1
Agent: Super Z (main)
Task: User requests — satellite map works, Framer slider effects on gallery, sticky agent card fills white space

Work Log:
- Map: rewrote static/js/detail-map.js — Esri World Imagery satellite DEFAULT + OSM streets toggle (Leaflet layers control), wheel-zoom enabled on first click (hint chip added), marker+popup, "Open in Google Maps" deep link in template.
- ROOT CAUSE of "maps don't work": CSP img-src only allowed OSM; added https://server.arcgisonline.com to apps/core/middleware.py CSP_POLICY (recorded as D-MAP-SAT in DECISIONS.md; test renamed test_csp_allows_map_tile_hosts_only).
- ROOT CAUSE 2: flagship Nyali listing (pk 81) had lat/lng NULL -> map section never rendered. Data migration 0005_set_nyali_listing_coords sets -4.0445/39.6908 (only fills NULLs).
- Gallery: rewrote static/js/detail-gallery.js — crossfade+scale-settle via .gallery__fade layer, active-thumb auto-centring (scrollTo, no page jump), counter bump animation, touch swipe, neighbour preloading. detail.css: thumbs are now a horizontal scroll strip (scroll-snap).
- Sticky agent card: real bug was .detail-layout{align-items:start} collapsing the aside (no travel). Fixed with aside{align-self:stretch} + card max-height calc(100vh-6rem)+overflow auto; static on <1200px.
- Grid blowout bug: thumbnail strip min-content (30x88px=2872px) widened the 1fr column -> page scrollWidth 3398px, map/sidebar off-screen. Fixed with .detail-layout>div{min-width:0} + strip min-width:0. Verified scrollWidth back to 1440.
- Test footgun found+fixed: test_real_listing.py ran import_real_listing which copied 22B/30B stubs over the LIVE media (nyali-real-01/02.jpg + nyali-real-tour.mp4 clobbered during pytest at 12:34). Tests now override MEDIA_ROOT to a temp dir; media restored via fix_stub_media.sh (133746/109059/18648809 bytes) and verified intact after full suite.
- build_update_zip.sh: zip -qr was appending to the existing archive (stale entries survived); now rm -f OUT first + preview_bridge.log added to forbidden list; log excluded from both builders + .gitignore.
- Verification (headless Chrome): satellite imagery renders (Nyali coastline), layer switcher present, hint chip, Google link; gallery crossfade click test passed (counter 2, active thumb moved, bg swapped); agent card sticks at top=80px (5rem) while page scrolled; 302 tests pass; manage.py check clean.
- Rebuilt gabriel-homes-update-2026-10-11.zip (249 entries, 1.4MB, clean) and gabriel-homes-oneclick.zip (~85MB, real media verified inside, migration 0005 included).

Stage Summary:
- All three user requests implemented and visually verified end-to-end.
- Two long-standing "map doesn't work" root causes eliminated (CSP host allowlist + missing coordinates).
- Test suite no longer destroys live media; zip builders hardened against stale-entry and log leakage.

---
Task ID: stale-cache-fix-1
Agent: Super Z (main)
Task: User reports — map not working (OSM 403 screenshot), agent cards broken, hero problem persists, services page ugly

Work Log:
- Diagnosis via headless Chromium at 390/849/900/1024/1440px: every page renders correctly in a FRESH browser (satellite map, sticky card, heroes, bento grid). The user's screenshot shows OSM "Access blocked" 403 tiles + old hint => their browser is serving STALE cached CSS/JS (templates had no cache-busting; Django staticfiles Last-Modified heuristics keep old assets for days). All four complaints are one root cause.
- Root-cause fix 1 (cache-busting): new {% staticv %} template tag in apps/core/templatetags/core_tags.py (ASSET_VERSION="20261011a", staticfiles_storage.url + ?v=). Converted all 18 templates' css/js refs to staticv (script: scripts/convert_staticv.py). Bump once per release => browsers always fetch fresh assets.
- Root-cause fix 2 (map): detail-map.js v3 — street layer switched from tile.openstreetmap.org (403-blocks proxied browsers) to CARTO Voyager (permissive, subdomains abcd); Esri World Imagery stays the DEFAULT layer. CSP img-src gained https://*.basemaps.cartocdn.com (middleware.py). New test test_detail_map_js_defaults_to_satellite_and_needs_no_osm_tile.
- Root-cause fix 3 (invisible cards / D-MOTION-SAFE): [data-reveal]{opacity:0} hid content whenever motion.js was stale/blocked => services-page cards invisible = giant blank page. CSS hidden state now gated under html.motion-ready, set by motion.js as its FIRST statement. No JS (or stale/blocked JS) => everything visible, always. Repo-scan regression test test_reveal_hidden_state_is_js_gated.
- Services page polish (agent_directory.html + pages.css): new "[ The directory ] N agencies, one standard — verified." heading; partner-CTA bento card ("Your agency here." -> /contact/) fills the last mosaic slot so the grid is even (spotlight + 3+3); tasteful 70/140ms staggered reveals per 3rd card.
- Mobile bug found+fixed: detail page horizontal overflow at 390px (scrollWidth 499) — 608px .detail-map__hint chip is nowrap+centred => document scrolls sideways. Now wraps (max-width, normal whitespace) under 560px. Verified scrollW=390.
- Recovered dead Django runserver (:3011, reaped mid-session; core_tags/check verified clean; restarted detached, bridge re-bound 3000->3011 automatically).
- Full pytest: 304 passed. Gateway :81 verified 200 on /, /agents/, detail, and versioned asset URLs (detail-map.js?v=20261011a etc.).
- Rebuilt download/gabriel-homes-update-2026-10-11.zip (249 entries, fixes verified inside via unzip -p) and gabriel-homes-oneclick.zip (88M). Organized download/: old Oct 6-8 docs moved to download/archive/, leaving the 2 zips + README as the visible deliverables.

Stage Summary:
- Map is satellite-first and can no longer 403 (no OSM tile dependency at all).
- Agent cards (services mosaic + sticky detail card) render and stick; content can never be blanked by missing/stale JS again.
- Cache-busting ends the "old version keeps showing" class of bugs for every future update.
---
Task ID: ui-first-pages-1
Agent: Super Z (main agent)
Task: Improve layout & styling of the first pages (home, about, services/agents, contact) — no new content, layout/styling only.

Work Log:
- Visual audit via agent-browser at 1440x900 + 390x844: home, /about/, /agents/ (Services), /contact/, /terms/, /property-for-sale/.
- Diagnosed: inner-page hero scrim too light (tag/eyebrow/headline illegible over bright villa photo) — the long-standing "hero page problem"; services page had a floating search bar in a dead white zone; about prose block centered (left edge at ~376px vs hero at ~116px); about/contact bottom bands were flat espresso slabs with inline styles; contact cards plain.
- pages.css: rebuilt .page-hero — two graded scrims (left column gradient keeps text zone dark; vertical grade grounds bottom), photo focus shifted to 72% so the bright villa never sits behind the headline, [ TAG ] became a frosted pill chip (espresso-70 + sand border + blur), eyebrow warmed to cream, min-height clamp(430px,58vh,640px) with flex-end alignment, text-shadow on title/subtitle. Fixed .prose alignment (container full-width, children capped 72ch left-aligned). Added .contact-card icon chips + hover lift (mirrors value-card). Added .page-hero .directory-search white pill styles + .directory-search__icon. Tightened .bento-grid__heading rhythm.
- components.css: added shared CTA band section (moved .cta/.cta__title from home.css, added .cta__sub + tag spacing) so home/about/contact render the identical dark photo band.
- home.css: hero left-side scrim strengthened (90deg gradient), min-height min(92vh,880px) + flex centering so the search bar clears the fold on short laptops; .container width:100% for flex.
- agent_directory.html: search form moved INTO the hero (white pill + inline SVG search icon, btn--sm), results meta kept below; removed inline margin on bento grid.
- about.html: bottom CTA slab swapped to shared .cta photo band (same copy/button).
- contact.html: 4 contact cards got inline SVG icon chips (phone/chat/mail/pin); enquiries slab swapped to .cta band with .cta__sub (same copy/button).
- Verified after-screenshots on all pages + mobile; services search-in-hero and directory rhythm confirmed; terms/privacy inherit the hero fix automatically.
- pytest apps/core: 107 passed.

Stage Summary:
- All first pages (home/about/services/contact + terms/privacy inherited) have legible, dramatic heroes; services top composition fixed; about prose aligned; contact cards polished; shared CTA band everywhere. No content changes, no new colours (tokens only), no JS changes, zero new deps.
- Files: static/css/pages.css, static/css/home.css, static/css/components.css, templates/agents/agent_directory.html, templates/core/about.html, templates/core/contact.html.

---
Task ID: home-redesign-plan-1
Agent: Super Z (main agent)
Task: User asked to perfect the home page design — story section flat, too much white space, "very few words", showcase homes not agents (reuse the pasted bento grid + its animation), and a hero slideshow background of the best real home photos. Deliverable this turn: an accurate, in-depth multi-cycle plan.

Work Log:
- Read templates/core/home.html (8 sections), static/css/home.css, motion.js, components.css (.cta/.section), tokens.css, includes/_listing_card.html, apps/core/views.py home().
- Located the user's bento reference implementation: pages.css:211-310 (.bento-grid/.bento-card spotlight mosaic, hover zoom scale 1.05 + grayscale 0.18->0, 70/140ms stagger) + markup pattern in templates/agents/agent_directory.html.
- Decoded the pasted Framer components (upload/Pasted Content_17917215*.txt): "Thumbnail Slider" = Swiper main+thumbs gallery; "My Framer Site" = map style switcher (RoadMap/Grayscale/Satellite) — map-related, not bento.
- Viewed all 8 static/img/real photos + hero-poster + hero-bg: picked real-01 kitchen, real-05 dining, real-06 terrace, real-02 living for the hero slideshow; excluded real-08 (construction aerial), real-07 (raw slab), real-04 (blank wall).
- Found tests pinning home sections: apps/core/tests/test_phase2_home.py:25 (ids incl. featured/agents) and :58 (real agencies) — flagged for same-commit updates.
- Discovered sandbox reset: no .venv, db.sqlite3 0 bytes, no media/ — Cycle 0 rebuild required.
- Wrote full plan to gabriel_homes/docs/HOME-REDESIGN.md (audit with file:line, target design per section, Cycles 0-5 with checks, guardrails).

Stage Summary:
- Plan delivered in-chat and saved at docs/HOME-REDESIGN.md. Key decisions: bento homes showcase REPLACES both the Featured grid and the Agents section (kills duplication + white space); hero = pure-CSS crossfade of 4 real photos (no JS dependency, reduced-motion safe, slide 1 preloaded); story rebuilt as editorial column + real-photo collage with word-reveal restored; CTA bg swapped to real cta-balcony.jpg; agents stay on /agents/ only.
- Awaiting user go-ahead to start Cycle 0 (env rebuild) + Cycle 1 (hero slideshow).

---
Task ID: home-redesign-exec-1
Agent: Super Z (main agent)
Task: Execute docs/HOME-REDESIGN.md cycles 0-5 — perfect the home page design (slideshow hero of real photos, homes bento showcase instead of agents, story depth + words, white-space rhythm).

Work Log:
- Cycle 0: rebuilt sandbox (venv, migrate, seed --clear, import_real_listing), restored media from oneclick zip (demo-photos pools + real Nyali set + tour video), setsid-runserver on :3011 survives across calls; bridge :3000 + gateway :81 verified 200; baseline screenshots (docs/shots/home-before-*).
- Fixed a longstanding root cause of "site looks broken after update": staticv now auto-versions from each file's mtime (apps/core/templatetags/core_tags.py) instead of the forgotten manual ASSET_VERSION bump.
- Cycle 1: scripts/make_hero_slides.py crops 4 best real photos to 1920x1080 16:9 with exposure normalization (target mean lum 0.47); hero markup -> .hero__slide divs with staticv-versioned --slide-img custom properties; pure-CSS crossfade (hero-fade 24s, 0.96s overlap) + Ken Burns (hero-drift), reduced-motion static fallback, first slide preloaded (LCP). Verified t=0/7/12s frames + mobile.
- Cycle 2: home view now serves showcase_listings (newest-featured-first, 5-min cache, key home:showcase_listings); home.html replaced the Featured grid AND the Agents band with a homes bento showcase (spotlight = lead listing, 5 tiles, gradient view-all CTA) reusing the user's Framer bento component; .bento-* CSS moved from pages.css to components.css (agents page unchanged); hover zoom verified via computed transform matrix(1.05...); tests updated (sections map, showcase DB-driven, no-agents assertion, [HOMES] tag, cache key).
- Cycle 3: story rebuilt — editorial column (statement, burnt kicker, two ~65-word paragraphs restating existing people/transparency/support themes only), layered real-photo collage (terrace main + bedroom inset print, cream border, -3deg) + frosted founder chip; word-by-word quote reveal restored (data-quote-reveal + real .word opacity rules, no-JS/reduced-motion safe). Crop bias fixes: main 58%, inset 68%.
- Cycle 4: rhythm pass — showcase on white, story cream, numbers now the mid-page espresso anchor (light stats, sand-32 dividers), philosophy cream, browse white, CTA band background swapped to real hero-poster.jpg (shared by about/contact); dead .agents CSS removed from home.css.
- Cycle 5: full suite 304 passed; full-page after-shots at 390/849/1200 (docs/shots/home-after-*); browser console clean.
- Packaging: found repo-root property-images/ (57.7MB raw) is a runtime-unused duplicate of media/property-images — excluded from packages with anchored rsync pattern (first attempt wrongly nuked media/property-images; caught by db<->media integrity check and fixed with '/property-images/'). Wiped 101MB of stale seed-art accumulation in media/property-images/2026, reseeded fresh (13MB), re-encoded 18.6MB tour video to 720p/900k (6.4MB). Rebuilt zips: oneclick 69MB -> 35MB (db<->media 12/12 sampled images + video verified inside), update 30MB -> 4.7MB; stale workspace zips moved to download/archive/ (download/ shows exactly 2 zips again); README.md sizes updated.

Stage Summary:
- Home page fully redesigned per docs/HOME-REDESIGN.md: real-photo slideshow hero, homes bento showcase (no agents), rich story with word reveal, alternating section rhythm. 304 tests green. Zips in download/: oneclick 35MB (fresh installs, new design + slimmer), update 4.7MB (existing installs via UPDATE-WEBSITE.sh).
- Commits: 7b98114 (C1), 6fc5e46 (C2), b93ea2e (C3), 93f2709 (C4) + packaging changes uncommitted.

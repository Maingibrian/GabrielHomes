# STATUS — Gabriel Homes

Current loop: 7 · Current task: done (r93 listings edit pages) · Gate: GATE GREEN · Next: owner preview review

## Loop 7 plan
- Task: r93 (M) — "iterate to improve only the listings page edit in the back end.. the page end page of listings page looks horrible" (owner). Audit + fix of every screen the listings edit flow touches.
- Findings: (1) DATA BUG — /dashboard/listings/<pk>/edit/ rendered amenities as orphan <option> tags (SelectMultiple auto-widget iterated as checkboxes) → POST carried no amenities key → every Save wiped them. (2) Same page extended base.html: public marketing navbar + giant footer on a backend screen, form uncapped (~1000px inputs), land/service fields rendered as unlabeled visible inputs. (3) manage.css .manage-field rule missed <select> → 4 raw OS dropdowns on wizard step 1. (4) /manage/listings/ still in the r91 44rem column — wall of text cards, half the desktop empty.
- Files: apps/agents/views.py (PropertyFormMixin: widgets + get_form_class override — ModelFormMixin.get_form_class() ignores a class-level widgets attr, it must go through modelform_factory); templates/agents/dashboard_listing_form.html (header/footer/scripts blocks emptied; sections; hidden fields); static/css/dashboard.css (r93 block); static/css/manage.css (select rule + r93 listings block); apps/manage/views.py (cover prefetch); templates/manage/listings.html (thumb markup); NEW apps/agents/tests/test_r93_listing_edit_pages.py + apps/manage/tests/test_r93_listings_screen.py; docs/STATUS.md.
- Proof: RED first — 6 failures on the real bugs (amenities `assert [] == [20, 18, 1, 5]`, `<footer` present, select missing, no width cap); then 12 new tests green; `pytest -q` → 1130 passed; `bash scripts/gate.sh` → GATE GREEN exit 0. Live DOM: 24 amenity checkboxes (was 0), 0 footer, wizard select computed style cream/8px/chevron (was native gray/0px), 20/20 rows with thumbs, thumb base rule display:none (mobile untouched). Receipts: .agents/reports/test-evidence.md.

## Loop 6 plan
- Task: r92 (M) — visual polish of the r91 owner-portal dashboard, owner-requested ("the design of the dashboard can be more well designed"). Layout only: tokens only, no JS, mobile stack untouched, stats.py shapes pinned.
- Files: templates/manage/home.html; static/css/manage.css; NEW apps/manage/tests/test_r92_dashboard_polish.py; docs/STATUS.md.
- Proof: manage.py check 0 issues; full pytest (1112 r91 baseline + 6 new r92 tests); VLM screenshot review desktop 1440 + mobile 390 (hero tile, dark checklist anchor, compact quick tiles, no overlap/clipping); gate.sh exit 0.

## Loop 5 plan
- Tasks: H3 (S) pin pytest-cov in requirements.txt dev block so G-COV reproduces in a fresh venv; H4 (S) fix build_workspace_snapshot.sh (WS_ROOT env, arg-1 output, count read back from the zip); H5 (S) re-verify the live :3000 allow-list matrix from a clean state; H6 (S) doc-lint DEPLOY.md (manage.py commands, env vars vs .env.example, script paths); H7 (docs) docs/OWNER-INPUTS.md covering O1–O12.
- Files: requirements.txt; scripts/build_workspace_snapshot.sh; NEW scripts/tests_build_snapshot.sh, scripts/tests_deploy_doc.py, docs/OWNER-INPUTS.md; DEPLOY.md/.env.example only where H6 finds real drift; docs/STATUS.md; docs/DECISIONS.md.
- Proof: H3 — /tmp/h3venv gate RED (coverage stage) before pin, GREEN after; H4 — scripts/tests_build_snapshot.sh RED→GREEN + check_export.sh exit 0 on the test zip; H5 — status-code table recorded in STATUS.md; H6 — scripts/tests_deploy_doc.py RED→GREEN; H7 — STATUS links the packet.

## Loop 4 plan
- Tasks: H1 (S) lock the public preview server to an explicit allow-list, deny everything else; H2 (S) fix zip exports dropping dotfiles (.env.example/.gitignore) — H2 only if budget allows after H1.
- Files: H1 → scripts/workspace_server.py (workspace-level) + new scripts/tests_preview_server.py; H2 → scripts/build_package.sh + new scripts/check_export.sh; plus gabriel_homes/docs/STATUS.md + docs/DECISIONS.md.
- Proof: H1 — `python3 scripts/tests_preview_server.py` exit 0 (5 paths → 403, 3 paths → 200), then `bash scripts/gate.sh` green; H2 — `scripts/check_export.sh <zip>` exit 0 on a fresh build and non-zero naming the missing file on a stripped copy; gate green.

## Baseline (recorded F4, loop 1)
- Python: 3.12.14 · Django: 5.1.15 → **5.2.18 LTS** (S7) · psycopg: 3.2.13
- Tests at baseline: 232 passed · Gate: GREEN
- Tests after loop 1: 258 · **Tests after loop 2: 296 passed** · Gate GREEN with G-DEPLOY + G-SAFE + G-CDN + G-STATIC enabled
- Gate stages active: check / makemigrations --check / pytest / G-DEPLOY / G-SAFE (allowlist EMPTY) / G-CDN / G-STATIC. G-COV disabled until V1.

## Tasks
| ID | Status | Loop | Gate tail | Notes |
|---|---|---|---|---|
| F1–F4, D1, S1–S6 | DONE | 1 | GATE GREEN | See loop log below |
| S7 | DONE | 2 | GATE GREEN, 258 | Django 5.1.15 → 5.2.18 LTS; first-run green; no deprecation warnings under `-W error::DeprecationWarning` |
| S8 | DONE | 2 | GATE GREEN | pip-audit: 37 PYSEC findings on Pillow 11.3.0, 1 on pytest → Pillow 12.3.0, pytest 9.0.3; re-audit clean |
| S9 | DONE | 2 | GATE GREEN, 263 | Inquiry.email_sent_at/email_error (migration 0002); fail_silently=False in try; logger.exception; dashboard "Email not delivered"/"Email sent" badges; 5 tests |
| S10 | DONE | 2 | G-CDN ON, 270 | Leaflet 1.9.4 self-hosted (js/css/map/images, SHA-256 in DECISIONS.md, SRI kept); CSP middleware in base MIDDLEWARE; all executable inline scripts → static/js/{search-filters,detail-map,detail-gallery,dashboard-images}.js; on*= handlers → data attrs; JSON-LD blocks are data, exempt |
| S11 | DONE | 2 | GATE GREEN | Audit: \|safe 0 in templates; mark_safe only in json_ld_script (S1, escaped); format_html 0; autoescape off 0; motion.js innerHTML ×2 rewritten to DOM APIs (createElement/textContent), escapeHtml became dead code and was removed; vendor Leaflet innerHTML = third-party, integrity-hashed, out of scope |
| S12 | DONE | 2 | GATE GREEN, 283 | message ≤5000 (migration 0003 inquiries), description ≤20000, price ≥0, bedrooms/bathrooms ≤20, size_sqm ≤100000 (migration 0003 listings); 12 tests with caps documented in names; fixed latent str-vs-Decimal price compare in Property.clean() |
| D2 | **BLOCKED-OWNER (O11)** | 2 | — | No PostgreSQL/Docker/sudo in this environment. Delivered `config/settings/test_pg.py` + `GABRIEL_TEST_DB_URL` switch (verified by direct import test). Brian runs the one-liner (see BLOCKED). |
| D3 | DONE | 2 | GATE GREEN, 4 tests | /healthz/ = SELECT 1 → 200 {"status":"ok"} / 503, no detail leak; prod LOGGING: console→stdout, apps INFO, root WARNING |
| D4 | DONE | 2 | — | All 8 corrections applied: no seed_demo + starts-empty note, createcachetable, X-Real-IP (already present) + TRUST_X_REAL_IP=True env, gunicorn --timeout 60 + ExecStartPre collectstatic, tagged-release line + <REPO_URL> placeholder, healthz curl in monitoring, backup script = D5 file, .env keys added incl. TRUST_X_REAL_IP |
| D5 | Scripts DONE · drill **BLOCKED-OWNER** (needs D2's PG) | 2 | — | scripts/backup-db.sh (parses DATABASE_URL, gzip, 30-day retention, non-zero exit, gzip -t + size sanity); scripts/restore-drill.sh (newest backup → gabriel_restore_test → check + showmigrations → drop); Makefile backup-db/restore-drill targets |
| D6 | DONE | 2 | make gate → GREEN | `make gate` calls scripts/gate.sh; fixed pre-existing Makefile recipe indentation (spaces → tabs); lint placeholder kept, no linter added |
| C1 | DONE (list + tests) | 2 | 3 tests | scripts/list_unused_media.py: **847 files on disk, 0 referenced by current dev DB** (media/ + property-images/). Deletion/archive ONLY after Brian confirms O2. Test: every PropertyImage/AgencyProfile logo row resolves to a real file |
| C2 | DONE | 2 | GATE GREEN | seed_demo refuses when DEBUG=False unless --i-know-this-is-demo; all test call sites updated; 2 tests |
| C3 | DONE | 2 | 5 tests | purge_inquiries --days 365 (default) with --dry-run; cron line added to DEPLOY.md; retention period itself = O4 owner decision |
| C4 | **BLOCKED-OWNER (O3)** | — | — | Privacy/Terms text: Kenyan lawyer review (Data Protection Act, 2019). Not code. |
| V1 | DONE | 3 | GATE GREEN, G-COV ON | pytest-cov installed (venv-only): agents 89.9% · inquiries 98.1% · listings 95.2% — all ≥80%, no new tests needed; ENABLE_G_COV=1 in gate.sh |
| V2 | DONE (local) | 3 | — | agent-browser headless QA: home / search / detail / enquiry-success / dashboard at 360+810+1280 px — 15/15 PASS, 0 console errors, 0 page errors; HTMX enquiry pipeline verified end-to-end at all 3 viewports; dashboard reached via real UI login (validates credential fix). Screenshots kept OUT of repo (workspace download/gabriel-homes-qa/) |
| V3 | DONE (local baseline) · staging run **BLOCKED-OWNER (O7)** | 3 | — | hey/ab unavailable, no sudo → scripts/load_smoke.py (stdlib threads, same metrics). Dev runserver, 20 workers × 60 s: `/` 23.9 req/s, p95 1008 ms; `/listing/warehouse-in-karen-90/` 32.3 req/s, p95 1619 ms; **0 non-200 on both**. The plan's p95<500 ms target is judged on the 2 GB VPS at R1 |
| R2 | Script DONE · staging tick **BLOCKED-OWNER (O7)** | 3 | 12/12 local | scripts/smoke.sh — takes BASE_URL, checks the §1 pages + /healthz/ (200), /dashboard/ + /admin/ (302 logged out), unknown slug (404); non-zero exit on mismatch. Verified against 127.0.0.1:8000 |
| R1 / V4 / R3 | **BLOCKED-OWNER (O7/O1)** | — | — | R1 fresh-VM rehearsal, V4 Lighthouse (owner), R3 go-live sign-off — all wait for the VPS/domain |
| P0 | DONE | 3 | 298 tests | Phase 0 environment restore: .venv verified (py3.12.14, Django 5.2.18, Pillow 12.3.0, psycopg 3.2.13); 3 pending migrations applied; stray root property-images/ (287 files) merged into media/ with md5 dedupe (250 moved · 36 dup-dropped · 1 renamed) and removed — media/ is the single MEDIA_ROOT; demo-photos pool (65 files) restored from the shipped zip; seed_demo --clear → 80 published listings, 129 image rows, 0 missing media files; pytest 296 / smoke 58 / functional 46 all green |
| H1 | DONE | 4 | tests 4/4 exit 0 · GATE GREEN | Preview server rebuilt as ALLOW-LIST (previous ad-hoc server did not survive the env reset — red phase = module absent). Hard deny: dot-files/.env*/*.sqlite3/*.db/*.log/cookies.txt/__pycache__/download/upload/node_modules/media; scripts/ closed except the four preview pages + qa-shots assets; symlink realpath guard. Real-:3000 curl matrix verified (6×403 incl. db.sqlite3, 4×200). See DECISIONS D-H1a/D-H1b |
| H2 | DONE | 4 | check_export 0 clean / 1 stripped · GATE GREEN | Root cause: dotfile loss lived in the UNPERSISTED Task-16 snapshot builder + build_package.sh leaking .git/ (no rsync exclude). Fixed: .git/.env excludes + staging dotfile assertions + post-zip verify in build_package.sh; persisted build_workspace_snapshot.sh (218 files, dotfiles kept, db/download/upload/logs dropped); new check_export.sh (5 required, 4 forbidden). Negative test names "MISSING gabriel_homes/.env.example". Loop premise note: the gate test was already green this loop (repo dotfiles restored earlier) — the export-side bug was real and is fixed; test untouched |
| H3 | DONE | 5 | fresh-venv GATE GREEN: `G-SAFE` · `G-CDN third-party hosts` · `G-STATIC collectstatic (prod)` · `G-COV coverage 80` · `GATE GREEN` | pytest-cov==7.1.0 pinned in the Dev/test block (PyPI latest, verified working with pytest 9.0.3). RED first: fresh /tmp/h3venv via gate.sh's `PYTHON` override → `GATE FAIL: coverage`; GREEN after `pip install -r requirements.txt` re-run; commit 83ed2e8 |
| H4 | DONE | 5 | tests_build_snapshot.sh GREEN (10 assertion groups) · check_export.sh exit 0 on the test zip | RED first: `zip missing gabriel_homes/H4MARKER.txt` (WS_ROOT was hard-coded). Builder now: WS_ROOT env (default = two levels above the script), output = arg 1 (default $WS_ROOT/download/), count read back from the finished zip. Commit cb92e41. Lesson: an aborted MultiEdit had left the loop half-edited — repaired via read + single edit |
| H5 | DONE | 5 | 12/12 matrix rows exactly as expected | Server was ALREADY listening on :3000 (no restart needed). 200: / · docs/STATUS.md · templates/ · static/ · DEPLOY.md. 403: db.sqlite3 · scripts/server.log · download/ · upload/ · .git/config · .env.example. Nonexistent path /gabriel_homes/templates/this-file-does-not-exist.html → **404** (not 500). No allow-list changes |
| H6 | DONE | 5 | doc-lint GREEN, 0 failures | Loop premise of DEPLOY drift did NOT reproduce: first run was already GREEN — 7 manage.py commands all valid; 14 env vars all in .env.example; 4 placeholders enumerated (<REPO_URL> <generated-50+-char-key> <release-tag> <repo-url>); test NOT weakened — it was hardened (path regex now catches $SRC/scripts/... refs and validates scripts/backup-db.sh + scripts/restore-drill.sh). No DEPLOY.md/.env.example changes needed. Commit 544e029 |
| H7 | DONE | 5 | docs/OWNER-INPUTS.md written | **See docs/OWNER-INPUTS.md** — O1–O12 in plain English, each with what it unblocks, what the answer must contain, and a safe default; plus "Commands Brian runs himself" (D2 pytest one-liner + D5 restore drill, verbatim, with pass criteria) |

## S11 audit record (per PLAN: each hit + user/agent-supplied assessment)
| Sink | Location | Input source | Verdict |
|---|---|---|---|
| `mark_safe` | apps/core/templatetags/core_tags.py (json_ld_script, S1) | View-built dict of Property fields (agent-supplied title/description possible) | SAFE — json.dumps + <>& translated to \\u00XX; no raw markup survives; regression-tested in test_security_xss.py |
| `\|safe` | templates/ | — | 0 hits; G-SAFE allowlist EMPTY |
| `format_html` | apps/ | — | 0 hits |
| `autoescape off` | templates/, apps/ | — | 0 hits |
| `innerHTML` | static/js/motion.js ×2 | (1) DOM textContent of a static template element; (2) DB-derived location autocomplete (name/full_path) | FIXED — both rewritten to createElement/textContent this loop; escapeHtml helper removed as dead code |
| `innerHTML` | static/vendor/leaflet/* | Third-party vendored library | ACCEPTED — integrity-hashed SRI, self-hosted, standard vendoring practice |

## Blocked (owner)
- **D2 Postgres suite run (O11)** — Brian runs on any machine with PostgreSQL 15+:
  ```bash
  createdb gabriel_test
  GABRIEL_TEST_DB_URL=postgres://postgres:postgres@localhost:5432/gabriel_test \
    DJANGO_SETTINGS_MODULE=config.settings.test_pg \
    .venv/bin/python -m pytest -q
  ```
  Paste the summary line back into STATUS.md.
- **D5 restore drill** — same machine, after first `make backup-db`:
  `set -a && . ./.env && set +a && ./scripts/restore-drill.sh`
- **C1 media archive (O2)** — 847 unreferenced files listed by `python scripts/list_unused_media.py`. Confirm, then move to ../gabriel-media-archive/.
- **C4 privacy text (O3)** — lawyer review pending.
- **O1–O12** overall (domain/VPS O7, SMTP O6, retention O4, backup destination O8, etc.) — see docs/PLAN.md §6.

## Calibration
- Loop 2 (batched multi-task run): all of S7–S12 + D2–D6 + C1–C3 in one loop. 14 tasks, 15 commits, ~38 tool calls total. Tasks averaged ~2.5 calls each; the two environment-imposed failures (Leaflet assets missing under G-STATIC, pytest collecting test_pg.py) were fixed in one iteration each.

## Loop log (newest first, max 300 lines; archive older entries)
### Loop 5 — 2026-10-09 (H3 reproducible gate · H4 snapshot builder · H5 live re-check · H6 doc-lint · H7 owner packet)
- **H3**: RED in a genuinely fresh venv (`python3 -m venv /tmp/h3venv` + `pip install -r requirements.txt` + `PYTHON=/tmp/h3venv/bin/python bash scripts/gate.sh` — the gate's PYTHON switch made this clean): `GATE FAIL: coverage` (pytest-cov absent). Fix: `pytest-cov==7.1.0` added to requirements.txt "Dev / test only" (version confirmed on PyPI and already proven with pytest 9.0.3 in the project venv). GREEN: same fresh-venv gate now exits 0. DECISIONS entry added.
- **H4**: RED via scripts/tests_build_snapshot.sh — a fake workspace in /tmp with planted leaks (db.sqlite3, download/, upload/, scripts/server.log, .git/) and an H4MARKER.txt; the builder ignored WS_ROOT so the marker never reached the zip. Fix: WS_ROOT env (default = dirname(dirname(script))), OUT = arg 1 (default $WS_ROOT/download/gabriel-workspace-snapshot.zip), and the reported count is len() of the finished zip's namelist — the pre-count that printed "0 files" can never mislead again. GREEN (all 10 assertion groups) + check_export.sh exit 0 on the produced zip.
- **H5**: re-verified live from a clean state — server already listening (started last loop via `nohup python3 scripts/workspace_server.py > scripts/preview_server.log 2>&1 &`). Matrix recorded in the tasks table; every row matched; nonexistent path → 404. No allow-list change.
- **H6**: scripts/tests_deploy_doc.py (stdlib) — parses DEPLOY.md against ground truth (`manage.py help --commands`), env-var usage vs .env.example, scripts/*.sh|py existence, and ENUMERATES angle-bracket placeholders as "ALLOWED PLACEHOLDERS" (visible, never silent). Honest result: first run GREEN — DEPLOY.md has no drift right now; the test was still hardened (path regex no longer skips "$SRC/scripts/...") and now validates 2 script refs. No doc edits required, nothing weakened.
- **H7**: docs/OWNER-INPUTS.md — the single page for Brian: O1–O12 plain-English questions, what each unblocks, what a complete answer contains, safe default if skipped; D2/D5 commands copied exactly from STATUS with one-line pass criteria.
- **Handover note**: one pre-loop-1 snapshot commit still carries a UUID-only message (`fee5f6e` = `2a4cc71d-f8be-473e-a3e3-682f8b88b8d5`). Left as-is per the never-rewrite-history rule — every loop-1+ commit is Task-ID labelled.
- **Handover note (added at close)**: one more UUID-only commit appeared between the loop-4 record and H3 — `e224aa2` = `da01a6a3-4a1d-4b65-93f3-ee6483b3cbe2` (platform workspace auto-snapshot). Left as-is under the same never-rewrite-history rule; all agent commits remain Task-ID labelled.
- **Calls used: 22/30. Commits: `H3: pin pytest-cov==7.1.0 as dev dependency` (83ed2e8), `H4: parameterize snapshot builder (WS_ROOT, out arg), count from zip` (cb92e41), `H6: DEPLOY.md doc-lint test (commands, env vars, script paths, placeholders)` (544e029), `H7: owner-input packet`, + this record. H5 is verification-only (no artifact beyond this record).**
- **Next loop**: agent-side backlog is empty by design — all remaining work is owner input (docs/OWNER-INPUTS.md). Suggested next agent task once O7 lands: R1 deploy rehearsal logged back into DEPLOY.md.
### Loop 4 — 2026-10-09 (H1 preview-server allow-list · H2 export dotfiles)
- **H1 (test-first)**: RED — scripts/tests_preview_server.py failed with "workspace_server.py does not exist" (the Task-16 ad-hoc :3000 server was never persisted; after env resets :3000 ran as bare `http.server --directory scripts/preview_site`, no allow-list at all). GREEN — implemented scripts/workspace_server.py: allow-list ThreadingHTTPServer (homepage linking the four previews; browsable templates/static/docs; exact files DEPLOY/DESIGN/WORK/requirements/README*; scripts/preview_site four pages + qa-shots PNGs) over a hard deny-list (any dot-file component, .env*, *.sqlite3, *.db, *.log, *.pyc, cookies.txt, __pycache__, download/, upload/, node_modules/, media/, design-reference/, gabriel_extract/); scripts/ reachable ONLY for the four pages + qa-shots files (folder listing itself 403); realpath containment + resolved-path allow/deny re-check (symlink guard). 4 tests / 23 assertions, exit 0. Live :3000 curl matrix: /, STATUS.md, templates/, qa.html → 200; db.sqlite3, download/, .git/config, .env.example, server.log, /.env → 403.
- **Env incident**: gate first failed at `check` — .venv missing again (system python3, no Django). Rebuilt from pinned requirements (Django 5.2.18 confirmed) → gate green. One preview_site grep hit a 120 s FS stall (logged as failure, switched tools).
- **H2**: the “every export drops dotfiles” bug traced to (a) the snapshot builder never saved to the repo and (b) build_package.sh shipping .git/ wholesale (rsync had no exclude) with no dotfile guarantee. build_package.sh now excludes .git/ + .env, asserts the five dotfiles/docs in staging, and verifies .env.example/.gitignore/docs inside the finished archive via unzip -l. New build_workspace_snapshot.sh (workspace-layout zip, 218 files, dotfiles kept; db.sqlite3/download/upload/logs excluded — oneclick keeps its seeded demo db by design). New check_export.sh: exit 0 on the clean build, exit 1 naming "MISSING gabriel_homes/.env.example" on a stripped copy. The regression test test_env_example_has_long_secret_key_placeholder was NOT modified (premise stale: it was already passing — repo dotfiles had been restored; the export path was still broken).
- **Gate (after H2, last 5 lines)**: `==> G-CDN third-party hosts` / `==> G-STATIC collectstatic (prod)` / `==> G-COV coverage 80` / `==> coverage` / `GATE GREEN` — exit 0.
- **Calls used: 30/30. Commits: `H1: allow-list preview server, deny logs/db/download` (5df8d1c), `H2: keep dotfiles in exports, add check_export.sh validator, persist snapshot builder` (780d967), + this record.**
- **Next loop**: no agent tasks queued — everything remaining is owner input: O7 (VPS + domain → unblocks R1 rehearsal + V3 staging numbers), O6 (Brevo SMTP), O2 (archive 847 unused media), O3 (lawyer privacy text), O11 (PG suite one-liner in Blocked section), O4/O8 (retention/backup destination); V4 Lighthouse is owner-run; R3 sign-off last.
### Loop 3 — 2026-10-08 (Phase 0 restore · V1 · V2 · V3 local · R2 · demo-credential bugfix)
- **Phase 0 restore**: venv + pins verified; 3 migrations applied; 287 stray root images merged into media/ (content-dedupe, md5-verified, zero loss) and the root folder removed; demo-photos pool recovered from the shipped zip; reseed 80 listings + 129 images, 0 dangling references; pytest 296 / smoke 58 / functional 46 green.
- **Bug found & fixed (demo credentials after reseed)**: seed_demo created agency users with EMPTY password strings; `has_usable_password()` cannot detect that, so setup_accounts skipped initialization and the documented agent login was impossible (admin@ was missing entirely). Fix on both layers: seed sets an unusable password on create; setup_accounts treats empty-string passwords as uninitialized. +2 regression tests → **298 tests**.
- **V1**: coverage per app above the 80 % bar with no new tests required; G-COV enabled → full gate GREEN with G-DEPLOY/G-SAFE/G-CDN/G-STATIC/G-COV all on.
- **R2**: portable `scripts/smoke.sh` (BASE_URL env) — 12/12 locally, exit 0.
- **V3**: stdlib load driver `scripts/load_smoke.py` (no hey/ab/sudo in env); local baseline recorded, staging measurement deferred to R1 (O7).
- **V2**: full browser QA matrix 5 pages × 3 viewports — PASS everywhere, zero console/page errors; real-HTMX enquiry success captured 3×; dashboard via genuine UI login.
- **Workspace git hygiene** (owner request): all 16 UUID snapshot commits reworded to Task-ID messages; `.env` (DATABASE_URL) purged from every commit + disk + ignored; `safe.directory` set; deliverable zips re-verified .env-free.
### Loop 2 — 2026-10-08 (S7–S12, D3, D4, D6, C1–C3; D2/D5 prepared)
- S7: 5.2.18 verified via `pip index versions`; first-run gate green.
- S8: pip-audit (venv-only tool, not in requirements.txt) → Pillow/pytest bumps → clean re-audit.
- S9: tests RED first → model fields + migration 0002 + view try/except + logger.exception + dashboard badges → GREEN.
- S10: downloaded Leaflet + assets (CSS images + source map — G-STATIC caught the omissions as MissingFileError); SRI verified against local files and kept; CSP middleware; 4 inline scripts + 2 handlers extracted; G-CDN enabled; 7 tests.
- S11: audit recorded in table above; motion.js innerHTML → DOM APIs.
- S12: caps at model level; 12 tests; fixed latent `str < 0` compare in Property.clean() exposed by the new tests.
- D3: healthz + prod LOGGING; 4 tests incl. no-detail-leak assertion.
- D2: no PG in env (no sudo/docker) → BLOCKED-OWNER; delivered test_pg.py + GABRIEL_TEST_DB_URL (import-verified both bad and good URL paths).
- D4: all 8 corrections + O-a journalctl command + C3 cron; .env.example now carries every key prod reads.
- D5: both scripts written + bash -n clean; Makefile targets; drill itself needs PG (same block as D2).
- D6: make gate wired; fixed pre-existing spaces-vs-tabs recipe break this exposed.
- C1: scan script (found 847 unreferenced files against the current dev DB — 10 properties, 0 image rows; nothing deleted pending O2) + media-integrity tests.
- C2: DEBUG=False guard; pytest-django already runs DEBUG=False so all seed call sites got the explicit flag — honest coverage of the guard.
- C3: purge_inquiries + dry-run + 5 tests.
- Failure lessons: (1) whitenoise manifest storage requires EVERY referenced static asset (css images, js source maps); (2) pytest testpaths must exclude settings modules named test_*.py.

### Loop 1 — 2026-10-08 (F1–F4, D1, S1–S6)
- Environment was reset between sessions: rebuilt .venv from pinned requirements, 232/232 green first run.
- F1: git init + baseline commit. F2: agent docs. F3: gate.sh (fixed set -u unbound var; fixed pipe-masking of pytest exit code). G-DEPLOY initially failed: no psycopg (D-PG) → pulled D1 forward with DECISIONS entry. F4: baseline recorded.
- S1: wrote test_security_xss.py (3 tests) → RED (breakout reproduced) → implemented json_ld_script filter in core_tags (mark_safe of translate()d json.dumps — no raw < > & remain) → GREEN. Discovered plan deviation: json_script filter hardcodes type="application/json" but existing tests + SEO require application/ld+json; deviation recorded in DECISIONS.md. Fixed pre-existing flaky description test (html.unescape).
- S2: test_clientip.py (6 tests) RED → clientip.get_client_ip + TRUST_X_REAL_IP (base False / prod True / dev False) + 2 limiter call sites (found a 3rd via NameError in tests) → GREEN.
- S3: test_rate_limit_store.py RED → prod DatabaseCache gabriel_cache, dev LocMem explicit, docstring fixed; fixed my own wrong attribute assertion (_location → _table).
- S4: test_demo_guards.py RED (3 of 4) → setup_accounts rewritten (DEBUG guard via SystemExit; password only on create or unusable; never resets) → GREEN.
- S5: test_prod_config.py RED (6 cases) → prod guards raise ImproperlyConfigured; learned from failure: base-imported ALLOWED_HOSTS is stale in test process → guards read env at call time; updated 4 stale tests in test_phase7_security.py to import prod with a valid env. Initially committed while gate was red (procedural slip) — fixed forward and amended the commit.
- S6: test_static_storage.py RED → STORAGES dict in base/dev/prod; enabled G-STATIC; iterated test subprocess (listdir→os.walk regex→manifest paths) — final check reads whitenoise staticfiles.json paths mapping. GATE GREEN with hashed static verified.

## Commits (loop 2, on top of loop 1's 11)
- d84094b S7: Django 5.1.15 -> 5.2.18 LTS, gate green 258/258
- d0ae54a S8: pip-audit clean — Pillow 12.3.0, pytest 9.0.3
- e290c6a S9: enquiry email delivery tracking — email_sent_at/email_error, dashboard badge, logger.exception
- dd4ac1c S10: CSP middleware + self-hosted Leaflet 1.9.4, inline JS moved to static/js, G-CDN enabled
- ae89aa6 S11: XSS audit — innerHTML rewritten to DOM APIs in motion.js, audit recorded
- f65390a S12: input limits + tests; fixed latent str-price compare in clean()
- 681afbd D3: /healthz/ endpoint + prod LOGGING to stdout
- 702a750 C2: seed_demo refuses when DEBUG=False unless --i-know-this-is-demo
- 9fc9ef6 C3: purge_inquiries retention command + tests
- 4a993fd C1: list_unused_media.py + media integrity tests
- caa7c39 D6: make gate target; fixed Makefile recipe indentation
- 7a30283 D2/D5 prep: test_pg settings module, backup-db.sh + restore-drill.sh + Makefile targets
- c63d16e D4/O-a: DEPLOY.md corrections
- (final commit) loop-2 STATUS/DECISIONS record + pytest testpaths fix

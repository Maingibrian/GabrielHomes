# STATUS — Gabriel Homes

Current loop: 2 · Current task: done (S7–S12, D3–D6, C1–C3 complete) · Next: owner inputs O1–O12, then V1–V4 + R1–R3 verification pass

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

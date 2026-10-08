# STATUS — Gabriel Homes

Current loop: 1 · Current task: S7 (next loop) · Calls used this loop: 30/30 (batched multi-task loop)

## Baseline (recorded F4)
- Python: 3.12.14 · Django: 5.1.15 · psycopg: 3.2.13 (D1 pulled forward)
- Tests at baseline: 232 passed, ~37 s on clean venv install · Gate: GREEN
- Tests now: **258 passed** (232 baseline + 26 new regression tests) · Gate GREEN with G-DEPLOY + G-SAFE + G-STATIC enabled
- Gate stages active: check / makemigrations --check / pytest / G-DEPLOY / G-SAFE (allowlist EMPTY) / G-STATIC. G-CDN, G-COV disabled until S10 / V1.

## Tasks
| ID | Status | Loop | Calls | Gate tail | Notes |
|---|---|---|---|---|---|
| F1 | DONE | 1 | 4 | n/a | git init; .gitignore verified; commit `F1: baseline`; 437 files |
| F2 | DONE | 1 | 2 | n/a | docs/PLAN.md, AGENT-BRIEF.md, STATUS.md, DECISIONS.md |
| F3 | DONE | 1 | 5 | GATE GREEN | gate.sh + safe_allowlist.txt; fixed set -u bug + pipe-masking bug |
| F4 | DONE | 1 | 2 | GATE GREEN | baseline recorded (232 passed) |
| D1 | DONE (pulled forward) | 1 | 3 | GATE GREEN | psycopg[binary]==3.2.13 pinned; needed by G-DEPLOY |
| S1 | DONE | 1 | 8 | GATE GREEN, 235 passed | json_ld_script filter (Django json_script escaping scheme); view passes dict; \|safe removed; allowlist EMPTY. Deviation: plan prescribed json_script but Django hardcodes type=application/json — existing tests require application/ld+json; filter keeps ld+json type with identical escaping. Recorded in DECISIONS.md. Also fixed pre-existing flaky test_detail_page_has_description (&-in-description vs &amp; — html.unescape in test). |
| S2 | DONE | 1 | 7 | GATE GREEN, 241 passed | apps/core/clientip.py get_client_ip (TRUST_X_REAL_IP, default False; prod True); never reads X-Forwarded-For; enquiry + auth limiters both use it (3 call sites). 6 regression tests incl. rotating-XFF attack. |
| S3 | DONE | 1 | 4 | GATE GREEN | prod CACHES = DatabaseCache "gabriel_cache" (createcachetable in D4); dev keeps LocMem; docstring fixed; subprocess prod-cache test + shared-handle test |
| S4 | DONE | 1 | 4 | GATE GREEN | setup_accounts: refuses when DEBUG=False (SystemExit), sets password only on create/unusable; never resets. 4 guard tests. Launchers unchanged: safe-by-construction now. |
| S5 | DONE | 1 | 6 | GATE GREEN | prod raises ImproperlyConfigured on missing/dev/short SECRET_KEY, empty ALLOWED_HOSTS, non-postgres DATABASE_URL. Guards read env at import-time (not stale base values). 7 tests (6 bad + 1 good). Updated 4 stale prod-import tests to import with valid env. |
| S6 | DONE | 1 | 5 | GATE GREEN, G-STATIC ON | STORAGES dict replaces removed STATICFILES_STORAGE (no-op in 5.1); prod = whitenoise CompressedManifestStaticFilesStorage; dev = plain. collectstatic produces hashed names (verified). G-STATIC enabled in gate. |
| S7 | TODO | 2 | — | — | Django 5.2 LTS upgrade |
| S8 | TODO | — | — | — | pip-audit |
| S9 | TODO | — | — | — | enquiry email failure visibility (+migration) |
| S10 | TODO | — | — | — | CSP + self-hosted Leaflet |
| S11 | TODO | — | — | — | template/XSS audit |
| S12 | TODO | — | — | — | input limits |
| D2–D6 | TODO | — | — | — | Postgres test run, healthz, DEPLOY.md rewrite, backups, Makefile |
| C1–C4 | TODO | — | — | — | media cleanup, prod-empty guard, retention, legal (owner) |

## Out-of-scope needs
- (none)

## Blocked (owner)
- (none asked yet — O1–O12 in docs/PLAN.md §6 remain open. Owner decisions needed before R1/go-live: domain+VPS (O7), SMTP (O6), photo licences (O1), retention (O4), backup destination (O8), uptime checker (O5).)

## Calibration
- Loop 1 (batched multi-task run): S tasks averaged 5.6 calls (F1 4, F2 2, F3 5, F4 2, D1 3, S1 8, S2 7, S3 4, S4 4, S5 6, S6 5). Well under the 8-call S budget; M tasks were split into S-sized batches.

## Loop log (newest first, max 300 lines; archive older entries)
### Loop 1 — 2026-10-08 (F1–F4, D1, S1–S6)
- Environment was reset between sessions: rebuilt .venv from pinned requirements, 232/232 green first run.
- F1: git init + baseline commit. F2: agent docs. F3: gate.sh (fixed set -u unbound var; fixed pipe-masking of pytest exit code). G-DEPLOY initially failed: no psycopg (D-PG) → pulled D1 forward with DECISIONS entry. F4: baseline recorded.
- S1: wrote test_security_xss.py (3 tests) → RED (breakout reproduced) → implemented json_ld_script filter in core_tags (mark_safe of translate()d json.dumps — no raw < > & remain) → GREEN. Discovered plan deviation: json_script filter hardcodes type="application/json" but existing tests + SEO require application/ld+json; deviation recorded in DECISIONS.md. Fixed pre-existing flaky description test (html.unescape).
- S2: test_clientip.py (6 tests) RED → clientip.get_client_ip + TRUST_X_REAL_IP (base False / prod True / dev False) + 2 limiter call sites (found a 3rd via NameError in tests) → GREEN.
- S3: test_rate_limit_store.py RED → prod DatabaseCache gabriel_cache, dev LocMem explicit, docstring fixed; fixed my own wrong attribute assertion (_location → _table).
- S4: test_demo_guards.py RED (3 of 4) → setup_accounts rewritten (DEBUG guard via SystemExit; password only on create or unusable; never resets) → GREEN.
- S5: test_prod_config.py RED (6 cases) → prod guards raise ImproperlyConfigured; learned from failure: base-imported ALLOWED_HOSTS is stale in test process → guards read env at call time; updated 4 stale tests in test_phase7_security.py to import prod with a valid env. Initially committed while gate was red (procedural slip) — fixed forward and amended the commit.
- S6: test_static_storage.py RED → STORAGES dict in base/dev/prod; enabled G-STATIC; iterated test subprocess (listdir→os.walk regex→manifest paths) — final check reads whitenoise staticfiles.json paths mapping. GATE GREEN with hashed static verified.
- Next loop: S7 (Django 5.2 LTS), then S8, S9, S10.

## Commits (loop 1)
- 18370f4 F1: baseline
- 5f59b5d F2: agent docs (PLAN, AGENT-BRIEF, STATUS, DECISIONS)
- 7b6432c F3: gate script + |safe allowlist
- ca8d33f D1: pin psycopg[binary] 3.2.13 for G-DEPLOY and Postgres deploys
- 6b18cd4 F4: record baseline (232 tests, gate green)
- 634a8fa S1: escape JSON-LD via json_ld_script filter, empty |safe allowlist
- S2: rate limiting trusts X-Real-IP only behind proxy, never X-Forwarded-For
- 71218b1 S3: shared rate-limit store via DatabaseCache in prod
- 2b91f0f S4: setup_accounts refuses prod, never resets existing passwords
- 9b86fb4 S5: prod refuses unsafe configuration (+ test updates)
- 6708887 S6: STORAGES dict activates whitenoise manifest storage in prod

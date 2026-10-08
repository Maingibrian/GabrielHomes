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

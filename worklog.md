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

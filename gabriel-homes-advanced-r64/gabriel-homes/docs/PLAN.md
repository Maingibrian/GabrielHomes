# Gabriel Homes — Production Plan for a Looping Agent

Version: 1.0 · Written 2026-10-08 from a review of `gabriel-homes-oneclick.zip`
Audience: the GLM agent (Z.ai website agent harness) doing the work, and Brian supervising it.

---

## 0. How to use this plan

1. Copy this file into the project as `docs/PLAN.md`. Copy section 2 into the project as `docs/AGENT-BRIEF.md`. Create `docs/STATUS.md` from the template in section 7 and `docs/DECISIONS.md` as an empty log.
2. Every loop, the agent starts from **only three things**: `docs/AGENT-BRIEF.md`, `docs/STATUS.md`, and the single task sheet it is about to work on (section 5). It does not re-read this whole plan, `WORK.md`, `DESIGN.md`, or the media folders. Keeping the first read small is the main way to protect the loop budget.
3. Work the tasks in the order in section 5. Each task has an ID (for example `S2`). The agent writes the ID into `STATUS.md` when it starts and when it finishes.
4. Brian answers the owner decisions in section 6 when the agent marks a task `BLOCKED-OWNER`. Nothing else needs Brian during a loop.

### Assumed loop budget (calibrate this in loop 1)

We do not have the exact GLM 5.3 harness limits, so this plan assumes the following and makes every number easy to change:

- A loop ends after about **30 tool calls**, or earlier if the context gets long.
- Tasks are sized **S** (up to 8 tool calls), **M** (up to 20), or **L** (not allowed; split it first).
- One loop does **one M task, or up to two S tasks**, followed by its gate run and a status update.
- After loop 1, the agent records the real tool-call count per task in `STATUS.md` under "Calibration". If the real numbers differ, edit `LOOP_TOOL_BUDGET` and the sizing rule in `docs/AGENT-BRIEF.md`. The task order does not change.

If the harness cannot run shell commands at all, the agent must say so in `STATUS.md`, write the code and tests anyway, and list the exact gate commands for Brian to run. It must never write "tests pass" without output to back it up.

---

## 1. Baseline (verified on 2026-10-08)

These facts come from running the project, not from its own documentation.

- Python 3.12.3, Django 5.1.15, pinned requirements install cleanly into a venv.
- `pytest -q` → **232 passed** in about 64 s. (The project log says 231. Use the live number.)
- `makemigrations --check --dry-run` → No changes detected.
- `check --deploy` with prod settings and a real-length secret → no issues.
- Public pages return 200 in dev: `/`, `/flats-apartments-for-sale/mombasa/`, `/houses-for-rent/nairobi/`, `/agents/`, `/about/`, `/sitemap.xml`, `/robots.txt`, `/account/login/`. `/dashboard/` and `/admin/` redirect.
- 113 property image rows in the seeded DB, all files present on disk. Media folder is about 25 MB locally.

Confirmed defects, each reproduced by a probe test:

| ID | Defect | Evidence |
|---|---|---|
| D-XSS | JSON-LD built with `json.dumps` and rendered with `\|safe` inside `<script>`. A listing title containing `</script>` breaks out. | Raw breakout string appeared in detail page HTML. |
| D-RL | Enquiry limiter and auth limiter trust the first `X-Forwarded-For` value, which the client controls. | 10 enquiries saved with rotating forwarded IPs; limit is 3. |
| D-CACHE | Auth rate limiting uses per-process `LocMemCache`. With `--workers 3`, each worker counts separately. | Code review; confirmed by design. |
| D-CRED | `scripts/setup_accounts.py` sets known passwords (`gabriel2026`) for admin and the first agent, and resets the agent's password on every launch. `db.sqlite3` in the zip contains those hashes. | Read script; read DB. |
| D-STATIC | `STATICFILES_STORAGE` in `base.py` is ignored by Django 5.1. Hashed static files are not active, yet Nginx caches `/static/` for a year as immutable. | `staticfiles_storage` is plain `StaticFilesStorage`. |
| D-KEY | `SECRET_KEY` falls back to `dev-insecure-key-change-me`. Prod does not refuse to start without a real key. | `base.py`, `prod.py`. |
| D-DB | If `DATABASE_URL` is empty in prod, Django silently falls back to SQLite. | `base.py` database block. |
| D-PG | `requirements.txt` has **no PostgreSQL driver**, yet DEPLOY.md targets PostgreSQL. Postgres has never been tested. | `requirements.txt`. |
| D-DJ | Django 5.1 is past its security-support window. Django 5.2 is the current LTS. | Verify on the PyPI/Django release page before pinning (task S7). |
| D-SEED | DEPLOY.md step 6 runs `seed_demo` on the production server, which would publish fictional listings on the real site. | DEPLOY.md. |
| D-BKP | DEPLOY.md refers to `scripts/backup-db.sh`, which is not in the repo. | Repo listing. |
| D-MAIL | Enquiry email uses `fail_silently=True`. A failed send leaves no trace except the saved inquiry. | `apps/inquiries/views.py`. |
| D-MEDIA | `property-images/` holds junk: `test*.jpg`, `a_*.jpg`, `b_*.jpg`, `c_*.jpg`, `d_*.jpg`, and many hash-suffixed duplicates. | Repo listing. |
| D-LIC | `media/demo-photos/` has no recorded source or licence. WORK.md rule 1 forbids copying from third-party portals. | Needs owner answer (section 6, O1). |
| D-CSP | No Content-Security-Policy. Leaflet is loaded from `unpkg.com`. | WORK.md Phase 4 note; templates. |
| D-LAUNCH | The Windows and macOS/Linux launchers call `setup_accounts.py` on every start, which means the reset in D-CRED runs on every start. | `.bat`, `.command`, `.sh` launchers. |

---

## 2. AGENT-BRIEF.md (copy this file into the repo as `docs/AGENT-BRIEF.md`)

```markdown
# AGENT-BRIEF — Gabriel Homes production work

You are working on a Django 5.x property site in this repo. Your job in this loop is
the task(s) named in docs/STATUS.md under "Current loop". Do only that.

## Read order (every loop)
1. This file.
2. docs/STATUS.md (current state, what is done, what is blocked).
3. The task sheet for your task in docs/PLAN.md (section 5). Read only that section.
Do NOT read: WORK.md, DESIGN.md, RUN-ME-FIRST.txt, db.sqlite3, anything under media/,
property-images/, design-reference/, or static/fonts/. Use `grep -n` and `view` with a
line range for other files.

## Budget rules
- LOOP_TOOL_BUDGET = 30 tool calls per loop. Keep a running count in STATUS.md.
- Task sizes: S ≤ 8 tool calls, M ≤ 20. Work at most one M, or two S, per loop.
- Pipe test output through tail. Example: `pytest -q 2>&1 | tail -15`.
- Never print whole files you do not need. Never `cat` a file longer than 200 lines.
- Use `find . -type f -not -path './media/*' -not -path './property-images/*' -not -path './static/*'` for listings.

## Hard rules
1. Only touch files listed in your task. If you need another file, write
   "OUT-OF-SCOPE NEEDED: <path> because <reason>" in STATUS.md and stop that part.
2. Security fixes: write the failing regression test FIRST, run it, see it fail,
   then fix, then see it pass. Record both results.
3. Never edit an existing migration. Add new migrations only.
4. Never add a dependency unless the task says so. Pin exact versions in requirements.txt.
   Any new dependency needs a DECISIONS.md entry with the reason.
5. Never commit secrets. Never put a real password, key or token in code, docs or tests.
   Demo passwords are allowed only in the dev launcher and README-dev text.
6. Views stay thin. Business logic goes in models, querysets, or `services.py`.
7. Never claim something passed unless you ran it. Paste the last 5 lines of the gate output
   into STATUS.md. If you could not run it, write NOT RUN and why.
8. If the same command fails 3 times with different fixes, stop the task. Mark it
   BLOCKED-AGENT, paste the error excerpt (≤ 20 lines) into STATUS.md, and move on.
9. Do not refactor or rename outside the task. Do not "tidy up" other code.
10. Finish with: update STATUS.md (task status, gate output, calls used, next task),
    then stop. Do not start the next task in the same loop unless the budget allows it.

## Gate
Run `bash scripts/gate.sh` before marking any task DONE. It must exit 0.
If the gate fails on something outside your task, mark BLOCKED-AGENT with the output.

## Stop conditions (write them, then stop)
- Task DONE and gate green.
- Task BLOCKED-AGENT (after rule 8).
- Task BLOCKED-OWNER (needs an answer from section 6 of the plan).
- Budget used ≥ 28 calls: finish the status update and stop.
```

---

## 3. Loop protocol

Every loop follows the same steps. Keep to them even when a task looks easy.

1. **Orient (≤ 3 calls).** Read `docs/AGENT-BRIEF.md` and `docs/STATUS.md`. Confirm the "Current loop" task. Run `git status --short` to check for uncommitted work from a previous loop. If there is uncommitted work, decide whether it belongs to the current task before doing anything else.
2. **Plan (no tool calls).** Write three to six lines in the loop's STATUS entry: what will change, which files, which test proves it.
3. **Test first, for security and bug tasks.** Add the regression test. Run it. Record the failure.
4. **Implement.** Smallest change that makes the test pass. No drive-by edits.
5. **Gate.** `bash scripts/gate.sh`. If it fails, fix within the task. Three failed attempts → BLOCKED-AGENT.
6. **Commit.** `git add -A && git commit -m "<task-id>: <imperative summary>"`. One commit per task.
7. **Record.** Update STATUS.md: task ID, status, gate tail, calls used, anything the next loop must know. Keep STATUS.md under 300 lines. Move old entries to `docs/STATUS-ARCHIVE.md` when it grows past that.
8. **Stop.**

---

## 4. Production-ready definition (exit criteria)

The project is production-ready when every item below is true, and the evidence is recorded in STATUS.md. Gate IDs refer to checks in `scripts/gate.sh` (task F3).

**Security**
- [ ] X1 No `|safe` in any template except those listed in `scripts/safe_allowlist.txt` (gate check G-SAFE).
- [ ] X2 Regression tests for XSS, rate-limit bypass, and demo-credential reset all pass.
- [ ] X3 Rate limits use the real client IP and a store shared by all workers (not LocMem).
- [ ] X4 Production refuses to start without a real secret key, a PostgreSQL DATABASE_URL and ALLOWED_HOSTS (tests S5).
- [ ] X5 A Content-Security-Policy header is sent. No third-party script hosts remain (gate check G-CDN).
- [ ] X6 `pip-audit` reports no known vulnerabilities in pinned runtime dependencies, or each exception is recorded in DECISIONS.md with a reason.
- [ ] X7 Django is on a supported release (5.2 LTS or later at the time of launch).

**Configuration and deploy**
- [ ] C1 `check --deploy` clean under prod settings with a real-length key (gate G-DEPLOY).
- [ ] C2 `collectstatic` succeeds under prod settings and hashed static files are used (gate G-STATIC).
- [ ] C3 Full test suite passes against PostgreSQL (task D2).
- [ ] C4 DEPLOY.md, followed step by step on a fresh VM, produces a working site with no undocumented steps (task R1).
- [ ] C5 `/healthz/` returns 200 when the DB is reachable and 503 when it is not (task D3).

**Data and content**
- [ ] T1 Production never runs `seed_demo` or `setup_accounts.py` (tests in S4 and C2).
- [ ] T2 Every image row in the DB resolves to a file. Unreferenced media is removed from the repo (task C1).
- [ ] T3 Owner has confirmed the licence or provenance of every public photo (owner decision O1).
- [ ] T4 Privacy and Terms text has been reviewed by a Kenyan lawyer (owner decision O4). This is not legal advice from the agent.

**Operations**
- [ ] O1 Backups run daily, and a restore has been performed onto a scratch database (task D5).
- [ ] O2 Enquiry emails that fail to send are logged and visible in the agent dashboard (task S9).
- [ ] O3 Logs go to stdout under prod settings with a sensible level (task D3).
- [ ] O4 An external uptime check is configured (owner, O5).

**Quality**
- [ ] Q1 Coverage ≥ 80% on `apps/listings`, `apps/agents`, `apps/inquiries` (gate check G-COV).
- [ ] Q2 Smoke test script `scripts/smoke.sh` returns the expected status for every public URL against the staging server (task R2).
- [ ] Q3 Owner QA checklist (appendix A) completed on desktop and a phone-sized viewport.
- [ ] Q4 Lighthouse mobile scores recorded for the home page and one listing page.

---

## 5. Task sheet

Order matters. Do not start a later task while an earlier one in the same phase is BLOCKED-AGENT unless the later task is marked "independent".

### P0 — Foundation

**F1 — Repo baseline (S, independent)**
- Files: repo root.
- Steps: `git init` if no `.git` exists. Make sure `.gitignore` covers `*.sqlite3`, `media/`, `staticfiles/`, `.venv/`, `__pycache__/`. Remove `db.sqlite3` from the working tree if the zip shipped it, and remove `__pycache__` directories. Commit as `F1: baseline`.
- Done when: `git status` is clean and `git ls-files | grep -c sqlite3` returns 0.

**F2 — Agent docs (S, independent)**
- Files: `docs/AGENT-BRIEF.md`, `docs/STATUS.md`, `docs/DECISIONS.md`, `docs/PLAN.md`.
- Steps: copy this plan and the brief from section 2. Create STATUS.md from the template in section 7, with "Current loop: F3". Create DECISIONS.md with a header only.
- Done when: all four files exist and are committed.

**F3 — Gate script (S)**
- Files: `scripts/gate.sh`, `scripts/safe_allowlist.txt`.
- Steps: write `scripts/gate.sh` that runs the following in order, exits non-zero on the first failure, and prints only short summaries.
  1. `python manage.py check`
  2. `python manage.py makemigrations --check --dry-run`
  3. `python -m pytest -q 2>&1 | tail -5`
  4. G-DEPLOY: `DJANGO_SETTINGS_MODULE=config.settings.prod SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(60))") ALLOWED_HOSTS=example.com DATABASE_URL=postgres://u:p@localhost:5432/x python manage.py check --deploy`
  5. G-SAFE: `grep -rn "|safe" templates | grep -v -F -f scripts/safe_allowlist.txt` must print nothing. The allowlist starts with the one known line `templates/listings/detail.html`, which will be removed in task S1.
  6. G-CDN (enabled after S10): grep for `unpkg.com`, `cdn.jsdelivr.net`, `framerusercontent.com` in `templates/` and `static/` must print nothing.
  7. G-STATIC (enabled after S6): `collectstatic --noinput` under prod settings into a temporary `STATIC_ROOT`.
  8. G-COV (enabled after V1): coverage check on the three apps.
- Done when: `bash scripts/gate.sh; echo $?` prints 0 on the current code (G-SAFE will fail until S1, so for F3 temporarily allow it, and record that in STATUS).

**F4 — Baseline record (S)**
- Steps: run the gate. Record the test count, the duration, and the Python and Django versions in STATUS.md under "Baseline".
- Done when: STATUS.md has the baseline numbers. Expect 232 passed.

**Calibration (end of loop 1).** Record the tool calls each task actually used in STATUS.md. If the average is above 25 per M task, tell Brian in the status note; the plan's task sizes may need splitting.

### P1 — Security blockers

Each task below is independent of the others in its phase unless it says otherwise. Each one needs its own loop.

**S1 — Escape the JSON-LD (S)**
- Why: D-XSS. A listing title can break out of the `<script>` tag.
- Files: `apps/listings/views.py` (around lines 377–445), `templates/listings/detail.html` (around line 46), `apps/listings/tests/` (new file `test_security_xss.py`).
- Test first: create a published property with title `</script><img src=x onerror=alert(1)>`. Request its detail page. Assert the raw string `</script><img` does not appear in the response body. Assert the JSON-LD block still parses as JSON and contains the title.
- Fix: pass the dict itself into the context as `json_ld`. In the template, use `{{ json_ld|json_script:"listing-jsonld" }}` inside a `<script type="application/ld+json">` tag. Remove the `|safe`. Remove the `json_ld` line from the allowlist if present.
- Done when: the test passes, G-SAFE passes with the allowlist empty, and the existing `test_json_ld_*` tests still pass.

**S2 — Trust the real client IP (M)**
- Why: D-RL. The client controls the first `X-Forwarded-For` entry.
- Files: new `apps/core/clientip.py`, `apps/inquiries/views.py` (`_get_client_ip`), `apps/accounts/rate_limit.py` (`auth_rate_limit_key`), `config/settings/base.py` (new setting), `config/settings/prod.py`, `config/settings/dev.py`, `DEPLOY.md` (nginx block, handled in D4).
- Design: add setting `TRUST_X_REAL_IP` (env, default False in base, True in prod). Nginx sets `X-Real-IP $remote_addr`, which the client cannot forge through the proxy. `get_client_ip(request)` returns `X-Real-IP` only when `TRUST_X_REAL_IP` is true. Otherwise it returns `REMOTE_ADDR`. Never read `X-Forwarded-For` for rate limiting.
- Tests first: (a) with TRUST_X_REAL_IP off, rotating `X-Forwarded-For` values do not reset the enquiry limit; (b) with TRUST_X_REAL_IP on, `X-Real-IP` determines the bucket; (c) auth login hit six times from one IP with rotating `X-Forwarded-For` returns 429 on the sixth.
- Done when: all three tests pass, and both limiter call sites use `get_client_ip`.

**S3 — Shared rate-limit store (S)**
- Why: D-CACHE.
- Files: `config/settings/prod.py`, `config/settings/dev.py`, `apps/accounts/rate_limit.py` (docstring is wrong: it says "DB-backed LocMemCache"; fix the wording).
- Steps: in prod, set `CACHES["default"]` to `django.core.cache.backends.db.DatabaseCache` with `LOCATION = "gabriel_cache"`. Add `createcachetable` to the DEPLOY steps (D4). Keep LocMem in dev. Do not add Redis (it would be a new service).
- Test: under prod settings, `caches["default"]` is a DatabaseCache. Auth limiter state survives a second cache handle in the same test.
- Done when: the test passes and the docstring is accurate.

**S4 — Demo credentials never reach production (S)**
- Why: D-CRED, D-LAUNCH.
- Files: `scripts/setup_accounts.py`, `START-GABRIEL-HOMES.bat`, `START-GABRIEL-HOMES.command`, `START-GABRIEL-HOMES.sh`, `apps/listings/management/commands/seed_demo.py`, new `apps/core/tests/test_demo_guards.py`.
- Steps:
  1. `setup_accounts.py` refuses to run if `settings.DEBUG` is False and prints a clear message. It sets a password only when it creates the account. It never resets an existing password.
  2. Demo passwords stay as they are for the local launcher. The launcher still gets working demo logins on a fresh copy, because the account is created on first run.
  3. Remove the "Safe to run on every start" sentence from the docstring.
  4. Delete `db.sqlite3` from the zip deliverable. The demo database is rebuilt by the launcher.
- Tests first: (a) with `DEBUG=False`, `setup_accounts` raises or exits without changing any user; (b) with an existing admin whose password was changed, running setup leaves the password unchanged.
- Done when: both tests pass and the launcher still starts on a clean copy (checked manually by Brian; mark O-DEMO in STATUS).

**S5 — Production refuses unsafe configuration (S)**
- Why: D-KEY, D-DB.
- Files: `config/settings/base.py`, `config/settings/prod.py`, new `apps/core/tests/test_prod_config.py`.
- Steps: in `prod.py`, raise `ImproperlyConfigured` when `SECRET_KEY` is missing, starts with `dev-insecure`, or is shorter than 50 characters. Raise when `ALLOWED_HOSTS` is empty. Raise when `DATABASE_URL` is empty or does not start with `postgres`. Keep the dev default key in base only for dev.
- Tests: run a subprocess with each bad environment and assert a non-zero exit with the expected message. Run once with a good environment and assert success.
- Done when: the tests pass and `make deploy-check` (after D6) still works with a dummy postgres URL.

**S6 — Use STORAGES, so hashed static files are active (S)**
- Why: D-STATIC.
- Files: `config/settings/base.py` (line with `STATICFILES_STORAGE`), `config/settings/dev.py`, `config/settings/prod.py`.
- Steps: replace the removed setting with `STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}` in prod. In dev, use `StaticFilesStorage` for staticfiles so runserver does not need collectstatic.
- Tests: under prod settings, `staticfiles_storage` is a manifest storage. The test suite stays on dev settings (pyproject already points there).
- Done when: G-STATIC passes in the gate, and `collectstatic` produces hashed filenames in `STATIC_ROOT`.

**S7 — Move to Django 5.2 LTS (M)**
- Why: D-DJ.
- Precondition: S1–S6 are DONE, so the baseline is stable.
- Steps: check the current 5.2 LTS patch version on the Django download page or via `pip index versions Django`. Update `requirements.txt` to that exact version. Run the full gate. Fix any deprecation or breakage. Record each change in DECISIONS.md.
- Done when: the gate is green on Django 5.2 LTS and `pip show Django` matches the pin.

**S8 — Dependency audit (S)**
- Steps: `pip install pip-audit` into the venv only (it is not added to requirements.txt; record that in DECISIONS.md). Run `pip-audit -r requirements.txt`. Upgrade any runtime package with a known vulnerability to the fixed version, then rerun the gate. Record any exception with a reason.
- Done when: pip-audit reports no unresolved runtime findings.

**S9 — Enquiry email failures are visible (M, includes a migration)**
- Why: D-MAIL.
- Files: `apps/inquiries/models.py` (new field), new migration in `apps/inquiries/migrations/`, `apps/inquiries/views.py`, `templates/agents/dashboard_inquiries.html`, `apps/inquiries/tests/test_email_failure.py`.
- Steps: add `email_sent_at` (nullable DateTimeField) and `email_error` (short text, max 300 characters) to Inquiry. In `_send_enquiry_email`, use `fail_silently=False` inside a try. On success, set `email_sent_at`. On failure, set `email_error`, log with `logger.exception`, and still return the success partial to the visitor. In the agent inquiries table, show a badge "Email not delivered" when `email_error` is set.
- Tests first: mock `send_mail` to raise. Assert the inquiry is saved, `email_error` is set, the visitor gets the success partial, and the dashboard shows the badge.
- Done when: tests pass, `makemigrations --check` is clean after the new migration is created, and no existing migration was edited.

**S10 — Content-Security-Policy and self-hosted map library (M)**
- Why: D-CSP.
- Steps:
  1. Download Leaflet 1.9.4 JS and CSS into `static/vendor/leaflet/`. Record the exact source URL and SHA-256 in DECISIONS.md. Do not add an npm dependency.
  2. Replace the unpkg `<script>` and `<link>` in the listing template with local `{% static %}` references. Keep the Leaflet integrity attributes only if they still match the local file, otherwise remove them.
  3. Add `apps/core/middleware.py` with `ContentSecurityPolicyMiddleware`. Policy: `default-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`. Adjust only if a test shows a real need, and record each adjustment.
  4. Search templates for inline `<script>` blocks and `onclick=`-style handlers. Move them into `static/js/` files, or record in DECISIONS.md why they must stay.
  5. Enable G-CDN in gate.sh.
- Tests: the header is present on a listing page and the home page. The detail page loads no script from an external host (parse the HTML and check).
- Done when: tests pass, G-CDN passes, and the map still renders in the browser (V2).

**S11 — Template and XSS audit (S)**
- Steps: grep templates and Python for `|safe`, `mark_safe`, `format_html`, `autoescape off`, `innerHTML`. For each hit, record in STATUS.md whether the input can contain user- or agent-supplied text. Fix any that can. Keep `static/js/motion.js` innerHTML only if its input is a literal string from the file, and record that.
- Done when: G-SAFE passes with an allowlist that has a written reason beside each entry.

**S12 — Input limits (S)**
- Steps: confirm the enquiry form caps `message` length, and that `name`, `email`, and `phone` have max lengths and validators. Confirm the listing form caps `title` and `description` and that `size_sqm`, `price`, and `bedrooms` reject negatives and absurd values. Add tests for the caps.
- Done when: tests pass and the caps are documented in the test names.

### P2 — Platform, deploy, and parity

**D1 — PostgreSQL driver (S)**
- Why: D-PG.
- Steps: add `psycopg[binary]` pinned to the version that matches Python 3.12 (check PyPI). Add a DECISIONS.md entry. Confirm `settings.DATABASES` picks up `django.contrib.postgres` in prod.
- Done when: `pip install -r requirements.txt` succeeds and the gate is green.

**D2 — Full test run on PostgreSQL (M)**
- Steps: start a local PostgreSQL 15+ (Docker, or the owner's machine). Run `DATABASE_URL=postgres://... python -m pytest -q` with dev settings forced to honor `DATABASE_URL`. Note: dev.py currently forces SQLite. Add a test-only env switch `GABRIEL_TEST_DB_URL` read by a test settings module `config/settings/test_pg.py`, with a DECISIONS.md entry. Fix any failures that are PostgreSQL-specific, such as case sensitivity in filters and ordering of nulls.
- Done when: the suite passes on PostgreSQL. Record the count.
- If the agent has no way to run PostgreSQL, mark BLOCKED-OWNER: ask Brian to run the command and paste the summary.

**D3 — Health check and logging (S)**
- Files: `apps/core/views.py`, `config/urls.py`, `config/settings/prod.py`, new `apps/core/tests/test_health.py`.
- Steps: add `/healthz/` that runs `SELECT 1` and returns `200 ok` or `503 unavailable`. It returns no details. Add `LOGGING` to prod: console handler to stdout, `INFO` for the `apps` loggers, `WARNING` for root. Exclude `/healthz/` from request logging if the logger is noisy.
- Tests: 200 when the DB is up. Mock the DB cursor to raise and assert 503.
- Done when: tests pass.

**D4 — Rewrite DEPLOY.md corrections (M)**
- Files: `DEPLOY.md`, `Makefile`.
- Steps, in order:
  1. Remove the `seed_demo` line from step 6. Add a sentence that production starts empty, and that listings are entered through the agent dashboard or the admin.
  2. Add `python manage.py createcachetable` to step 6 (needed by S3).
  3. In the nginx block, add `proxy_set_header X-Real-IP $remote_addr;` and keep `X-Forwarded-For`. Add the env line `TRUST_X_REAL_IP=True` to the `.env` example (S2).
  4. Add `--timeout 60` to the gunicorn command. Add `ExecStartPre` or a note to run `collectstatic` before restart.
  5. Replace "git pull" with a neutral line: "deploy the tagged release (git tag or archive) you intend to ship." Keep a placeholder for the repo URL.
  6. Add the health check to the monitoring section: `curl -fsS https://<domain>/healthz/`.
  7. Replace the reference to `scripts/backup-db.sh` with the file from task D5.
  8. Add the `.env` keys introduced by this plan to the `.env` example: `TRUST_X_REAL_IP`, `DATABASE_URL`, and `SECURE_SSL_REDIRECT`.
- Done when: every command in DEPLOY.md exists in the repo or in the OS, and every env key used is in `.env.example`. Check this with grep in STATUS.md.

**D5 — Backups and a real restore drill (M)**
- Files: `scripts/backup-db.sh` (new), `Makefile` (`backup-db` target uses the `DB_USER` and `DB_NAME` variables, not hard-coded values), `scripts/restore-drill.sh` (new).
- Steps: `backup-db.sh` writes a gzipped `pg_dump` with a timestamp, reads `DATABASE_URL`, keeps 30 days, and exits non-zero on failure. `restore-drill.sh` restores the newest backup into `gabriel_restore_test`, runs `manage.py check` and `showmigrations` against it, then drops it.
- Done when: the drill succeeds on the PostgreSQL instance from D2, and the output is recorded in STATUS.md.

**D6 — Makefile gate target (S)**
- Steps: add `make gate` that calls `bash scripts/gate.sh`. Keep the existing targets. Remove the placeholder lint target or make it run `python -m pyflakes` only if pyflakes is added to dev tooling with a DECISIONS.md entry.
- Done when: `make gate` exits 0.

### P3 — Data and content

**C1 — Remove unused media (S, needs owner O1 for the demo photos)**
- Steps: write `scripts/list_unused_media.py` that lists files under `media/` and `property-images/` that no `Property`, `PropertyImage`, or `AgencyProfile` row references. Run it. Put the list in STATUS.md. Do not delete anything until Brian confirms (O2). Then move the confirmed files to `../gabriel-media-archive/`, outside the repo. Add a test that every referenced image exists.
- Done when: the referenced-images test passes and the repo has no `test*`, `a_*`, `b_*`, `c_*`, `d_*` junk files.

**C2 — Production starts empty (S)**
- Files: `apps/listings/management/commands/seed_demo.py`, tests.
- Steps: `seed_demo` refuses to run when `DEBUG` is False, unless `--i-know-this-is-demo` is passed. Add a test.
- Done when: the test passes.

**C3 — Inquiry data retention (S)**
- Files: `apps/inquiries/management/commands/purge_inquiries.py` (new), test.
- Steps: the command deletes inquiries older than `--days` (default 365) and prints the count. Owner sets the retention period (O4). Add a DEPLOY.md cron line for it.
- Done when: the command has a test and a dry-run flag.

**C4 — Privacy and Terms text (owner and lawyer, not code)**
- The privacy page must say what enquiry data is collected (name, email, phone, message), why, who receives it (the listing agent), how long it is kept (C3), how to request deletion, and a contact address. Brian arranges a Kenyan lawyer to review it against the Data Protection Act, 2019. The agent does not write legal conclusions. Mark BLOCKED-OWNER until O3 is answered.

### P4 — Operations

**O-a — Logging and alerts (S)**
- Steps: confirm D3 logging works. Document in DEPLOY.md the one command that shows the last hour of errors: `journalctl -u gabriel-homes --since "1 hour ago" -p err`.
- Done when: DEPLOY.md contains it.

**O-b — Admin path (S, optional)**
- Steps: read the admin URL from an env var `ADMIN_URL` with default `admin/`. Test that the default still works. Record in DECISIONS.md.
- Done when: test passes.

### P5 — Verification

**V1 — Coverage and gate (S)**
- Steps: run `pytest --cov=apps/listings --cov=apps/agents --cov=apps/inquiries --cov-report=term-missing -q`. If any app is below 80%, add tests for the uncovered branches. Enable G-COV in gate.sh with the 80% threshold.
- Done when: G-COV passes.

**V2 — Browser QA (harness with a browser, or Brian)**
- If the harness has a headless browser, capture screenshots of the home, search results, listing detail, enquiry success, and agent dashboard at 360, 810 and 1280 px. Keep screenshots out of the repo. Record pass or fail per page in STATUS.md, with notes.
- If not, mark BLOCKED-OWNER and give Brian the checklist in appendix A.
- Done when: every page in appendix A is marked pass or has a logged issue.

**V3 — Load smoke test (S, run on staging)**
- Steps: with `hey` or `ab`, send 20 concurrent requests for 60 seconds to `/` and one listing page on the staging server. Record requests per second, p95 latency, and any non-200 response. Target: no non-200 responses, p95 under 500 ms on the 2 GB VPS. Record the numbers.
- Done when: numbers are recorded and any failures are logged as new tasks.

**V4 — Lighthouse (owner)**
- Brian runs Lighthouse on mobile for the home page and one listing page. Record the four scores. The bar is set by the owner.

### P6 — Launch rehearsal

**R1 — Fresh server rehearsal (M)**
- Steps: on a clean Ubuntu 22.04 or 24.04 VM, follow DEPLOY.md exactly. Log every deviation in STATUS.md as a DEPLOY.md defect. Fix the defects in DEPLOY.md, not in your memory of what it should say.
- Done when: the site answers on the staging hostname over HTTPS, `/healthz/` returns 200, and the deviation list is empty or each item has a fix.

**R2 — Smoke script (S)**
- Files: `scripts/smoke.sh` (new).
- Steps: a bash script that takes `BASE_URL`, requests the URLs from section 1 plus `/healthz/`, and expects 200 for public pages, 302 for `/dashboard/` and `/admin/` when not logged in, and 404 for an unknown listing slug. Exits non-zero on mismatch.
- Done when: it passes against the staging server.

**R3 — Go-live sign-off (owner)**
- Brian ticks every box in section 4. The agent prepares a one-page summary in STATUS.md listing the evidence for each box and the open risks.

### P7 — First week after launch

**L1 — Watch (owner, with agent help if asked)**
- Daily for seven days: check the health endpoint, backup logs, failed-email badges, and error logs. Any new error becomes a task in a new phase, `P8`.

---

## 6. Owner decisions (answer these; the agent cannot)

| ID | Question | Blocks |
|---|---|---|
| O1 | Who owns or licensed `media/demo-photos/` and `property-images/`? If unknown, replace them with owner-supplied photos or neutral placeholders before launch. | C1, C4, go-live |
| O2 | OK to move the unused media listed by C1 out of the repo? | C1 |
| O3 | Lawyer review of privacy and terms text (name the lawyer). | C4, go-live |
| O4 | Inquiry retention period (suggested: 365 days) and who may delete a person's data on request. | C3 |
| O5 | Uptime checker (free service of your choice) and where alerts go. | O4 in section 4 |
| O6 | SMTP provider and credentials for `hello@gabrielhomes.co.ke`. Are SPF and DKIM set on the domain? | S9 test in staging, go-live |
| O7 | VPS provider, Ubuntu version, and DNS for `gabrielhomes.co.ke`. | R1 |
| O8 | Backup destination and credentials (for example B2 or S3). | D5 off-site step |
| O9 | Are agents created manually by admin only? (The plan assumes yes.) | Security review sign-off |
| O10 | Error reporting: logs only at launch (recommended), or add a hosted error tracker later? | O-a |
| O11 | Run PostgreSQL tests (D2) if the agent cannot. | D2 |
| O12 | Run the launcher on a clean machine (S4 manual check). | S4 |

---

## 7. Templates

### docs/STATUS.md (template)

```markdown
# STATUS — Gabriel Homes

Current loop: <number> · Current task: <ID> · Calls used this loop: <n>/30

## Baseline
- Python: <version> · Django: <version> · Tests: <passed count> · Gate: <green/red>

## Tasks
| ID | Status | Loop | Calls | Gate tail (last 5 lines) | Notes |
|---|---|---|---|---|---|
| F1 | DONE | 1 | 6 | ... | |
| S1 | TODO | — | — | — | |

## Out-of-scope needs
- (none)

## Blocked (owner)
- O-<id>: <question> — asked on loop <n>

## Calibration
- Loop 1 averages: S tasks <n> calls, M tasks <n> calls.

## Loop log (newest first, max 300 lines; archive older entries)
### Loop <n> — <date>
- Task <ID>: <what changed, files, test that proves it>
- Gate: <paste last 5 lines>
- Next: <task ID>
```

### Commit message format

`<TASK-ID>: <imperative summary>` for example `S1: escape JSON-LD via json_script`.

---

## 8. Failure modes and how to handle them

| Failure | Sign | Response |
|---|---|---|
| Looping on one error | Same command fails three times | Rule 8 of the brief: BLOCKED-AGENT, record excerpt, move on. |
| Scope creep | Diff touches files outside the task | Revert the extra files. Log OUT-OF-SCOPE NEEDED. |
| False "done" | Status says DONE with no gate output | Reopen the task. The gate tail is mandatory. |
| Context loss between loops | Agent re-discovers the codebase | Improve STATUS.md, not the chat. Next loop reads STATUS first. |
| Burning budget on reads | Many views of large files | Use `grep -n` and line ranges. Never open media or the DB. |
| Migration conflicts | Edited an old migration | Revert it. Create a new migration. |
| Test flakiness on time | Random failures near midnight or timezone | Freeze time in the test. Note it in DECISIONS.md. |
| Manifest static errors in tests | "Missing staticfiles manifest entry" | Tests use dev settings. Only G-STATIC uses prod settings and runs `collectstatic` first. |
| Dependency pulled in silently | requirements.txt changes without a DECISIONS entry | Revert, or record the decision. |
| Visual drift | Pages look generic | Not a code gate. Logged in V2 with screenshots. Fixing it is a new task. |

---

## Appendix A — Owner QA checklist (desktop and a 390 px phone)

1. Home: hero search works; "for sale" and "for rent" links go to the right SEO URLs.
2. `/flats-apartments-for-sale/mombasa/`: results show; filters combine; pagination works; empty state shows for a nonsense filter.
3. A listing: gallery changes image; map shows; the call and WhatsApp buttons open correctly on phone; the sticky bottom bar stays reachable.
4. Enquiry: submit a valid enquiry; success message shows; the email arrives at the agent address (staging); submitting five times in a minute shows the rate-limit message.
5. Save a listing while logged in; it appears under `/account/saved/`.
6. Log in as an agent. Create a listing, upload two photos, set one as cover, publish it. It appears on the public site. Edit another agent's listing URL: you get a 404.
7. Agent dashboard inquiries: an email-failed inquiry shows the badge (staging test with SMTP off).
8. Admin login works. The admin can see all listings.
9. Sign-up and password reset emails arrive.
10. Footer and legal pages load. Privacy page matches the lawyer-reviewed text.
11. Keyboard only: tab through the header and the search form; focus is visible.
12. The page works with JavaScript off for search and listing pages.
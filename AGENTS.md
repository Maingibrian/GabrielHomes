# AGENTS.md — Gabriel Homes repo coordination entry point

Before planning or editing anything, read AGENTS.md and AGENTS-COLLAB.md.
State the rules and traps that apply to this task before you start.

## Reading order
1. `AGENTS-COLLAB.md` — live state: current round, in-flight decisions, latest handoff.
2. This file — stable rules, verification gate, done-when.
3. `.agents/memory/traps.md` — pitfalls that already cost a round.
4. The relevant spec in `specs/active/`, if one exists for your change.
5. Code.

Inside the Django tree, `gabriel-homes-advanced-r64/gabriel-homes/docs/AGENT-BRIEF.md`
is the per-loop working protocol (tool budget, task scoping, gate rule); read it
before working there. `docs/STATUS.md` + `docs/DECISIONS.md` hold loop history;
`LOOP/` holds the design-loop runbook.

## Project structure (one paragraph)
Git root `/home/z/my-project` (branch `main`, remote `Maingibrian/GabrielHomes`).
The Django 5.2 project lives at `gabriel-homes-advanced-r64/gabriel-homes/`:
`config/` (settings base/dev/prod), `apps/` (accounts, agents, core, inquiries,
listings, locations, manage), `templates/`, `static/` (vendored MapLibre),
`media/` (`demo-photos/` is tracked on purpose — see traps), `docs/`, `LOOP/`,
plus management commands (`seed_demo`, `bootstrap_owner`) and `scripts/gate.sh`.
Repo-root `scripts/launch_preview.py` runs the sandbox preview daemon.
`db.sqlite3` and `.venv` are untracked; a sandbox recycle deletes them.

## Non-negotiable rules
1. **Preview chain** — browser → `https://preview-chat-*.space-z.ai` →
   `*.fcapp.run` gateway → caddy `:81` → bridge `:3000` (inside runserver,
   `GABRIEL_PREVIEW_BRIDGE=1`) → runserver `:8000`. The launch script
   (`scripts/launch_preview.py`, repo root) must set
   `CSRF_TRUSTED_ORIGINS=http://127.0.0.1:81,https://*.space-z.ai` and
   `EXTRA_ALLOWED_HOSTS=.space-z.ai,.fcapp.run`. Without the first, every POST
   form 403s (CSRF origin); without the second, every public-URL page 400s
   (DisallowedHost) before any view runs. Verify logins through the **public
   URL**, not just localhost — a localhost-only check once masked the Host bug.
2. **Rate limiting** — never key on raw `X-Forwarded-For` (its first entry is
   client-controlled → bucket rotation). Always
   `apps/core/clientip.py::get_client_ip()`; `X-Real-IP` is trusted only when
   `TRUST_X_REAL_IP=True` (prod).
3. **Sandbox recycle** — the sandbox is wiped between sessions. Everything
   durable (code, docs, coordination files) must be committed AND pushed to
   GitHub before you stop. `db.sqlite3`, `.venv`, `/tmp` pidfiles are
   disposable; the restore recipe is in `.agents/memory/lessons.md`.
4. Never edit an existing migration; add new ones only (AGENT-BRIEF rule 3).
   No new dependencies without a `docs/DECISIONS.md` entry.
5. `seed_demo` refuses to run when `DEBUG=False` unless `--i-know-this-is-demo`;
   sample enquiries need `--with-enquiries` or the portal inbox is silently empty.
6. `media/demo-photos/` stays tracked in git — untracked pools caused the
   "cards are back" regression three times (r57).
7. The platform makes UUID auto-commits (e.g. `a3dd47fe`); do not rewrite
   history — commit on top.

## Verification gate
From `gabriel-homes-advanced-r64/gabriel-homes/`:
```
.venv/bin/python manage.py check                     # 0 issues
.venv/bin/python -m pytest -q 2>&1 | tail -5         # baseline 1102 passed (r90)
bash scripts/gate.sh                                 # must exit 0
```
Live, if the preview is running: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:81/`
→ 200, and a real owner login through the public preview URL.

## Done-when
The verification command has run AND its real output is pasted into your
handoff block in `AGENTS-COLLAB.md` (suite runs also go to
`.agents/reports/test-evidence.md`). No claim of completion without a receipt.
If you could not run something, write NOT RUN and why.

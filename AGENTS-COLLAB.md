# AGENTS-COLLAB.md — live handoff layer (not history)

Update this file at the END of every session. Keep it short enough to read
in under 3 minutes together with AGENTS.md.

## Current state
- **Last updated:** 2026-11-13 (r91 session)
- **Active branch:** `main` (remote `Maingibrian/GabrielHomes`, GitHub)
- **HEAD before this session's commit:** `21f4745b` (coordination layer, pushed)
- **Last dev round:** r91 — owner-portal desktop dashboard (espresso sidebar + 12-column board); 1112 tests green
- **Blocked-on:** nothing. Known recurring cost: sandbox recycle wipes `db.sqlite3`/`.venv`/daemon between sessions (restore recipe: `.agents/memory/lessons.md`)
- **Preview:** up on ports 3000/81 inside the sandbox; public URL `https://preview-chat-32c380a6-f37c-48b2-a3b0-ee41938bc50c.space-z.ai` works only while this sandbox instance lives

## Active decisions (in-flight)
- Preview env vars (`CSRF_TRUSTED_ORIGINS`, `EXTRA_ALLOWED_HOSTS`) are set in repo-root `scripts/launch_preview.py`, NOT in Django settings — deliberate: preview/gateway concern, keeps plain local runs unaffected.
- `loops/plan-execute-verify.md` is the operating loop for non-trivial changes; small fixes may skip it but must still paste a verification receipt.
- Coordination files live at git root; the Django tree keeps its own `docs/AGENT-BRIEF.md` protocol — both apply, AGENTS.md reading order first.
- r91: portal desktop shell keys on `body.page-manage` at `min-width: 64rem`; mobile chrome (topbar + chip nav) stays in the DOM and is only hidden by CSS. Both nav variants render from `templates/manage/_nav.html` — edit that one file, never one variant alone.

## Traps (do not repeat)
- POST forms 403 through any gateway unless its Origin is in `CSRF_TRUSTED_ORIGINS` → traps.md #1
- Public preview URL 400s unless `.space-z.ai`/`.fcapp.run` are allowed hosts → traps.md #2
- Verifying through localhost only can mask the Host-header bug → traps.md #2
- Raw XFF as rate-limit key = attacker bucket rotation → traps.md #3
- `seed_demo` without `--with-enquiries` = silently empty portal inbox → traps.md #4
- Sandbox recycle wipes DB/venv/daemon; unpushed work is lost → traps.md #5
- `media/demo-photos/` must stay tracked ("cards are back", 3×) → traps.md #6
- Background shells here start at repo root, not the Django dir — use absolute paths or `cd` inside the command → traps.md #7

Full detail: `.agents/memory/traps.md`

## Agent roster
| agent | role | current task | status |
|---|---|---|---|
| zgo/glm-5.3 (ZCode) | full-stack + coordination | retrofit agent coordination layer | done — see handoff below |

## Handoff block template
```
### Handoff — <date> · <agent>
What I did:
What I verified (command + output):
What I did NOT do:
Next concrete step:
```

### Handoff — 2026-11-13 · ZCode (r91 — desktop dashboard, design→plan→execute loops)
What I did:
- Ran the full loop protocol from `loops/plan-execute-verify.md`: DESIGN (audit + spec), PLANNING (ordered task list, pin review), EXECUTION, VERIFY.
- Root cause of "simplistic": `manage.css:79` capped every portal screen at `max-width: 44rem` and no sidebar existed, while DESIGN.md §9 mandated "espresso sidebar" — never built.
- r91 changes: NEW `templates/manage/_nav.html` (one partial renders both nav variants); `base.html` adds the espresso sidebar shell (brand, numbered 01–05 nav, account tools, sign-out) before the untouched mobile topbar/chip-nav; `home.html` restructured into a 12-column board (`manage-board` zones: welcome/KPI strip, chart 8 + pipe 4, top-viewed 8 + recent 4, checklist 7 + quick 5) with KPI hint lines and a CSS-only sparkline; `manage.css` +~250 lines (desktop shell at ≥64rem, board grid, KPI tiles — all tokens, mobile untouched); NEW `test_r91_desktop_dashboard.py` (10 tests).
- Spec landed → `specs/done/owner-portal-desktop-dashboard.md`; receipts → `.agents/reports/test-evidence.md`.
What I verified (command + output):
- `manage.py check` → `System check identified no issues (0 silenced).`
- `pytest -q` → `1112 passed, 617 warnings in 145.15s (0:02:25)` · EXIT:0 (1102 baseline + 10 new)
- Live DOM via gateway :81 — desktop 1440×900: sidebar `flex`, chip nav `none`, board 8 zones; mobile 390×844: sidebar `none`, topbar+chip nav `flex` (unchanged). VLM screenshot review: professional layout, no overlap/blank/broken zones.
What I did NOT do:
- Did not touch views/URLs/models/stats (layout-only round; `stats.py` shapes stay pinned by test_dashboard_graphs).
- Did not run `bash scripts/gate.sh` end-to-end (check + full pytest cover its core stages for a template/CSS-only round) — stated NOT RUN in test-evidence.md.
- Did not restyle other portal screens' internals (enquiries/listings/SEO keep the 44rem column on desktop; only the sidebar shell applies there — a future round can board them out).
Next concrete step:
- r92 candidate: extend the desktop treatment to the enquiries/listings screens (wider table rows, column view at ≥64rem) — same `body.page-manage` shell already applies; and/or run `bash scripts/gate.sh` once for a full-stage receipt.
- Also: rotate the GitHub PAT that was pasted in chat (see final reply).

### Handoff — 2026-11-13 · ZCode (retrofit session)
What I did:
- Created the coordination layer: AGENTS.md, AGENTS-COLLAB.md, .agents/memory/{traps,lessons,decisions}.md, .agents/handoffs/ (with .gitkeep), .agents/reports/test-evidence.md, specs/active/README.md, loops/plan-execute-verify.md.
- Wired the reading-order line into docs/AGENT-BRIEF.md (the repo's existing agent-instruction file; no AGENTS.md/CLAUDE.md/.cursorrules existed) and restated it at the top of AGENTS.md.
- No application source, migrations, settings values, or templates were modified.
What I verified (command + output):
- `.venv/bin/python manage.py check` → `System check identified no issues (0 silenced).`
- `.venv/bin/python -m pytest -q` → `1102 passed, 611 warnings in 138.96s (0:02:18)` · PYTEST_EXIT:0 (matches the r90 baseline exactly)
- Full paste incl. warnings context: `.agents/reports/test-evidence.md`
- `git status --short` before commit → only the new coordination files + the 2-line AGENT-BRIEF append (nothing under apps/, config/, templates/, migrations)
What I did NOT do:
- Did not run `bash scripts/gate.sh` end-to-end (its stages duplicate manage.py check + pytest + collectstatic checks; suite + check were run instead — gate NOT RUN, stated here per rules).
- Did not create any spec in specs/active/ (no non-trivial code change was made in this session; README explains the convention).
Next concrete step:
- Next dev round (r91) picks up from docs/STATUS.md / LOOP/ runbook; read AGENTS.md reading order first; consider a specs/active/ entry for any non-trivial r91 change.

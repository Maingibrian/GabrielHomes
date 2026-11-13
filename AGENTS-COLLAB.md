# AGENTS-COLLAB.md — live handoff layer (not history)

Update this file at the END of every session. Keep it short enough to read
in under 3 minutes together with AGENTS.md.

## Current state
- **Last updated:** 2026-11-13
- **Active branch:** `main` (remote `Maingibrian/GabrielHomes`, GitHub)
- **HEAD before this session's commit:** `a3dd47fe` (platform UUID auto-commit; last dev commits: `33018bba`, `914d257a` preview fixes on top of r90 `19f67359`)
- **Last dev round:** r90 — backend reassessment (owner portal usability); 1102 tests green at that commit
- **Blocked-on:** nothing. Known recurring cost: sandbox recycle wipes `db.sqlite3`/`.venv`/daemon between sessions (restore recipe: `.agents/memory/lessons.md`)
- **Preview:** up on ports 3000/81 inside the sandbox; public URL `https://preview-chat-32c380a6-f37c-48b2-a3b0-ee41938bc50c.space-z.ai` works only while this sandbox instance lives

## Active decisions (in-flight)
- Preview env vars (`CSRF_TRUSTED_ORIGINS`, `EXTRA_ALLOWED_HOSTS`) are set in repo-root `scripts/launch_preview.py`, NOT in Django settings — deliberate: preview/gateway concern, keeps plain local runs unaffected.
- `loops/plan-execute-verify.md` is the operating loop for non-trivial changes; small fixes may skip it but must still paste a verification receipt.
- Coordination files live at git root; the Django tree keeps its own `docs/AGENT-BRIEF.md` protocol — both apply, AGENTS.md reading order first.

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

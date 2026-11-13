# specs/active/ — one spec per non-trivial change

Convention: before starting any non-trivial change (anything that will take more
than a trivial fix, or that touches multiple files), create
`specs/active/<name>.md` here containing:

- **Goal** — one paragraph, what and why.
- **Scope** — files/areas that will change (and explicit non-goals).
- **Acceptance criteria** — binary, checkable statements.
- **Done-when** — the exact verification command(s) whose green output proves
  it, matching the AGENTS.md verification gate (`manage.py check`, `pytest -q`,
  `bash scripts/gate.sh` where applicable).

Move the spec to `specs/done/` (create it) when the change lands, or delete it
if abandoned (record why in `.agents/memory/decisions.md`).

No specs are active right now. The last landed work is r90 (backend
reassessment, commit `19f67359`); its record lives in the Django tree's
`docs/STATUS.md` / `docs/DECISIONS.md`, which remain the canonical per-round
history.

# plan-execute-verify — the operating loop for non-trivial changes

## Goal
Ship each non-trivial change as: a written plan → execution → verified outcome,
with a pasted receipt. No step is "done" because it looks done; it is done when
the verification gate output says so (AGENTS.md "Done-when").

## Steps
1. **Plan.** Read AGENTS.md + AGENTS-COLLAB.md + traps.md. State the rules and
   traps that apply. Write `specs/active/<name>.md` (goal, scope, acceptance
   criteria, done-when). If no plan survives contact with the code, stop and
   rewrite the plan before touching anything.
2. **Execute.** Smallest change that satisfies the spec. Follow AGENT-BRIEF
   hard rules (no out-of-scope edits, failing test first for security fixes,
   never edit migrations, no new deps without a DECISIONS entry).
3. **Verify.** Run the gate: `manage.py check`, `pytest -q`, `bash scripts/gate.sh`
   (from the Django dir). Paste the real tail into the handoff and
   `.agents/reports/test-evidence.md`. NOT RUN must be stated explicitly.
4. **Record.** Update AGENTS-COLLAB.md (current state, decisions, traps if a
   new one was found, handoff block). New trap found → append to traps.md.
5. **Persist.** Commit and push to GitHub before stopping (sandbox recycle
   destroys unpushed work).

## Max iterations
5 per task. An iteration = one plan→execute→verify pass.

## Stop conditions
- No measurable progress in 2 consecutive iterations (same failure, or output
  unchanged) — stop, reassess the plan itself.
- A new trap invalidates the plan's assumptions — stop, write the trap into
  traps.md, rewrite the plan (counts as a new task).

## Escalation
Set `task:blocked` in AGENTS-COLLAB.md ("Current state" → Blocked-on), write
the blocker in a handoff block (what was attempted, exact error, what is
needed), and stop. Do not burn iterations guessing.

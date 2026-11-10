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

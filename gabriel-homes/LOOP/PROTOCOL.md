# PROTOCOL.md — design-loop operating rules (condensed)

Condensed from LOOP/SCHEDULED-TASK.md §2-§6 so any run can follow the rules without
the original prompt. The runbook remains the authoritative text.

## Start of every run (in order)
1. Read PROTOCOL.md, STATE.md, SCORECARD.md, LOCKS.md, the last 5 JOURNAL entries,
   and any NOTES/<ID>.md for items you might take.
2. Run the baseline gates (`manage.py check`, `makemigrations --check --dry-run`,
   `pytest -q`) and record the REAL results. Red gates ⇒ your role is REPAIR:
   fix that first, nothing else.
3. Read the previous run's "FOR THE NEXT RUN" line; do it unless already locked.
4. Choose a role, claim the item in LOCKS.md, then work.

## Roles (first that applies)
- **REPAIR** — gates red at start.
- **PLANNER** — SCORECARD.md missing (that run is PLAN-ONLY, no code), or run
  number multiple of 5 (retrospective: read last 5 journal entries, re-weight,
  split stuck items, add new, prune duplicates, log reasoning).
- **AUDITOR** — any item READY-FOR-AUDIT not built by you. Re-run gates, re-read
  code, grade from scratch WITHOUT seeing the builder's scores first; record both
  scores, lower wins; promote to MET-T1/T2 or demote naming the exact failing
  checks. Max 3 audits per run.
- **BUILDER** — otherwise. Highest-priority unblocked item. A builder may only
  move an item to READY-FOR-AUDIT, never to MET.
- **WATCH** — the run after every retrospective. Re-verify gates, spot-check ~20%
  of MET items (deterministic pick by run number), token-drift check via the F1
  test. Any failure ⇒ item REGRESSED.

## Locks
Before editing, append `ITEM | run-id | claimed-at | expires-at (claim + 45 min)`
to LOOP/LOCKS.md and re-read the file. A live lock on the same item or file ⇒ pick
a different item. Release your lock at run end. Hotspot files (home.html, home.css,
search.css, motion.js, base.html): re-read right before editing, keep edits small,
never rewrite a whole hotspot file.

## Self-grading
Score 0-4 per dimension D1-D8 (see RUBRIC.md). Evidence tiers E1/E2/E3. No evidence
⇒ capped at 2; D2/D3/D6 without E3 ⇒ capped at 3, tagged visual-unverified, batched
into ONE OWNER_NEEDS line. MET-T1 = all applicable dimensions ≥3 + all binary checks
pass + gates green + audited by a different run. MET-T2 = same at 4. Statuses:
TODO, WIP, READY-FOR-AUDIT, MET-T1, MET-T2, REGRESSED, BLOCKED.

## Priority
`priority = weight × (target − current) × (1 + 0.5 × failed_attempts) + 1 per 3
runs untouched`. REGRESSED counts double. Skip items whose `needs` are not MET-T1
or READY-FOR-AUDIT. MET items are FROZEN (edit only for regression).
Failed attempt (audit demote or red gates) ⇒ attempts+1 + NOTES/<ID>.md root-cause
note; next builder reads it and tries a different approach. At 3 attempts
decompose into ID.a/ID.b; at 5 attempts BLOCKED + one OWNER_NEEDS line.
Once MET-T1 share ≥ 50%: builders take ONE item deeply, checking neighbouring MET
items for conflicts. All MET-T1 ⇒ planner raises top-weight items to Tier 2.
All MET-T2/BLOCKED ⇒ STEADY STATE: only WATCH works; other runs journal
"steady state: nothing to do" and stop. Do not churn.

## Non-negotiables (always)
No Framer runtime; no copying buyrentkenya.com text/images/markup. No invented
data; demo data stays labelled; record gate results exactly. Only tokens.css
values (new colour/font/radius/size ⇒ DECISIONS entry). CSP stays strict
(script-src 'self'); vendored libs self-hosted, pinned SRI when tag-loaded, no
sourceMappingURL, test-covered. Every effect respects prefers-reduced-motion and
works with JS blocked (D-MOTION-SAFE). Views stay thin; no out-of-scope refactors
without logging why. Gates must end green; test count never goes down (baseline
518). Docs are part of done: no READY-FOR-AUDIT without SCORECARD row, JOURNAL
entry and any DECISIONS entry.

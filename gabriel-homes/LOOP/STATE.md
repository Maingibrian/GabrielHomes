# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 15
- **Run type:** PLANNER (plan-only, no code) — SCORECARD.md did not exist, so per
  protocol §3b this run built the team framework. Role ladder: gates were green,
  no item READY-FOR-AUDIT, planner rule fired first.
- **Timestamp:** 2026-11-05 ~08:52 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md (verbatim runbook; PROTOCOL.md = condensed
  §2-§6; RUBRIC.md = §4). Cron note said "last was r13" but STATE.md said 14 →
  this is r15 (D-LOOP-15c).

## Gates (real results)
| Gate | Start of run | End of run |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **518 passed** (86.0s) | **518 passed** (plan-only; no code touched) |

## What this run created (LOOP/)
PROTOCOL.md (condensed §2-§6) · RUBRIC.md (D1-D8, E1-E3, caps, MET-T1/T2) ·
SCORECARD.md (17 seed items F1-F5/H1-H4/G1-G4/L1-L4 + cross-cutting Q1-Q4, each
with binary checks + proving-test spec; initial priorities computed) · LOCKS.md ·
JOURNAL.md (r15 entry). Existing STATE/BACKLOG/OWNER_NEEDS/docs/DECISIONS kept in
use; docs/DESIGN-ADDENDUM.md arrives with item F4.

## Backlog reconciliation (D-LOOP-15a)
The pre-loop cadence said "run 15 = P2-3 (SiteContent model)". The design-loop
runbook now defines the work items; P2-3..P6 stay live in BACKLOG.md and are
re-weighted at the r20 retrospective (owner may re-prioritise the portal slices).

## Item states
All 17 items TODO (self-score —, attempts 0, last-touched r15). Unblocked leaders
by priority: F1 15, F2 15, H1 15, L1 15. F2 unblocks 7 items (F5,H2,H3,G1,G2,G3,G4);
F1 also feeds L2 (pin font) and every token-touching item.

## Next slice
**Run 16 = BUILDER: F2 (capability gate)** — static/js/fx-gate.js setting
html[data-fx] ∈ {rich,lite,none}, every-effect-keys-off-data-fx contract, decision-
table proving test test_f2_capability_gate.py (test count must rise above 518).
Then F1 (token-integrity ratchet) if time remains in the box.

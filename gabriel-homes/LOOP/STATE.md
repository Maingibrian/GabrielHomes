# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 21 (next) — r20 completed
- **Run type r20:** PLANNER→AUDITOR — retrospective over r15–r19
  (D-LOOP-20a..e); H3 audited MET-T1 (21/21 E3 checks).
- **Timestamp:** 2026-11-05 ~14:14 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed rules LOOP/PROTOCOL.md;
  rubric LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | End |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **556 passed** | **556 passed** (docs+audit only) |

Ratchets (F1): sub-13px 44, hex 236 — held (survey re-run; SCORECARD line
corrected from stale "44/238").

## Shipped this run
- **Retrospective (docs-only):** priorities recomputed with the untouched
  bonus (+1): L1 16 · G2 16 · F3 13 · F4 13 · G1/L2/L3 13 · F5/H4 10;
  H2/G3/G4/L4 needs-blocked. Build order fixed: r21 WATCH overlay + F3
  (folds HYG-1) → r22 G2 → L1. H2 pre-split H2.a structure / H2.b motion.
  BACKLOG P4-1→H2, HYG-1→F3, P5-3→Q2; P4-4 needs a DECISIONS-FIRST rule
  before touching home's frozen section order.
- **H3 → MET-T1** (audit): 5/5 proving tests + new Playwright E3 suite
  scripts/r20_e3_h3_audit.py — 21/21: snap rail computed styles (82%/88%),
  scrollable, bento-shift NOT live at 390px, keyboard walk 0→1470 over all
  7 cards, reduced-motion kills the grow animation, JS-blocked context
  still flex+scrollable+visible, desktop rich+fine stays grid + is-live.
  Screenshots LOOP/audit-screens/r20-e3-h3-*.png.

## Item states (SCORECARD)
MET-T1: F1, F2, H1, H3 (4/17 = 24%). READY-FOR-AUDIT: none. TODO: 13.
Unblocked leaders: L1 (16), G2 (16), F3 (13), F4 (13), G1/L2/L3 (13).

## Next slice
**Run 21 = WATCH overlay first (D-LOOP-20e):** gates re-verify +
deterministic MET spot-check (21 mod 4 = 1 → **F2** from sorted
[F1,F2,H1,H3]: re-run test_f2_capability_gate.py, confirm
LOOP/audit-screens/r17-e3-*.png exist) + mandatory F1 drift test
(survey expects 44/236). Any failure ⇒ REGRESSED, pre-empts the build.
**Then BUILDER F3** (image & video diet, 13; folds HYG-1 dead home.css
purge; static/ baseline table FIRST; hero-loop.mp4 gated fx=rich &&
!Save-Data with poster or documented removal). Suite must stay ≥ 556.

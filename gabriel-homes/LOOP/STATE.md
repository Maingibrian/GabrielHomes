# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 23 (next) — r22 completed
- **Run type r22:** AUDITOR→BUILDER — F3 audited → MET-T1 (sub-13px
  expectation corrected 44→43, D-LOOP-22a); G2 built → READY-FOR-AUDIT.
- **Timestamp:** 2026-11-05 ~15:55 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed rules LOOP/PROTOCOL.md;
  rubric LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | End |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **562 passed** | **569 passed** |

Ratchets: sub-13px **43** (corrected expectation — HYG-1 carried one
sub-13px line out after the r21 WATCH count; ceiling constant stays 44),
hex **217 held**, image bytes **4,185,045 exact held**.

## Shipped this run
- **F3 → MET-T1** (audited r22): 6/6 tests, independent byte walk exact,
  width/height 12/12 incl. multi-line tag, E3 smoke re-run 13/13.
- **G2 → READY-FOR-AUDIT**: CSS-only shared-element transitions —
  @view-transition inside @supports (CSSOM-verified in Chromium),
  fail-closed `html { view-transition-name: none }` re-enabled only under
  fx=rich|lite, inline-name override for no-gate/fx=none; prop-<pk> names
  on search rows, 4 home market cards, detail hero (both branches);
  _listing_card unnamed (detail duplicates trap); HTMX partial carries
  names. E3 14/14 (scripts/r22_e3_g2_audit.py; r22-e3-g2-{lite,none}.png).
- Queue note: HYG-2 = delete orphaned _home_property_card.html (BACKLOG).

## Item states (SCORECARD)
MET-T1: F1, F2, F3, H1, H3 (5/18 = 28%). READY-FOR-AUDIT: G2. TODO: 12.
Unblocked leaders: L1 (16), H2 (16 — slice H2.a structure per D-LOOP-20b),
F4 (13), G1/L2/L3 (13). L4 unblocked once G2 audits clean.

## Next slice
**Run 23 = AUDITOR first**: audit G2 (mechanical — re-run gates,
7/7 test_g2_view_transitions.py, re-run scripts/r22_e3_g2_audit.py expect
PASS, re-read D-LOOP-22b). **Then BUILDER L1** (map & list sync, 16 —
two-way highlight, keyboard, aria-live count, Map pill; owner layout kept)
— or the H2.a structure slice (D-LOOP-20b) if L1 looks too big for one box.
Suite must stay ≥ 569.

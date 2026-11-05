# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 24 (next) — r23 completed
- **Run type r23:** AUDITOR→BUILDER — G2 audited → MET-T1; L1 built →
  READY-FOR-AUDIT (two-way highlight, oob aria-live count, Map pill).
- **Timestamp:** 2026-11-05 ~16:45 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed rules LOOP/PROTOCOL.md;
  rubric LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | End |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **569 passed** | **581 passed** |

Ratchets: sub-13px **43**, hex **217**, image bytes **4,185,045** — all
held (no hex added; rgba pulses are F1-exempt per existing precedent).

## Shipped this run
- **G2 → MET-T1** (audited r23): 7/7 tests, E3 14/14 re-run, D-LOOP-22b.
- **L1 → READY-FOR-AUDIT**: rows `id=listing-row-<pk>` + `data-listing-pk`;
  map JSON gains `id`; search-map.js delegated row→pin `.is-hot`, pin→row
  scroll + `.is-flashed` (behaviour reads html[data-fx]); Map pill via
  IntersectionObserver (hidden in markup, focus returns to tabindex=-1
  map); `#results-count` aria-live=polite + HTMX partial re-sends it
  `hx-swap-oob` (count was stale on filter swaps — fixed). E3 15/15 with
  live tiles (scripts/r23_e3_l1_audit.py; r23-e3-l1-{map,flash}.png).
  Focus rule: the maplibre popup owns focus after pin click (D-LOOP-23a).

## Item states (SCORECARD)
MET-T1: F1, F2, F3, G2, H1, H3 (6/18 = 33%). READY-FOR-AUDIT: L1.
TODO: 11. Unblocked leaders: F4 (13, unblocks G3+G4), H2.a slice (16,
D-LOOP-20b), G1/L2/L3 (13). L4 unblocked (G2 MET).

## Next slice
**Run 24 = AUDITOR first**: audit L1 (mechanical — re-run gates,
12/12 test_l1_map_list_sync.py, re-run scripts/r23_e3_l1_audit.py expect
PASS — live tiles ARE reachable from this sandbox, re-read D-LOOP-23a).
**Then BUILDER F4** (motion vocabulary, 13 — docs/DESIGN-ADDENDUM.md ≤6
effects + archetypes; map shipped effects incl. the G2 pair + L1
flash/scroll; unblocks G3+G4) — or the H2.a structure slice (D-LOOP-20b)
if the addendum looks too small for one box. Suite must stay ≥ 581.

# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 27 (next) — r26 completed
- **Run type r26:** AUDITOR→BUILDER — F4 audited MET-T1 (with an in-audit
  coverage correction, D-LOOP-26a); L2 built → READY-FOR-AUDIT
  (basemap palette recolour, D-LOOP-26b).
- **Timestamp:** 2026-11-05 ~21:15 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed LOOP/PROTOCOL.md; rubric
  LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | End |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **597 passed** | **603 passed** (+6 L2) |

Ratchets: sub-13px **43**, hex **215**, image bytes **4,191,687** — all
held (JS reads tokens at runtime; no CSS hex, no image changes).

## Shipped this run
- **AUDIT F4 → MET-T1**: 7/7 tests; exhaustive effect hunt (9 keyframes +
  JS surfaces) found 2 unmapped hooks — fixed in-audit (gallery-count-bump
  → M5; manage-card-in declared portal-scoped; SHIPPED_TOKENS tightened);
  archetypes verified rendering (D-LOOP-26a).
- **BUILDER L2 → READY-FOR-AUDIT**: test_l2_basemap_palette.py FIRST
  (6 tests, red 4); search-map.js ordered rule list applied in the map
  load handler — first-match-wins per paint property, getLayer + try/catch
  guards (missing ids never fatal), colours read at RUNTIME from
  tokens.css (--paper land, --sand water, --cream roads, --taupe labels),
  zero hex. E3 r26_e3_l2.py **7/7 with live tiles**: zero console errors,
  L1 sync intact, vintage-atlas Mombasa verified visually
  (r26-e3-l2-map-region.png). D-LOOP-26b.

## Item states (SCORECARD)
MET-T1: F1, F2, F3, F4, H1, H3, G2, L1 (8/18 = 44%) + H2 (a-slice MET).
READY-FOR-AUDIT: L2. TODO: 9 (leaders: G1 13, L3 13; G3/G4 unblocked).

## Next slice
**Run 27 = AUDITOR**: audit L2 (6/6 test_l2_basemap_palette.py, re-run
scripts/r26_e3_l2.py expect PASS, re-read D-LOOP-26b, eyeball the map
screenshot). Then **BUILDER G1** (floating pill nav, 13 — hide/return on
scroll under fx lite+rich, full nav from 1024px, mobile-menu inline styles
→ CSS, Escape closes, skip link) or L3 (row conversion, 13). Suite ≥ 603.

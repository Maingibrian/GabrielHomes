# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 29 (next) — r28 completed
- **Run type r28:** AUDITOR→BUILDER — G1 audited MET-T1 (from scratch,
  zero gaps, aud=self); L3 built → READY-FOR-AUDIT (row conversion &
  density).
- **Timestamp:** 2026-11-05 ~23:15 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed LOOP/PROTOCOL.md; rubric
  LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | End |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **609 passed** | **615 passed** (+6 L3) |

Ratchets: sub-13px **43**, hex **215**, image bytes **4,191,687** — all
held (no new px font-sizes, no new hex; WhatsApp icon is currentColor).

## Shipped this run
- **AUDIT G1 → MET-T1**: 6/6 tests; E3 r27_e3_g1.py re-run **10/10**
  (hide/return + focusin, fx=none never hides, JS-blocked visible);
  D-LOOP-27a verified line-by-line; 1280px visible/hidden screenshots
  eyeballed. aud=self 3,3,3,4,4,3,4,4.
- **BUILDER L3 → READY-FOR-AUDIT**: test_l3_row_density.py FIRST (6, red
  3); WhatsApp = ink primary pill + original inline SVG (brand→agent
  fallback unchanged, wa.me prefills title), Call/Email secondary
  outlines, View → quiet link; truncatewords 34→28; row height 500 fixed
  → auto / min-height 320; padding + h2 clamps tightened. E3 smoke:
  row renders 445px content-driven, hierarchy correct, zero errors
  (r28-l3-row.png).

## Item states (SCORECARD)
MET-T1: F1, F2, F3, F4, H1, H3, G1, G2, L1, L2 (**10/18 = 56%**) + H2
(a-slice). READY-FOR-AUDIT: L3. TODO: 7 (F5/H4 10; G3 unblocked).

## Next slice
**Run 29 = AUDITOR**: audit L3 (6/6 test_l3_row_density.py, re-render a
search page — check the WhatsApp>Call/Email>View hierarchy + row height
yourself, verify brand-channel logic unchanged, eyeball r28-l3-row.png).
Then **BUILDER F5** (Lenis, 10 — vendor under hygiene rules, fx=rich
only, off touch, replaces the scrollIntoView hack) or H4 (archetype
tags, 10). Suite ≥ 615.

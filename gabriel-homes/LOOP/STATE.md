# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 35 (next) — r34 completed
- **Run type r34:** AUDITOR→BUILDER — H2.b audited → H2 full MET-T1
  (a-slice r25 + b-slice r34, zero gaps); G4 built → READY-FOR-AUDIT
  (cursor-view bubble + magnetic CTAs; D-LOOP-34a).
- **Timestamp:** 2026-11-06 ~04:55 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md (+ PROTOCOL/RUBRIC/SCORECARD).

## Gates (real results)
`manage.py check` OK · `makemigrations --check --dry-run` OK · pytest
**648 → 655 passed** (+7 G4; F1 re-pinned constants re-verified 8/8).
Ratchets: sub-13px **43** (constant re-pinned to the r22-recorded count),
hex **211** (legitimate drop — the r34 dead-tail repair removed 3 hex
literals; re-pinned per D-LOOP-30c precedent), image bytes **4,191,687** —
held.

## Shipped this run
- **AUDIT H2.b → H2 full MET-T1**: 10/10 + E3 r33_e3_h2b.py 18/18 (fresh
  server) + D-LOOP-33a verified line-by-line + rich-hero screenshot —
  zero gaps.
- **BUILDER G4 → READY-FOR-AUDIT**: cursor "View" bubble (JS-built,
  aria-hidden, transform-positioned) on .listing-row + .nearby-card;
  magnetic primary CTAs (hero submit, header Enquire, detail WhatsApp)
  clamped ±8px; gate = fx=rich AND (pointer: fine) AND (hover: hover);
  keyboard never triggers it; bento excluded (M4 owns that pointer).
  cursor-view → M5 confirm, magnetic → M6 invite (cap 6 intact).
  test_g4_pointer_polish.py **7/7**; E3 r34_e3_g4.py **18/18**;
  both screenshots eyeballed.
- **Latent defect repaired (D-LOOP-34a)**: components.css ended in a dead
  rule fragment (orphan declarations + stray `}`, pre-existing in HEAD);
  after the G4 append the browser dropped the following rule — diagnosed
  via in-browser brace balance (276/277); dead text removed → hex 214→211.

## Item states (SCORECARD)
MET-T1: F1, F2, F3, F4, F5, H1, H2, H3, H4, G1, G2, G3, L1, L2, L3, L4
(**16/18 = 89%**). READY-FOR-AUDIT: G4. TODO: none. (+ Q1-Q4 WATCH rows.)

## Next slice
**Run 35 = AUDITOR**: audit G4 (7/7 test_g4_pointer_polish.py, re-run
scripts/r34_e3_g4.py expect ALL PASS, re-read D-LOOP-34a, eyeball
r34-g4-row-cursor.png + r34-g4-magnet.png). Then **PLANNER retrospective**
(r35 is a multiple of 5): re-weight/split/add/prune; if G4 passes, every
work item is MET-T1 → raise the top-weight items to Tier 2 per §5 and log
it. Suite ≥ 655. OPS: pkill any 8765 server before starting a fresh one
(stale-template trap); E3 needs scroll_into_view for below-fold targets and
.lower() on uppercase-transform text.

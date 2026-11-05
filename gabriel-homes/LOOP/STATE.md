# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 22 (next) — r21 completed
- **Run type r21:** WATCH→BUILDER — WATCH overlay clean (F2 spot-check 22/22,
  r17 E3 artifacts present, F1 drift held); F3 built → READY-FOR-AUDIT.
- **Timestamp:** 2026-11-05 ~14:45 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed rules LOOP/PROTOCOL.md;
  rubric LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | End |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **556 passed** | **562 passed** |

Ratchets: hex **236 → 217** (HYG-1 dead rules carried 19; F1 HEX_BASELINE
240→217 with history), sub-13px **44 held**, static image bytes
6,161,625 → **4,185,045** (new exact ratchet; zero images >250KB).

## Shipped this run
- **F3 → READY-FOR-AUDIT**: market-filter cards → 900px WebP q82 +
  width/height (660→146KB worst); hero slides 1–4 → WebP q85 native
  (preload/LCP kept); seed-source stock re-encoded JPEG in place (seed
  scripts copy them at seed time); 7 JPGs deleted after ref updates;
  hero-loop.mp4 deferred to H2 via contract test (D-LOOP-21a);
  HYG-1 purge executed (home.css 1461→1342 lines; boundary rule: a rule
  dies when ANY hv2 token is template-absent). E3 smoke 13/13
  (scripts/r21_render_smoke.py; r21-{home,search}-after-diet.png).
- WATCH overlay clean per D-LOOP-20e (no REGRESSED).

## Item states (SCORECARD)
MET-T1: F1, F2, H1, H3 (4/17 = 24%). READY-FOR-AUDIT: F3. TODO: 12.
Unblocked leaders: L1 (16), G2 (16), H2 (16, needs F2 ✓+F3 built),
F4 (13), G1/L2/L3 (13).

## Next slice
**Run 22 = AUDITOR first**: audit F3 (mechanical — re-run gates, 6/6
test_f3_media_diet.py, scripts/f1_token_survey.py expect 44/217, re-run
scripts/r21_render_smoke.py expect PASS; check the seed-source re-encode
rationale in D-LOOP-21b). **Then BUILDER G2** (shared-element
transitions, 16, unblocks L4; test_g2_view_transitions.py first) — or
H2.a structure slice only (D-LOOP-20b) if G2 looks too big for one box.
Suite must stay ≥ 562.

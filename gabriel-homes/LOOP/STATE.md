# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 17
- **Run type:** AUDITOR→BUILDER — F2 audited MET-T1 (E3 browser evidence);
  F1 token integrity built and left READY-FOR-AUDIT.
- **Timestamp:** 2026-11-05 ~11:58 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed rules LOOP/PROTOCOL.md;
  rubric LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | End |
|---|---|---|
| `manage.py check` | OK — 0 issues | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | **532 passed** | **540 passed** |

Ratchets (F1): hard-coded hex outside tokens.css 240 → **238**; sub-13px
font sizes **44** (allowlisted, may only go down). Survey tool:
scripts/r17_f1_survey.py.

## Shipped this run
- **F2 → MET-T1** (audit): decision table, wiring and fail-closed behaviour
  now ALSO verified in a real browser (Playwright, scripts/r17_e3_fx_audit.py):
  reduced-motion ⇒ fx=none + all 57 reveals instant + bento off; gate blocked
  ⇒ attribute null (fail-closed); rich+fine ⇒ bento is-live. Screenshots in
  LOOP/audit-screens/r17-e3-*.png. Frozen; WATCH spot-checks only.
- **F1 → READY-FOR-AUDIT**: test_f1_token_integrity.py (8 tests) written
  first, then: price-pin font var(--font-body)→var(--font-sans) (r13 finding
  confirmed — undefined var silently killed the declaration), detail.css
  font-body fallback removed, --paper defined in tokens.css (#f3eee6, was an
  inline-fallback-only token), both --paper fallbacks removed, 13px-floor
  allowlist (12 pairs, reasons) + hex/sub-floor ratchets recorded.

## Item states (SCORECARD)
MET-T1: F2. READY-FOR-AUDIT: F1. All other 15 items TODO. Next-highest
unblocked priorities: H1 (15, biggest user-visible), L1 (15), then F3 (12),
F4 (12). F5/G1/H2/H3/G2/G3/G4 unblocked by F2 or waiting on F3/F4.

## Next slice
**Run 18 = AUDITOR first (F1 — mechanical: gates + scripts/r17_f1_survey.py,
expect 44/238 and 8/8 F1 tests), then BUILDER: H1** (home order & diet;
test_h1_home_order.py defines the target id order first; moved sections need
destination checks — nothing silently deleted). L1 is the fallback if H1 is
too big for one time-box. Suite must stay ≥ 540.

# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 16
- **Run type:** BUILDER — F2 (capability gate) built and left READY-FOR-AUDIT.
  One failed attempt mid-run (gates red; root cause + fix in NOTES/F2.md).
- **Timestamp:** 2026-11-05 ~09:58 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed rules LOOP/PROTOCOL.md;
  rubric LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | Mid-run | End |
|---|---|---|---|
| `manage.py check` | OK — 0 issues | — | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | — | OK — no changes |
| `pytest -q` | **518 passed** | **12 failed** / 520 (template-comment leak) | **532 passed** |

## F2 shipped (READY-FOR-AUDIT, self 3,n/a,n/a,3,3,n/a,3,3 · E2 · attempts 1)
- **static/js/fx-gate.js** (new, ~1.6KB, deferred): sets html[data-fx]
  ∈ {rich, lite, none} — reduced-motion ⇒ none; Save-Data / ≤4 cores / ≤4 GB
  ⇒ lite; else rich — plus html[data-fine] on (hover:hover)(pointer:fine).
- **motion.js / bento-shift.js**: all capability checks now read the gate;
  prefers-reduced-motion appears ONLY in fx-gate.js (pytest-pinned). Missing
  attribute fails closed to "none". Bento shape-shift = rich + fine pointer
  only; under fx=none it never runs (runbook: "no effect runs under none").
- **base.html**: gate loaded OUTSIDE {% block scripts %} (child overrides
  cannot drop it), before motion.js; <html> carries no hardcoded data-fx.
- **Proving tests**: apps/core/tests/test_f2_capability_gate.py (14) —
  decision-table mirror, single-source-of-truth scan, wiring order, fail-closed,
  no hardcoded gate attrs. Plus Node execution of the real computeFx: 10/10
  cases (manual harness; see NOTES/F2.md — not part of pytest).

## Decisions
docs/DECISIONS.md → Loop 16: D-LOOP-16a (gate = single decision point),
16b (fail-closed both ways), 16c (bento under none/lite = off entirely).
Failed attempt 1 documented in LOOP/NOTES/F2.md (multi-line {#…#} template
comment leak — one-line rule for template comments).

## Item states (SCORECARD)
F2 READY-FOR-AUDIT (needs a DIFFERENT run's audit to reach MET-T1). All other
16 items TODO. Next-highest unblocked priority: F1 (15), then H1 (15), L1 (15).

## Next slice
**Run 17 = AUDITOR first (F2), then BUILDER: F1.** Audit F2 per §3c (re-run
gates, grade from scratch without reading r16's self-scores, lower score wins;
open E3 step = forced data-fx browser check). Then build F1: token-integrity
ratchet test first, then --font-body→--font-sans, --paper definition, 13px
font floor allowlist, hard-coded hex baseline. Test count must stay ≥ 532.

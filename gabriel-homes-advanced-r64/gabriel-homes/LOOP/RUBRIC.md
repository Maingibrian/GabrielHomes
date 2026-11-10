# RUBRIC.md — Gabriel Homes design-loop grading rubric

Source of truth: LOOP/SCHEDULED-TASK.md §4. Nobody may change the rubric to raise a
score; rubric changes require a docs/DECISIONS.md entry.

## Dimensions (score 0-4 each)

| D | Dimension | What it measures |
|---|---|---|
| D1 | Brief & token fidelity | Matches BRIEF.md + tokens.css; no invented values |
| D2 | Visual craft | Typography, spacing, alignment, restraint |
| D3 | Motion | Purposeful, restrained; maps to the addendum vocabulary |
| D4 | Performance | Budgets, weight, CLS, deferred JS |
| D5 | Accessibility | Contrast, focus, keyboard, aria |
| D6 | Mobile | Works and reads well at small widths |
| D7 | Resilience | Works with JS blocked and under fx=none |
| D8 | Tests & docs | Proving test exists; SCORECARD/JOURNAL/DECISIONS current |

Scale: **0** absent · **1** broken or partial · **2** works but generic / has gaps ·
**3** meets the benchmark (Tier 1) · **4** exemplary (Tier 2).

## Evidence tiers

- **E1** read the code
- **E2** test, gate or measurement
- **E3** rendered (screenshot or real browser)

## Caps (hard rules)

- A score with no evidence is capped at **2**.
- D2, D3, D6 without E3 are capped at **3** and tagged `visual-unverified`.
  Such items can still reach MET-T1, but they are batched into ONE OWNER_NEEDS.md
  line ("Please eyeball these pages on your phone: ...").

## Promotion thresholds

- **MET-T1** — every applicable dimension ≥ 3, every binary check passes, gates
  green, and a **different** run audited it.
- **MET-T2** — the same, at **4** for the applicable dimensions.

## Statuses

TODO · WIP · READY-FOR-AUDIT · MET-T1 · MET-T2 · REGRESSED · BLOCKED

## Cross-cutting (graded by WATCH, enforced on every item)

Q1 performance budget · Q2 accessibility · Q3 resilience · Q4 docs — see SCORECARD.

# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 36 (next) — r35 completed
- **Run type r35:** AUDITOR→PLANNER (+WATCH overlay) — G4 audited MET-T1
  (**all 17 work items now MET-T1**); WATCH spot-check F5 clean; retro
  raised the six weight-5 items to Tier 2 (D-LOOP-35a).
- **Timestamp:** 2026-11-06 ~05:05 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md (+ PROTOCOL/RUBRIC/SCORECARD).

## Gates (real results)
`manage.py check` OK · `makemigrations --check --dry-run` OK · pytest
**655 passed** (unchanged — audits + docs only this run).
Ratchets: sub-13px **43**, hex **211**, image bytes **4,191,687** — held
(WATCH re-surveyed; F5 E3 ALL PASS).

## Shipped this run
- **AUDIT G4 → MET-T1**: 7/7 + E3 r34_e3_g4.py 18/18 (fresh server) +
  D-LOOP-34a verified against code (279/279 braces, gate needles,
  M5/M6 rows, cap 6) + both screenshots — zero gaps, aud=self.
- **WATCH overlay** (deterministic 35 mod 16 = 3): F5 6/6 + E3 ALL PASS;
  F1 drift 211/43 held; nothing REGRESSED.
- **RETRO (r35, docs-only)**: 0 failed attempts in r30-r34, no splits /
  prunes / additions; per §5 raised F1, F2, H1, H2, G2, L1 to **Tier 2**;
  ledger denominator corrected to the canonical **17** (the historical
  "/18" was an off-by-one convention) → MET share **17/17 (100%) at T1**.

## Item states (SCORECARD)
MET-T1: all 17 work items (F1-F5, H1-H4, G1-G4, L1-L4) — **17/17 (100%)**.
Targets: F1, F2, H1, H2, G2, L1 = **T2** (raised r35); the other 11 stay T1.
TODO: none. (+ Q1-Q4 WATCH rows remain cross-cutting.)

## Next slice
**Run 36 = BUILDER**: take ONE T2 lift deeply — suggested **H2** (five 3s →
4s with evidence; richest existing E3 harness r33_e3_h2b.py +
r24_e3_h2a_audit.py) or **F2** (the keystone gate: three-tier live E3
matrix + docs). A T2 claim (all applicable dims 4, binary checks green)
must then be audited by a DIFFERENT run to become MET-T2. Suite ≥ 655.
OPS: pkill any 8765 server before starting a fresh one; E3 needs
scroll_into_view for below-fold targets and .lower() on uppercase text.
Do not churn: T1 items other than the six raised stay frozen.

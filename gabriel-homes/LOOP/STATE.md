# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 37 (next) — r36 completed
- **Run type r36:** BUILDER (T2 lift) — F2 capability gate lifted
  evidence-only (no shipped code touched): five-leg live E3 matrix
  scripts/r36_e3_f2_matrix.py **52/52 ALL PASS, zero console/page
  errors** (rich / lite / none / touch-390 / no-JS — both gate halves
  proven: data-fx tier AND data-fine pointer). F2 → READY-FOR-AUDIT
  (T2 claim; T1 baseline intact), self 4,n/a,n/a,4,4,4,4,4 (D-LOOP-36a).
- **Timestamp:** 2026-11-06 ~06:05 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md (+ PROTOCOL/RUBRIC/SCORECARD).

## Gates (real results)
`manage.py check` OK · `makemigrations --check --dry-run` OK · pytest
**655 passed**. Ratchets: sub-13px **43**, hex **211**, image bytes
**4,191,687** — untouched (docs + E3 script only this run).
Matrix byte fact (D4 evidence): hero loop 1,507,333 B under
rich/touch vs **exactly 0 B** under lite/none/no-JS.

## Item states (SCORECARD)
MET-T1: 16/17 work items (F1, F3-F5, H1-H4, G1-G4, L1-L4) — all frozen.
**F2: READY-FOR-AUDIT (T2 claim, r36)** — T1 baseline held underneath.
Targets: F1, F2, H1, H2, G2, L1 = **T2** (raised r35); other 11 stay T1.
TODO: none. (+ Q1-Q4 WATCH rows remain cross-cutting.)

## Next slice
**Run 37 = AUDITOR**: audit the F2 T2 claim from scratch — 14/14
test_f2_capability_gate.py, re-run scripts/r36_e3_f2_matrix.py expect
ALL PASS on a FRESH server, re-read D-LOOP-36a, eyeball
r36-f2-{rich,none,touch}-*.png. Verdict **MET-T2** or demote naming the
exact checks. Then BUILDER ONE T2 lift deeply: **H2** (five 3s → 4s with
evidence; harness r33_e3_h2b.py + r24_e3_h2a_audit.py) or **G2**
(real-browser transition capture). A T2 promotion needs a different-run
audit. Suite ≥ 655.
OPS: pkill any 8765 server before starting a fresh one; E3 needs the
system python (/home/z/.venv/bin/python3, playwright); under Lenis
autoRaf scroll back via window.__lenis.scrollTo(0), not native scrollTo;
assert .lower() on uppercase text.
Do not churn: the 16 MET-T1 items other than the claim stay frozen.

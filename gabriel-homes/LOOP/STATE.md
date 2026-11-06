# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 38 (next) — r37 completed
- **Run type r37:** AUDITOR→BUILDER — (1) F2's T2 claim audited from
  scratch → **MET-T2, the project's first Tier-2 item** (14/14 tests +
  matrix re-run ALL PASS on a fresh server + D-LOOP-36a verified; one
  bookkeeping correction: the matrix is **53/53**, not 52 — counted
  programmatically, all green either way). (2) BUILDER H2 T2 lift
  (evidence-only, no code touched): scripts/r37_e3_h2_t2.py **24/24
  ALL PASS** across 5 legs → H2 READY-FOR-AUDIT (T2 claim; T1 intact),
  self 4,4,n/a,4,4,4,4,4. First real Q1 wire measurement recorded:
  css+js+fonts+LCP = **634,772 B** > 400 KB aspiration (fonts 290 KB
  are the lever) — Q1 WATCH row, not an H2 defect. (D-LOOP-37a.)
- **Timestamp:** 2026-11-06 ~06:35 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md (+ PROTOCOL/RUBRIC/SCORECARD).

## Gates (real results)
`manage.py check` OK · `makemigrations --check --dry-run` OK · pytest
**655 passed** (start and end of run). Ratchets: sub-13px **43**, hex
**211**, image bytes **4,191,687** — untouched (docs + E3 scripts only).

## Item states (SCORECARD)
**MET-T2: F2** (r37 audit). MET-T1: 15/17 (F1, F3-F5, H1, H3-H4,
G1-G4, L1-L4) — frozen. **H2: READY-FOR-AUDIT (T2 claim, r37)** —
T1 baseline held underneath. Targets: F1, F2✅, H1, H2, G2, L1 = T2.
TODO: none. (+ Q1-Q4 WATCH rows cross-cutting; Q1 now has a real
baseline: 634,772 B, fonts are the lever.)

## Next slice
**Run 38 = AUDITOR**: audit the H2 T2 claim from scratch — 10/10
test_h2_hero.py, re-run scripts/r37_e3_h2_t2.py expect ALL PASS on a
FRESH server (pkill-first), re-read D-LOOP-37a, eyeball
r37-h2-{rich,mobile,mobile-rich}-*.png. Verdict **MET-T2** or demote
naming the exact checks. Then BUILDER ONE T2 lift deeply: **G2**
(real-browser transition capture would be the exemplary evidence) or
**F1** (tokenisation pass over the 10 search.css hexes — natural T2
proof per its SCORECARD row). A T2 promotion needs a different-run
audit. Suite ≥ 655.
OPS: pkill any 8765 server before a fresh one; E3 needs the system
python (/home/z/.venv/bin/python3); under Lenis autoRaf scroll back via
window.__lenis.scrollTo(0); wait ~1.2s after navigation or screenshots
catch the hv2-rise entrance mid-fade; assert .lower() on uppercase text.
Do not churn: MET items other than the claim stay frozen.

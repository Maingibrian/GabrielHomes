# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 39 (next) — r38 completed
- **Run type r38:** AUDITOR→BUILDER — (1) H2's T2 claim audited from
  scratch → **MET-T2, the project's second Tier-2 item** (10/10 tests +
  scripts/r37_e3_h2_t2.py **24/24 ALL PASS** on a fresh server, wire
  accounting reproduced byte-for-byte; git tree proves r37 was
  evidence-only). (2) BUILDER F1 T2 lift: search.css tokenised to **zero
  hex** (8× #fff → var(--white), 2× #e7e4df → NEW token **--map-stage**,
  D-LOOP-38a), hex ratchet **211 → 201**, NEW pin test (suite 655 →
  **656**), computed-style A/B proof **13/13 identical** (render-
  invisible by construction), WCAG: all five touched text pairs ≥ 4.5:1.
  F1 READY-FOR-AUDIT (T2 claim; T1 intact), self 4,n/a,n/a,n/a,4,n/a,4,4.
- **Timestamp:** 2026-11-06 ~08:00 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md (+ PROTOCOL/RUBRIC/SCORECARD).

## Gates (real results)
`manage.py check` OK · `makemigrations --check --dry-run` OK · pytest
start **655 passed** → end **656 passed** (+1: the new search-css pin).
Ratchets: sub-13px **43**, hex **211 → 201** (legitimate drop — 10
search.css hex tokenised), image bytes **4,191,687** — untouched.

## Item states (SCORECARD)
**MET-T2: F2 (r37), H2 (r38).** MET-T1: 14/17 (F3-F5, H1, H3-H4,
G1-G4, L1-L4) — frozen. **F1: READY-FOR-AUDIT (T2 claim, r38)** — T1
baseline held underneath. Targets: F1, F2✅, H1, H2✅, G2, L1 = T2.
TODO: none. (+ Q1-Q4 WATCH rows cross-cutting; Q1 baseline 634,772 B,
fonts 290 KB are the lever.)

## Next slice
**Run 39 = AUDITOR**: audit the F1 T2 claim from scratch — 9/9
test_f1_token_integrity.py (incl. the new test_search_css_is_fully_
tokenised), re-run scripts/r38_e3_f1_ab.py before/after on a FRESH
server (pkill-first) expect **13/13 identical**, verify --map-stage in
tokens.css, re-read D-LOOP-38a, eyeball r38-f1-search-after.png. Verdict
**MET-T2** or demote naming the exact checks. Then BUILDER ONE T2 lift
deeply: **G2** (real-browser transition capture would be the exemplary
evidence) or **L1/H1** evidence packs. A T2 promotion needs a
different-run audit. Suite ≥ 656.
OPS: pkill any 8765 server before a fresh one; E3 needs the system
python (/home/z/.venv/bin/python3); under Lenis autoRaf scroll back via
window.__lenis.scrollTo(0); wait ~1.2s after navigation or screenshots
catch entrances mid-fade; assert .lower() on uppercase text; runserver
serves static from disk per-request, so an A/B snapshot "before" must be
captured BEFORE touching a css file. Do not churn: MET items other than
the claim stay frozen.

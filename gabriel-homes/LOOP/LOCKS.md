# LOCKS.md — who is working on what right now

Format: `ITEM | run-id | claimed-at | expires-at (claim + 45 min) | released`
Re-read this file before every claim. A live (unreleased, unexpired) lock on the
same item or the same file ⇒ pick a different item.

| ITEM | run-id | claimed-at | expires-at | released |
|---|---|---|---|---|
| PLAN (create RUBRIC/PROTOCOL/SCORECARD/LOCKS/JOURNAL, no code) | r15-planner | 2026-11-05 08:30 +03:00 | 2026-11-05 09:15 +03:00 | yes — 08:52 +03:00 |
| F2 (capability gate: fx-gate.js + motion.js + bento-shift.js + base.html + test_f2_capability_gate.py) | r16-builder | 2026-11-05 09:22 +03:00 | 2026-11-05 10:07 +03:00 | yes — 09:58 +03:00 |
| AUDIT F2 (gate re-run + from-scratch grading, §3c) | r17-auditor | 2026-11-05 11:20 +03:00 | 2026-11-05 12:05 +03:00 | yes — 11:41 +03:00 (verdict MET-T1) |
| F1 (token integrity: test_f1_token_integrity.py + search.css var fixes + allowlist + hex ratchet) | r17-builder | 2026-11-05 11:41 +03:00 | 2026-11-05 12:26 +03:00 | yes — 12:00 +03:00 (READY-FOR-AUDIT) |
| AUDIT F1 (gate re-run + ratchet recompute + from-scratch grading) | r18-auditor | 2026-11-05 12:48 +03:00 | 2026-11-05 13:33 +03:00 | yes — 12:52 +03:00 (verdict MET-T1) |
| H1 (home order & diet: test_h1_home_order.py + home.html section moves + destinations) | r18-builder | 2026-11-05 12:52 +03:00 | 2026-11-05 13:37 +03:00 | yes — 13:05 +03:00 (READY-FOR-AUDIT) |

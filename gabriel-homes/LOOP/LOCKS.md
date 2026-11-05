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
| AUDIT H1 (gates + test_h1_home_order.py + E3 destination renders) | r19-auditor | 2026-11-05 13:20 +03:00 | 2026-11-05 14:05 +03:00 | yes — 13:32 +03:00 (verdict MET-T1) |
| H3 (mobile bento: test_h3_mobile_bento.py + home.css carousel) | r19-builder | 2026-11-05 13:33 +03:00 | 2026-11-05 14:18 +03:00 | yes — 13:50 +03:00 (READY-FOR-AUDIT) |
| RETRO r20 (re-weight/split/add/prune per §3b; docs only, no code) | r20-planner | 2026-11-05 13:50 +03:00 | 2026-11-05 14:35 +03:00 | yes — 13:58 +03:00 (retro logged: D-LOOP-20a..e) |
| AUDIT H3 (gates + test_h3_mobile_bento.py + E3 rail @390px: snap, keyboard walk, bento-shift off) | r20-auditor | 2026-11-05 13:58 +03:00 | 2026-11-05 14:43 +03:00 | yes — 14:12 +03:00 (verdict MET-T1, 21/21 E3) |
| WATCH r20-overlay (gates + deterministic MET spot-check F2 [21 mod 4 = 1 of F1,F2,H1,H3] + F1 drift) | r21-watch | 2026-11-05 14:17 +03:00 | 2026-11-05 15:02 +03:00 | yes — 14:18 +03:00 (22/22 clean, drift held) |
| F3 (image & video diet: test_f3_media_diet.py + WebP pass + video contract + HYG-1 purge) | r21-builder | 2026-11-05 14:18 +03:00 | 2026-11-05 15:03 +03:00 | yes — 14:46 +03:00 (READY-FOR-AUDIT, 562 passed) |

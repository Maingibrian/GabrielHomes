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
| AUDIT F3 (gates + 6 F3 tests + survey re-run + E3 smoke re-run + D-LOOP-21 rationale) | r22-auditor | 2026-11-05 15:27 +03:00 | 2026-11-05 16:12 +03:00 | yes — 15:30 +03:00 (verdict MET-T1; sub-13px corrected 44→43, D-LOOP-22a) |
| G2 (shared-element transitions: test_g2_view_transitions.py + base.css @view-transition/@supports + per-listing names + fx opt-out) | r22-builder | 2026-11-05 15:30 +03:00 | 2026-11-05 16:15 +03:00 | yes — 15:55 +03:00 (READY-FOR-AUDIT, 569 passed) |
| AUDIT G2 (gates + 7 G2 tests + E3 re-run + D-LOOP-22b re-read) | r23-auditor | 2026-11-05 16:15 +03:00 | 2026-11-05 17:00 +03:00 | yes — 16:20 +03:00 (verdict MET-T1, E3 14/14) |
| L1 (map & list sync: test_l1_map_list_sync.py + search-map.js wiring + row identity + oob count + Map pill) | r23-builder | 2026-11-05 16:22 +03:00 | 2026-11-05 17:07 +03:00 | yes — 16:45 +03:00 (READY-FOR-AUDIT, 581 passed) |
| OWNER r24 (founder portrait wiring + H2.a hero structure slice incl. mobile hero defects from owner screenshots; files: about.html, home.html, home.css, static/img, test_h2_hero.py, test_founder_portrait.py) | r24-owner | 2026-11-05 17:20 +03:00 | 2026-11-05 18:05 +03:00 | yes — 17:55 +03:00 (session cut mid-run; resumed + completed by the 22:15 cron run: comment-leak REPAIR + H2.a + portrait, 590 passed, D-LOOP-24c) |
AUDIT L1 + H2.a (gates + 12/12 test_l1_map_list_sync.py + 7/7 test_h2_hero.py + E3 re-runs r23_e3_l1_audit.py & r24_e3_visual.py + from-scratch grading) | r25-auditor | 2026-11-05 17:46 +03:00 | 2026-11-05 18:31 +03:00 | yes — 18:07 +03:00 (L1 MET-T1 · H2.a MET-T1 · F4 built READY-FOR-AUDIT, 597 passed) |
AUDIT F4 (gates + 7/7 test_f4_motion_vocab.py + addendum-vs-code hook hunt + archetype render check) | r26-auditor | 2026-11-05 20:47 +03:00 | 2026-11-05 21:32 +03:00 | yes — 21:15 +03:00 (F4 MET-T1 · L2 built READY-FOR-AUDIT, 603 passed) |
| AUDIT L2 (gates + 6/6 test_l2_basemap_palette.py + E3 re-run scripts/r26_e3_l2.py + D-LOOP-26b re-read + map screenshot eyeball) | r27-auditor | 2026-11-05 21:45 +03:00 | 2026-11-05 22:30 +03:00 | yes — 22:25 +03:00 (L2 MET-T1 · G1 built READY-FOR-AUDIT, 609 passed) |
| AUDIT G1 (gates + 6/6 test_g1_pill_nav.py + E3 re-run scripts/r27_e3_g1.py + D-LOOP-27a re-read + 1280px hide/return eyeball) | r28-auditor | 2026-11-05 22:45 +03:00 | 2026-11-05 23:30 +03:00 | yes — 23:15 +03:00 (G1 MET-T1 · L3 built READY-FOR-AUDIT, 615 passed) |
| AUDIT L3 (gates + 6/6 test_l3_row_density.py + git-diff brand-channel verification + live search-page E3 re-render + hierarchy/row-height checks + r28-l3-row.png eyeball) | r29-auditor | 2026-11-05 23:50 +03:00 | 2026-11-06 00:35 +03:00 | yes — 00:45 +03:00 (L3 MET-T1 · F5 built READY-FOR-AUDIT, 621 passed) |
| AUDIT F5 (gates + 6/6 test_f5_smooth_scroll.py + E3 re-run scripts/r29_e3_f5.py + D-LOOP-29a re-read + base.html SRI sanity check + from-scratch grading) | r30-auditor | 2026-11-06 00:47 +03:00 | 2026-11-06 01:32 +03:00 | yes — 01:22 +03:00 (F5 MET-T1 · H4 built READY-FOR-AUDIT, 627 passed) |
| H4 (section rhythm: test_h4_section_rhythm.py + 5 data-archetype tags in home.html + addendum archetype correction + scripts/r30_e3_h4.py) | r30-builder | 2026-11-06 01:02 +03:00 | 2026-11-06 01:47 +03:00 | yes — 01:22 +03:00 (READY-FOR-AUDIT, 627 passed) |
| AUDIT H4 (gates + 6/6 test_h4_section_rhythm.py + E3 re-run scripts/r30_e3_h4.py + D-LOOP-30a re-read + r30-h4-home-390.png eyeball + from-scratch grading) | r31-auditor | 2026-11-06 02:18 +03:00 | 2026-11-06 03:03 +03:00 | yes — 02:40 +03:00 (H4 MET-T1 · G3 built READY-FOR-AUDIT, 636 passed) |
| G3 (scroll-linked: test_g3_scroll_linked.py + components.css @supports block + addendum M1 extension + scripts/r31_e3_g3.py) | r31-builder | 2026-11-06 02:36 +03:00 | 2026-11-06 03:21 +03:00 | yes — 03:20 +03:00 (READY-FOR-AUDIT, 636 passed) |
| AUDIT G3 (gates + 9/9 test_g3_scroll_linked.py + E3 re-run scripts/r31_e3_g3.py + D-LOOP-31a re-read + r31-g3-services.png eyeball + from-scratch grading) | r32-auditor | 2026-11-06 04:48 +03:00 | 2026-11-06 05:33 +03:00 | yes — 05:22 +03:00 (verdict MET-T1, 645 passed) |
| L4 (detail gallery: read detail-gallery.js FIRST + extend; test_l4_gallery.py + swipe + lightbox focus trap + keyboard + shared-element name) | r32-builder | 2026-11-06 04:56 +03:00 | 2026-11-06 05:41 +03:00 | yes — 05:24 +03:00 (READY-FOR-AUDIT, 645 passed) |

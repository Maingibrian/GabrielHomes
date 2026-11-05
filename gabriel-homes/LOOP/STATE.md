# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 18
- **Run type:** AUDITOR→BUILDER — F1 audited MET-T1; H1 (home order & diet)
  built and left READY-FOR-AUDIT. Two mid-run failed attempts, both fixed
  in-run (multi-line template comments — the r16 bug class again; and the
  live footer browse column breaking the page query budget).
- **Timestamp:** 2026-11-05 ~13:05 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes/
- **Protocol:** LOOP/SCHEDULED-TASK.md; condensed rules LOOP/PROTOCOL.md;
  rubric LOOP/RUBRIC.md; per-item contract LOOP/SCORECARD.md.

## Gates (real results)
| Gate | Start | Mid-run | End |
|---|---|---|---|
| `manage.py check` | OK — 0 issues | — | OK — 0 issues |
| `makemigrations --check --dry-run` | OK — no changes | — | OK — no changes |
| `pytest -q` | **540 passed** | **17 failed** (leaks + query budget) | **551 passed** |

Ratchets (F1): hex outside tokens.css 238 → **236**; sub-13px **44**
(pairs re-attributed: the newsletter form moved home.css → components.css).
Survey tool: scripts/f1_token_survey.py.

## Shipped this run
- **F1 → MET-T1** (audit): gates + survey recompute exact; test engineering
  graded 4 on D8; frozen; WATCH re-runs the survey.
- **H1 → READY-FOR-AUDIT**: home.html 569 → ~347 lines; top-level sections
  12 → 4 — exactly `hero, bento, recommended, nearby` (showcase id→bento).
  Moves: about lines → /about/; services dedup'd (page already had them);
  commitments → /checks/; FAQ + newsletter + closing CTA → footer
  (site-wide, details/summary, same form action); browse → curated footer
  hubs; talk-to-us → channels strip inside recommended (honest-blank kept).
  Proving tests: test_h1_home_order.py (11). E3: r18-home-desktop.jpg +
  r18-checks-commitments.jpg (download/preview-screenshots/).

## Failed attempts (both fixed in-run; no NOTES file — single cause each)
1. Five multi-line `{# … #}` template comments leaked onto pages (17 test
   failures) — the EXACT r16 bug class (NOTES/F2.md rule). All single-lined;
   grep for a `{#` without a same-line `#}` BEFORE finishing template edits.
2. Footer browse built LIVE first (context processor, 7 queries/request; one
   bad `location__path` FieldError on the way) → results-page query budget
   broke (21 > 15; baseline 14, ceiling 15). Replaced with curated
   query-free hubs; processor deleted; budget test green again.

## Item states (SCORECARD)
MET-T1: F1, F2. READY-FOR-AUDIT: H1. TODO: 14 items. Unblocked leaders:
H3 (15, needs F2 ✓), F3 (12), F4 (12), G1 (12, needs F2 ✓), L1 (15).

## Next slice
**Run 19 = AUDITOR first (H1: gates + test_h1_home_order.py + E3 on
destinations), then BUILDER: H3 (mobile bento carousel, priority 15,
unblocked by F2)** — keep the desktop bento-shift tests untouched. Suite
must stay ≥ 551. Dead home.css purge is queued (BACKLOG HYG-1) for the
F3/F4 pass, not this one.

# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 77 (next) — r76 completed
- **Run type r76:** BUILDER (owner round, off-loop) — THE MOBILE
  AUDIT + POSTER HERO. Owner ask: "audit the mobile view … one
  should not scroll to view data on the page", "the mobile hero
  should be different only — make it look like a poster by a
  graphics design person", then push with the provided PAT and stop.
  Delivered: (1) the page-level horizontal guard promoted from
  search.css to base.css (html overflow-x: clip + hidden fallback) —
  marquee tracks / market-veil pseudos / armed row slides can
  over-report scrollWidth but NO engine can open a sideways scroll;
  (2) THE MOBILE POSTER HERO ≤809px — same DOM, new layering: the
  slideshow becomes a framed, hairlined, shadowed print with edge
  margins, a gallery plate rule (MOMBASA — KENYAN COAST) BELOW the
  frame, the headline as the print's espresso-on-cream caption, the
  chip bar dropped, and the search pill re-laid as a three-row
  control plate (Buy|Rent / location / type + inset Search pill) so
  search + chips sit inside the first phone screen; the transparent
  melt-into-hero header retires ≤809px on HOME ONLY (solid in-flow
  espresso bar — cream text must never sit on the cream poster
  ground; content pages keep the overlay); (3) the results-page
  compaction ≤809px — market cards became three-up photo tiles
  (no 82vw carousel, no negative margins, arrows hidden so titles
  stop colliding), map 250→205px, headers tightened: the FIRST
  LISTING CARD moved from 986px to 719px — inside the 844px fold;
  (4) three VLM design passes on the poster (6.5 → 7.5 → SHIP);
  (5) THE CLOUD PUSH FINALLY HAPPENED — repo is
  Maingibrian/GabrielHomes (PAT in-message this time): remote added,
  unrelated histories merged with -s ours (local tree is a strict
  superset: 687 files, +80k lines, 0 real deletions; remote's
  committed .venv stays untracked), 727a1f4b..4ba13cd9 fast-forward
  pushed, then r76 work pushed on top. PAT never written to any
  file.
- **Timestamp:** 2026-11-11 ~22:00 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes/
- **Protocol:** LOOP/PROTOCOL.md + docs/BACKEND-PLAN.md (the backend plan).

## Gates (real results)
`manage.py check` 0 · `makemigrations --check` clean · pytest
**1049 passed** (1038 → 1049, +11 in
  apps/core/tests/test_r76_mobile_poster.py: guard, plate markup +
  scoping, poster relayer rules, desktop-survival, header exception,
  control plate, results compaction, carousel survival for 810+,
  zero-hex in the four touched blocks, no sub-13px in the new blocks).
  Migrations this run: none (pure CSS/template/tests).

## Where things stand
Public site: production-shaped (search, listings, enquiries, SEO,
security, deploy guide; three-state demo honesty; quotes band) and
now MOBILE-COMPLETE: poster hero ≤809px, desktop untouched ≥810px,
zero pannable overflow on every audited page (home, properties,
location, detail, about, contact, services, checks, privacy, login,
signup + all 12 manage screens + dashboard at 390px).
Owner portal: Phases 1-3 DONE (graphs, enquiries workflow, brand
assets, SEO, listing tools, categories, media library, testimonials,
newsletter compose) — all clean at 390px. Preview bootstrap:
scripts/start_preview.sh (seeds 80 listings + sample enquiries +
sample testimonials via --with-enquiries; preview owner login
owner@test.com / owner-preview-123 — reset to the documented value
r76).

## Next slice
**Run 77 = Phase 4 (trust & housekeeping)** per BACKEND-PLAN:
4A activity log (who changed what), 4B one-click backup (DB + media
download), 4C saved-search alerts UI (model exists, unused), 4D
in-portal help page. Also parked: P3-5 CSV import into /manage/,
P3-11 SEO per-page overrides + share image, P3-13 owner password
change + login log. Possible polish from the r76 design reviews:
subtitle still 3-4 lines at 390px (fine per final pass), header
SAVED/SIGN OUT top padding nit.
Suite ≥ 1049.

OPS: preview heals via scripts/start_preview.sh after sandbox
recycles (run pip in the FOREGROUND first if the venv is gone).
{# #} comments are SINGLE-line — use {% comment %} for anything
longer (guard test sweeps all portal screens). The portal's
stylesheet stack is pinned (tokens→base→components→manage). GIT:
remote origin = https://github.com/Maingibrian/GabrielHomes.git
(config carries NO token — push with a one-shot URL header when the
owner pastes a fresh PAT; last push 4ba13cd9 + r76).

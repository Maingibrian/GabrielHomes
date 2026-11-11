# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 76 (next) — r75 completed
- **Run type r75:** BUILDER (owner round, off-loop) — BACKEND-PLAN
  Phase 3 (content & taxonomy), all under /manage/site-content/ so the
  five section nav stays five: the Categories editor (add-by-name with
  derived slugs/levels, rename-in-place keeping URLs, hide/show with
  the public-menu chokepoints wired — hidden types leave the home
  dropdown, hidden counties leave related searches + autocomplete,
  hidden amenities stay off detail pages, and every existing page keeps
  working), the Media library (where-used grid, filter chips with
  honest counts, title search, caption editor, guarded delete — a live
  listing never loses its cover or its last photo, and the file leaves
  disk with the row), Testimonials (consent gate: no permission, no
  publication; hidden-when-none; demo-switch aware; the home page grew
  its 8th bubbly topic "What clients say."), and Newsletter compose
  (pick up to 10 live listings, preview exactly what goes out, send to
  confirmed-only subscribers with per-recipient unsubscribe links; one
  delivery path shared with the threshold trigger — compose_issue()).
  r75 lesson: pre-check duplicates instead of catching IntegrityError —
  a constraint error inside a test transaction poisons it.
- **Timestamp:** 2026-11-12 ~01:30 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes/
- **Protocol:** LOOP/PROTOCOL.md + docs/BACKEND-PLAN.md (the backend plan).

## Gates (real results)
`manage.py check` 0 · `makemigrations --check` clean · pytest
**1038 passed** (990 → 1038, +48: taxonomy 17, media 12, testimonials
14, newsletter 5... exact split in the four new test files; plus the
bubble-topic pin grown from 7 topics to 8). Migrations this run:
locations.0002 + listings.0011 (is_active flags) + core.0016
(Testimonial).

## Where things stand
Public site: production-shaped (search, listings, enquiries, SEO,
security, deploy guide; three-state demo honesty; new quotes band).
Owner portal: Phases 1-3 DONE (graphs, enquiries workflow, brand
assets, SEO, listing tools, categories, media library, testimonials,
newsletter compose). Preview bootstrap: scripts/start_preview.sh
(seeds 80 listings + sample enquiries + sample testimonials via
--with-enquiries; preview owner login owner@test.com /
owner-preview-123 — password reset this run).

## Next slice
**Run 76 = Phase 4 (trust & housekeeping)** per BACKEND-PLAN:
4A activity log (who changed what), 4B one-click backup (DB + media
download), 4C saved-search alerts UI (model exists, unused), 4D
in-portal help page. Also parked: P3-5 CSV import into /manage/,
P3-11 SEO per-page overrides + share image, P3-13 owner password
change + login log.
Suite ≥ 1038.

OPS: preview heals via scripts/start_preview.sh after sandbox
recycles (run pip in the FOREGROUND first if the venv is gone).
{# #} comments are SINGLE-line — use {% comment %} for anything
longer (guard test sweeps all portal screens). The portal's
stylesheet stack is pinned (tokens→base→components→manage). Owner
cloud PAT still pending — no file named gabriel exists anywhere
(searched upload/, download/, repo, /home/z, again r75) — push when
provided, delete after use.

# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 75 (next) — r74 completed
- **Run type r74:** BUILDER (owner round, off-loop) — the requested
  thorough re-audit + BACKEND-PLAN Phase 2 (listing tools), all on
  /manage/listings/: bulk status bar with honest publish refusals,
  per-row quick tools (featured toggle, one-click duplicate with real
  image FILE copies, inline price with derived period), the map pin
  picker on the self-hosted MapLibre stack (no new deps), and the
  five-step wizard with per-step draft saves. r74 lessons: the leak
  guard now forces a row onto /manage/listings/ (empty state skipped
  the {% if %} branch that held a leaking comment); Number("") is 0,
  not NaN — the pin picker read "no pin yet" as a pin at null island
  until parseFloat.
- **Timestamp:** 2026-11-11 ~22:00 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes/
- **Protocol:** LOOP/PROTOCOL.md + docs/BACKEND-PLAN.md (the backend plan).

## Gates (real results)
`manage.py check` 0 · `makemigrations --check` clean · pytest
**990 passed** (954 → 990, +36: 35 listing-tools + strengthened leak
guard). No migrations this run (views/forms/templates/JS only).

## Where things stand
Public site: production-shaped (search, listings, enquiries, SEO,
security, deploy guide; three-state demo honesty). Owner portal:
Phase 1 + Phase 2 DONE (dashboard graphs, enquiries workflow, brand
assets, SEO, listing tools: bulk/featured/price/duplicate/pin/wizard).
Preview bootstrap: scripts/start_preview.sh (seeds 80 listings +
sample enquiries via --with-enquiries; preview owner login
owner@gabrielhomes.co.ke / gabriel-preview-2026).

## Next slice
**Run 75 = Phase 3 (content & taxonomy)** per BACKEND-PLAN:
3A taxonomy editor (locations/types/amenities: add/rename/hide, no
deletes), 3B media library, 3C testimonials, 3D newsletter compose
(model + double opt-in exist). Alternative quick wins: in-portal
demo-switch toggle (checklist item action still says "ask Brian"),
P4-3 detail gallery polish.
Suite ≥ 990.

OPS: preview heals via scripts/start_preview.sh after sandbox
recycles (run pip in the FOREGROUND first if the venv is gone).
{# #} comments are SINGLE-line — use {% comment %} for anything
longer (guard test sweeps all portal screens AND now forces a row
onto /manage/listings/ so the full branch renders). The portal's
stylesheet stack is pinned (tokens→base→components→manage). Owner
cloud PAT still pending — no file named gabriel exists anywhere
(searched upload/, download/, repo, /home/z) — push when provided,
delete after use.

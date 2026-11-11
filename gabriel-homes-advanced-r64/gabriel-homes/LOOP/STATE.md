# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 74 (next) — r73 completed
- **Run type r73:** BUILDER (owner round, off-loop) — Owner Hub Phase 1
  per docs/BACKEND-PLAN.md: five portal sections (Home/Enquiries/
  Listings/Site content/SEO), graphs dashboard (CSS-only bars), the
  full enquiries workflow (pipeline statuses + auto-seen + notes +
  prefilled WhatsApp + CSV + spam folder), brand assets editor with
  public wiring, SEO & tracking (GA via local loader, zero inline
  scripts), read-first listings section. Found + fixed a LATENT bug:
  the portal had never loaded tokens.css/components.css since P2-1
  (all vars computed invalid — naked styles). Two multi-line {# #}
  comment leaks caught + portal-wide guard added.
- **Timestamp:** 2026-11-11 ~20:30 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes/
- **Protocol:** LOOP/PROTOCOL.md + docs/BACKEND-PLAN.md (the backend plan).

## Gates (real results)
`manage.py check` 0 · `makemigrations --check` clean · pytest
**954 passed** (881 → 954). Migrations: inquiries.0004/0005 (statuses
+ is_demo + InquiryNote + replied→contacted data), core.0015 (brand
assets + SEO fields).

## Where things stand
Public site: production-shaped (search, listings, enquiries, SEO,
security, deploy guide; three-state demo honesty). Owner portal:
Phase 1 DONE (dashboard, enquiries workflow, brand assets, SEO,
listings read-first). Preview bootstrap: scripts/start_preview.sh
(seeds 80 listings + sample enquiries via --with-enquiries; preview
owner login owner@gabrielhomes.co.ke / gabriel-preview-2026).

## Next slice
**Run 74 = Phase 2 (listing tools)** on /manage/listings/:
duplicate, bulk status change, featured toggle, inline price edit,
MapLibre click-to-set pin picker, then wizard + draft autosave.
Alternative quick wins: in-portal demo-switch toggle (checklist item
action still says "ask Brian"), P4-3 detail gallery polish.
Suite ≥ 954.

OPS: preview heals via scripts/start_preview.sh after sandbox
recycles (run pip in the FOREGROUND first if the venv is gone).
{# #} comments are SINGLE-line — use {% comment %} for anything
longer (guard test now sweeps all portal screens). The portal's
stylesheet stack is pinned (tokens→base→components→manage). Owner
cloud PAT still pending — push when provided, delete after use.

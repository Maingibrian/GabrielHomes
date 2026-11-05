# LOOP/BACKLOG.md — one slice ≈ 20 minutes, work strictly top-down

Tick items `[x]` when done, with run number. Never start a slice you cannot finish.

## P0 — Unprovable data & three-state behaviour
- [x] P0-1 **De-"verify" the public site.** Badge on `_listing_card.html` + `detail.html` becomes "Checked", rendered only when the owner flag is set (reuse `is_verified` column non-destructively as storage; no destructive migration). Rename claims in `about.html` (lines ~40, 66), `checks.html` (~81), `terms.html` (~41) to "checked" language. Tests: badge hidden by default, shown when flagged, copy has no "verified". **Done run 2** — also fixed Python-built meta descriptions (listings views ×2, core services view), dropped "Verified agency" chip text on detail card, owner-dashboard labels now say Checked, seed description + bio templates updated, dev demo rows fixed in place (80 rows, idempotent text swap). 13 new tests in `apps/core/tests/test_p0_checked_language.py`. CSS class hooks kept (invisible; logged in test docstring).
- [x] P0-2 **Agent directory claims.** Hero eyebrow "Experts"→"Directory", subtitle → "The agencies currently listing on Gabriel Homes.", heading "one standard — verified." → "N agencies on Gabriel Homes." (DB count kept), card chip + profile eyebrow → plain "Agency" (public ignores `is_verified` — dashboard storage only), directory + profile meta descriptions factual, owner flash message "marked checked". Migration 0005 self-heals 0003's inlined "verified details" bio (idempotent). 6 new tests (sweep now includes /agents/). **Done run 3.**
- [x] P0-3 **Designed empty state for `/agents/`.** Reuses the shared `.empty-state` component (search.css — same tokens, no new CSS). Three variants: empty directory (demo hidden / zero agencies) → "The directory is empty right now." + Browse/Contact paths; search miss → "No agencies match 'q'" + Clear search; agencies present → grid + partner CTA as before. "0 agencies" heading hidden at zero; JOIN-US card hidden when grid empty. QA run 4 also caught + fixed a multi-line `{#…#}` template-comment leaking raw text onto the page (guard test added). Spot-check via isolated-DB probe: home / properties / detail / location / agents all render designed states in demo-visible, demo-hidden and zero-listing. Screenshots at 360/810/1280 in LOOP/audit-screens/run4-*.png. 5 new tests. **Done run 4.**
- [x] P0-4 Three-state pytest harness: `apps/core/tests/test_p0_three_state_harness.py` — home / properties / detail / agents→about under (a) demo visible, (b) demo hidden, (c) zero listings; asserts designed fallbacks ("HOW WE CHECK" bento, `.empty-state`), 404s for hidden demo details, no template leaks, chrome intact. 12 tests. **Done run 8** — QA runs re-run this module instead of hand-probing.

## P1 — Single-owner mode
- [x] P1-1 **`/agents/` + `/agents/<slug>/` → permanent redirect to `/about/`.** Both public patterns now `RedirectView(permanent=True)` to `/about/` (route names kept so dashboard reversals resolve; old view classes + templates left in-repo unrouted — logged). Sitemaps never listed agent URLs (checked); nav/footer already had no agent links (grep + new chrome test). 6 new tests in `apps/core/tests/test_p1_agents_redirect.py` (301 both shapes, unknown slug, followed → /about/, no agent links in chrome on 3 page types, comment-leak guard on /about/); 3 agent-page tests in `test_p0_checked_language.py` became redirect assertions; legacy `test_demo_switch.py` test updated to the redirect contract. **Done run 5** — pytest 424 passed.
- [x] P1-2 Detail sidebar: brand contact card (Call / WhatsApp / Email) sourced from the new BrandSettings singleton row with empty code defaults (owner-editable at P3-8); buttons hidden when unfilled (honest blank). "Agency" chip/role gone; agency logo/name gone from the detail page; mobile bar + footer clearance gated on `has-contact-bar` body class (only when a channel exists). 10 new tests + 5 rewritten to the brand contract. **Done run 6** — pytest 432 passed.
- [x] P1-3 Listing cards: card template verified already agency-free (index tag, price, location, Checked badge only — guard test added); seed_demo DESCRIPTION_TEMPLATE ends "Contact Gabriel Homes directly to arrange a viewing."; migration listings.0008 heals old seeded rows (exact-sentence match, is_demo-stamped only, idempotent, reverse no-op) — dev DB 80/80 healed. 7 new tests in test_p1_no_agent_attribution.py; run-2 placeholder assertion updated to the new contract. **Done run 7.**
- [x] P1-4 Enquiry routing: env setting `OWNER_EMAIL` (empty default, .env.example documented) — set → every enquiry notification goes to the owner regardless of listing's (legacy) agency; unset/blank → dev/demo fallback to listing agent's display email; no recipient → no-op, S9 tracking untouched. Owner inbox verified at data level (cross-agency superuser queryset pinned). 6 new tests in `apps/inquiries/tests/test_p1_owner_routing.py`. **Done run 9 — P1 complete.**

## P2 — Portal foundation (/manage/)
- [x] P2-1 `manage` app scaffold: `apps.manage` app, `/manage/` URLs (`app_name="manage"`), `OwnerRequiredMixin` defined in the portal (anon → login w/ next, non-owner → 403, superuser → pass); cream/espresso portal base template (mobile-first, noindex, POST sign-out, NOT admin skin) + scaffold home with one primary action; layout-only manage.css on existing tokens. 8 tests. Visual smoke 360/1280 (run10-manage-*.png). **Done run 10.**
- [x] P2-2 `/manage/` home: counts (new enquiries sans spam, live listings via public chokepoint, drafts) + Setup Checklist — 6-item registry (4 derived from DB/settings: contact/hide_demo/real_listings/owner_email; 2 manual in `ChecklistItemState`, manage.0001), progressbar + %, START HERE banner = exact next step (first open item), plain-language messages on toggle, derived keys refuse hand-ticking. 14 tests; registry order pinned. Visual smoke via real login flow (run11-manage-*.png). **Done run 11.**
- [ ] P2-3 `SiteContent` typed model: key, kind (text / multiline / bool / url / image), value, draft_value, show/hide switch, help text; code defaults registry; idempotent data migration. Tests.
- [ ] P2-4 `{% site_content "key" %}` template tag: code fallback, show/hide hides the whole section wrapper cleanly, safe formatting only (escaped; no raw HTML; minimal whitelist). Tests incl. XSS escaping.
- [ ] P2-5 Content editor screens in portal: list, edit, preview-before-publish (draft → live), friendly validation, inline help. Tests: save → change appears on public page; non-owner blocked.
- [ ] P2-6 Wire `site_content` into hero, subtitle, buttons, stats, story, founder (name spelling becomes editable — site says "Gabriel Omulu", DESIGN.md says "Omulu/Omulu" vs reference "Omulu"; owner confirms), values, philosophy cards, CTA band, footer, about, services, FAQ.

## P3 — Portal modules (protocol §5 order)
- [ ] P3-1 Listings wizard: step flow Basics → Price → Details → Photos → Map pin → Review & publish; draft autosave (Basics + Price steps first). Tests.
- [ ] P3-2 Wizard Photos step: multi-upload, drag-reorder, cover pick, auto WebP via easy-thumbnails, upload validation. Tests.
- [ ] P3-3 Wizard Map pin + Review/publish steps (Leaflet picker; approximate-pin privacy). Tests.
- [ ] P3-4 Listings tools: duplicate, bulk status change, Sold / Let / Under offer, featured toggle, inline price edit. Tests.
- [ ] P3-5 CSV import ported from `/dashboard/import/` into `/manage/` (validated, idempotent, sample CSV). Tests.
- [ ] P3-6 Enquiries inbox: statuses New / Contacted / Viewing booked / Closed, notes, one-tap call & WhatsApp reply templates, CSV export, spam folder. Tests.
- [ ] P3-7 Homepage layout editor: toggle + reorder sections, featured pick or auto, hero image/video, neighbourhood tiles from locations that have listings. Tests.
- [ ] P3-8 Brand & contact editor: logo, favicon, phone, WhatsApp, email, address, hours, socials, map pin; palette presets only (design cannot be broken). Tests.
- [ ] P3-9 Taxonomy editor: locations, property types, amenities — add, rename, hide (no deletes). Tests.
- [ ] P3-10 Media library: upload, alt text, where-used, unused cleanup. Tests.
- [ ] P3-11 SEO editor: per-page and per-listing title/description, share image, Analytics + Search Console ID fields wired into base template. Tests.
- [ ] P3-12 Testimonials (owner-entered, consent flag, hidden when none), market notes, newsletter view. Tests.
- [ ] P3-13 Users & security: owner password change, optional limited staff role, login log (no new packages without logged reason). Tests.
- [ ] P3-14 Backup & export: one-click DB + media export, activity log, short in-portal help guide. Tests.

## P4 — Page-by-page design polish
- [ ] P4-1 Home hero: contrast pass on photo overlays; stats row at 810; verify reveals don't leave gaps in static captures.
- [ ] P4-2 About middle: currently one intro paragraph + long reveal gap → rebuild as story/values blocks from SiteContent.
- [ ] P4-3 Detail: multi-photo gallery + lightbox a11y + mobile sticky Call/WhatsApp bar verification.
- [ ] P4-4 Home: add DB-driven "Latest checked listings" + "Areas we serve" sections (BRIEF §8 items 3 & 8; hide cleanly at zero listings).
- [ ] P4-5 Checks / Services / Contact polish; real contact channels block once P3-8 fields exist (contact page currently shows no phone/email/WhatsApp). Note (run 6): search.html sets `body_class` in the view but never defines the template block — `.page-search` CSS rules never apply; same latent bug class fixed on detail.html in P1-2.
- [ ] P4-6 Footer: contact block + newsletter inline validation + wordmark tracking detail.

## P5 — SEO, performance, accessibility
- [x] P5-1 motion.js smooth-scroll selector — **closed as FALSE POSITIVE (run 8)**: byte-level check proves the file always had the correct `a[href^="#"]`; run 1's audit saw a terminal-transport artifact that ate two chars of the displayed line, not the file. Live check: anchor click scrolls, zero console errors. 3 regression-guard tests added (test_p5_motion_selector.py); D-MOTION-SAFE `motion-ready` gate pinned.
- [ ] P5-2 Lighthouse mobile (home / properties / detail), scores recorded in BRIEF log; fix top issues.
- [ ] P5-3 A11y pass: focus visibility on espresso sections, form-label association at runtime (axe or manual), clay-on-cream contrast. Run 8 bounded sweep: zero img-without-alt (incl. multi-line tags), filter inputs carry aria-labels — alt audit done; remaining items are focus/contrast/runtime labels.
- [ ] P5-4 SEO: unique title/meta on every page, canonicals, OG/share image, JSON-LD on detail, sitemap spot-check.

## P6 — Hardening & docs
- [x] P6-1 `check --deploy` clean on prod settings — **verified run 8**: 0 issues under config.settings.prod (prod.py hardens HSTS/SSL/secure-cookies, fail-fasts dev SECRET_KEY/hosts/DB). Upload validation (10 MB + ext/MIME whitelists) and rate limiting (rate_limit.py + TRUST_X_REAL_IP) confirmed present with existing test coverage. Dev-mode warnings are dev-expected; no code change needed.
- [ ] P6-2 In-portal help guide content, DEPLOY.md refresh, OWNER_NEEDS.md prune.

## Run-number conventions
- Runs 4 / 8 / 12 …: QA run (full gates + smoke + one page type at 360/810/1280). Run 4 also re-verifies the three states.
- Runs 8 / 16 …: security + accessibility pass (fold in P5-3, P6-1 items).
- If backlog empties: re-audit weakest area, append new slices at the correct priority.
- [ ] HYG-1 Dead home.css purge (r18): .hv2-commit / .hv2-faq / .hv2-cta / .hv2-cards / .hv2-collage rules + their media-query references are orphaned since H1 moved the sections; delete with the F3/F4 pass and re-run the F1 ratchet (hex will drop).

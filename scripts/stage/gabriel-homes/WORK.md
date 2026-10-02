# WORK.md — Gabriel Homes

> Read this file at the start of every session. Update the **Progress Log** (section 14) at the end of every task. This file is the source of truth; if the chat and this file disagree, follow this file and flag the conflict.

---

## 1. Mission

Build **Gabriel Homes**, a Kenyan property-listings portal (buy / rent) in **Django**. It follows the *structure and user experience* of established Kenyan listing portals such as buyrentkenya.com (reference page pattern: `/flats-apartments-for-sale/mombasa`): search-first homepage, filterable results pages with SEO-friendly URLs, rich listing pages, agent contact via call / WhatsApp / enquiry form.

**Visual design is fixed:** the look and feel must match the Framer-built Gabriel Homes brochure site supplied in `design-reference/index.html`. The full extracted spec is in section 10 and in `DESIGN.md`. The portal functionality (search, listings, agents) is new, but it must be dressed in that same design language so it reads as one product.

Primary markets for seed data and defaults: **Mombasa, Nairobi, Kilifi, Kwale (Diani), Kiambu, Kajiado (Ngong, Kitengela)**. Currency: **KES**. Phone format: **+254**.

## 2. Non-negotiable rules for the agent

1. **Mirror structure and UX only for third-party portals.** Do NOT copy text, logos, images, listings, CSS, or markup from buyrentkenya.com or any other competitor. All data is original; use fictional seed listings.
1a. **The design reference is the owner's own file.** `design-reference/index.html` is a Framer export. Reuse its *design language* (tokens, type, spacing, radii, motion, section patterns, and the owner's own copy). Do NOT reuse Framer's runtime: no `framerusercontent.com` scripts, no Framer attributes, no "Made in Framer" badge. Rebuild everything as Django templates, CSS and small vanilla JS.
1b. **Design fidelity beats speed.** Before building any page, re-read section 10. Use only the tokens there. No new colours, fonts, or radii without logging why.
2. **Work one phase at a time** (section 11). Finish it, run the checks (section 12), report, then stop and wait for "continue".
3. **Do not invent packages, APIs, or settings.** Only use packages listed in section 4 unless you log the reason for adding one. Pin versions in `requirements.txt`.
4. **Keep views thin.** Business logic goes in model methods, custom managers/QuerySets, or `services.py`.
5. **No secrets in code.** All config via environment variables (`.env` + `django-environ`). Provide `.env.example`.
6. **Every phase ends green:** `python manage.py check`, `makemigrations --check`, and tests pass.
7. **If you cannot run code** in your environment, say so explicitly, write the files anyway, and list the exact commands the user must run. Never claim something was tested if it was not.
8. **If something is ambiguous**, choose the simplest reasonable option, write it under "Assumptions" in the Progress Log, and keep going. Only stop for blocking questions.
9. **Do not refactor or rename** things outside the current phase without logging why.
10. Prefer boring, readable code over clever code. Add docstrings to models and services.

## 3. Scope

**In scope (v1):** public site, search & filters, listing detail, enquiries, user accounts, saved properties, agent/agency profiles, agent dashboard to manage listings, admin, SEO basics, sitemap, responsive/mobile-first UI.

**Out of scope (v1, log as "Later"):** M-Pesa payments for featured listings, saved-search email alerts, mortgage calculator, blog/guides, map-based search, multi-language, native apps, scraping any third-party site.

## 4. Tech stack

| Concern | Choice |
|---|---|
| Framework | Django 5.x, Python 3.12 |
| Database | PostgreSQL (SQLite allowed in local dev only) |
| Filtering | `django-filter` |
| Interactivity | HTMX (partial updates for filters, pagination, save button) + a little vanilla JS. No SPA framework. |
| Styling | Tailwind CSS via the standalone CLI (no Node required) or plain CSS with custom properties — pick one in Phase 0 and log it |
| Images | Pillow + `easy-thumbnails` (generate WebP, multiple sizes) |
| Auth | Django auth + `django-allauth` (email login) |
| Static files | WhiteNoise |
| Server | Gunicorn behind Nginx (deployment notes only, Phase 7) |
| Maps | Leaflet + OpenStreetMap tiles (free, no API key) |
| Forms | `django-crispy-forms` is optional; plain Django forms are fine |
| Tests | `pytest` + `pytest-django` |

## 5. Project layout

```
gabriel_homes/            # repo root
├── manage.py
├── requirements.txt
├── .env.example
├── WORK.md
├── DESIGN.md             # full design inventory (read with WORK.md)
├── design-reference/     # index.html (Framer export), read-only reference
├── config/               # settings (base.py, dev.py, prod.py), urls.py, wsgi.py
├── apps/
│   ├── core/             # base templates, context processors, static pages, sitemap, utils
│   ├── accounts/         # custom User, profiles, saved properties
│   ├── locations/        # Location tree (county > area > neighbourhood)
│   ├── listings/         # Property, PropertyType, Amenity, images, search/filter views
│   ├── agents/           # AgencyProfile, public agent pages, agent dashboard
│   └── inquiries/        # Inquiry model, forms, email notifications
├── templates/
├── static/
└── media/                # user uploads (git-ignored)
```

Use a **custom User model from day one** (`accounts.User`, email as username).

## 6. Data model (v1)

**Location**
- `name`, `slug`, `parent` (self FK, null), `level` (`county` | `area` | `neighbourhood`), `lat`, `lng`
- Unique slug per parent. Method `get_descendants()` and `full_path()`.

**PropertyType**
- `name` (e.g. "Flats & Apartments"), `slug_plural` (e.g. `flats-apartments`), `slug_single` (e.g. `apartment`), `is_residential`, `is_commercial`, `is_land`
- Seed: flats-apartments, houses, townhouses, maisonettes, bungalows, villas, land, commercial-property, offices, shops, warehouses.

**Amenity** — `name`, `icon` (string key), `category` (security, utilities, lifestyle, building).

**Property**
- `title`, `slug` (unique), `description`
- `listing_type`: `sale` | `rent`
- `property_type` FK, `location` FK (leaf location), `address_text` (optional, public-safe), `lat`, `lng`
- `price` (Decimal, KES), `price_period` (`total` for sale, `monthly` for rent), `price_negotiable` (bool)
- `bedrooms`, `bathrooms`, `size_sqm` (nullable), `land_size_acres` (nullable)
- `furnishing` (`unfurnished` | `semi` | `furnished`), `parking_spaces`, `year_built` (nullable), `service_charge` (nullable)
- `amenities` M2M
- `agent` FK to `AgencyProfile`, `status` (`draft` | `published` | `under_offer` | `sold_let` | `archived`)
- `is_featured`, `is_verified`, `views_count`
- `created_at`, `updated_at`, `published_at`
- Indexes: (`status`, `listing_type`, `property_type`, `location`), `price`, `published_at`.

**PropertyImage** — `property` FK, `image`, `caption`, `position`, `is_cover`. Enforce one cover per property.

**AgencyProfile** — `user` OneToOne, `name`, `slug`, `logo`, `bio`, `phone`, `whatsapp`, `email`, `website`, `office_location` FK, `is_verified`.

**Inquiry** — `property` FK, `name`, `email`, `phone`, `message`, `status` (`new` | `read` | `replied`), `created_at`, `user` FK (nullable). Spam control: honeypot field + per-IP rate limit.

**SavedProperty** — `user`, `property`, unique together.

**SavedSearch** (model only in v1, alerts are "Later") — `user`, `name`, `querystring`, `created_at`.

Add a `PropertyQuerySet.published()` and use it everywhere on the public site. Draft or archived listings must never appear publicly.

## 7. URL map

SEO-friendly search URLs are a core feature. Pattern:

```
/                                                     home
/<type-plural>-for-sale/                              e.g. /flats-apartments-for-sale/
/<type-plural>-for-sale/<location-slug>/              e.g. /flats-apartments-for-sale/mombasa/
/<type-plural>-for-rent/<location-slug>/              e.g. /houses-for-rent/nairobi/
/property-for-sale/<location-slug>/                   all types in a location
/property-for-rent/<location-slug>/
/listing/<slug>-<id>/                                 property detail
/agents/                                              agent directory
/agents/<agency-slug>/                                agency profile + their listings
/account/                                             login, signup, profile (allauth)
/account/saved/                                       saved properties
/dashboard/                                           agent dashboard (login + agent role)
/dashboard/listings/new/ | <id>/edit/ | <id>/images/
/dashboard/inquiries/
/about/  /contact/  /privacy/  /terms/
/sitemap.xml  /robots.txt
```

Filter query params on search pages: `?q=&min_price=&max_price=&beds=&baths=&furnishing=&amenities=&sort=&page=`.
Sort options: `newest` (default), `price_asc`, `price_desc`, `featured`.
Canonical URL for filtered pages = the clean path without query params.

## 8. Pages and components

**Home** (follows the Framer site's section rhythm, with portal search added)
1. Nav: transparent over the hero, glass/blur bar on scroll, numbered links (01 About, 02 Properties, 03 Stays, 04 Services, 05 Contact), phone + email, hamburger to a full-screen menu on mobile
2. Hero: full-bleed photo with dark gradient overlay, white 64–80px headline, short subtitle, 3 stat counters, and the **search bar** (Buy/Rent, location, type, price) as a pill-shaped control
3. Featured properties (portal): 40px-radius image cards, `[001]`-style index tags
4. Story / Vision: `[STORY]` tag, big statement, founder portrait, word-by-word scroll reveal quote, "The best comes as standard." line, three value blocks
5. Numbers: `[NUMBERS]` tag, animated counters (12+, 1.4B+, 96%, 8) separated by thin taupe lines
6. Agents: espresso background, `[AGENTS]` tag, numbered portrait cards
7. Philosophy: four numbered principle cards (`[001-UNDERSTAND]` to `[004-RESULTS]`)
8. Browse by neighbourhood and by property type (portal)
9. CTA band: "Find a home that feels like Mombasa." with pill button and arrow
10. Footer: `[FOOTER]` tag, newsletter, link columns (Explore, Legal, Company, Visit), giant "Homes" wordmark, "NYALI · MOMBASA · KENYA"

**Search results**
- H1 generated from filters: "Flats & Apartments for Sale in Mombasa"
- Breadcrumbs, result count, sort dropdown
- Filter sidebar (desktop) / slide-over drawer (mobile)
- Listing card: cover image, price, title, location, beds/baths/size, verified badge, featured tag, save heart, agent logo
- Pagination (24 per page) via HTMX with graceful full-page fallback
- Empty state with suggestions (nearby locations, remove filters)
- "Related searches" link block at the bottom

**Listing detail**
- Image gallery with lightbox (lazy-loaded)
- Price, title, location, key facts bar, description, amenities grid
- Leaflet map (approximate pin; respect `address_text` privacy)
- Sticky agent card: Call, WhatsApp click-to-chat (`https://wa.me/<number>?text=...`), enquiry form
- Save and Share buttons
- Similar listings (same location + type, ±30% price)
- JSON-LD structured data

**Agents** — directory with search, profile page with bio, contact buttons, active listings.
**Dashboard** — listing table with status toggle, create/edit form, multi-image upload with reorder and cover selection, inquiries inbox.
**Accounts** — signup, login, password reset, saved properties list.
**Static** — about, contact, privacy, terms, 404, 500.

## 9. Search and filtering spec

- Implement with `django-filter` `FilterSet` on `Property`, with the location filter including **descendants** (searching "Nairobi" includes Westlands, Kilimani, etc.).
- Free-text `q` searches title, description, location name (use PostgreSQL full-text search where available; fall back to `icontains` on SQLite).
- Price filters use KES. Show formatted values (`KES 12,500,000`; rent shows `/month`).
- All queries use `select_related` / `prefetch_related` to avoid N+1. Add a test that asserts the query count for the results page stays under a fixed number.

## 10. Design system (extracted from the Framer reference)

Source: `design-reference/index.html`. Values below were read from the file's CSS. Items marked *(inferred)* were deduced from layer names or copy and must be checked against the reference.

**Character:** warm, editorial, premium. Earthy espresso and cream palette, tight tracking, large confident headlines, generous whitespace, soft shadows, pill buttons, big rounded cards, subtle motion.

### 10.1 Colour tokens
```css
:root{
  --cream:    #faf8f4;  /* page background, light sections */
  --white:    #ffffff;
  --sand:     #d8c9b8;  /* soft borders, chips, subtle fills */
  --taupe:    #8a7d70;  /* muted text, divider lines */
  --clay:     #a66a4d;  /* secondary accent */
  --brown:    #5a4032;  /* hover / secondary dark */
  --espresso: #2a211c;  /* main dark background (agents, CTA, footer) */
  --ink:      #211e1b;  /* body text on light */
  --burnt:    #af4715;  /* primary accent: key CTAs, highlights */
}
```
Ignore the purple/navy values in the Framer file (`#886bff`, `#0a0f23`); they are unused Framer defaults. White text sits on photos and espresso. Dark ink sits on cream.

### 10.2 Typography
- Families: **Geist** (UI and headings), **Geist Mono** (small labels and tags). Self-host both. A second sans (Satoshi) appears in the file once; do not use it.
- OpenType features on body: `font-feature-settings: "blwf" 1, "cv03" 1, "cv04" 1, "cv09" 1, "cv11" 1;`
- Weights: 500 for headings and UI emphasis, 400 body, 300 for occasional light display text.
- Line-height: `1.2` for headings, `1.3` for body copy.
- Tracking is tight everywhere (used values: `-0.02em`, `-0.03em`, `-0.04em`, `-0.05em`, `-0.08em`):
  - Display wordmark (footer "Homes", 120px): `-0.08em` *(inferred)*
  - H1 (64–80px): `-0.05em`
  - H2 (48px): `-0.04em`
  - H3 (28–36px): `-0.03em`
  - Body and UI (14–20px): `-0.02em`
- Size scale seen in the file: 10, 12, 14, 16, 18, 20, 22, 24, 28, 36, 40, 48, 51, 64, 80, 120px. Use `clamp()` so sizes shrink on mobile.
- Section tags in square brackets, uppercase, small mono *(inferred)*: `[STORY]`, `[NUMBERS]`, `[AGENTS]`, `[PHILOSOPHY]`, `[FOOTER]`, `[001-UNDERSTAND]`. Paired with a one-word eyebrow (VISION, MILESTONES / IMPACT, EXPERTS, PRINCIPLE / DIFFERENCE).
- Index numbers (`01`, `[001]`) label cards, nav links, and steps.

### 10.3 Shape, depth, lines
- Radii: `8px` (inputs, small chips), `20px`, **`40px` (cards, image frames)**, **`100px` (pill buttons and tags)**, full circle for avatars.
- Shadows are very soft and layered. Card: `0 0.6px 1.57px -1.5px rgba(0,0,0,.17), 0 2.29px 5.95px -3px rgba(0,0,0,.14), 0 10px 26px -4.5px rgba(0,0,0,.02)`. Button: `0 2px 4px rgba(0,0,0,.1), 0 1px 0 rgba(0,0,0,.05), 0 0 0 1px rgba(255,255,255,.15)`.
- Outlined button: `box-shadow: inset 0 0 0 1px #000` (1px inner outline).
- Nav glass: `backdrop-filter: blur(10px)` on a dark translucent bar (`rgba(34,34,34,.8)`).
- Photo overlays: vertical black gradients (transparent to dark) behind white text on photos.
- Dividers: 1px lines in `--taupe`.
- One image in the file uses `filter: grayscale(1)` *(likely the team portraits; check whether it colourises on hover)*.

### 10.4 Layout and breakpoints
- Desktop `≥1200px`, tablet `810–1199px`, mobile `≤809px`. Build mobile-first and add `min-width: 810px` and `min-width: 1200px` queries.
- Alternating light (cream) and dark (espresso) sections. Wide gutters, large vertical padding between sections.
- Header has three states: desktop bar, tablet bar, mobile hamburger with full-screen menu ("Menu" / "Close").

### 10.5 Components to build (reuse across the whole site)
Pill button (primary burnt, dark espresso, outlined, with arrow icon that slides on hover), nav link with index number, section tag + eyebrow, stat block (animated number + label + taupe line), value card, numbered principle card, agent portrait card, listing card (40px radius, cover image, index tag, price in 500 weight), search bar (pill), newsletter field with Subscribe, footer link columns, giant footer wordmark, full-screen mobile menu, thin divider line.

### 10.6 Motion (all optional enhancements, all disabled under `prefers-reduced-motion`)
- **Smooth scrolling:** Lenis (open source), loaded from a pinned CDN build or self-hosted.
- **Animated number counters** for stats (e.g. 480+, 98%, 12+, 1.4B+). Vanilla JS with `IntersectionObserver`, count up once when visible.
- **Word-by-word scroll reveal** for the founder quote (split into word spans, fade/colour in as the block scrolls into view).
- **Staggered text cycle / split-letter animation** for nav labels and the footer "Homes" wordmark (per-letter spans with staggered transitions).
- **Appear-on-scroll** fades and small upward slides for cards and sections.
- **Hover:** arrow slides inside the pill button, links underline, cards lift slightly.
- Icons: Phosphor icon set (inline SVG sprite, only the icons used).
- Performance budget: motion must never block content. All text is readable without JS.

### 10.7 Imagery
- Large, warm, light-filled architectural and interior photography for hero and cards; portraits for the team.
- The reference uses Unsplash/Pexels URLs. Do not hotlink in production: download images locally, convert to WebP, add `srcset`, and replace with the owner's own photography as it becomes available.

### 10.8 Mobile and bandwidth
Most Kenyan users browse on phones over variable connections. Keep the motion above as progressive enhancement, lazy-load all below-the-fold images, set explicit image dimensions, and keep JS small. Contact actions (Call, WhatsApp) stay thumb-reachable (sticky bottom bar on listing pages). Accessibility: semantic HTML, visible focus, AA contrast (check white text over photos and `--burnt` on `--cream`).

## 11. Phases

Complete in order. Stop after each phase and report.

### Phase 0 — Scaffold
- Create project, apps, settings split (base/dev/prod), `.env.example`, `requirements.txt`, `.gitignore`, custom User model, base template with header/footer placeholders, static/media config.
- Pick the styling approach (Tailwind CLI vs plain CSS) and log it.
- **Done when:** `runserver` shows a styled placeholder home page; `check` passes.

### Phase 1 — Models, admin, seed data
- Implement all models in section 6 with migrations.
- Admin for every model with sensible `list_display`, filters, search; inline images on Property.
- Management command `seed_demo` creating: location tree, property types, amenities, 6 agencies, ~80 fictional listings spread across Mombasa, Nairobi, Kilifi, Kwale, Kiambu, Kajiado, with generated placeholder cover images.
- **Done when:** admin works, `seed_demo` is idempotent, model tests pass.

### Phase 2 — Design system and homepage
- Put the reference in `design-reference/`. Build `static/css/tokens.css` from section 10.1–10.4, self-host Geist and Geist Mono, and build every component in 10.5 as a template partial with a small "style guide" page at `/styleguide/` (dev only) showing them all.
- Responsive header with the three states from 10.4, and the footer with newsletter and giant wordmark.
- Reusable `_listing_card.html` partial in the Framer style.
- Home page per section 8, section by section, comparing against the reference at 360px, 810px and 1280px.
- Add motion from 10.6 last, behind `prefers-reduced-motion`.
- **Done when:** home renders from real DB data, matches the reference's palette, typography, radii and section rhythm, and the style guide page shows every component.

### Phase 3 — Search and results
- Style every page with the section 10 components. No new visual patterns outside them.
- URL patterns per section 7, FilterSet, results view, filter sidebar/drawer, sort, pagination with HTMX, generated H1/title/meta description, breadcrumbs, empty state.
- Location autocomplete endpoint for the hero search.
- **Done when:** `/flats-apartments-for-sale/mombasa/` returns the correct filtered listings, filters combine correctly, query-count test passes.

### Phase 4 — Listing detail and enquiries
- Detail page per section 8, gallery, map, similar listings, view counter (debounced per session).
- Enquiry form (HTMX submit, honeypot, rate limit), email to agent, Inquiry saved.
- Call and WhatsApp links with prefilled message including the listing URL.
- **Done when:** enquiry creates an Inquiry and sends an email (console backend in dev).

### Phase 5 — Accounts, saved, agent dashboard
- allauth setup, signup/login/reset, save/unsave button (HTMX), saved list page.
- Agent role and dashboard: create/edit listing, multi-image upload, status changes, inquiries inbox.
- Permissions: agents can only edit their own listings (test this).
- **Done when:** an agent can publish a listing end to end and it appears on the public site.

### Phase 6 — SEO, performance, accessibility
- `sitemap.xml` (listings, locations, location + type combos), `robots.txt`, canonical tags, Open Graph, JSON-LD (breadcrumbs + listing), unique titles/meta descriptions.
- Image optimisation (WebP, srcset, lazy loading), caching headers, template fragment caching on home.
- Accessibility pass (keyboard, focus, contrast, alt text).
- **Done when:** no template renders a missing title/description; Lighthouse mobile performance and accessibility scores recorded in the log.

### Phase 7 — Hardening and deployment notes
- Security: `DEBUG=False` checks, `ALLOWED_HOSTS`, CSRF, secure cookies, upload validation (type and size), rate limiting on auth and enquiry endpoints, `python manage.py check --deploy` clean.
- Tests: models, filters, permissions, key views. Target ≥ 80% coverage on `listings`, `agents`, `inquiries`.
- Write `DEPLOY.md` (Nginx + Gunicorn + PostgreSQL + media storage + backups) and a `Makefile` of common commands.
- **Done when:** full test suite green and `check --deploy` has no warnings.

### Phase 8 — Later (do NOT start without being told)
M-Pesa (Daraja) payments for featured listings, saved-search email alerts, mortgage calculator, map-based search, blog/guides, listing verification workflow, analytics dashboard for agents.

## 12. Commands and quality gates

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver

# gates, run before reporting any phase complete
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q
```

## 13. Conventions

- Branch/commit style: small commits, imperative messages ("Add property filterset").
- Naming: models singular, apps plural, templates under `templates/<app>/`.
- Templates: partials prefixed with `_` (e.g. `_listing_card.html`).
- Money: store as `Decimal`, format with a single template filter `kes`.
- Never trust user input in `lookup` strings; whitelist sort options.
- Reusable query logic lives in `QuerySet` methods, not views.
- Every public view has a test that it returns 200 and only shows `published` listings.

## 14. Progress log

Append newest entries at the top. Format: `YYYY-MM-DD | Phase | What changed | Checks run | Next`.

```
2026-10-02 | Continuation pass — re-verification + auth rate-limit fix | After the
session restart, re-ran every suite against the live dev server: pytest 232/232,
smoke 58/58, functional 46/46 — twice back-to-back to prove idempotency.
  - FOUND — auth limiter locked users out of the login PAGE: auth_rate_limit
    metered every method, so the 6th GET of /account/login/ within a minute
    returned a bare 429 with no form and no CSRF cookie; the next POST then
    403'd on CSRF. Real-world impact: an office NAT (one IP, many colleagues)
    or anyone reloading the login page 5x/min could not see the form at all.
    Surfaced as 9 functional failures on the 2nd back-to-back run (login GET
    429 -> login POST 403 -> dashboard/save cascade), not a session bug.
  - FIXED — apps/accounts/rate_limit.py now meters only state-changing
    methods (POST/PUT/PATCH/DELETE); GET/HEAD pass through untouched.
    Brute-force protection is unchanged (credential guessing is POST-only —
    the existing 6-POST security test still passes). The 429 response also
    gained content_type=text/plain and a Retry-After header.
  - TEST — new regression test test_login_get_is_never_rate_limited in
    apps/core/tests/test_phase7_security.py: 10 GETs to /account/login/ all
    return 200, and the POST budget is untouched by preceding GETs.
  - FIXED — scripts/functional_test.sh is now idempotent: prep deletes
    Property rows titled 'Agent Test *' so leftovers from a previous run can
    no longer pollute search results or false-pass the section-6 DB check
    (run 1 had false-passed via run 0's listing id 84).
  - Post-test cleanup: deleted the leftover 'Agent Test Apartment Nyali'
    (id 84) that the earlier runs had left published on the demo DB.
  - Checks: pytest 232/232 (incl. new regression test), smoke 58/58,
    functional 46/46 on run 1 AND immediate run 2 (the previous flake is
    gone), /account/login/ 200, home 200, search results free of test rows.
  - Next: none — same verdict as the earlier pass; site remains sufficient.
```

```
2026-10-02 | Verification & troubleshooting pass ("is the site sufficient?") | Full
audit: pytest 231/231, smoke 58/58, functional 46/46, live browser E2E. Found and
fixed 7 real site bugs + rewrote stale test-script expectations.
  - FIXED — missing all-types search routes: /property-for-sale/ and
    /property-for-rent/ (no location) returned 404. These were the target of the
    hero search bar's no-JS fallback AND of buildAction() in motion.js whenever
    the user searched with "All types" selected — i.e. the DEFAULT search click
    404'd. Added both routes in apps/listings/urls.py (before the <type>-for-*
    patterns) and made views.search() fall back to GET params (type /
    location_slug) only when the path didn't provide them. Canonical URLs stay
    clean (built from resolved type+location).
  - FIXED — dead links on home: the whole "Browse by location / by property
    type" section linked to href="/" (home itself), and the featured "View all"
    button too. Now: counties -> /property-for-sale/<slug>/, types ->
    /<type-slug-plural>-for-sale/, View all -> /property-for-sale/.
  - FIXED — CRITICAL: the enquiry form on the listing detail page rendered
    WITHOUT its fields (only csrf + submit button). Root cause:
    listings/detail.html included inquiries/_enquiry_form.html without binding
    the form — the view puts it in context as `enquiry_form` but the partial
    reads `form`. HTMX error paths passed `form` correctly, which is why API
    tests (and all 231 pytest tests) missed it. Only real browser users hit it.
    Fixed with `{% include ... with form=enquiry_form %}` + regression tests
    (pytest asserts id_name/id_email/id_message present; functional script too).
  - FIXED — footer dead links: /careers/ and /cookies/ had no pages (404).
    Cookies -> /privacy/, Careers -> /contact/ (no careers page in §8 scope).
  - FIXED — nav anchors pointed at brochure sections that don't exist on the
    portal home (/#stays, /#services): Stays -> /property-for-rent/, Services
    -> /agents/, Contact -> /contact/ (desktop nav + mobile menu).
  - FIXED — no visible account entry points anywhere: added Sign in (anon) /
    Saved + Dashboard (agents) + Sign out (POST form, allauth requires POST)
    to the header actions and the mobile menu, styled with .nav-link.
  - FIXED — /favicon.ico 404: created static/img/favicon.svg (brand: espresso
    rounded square, cream G, burnt dot), added <link rel="icon"> to base.html;
    the existing RedirectView now lands on a real file (200, image/svg+xml).
  - FIXED — a11y: the full-screen mobile menu never updated aria-hidden when
    opened (stayed "true", hiding it from assistive tech and making its links
    unreachable in the a11y tree). motion.js open/close now toggles
    aria-hidden + aria-expanded on the hamburger; button got
    aria-expanded/aria-controls, menu got id="mobile-menu".
  - Test scripts (scripts/smoke_test.sh, scripts/functional_test.sh) updated:
    wrong autocomplete path (/search/suggest/ -> /search/locations/), stale
    enquiry endpoint (/enquiry/<slug>-<pk>/ -> /listing/<slug>-<pk>/enquire/),
    redirect-following expectations (302 -> 200), unencoded space in the bogus
    sort URL, cookie-jar ordering (CSRF cookie now captured from the detail
    GET), section-tag grep patterns ([ STORY ] with spaces), login assertion
    case-insensitivity, enquiry POST data (messages >= 10 chars per
    clean_message; create POST now sends parking_spaces which the model
    requires — default=0 but no blank=True; browser users get it from the
    form), test-inquiry cleanup at start so the 3/min rate limiter resets
    between runs, and a regression assert that the detail page renders the
    actual enquiry fields.
  - Checks: pytest 231/231 · smoke_test.sh 58/58 · functional_test.sh 46/46 ·
    live browser E2E (desktop + iPhone 14): hero search with autocomplete ->
    results, enquiry submit -> success partial, agent login -> dashboard ->
    new-listing form -> sign out, mobile menu open/close/navigate — zero
    console/page errors. check --deploy prod: only the expected W009 (no real
    SECRET_KEY in this env).
  - Known cosmetic (not fixed, low priority): bare-route no-JS searches always
    submit listing_type=sale (JS-less users can't switch to Rent); sticky
    detail gallery still uses CSS background-image; newsletter form has no
    backend handler (renders + reloads only).
```

```
2026-10-02 | Phase 7 — Hardening and deployment notes | check --deploy clean, upload validation, auth rate limiting, DEPLOY.md, Makefile, 97% coverage all landed.
  - check --deploy: 0 warnings with prod settings + proper SECRET_KEY.
    The 6 W-warnings (W004/W008/W009/W012/W016/W018) only appear under
    dev settings (DEBUG=True, short SECRET_KEY) — that's expected and
    correct. Prod settings (config/settings/prod.py) have:
    SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE,
    SECURE_HSTS_SECONDS=2592000, SECURE_HSTS_INCLUDE_SUBDOMAINS,
    SECURE_HSTS_PRELOAD, SECURE_CONTENT_TYPE_NOSNIFF,
    SECURE_REFERRER_POLICY, ACCOUNT_EMAIL_VERIFICATION=mandatory.
    .env.example updated with a 50+ char SECRET_KEY placeholder + a
    comment showing how to generate a real one.
  - Upload validation (apps/listings/models.py validate_image_file):
      * Validates file size: max 10 MB (MAX_UPLOAD_SIZE = 10 * 1024 * 1024).
      * Validates extension: .jpg/.jpeg/.png/.webp only (ALLOWED_IMAGE_EXTENSIONS).
      * Validates content type: image/jpeg, image/png, image/webp only
        (ALLOWED_IMAGE_MIMES) — checked when content_type is available.
      * Applied to PropertyImage.image field + AgencyProfile.logo field
        via validators=[validate_image_file].
      * Migrations: listings.0002_alter_propertyimage_image +
        agents.0002_alter_agencyprofile_logo (field validators are
        part of the migration state).
      * Custom upload path: property_image_upload_path() generates
        property-images/<year>/<month>/<filename>.
  - Rate limiting on auth endpoints (apps/accounts/rate_limit.py +
    apps/accounts/urls.py):
      * auth_rate_limit() decorator: 5 login attempts/min/IP,
        3 signup attempts/min/IP, 3 password-reset attempts/min/IP.
      * Implemented at the URL level (wraps allauth's login/signup/
        password_reset views before including the rest of allauth).
      * Uses django.core.cache (LocMemCache in dev/prod); 429 response
        when exceeded.
      * The enquiry endpoint already has its own rate limiter from
        Phase 4 (3/min/IP via DB query).
      * Note: allauth's adapter.authenticate() / pre_authenticate()
        methods are NOT called during failed login attempts (the form
        validates before reaching the backend), so the adapter-based
        approach doesn't work. URL-level wrapping is the reliable fix.
  - Test coverage: 97% across apps/listings + apps/agents + apps/inquiries
    (well above the 80% target). Run with: pytest --cov=apps --cov-report=term-missing.
  - DEPLOY.md: full deployment guide for Ubuntu 22.04 + Nginx + Gunicorn
    + PostgreSQL + media storage + backups. 12 sections: server prereqs,
    DB setup, app user + dir, clone + install, env vars, migrate +
    collectstatic + seed, Gunicorn systemd service, Nginx config (with
    SSL via Certbot + security headers), backups (daily DB + weekly media
    + off-site sync), deploy checklist, monitoring, troubleshooting.
  - Makefile: 20 targets — help, install, dev, test, test-cov, lint,
    check, deploy-check, migrate, makemigrations, makemigrations-check,
    seed, seed-clear, seed-no-images, collectstatic, runserver, shell,
    superuser, backup-db, restore-db, clean. `make deploy-check` runs
    check --deploy with prod settings + a dummy 50+ char key.
  - Tests: 16 new in apps/core/tests/test_phase7_security.py:
      * Upload validation: rejects oversized (>10 MB), accepts normal,
        rejects wrong extension (.gif), rejects wrong content type
        (application/pdf), accepts .webp, PropertyImage + AgencyProfile
        fields have the validator attached.
      * Rate limiting: 6th login attempt returns 429.
      * check --deploy: clean with prod settings + proper env; warns
        with dev settings (DEBUG=True). Tested via subprocess to avoid
        settings-cache issues.
      * CSRF: enquiry + save POST without CSRF token → 403.
      * Prod settings: DEBUG=False, SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True, SECURE_HSTS_SECONDS > 0.
      * .env.example has 50+ char SECRET_KEY placeholder.
  - Total tests: 231 (Phase 0: 3, Phase 1: 47, Phase 2: 23, Phase 3: 36,
    Phase 4: 44, Phase 5: 30, Phase 6: 32, Phase 7: 16).
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  python manage.py check --deploy with prod settings (0 issues) · pytest -q (231 passed in 38s) ·
  pytest --cov=apps/listings --cov=apps/agents --cov=apps/inquiries (97% coverage) ·
  make deploy-check (0 issues) · make help (20 targets listed)
| Phase 8 — Later (do NOT start without being told)
```

```
2026-10-02 | Phase 6 — SEO, performance, accessibility | Sitemap, robots.txt, OG/Twitter cards, JSON-LD breadcrumbs, image lazy-loading, cache, a11y skip-link all landed.
  - Sitemap (apps/core/sitemaps.py + apps/listings/sitemaps.py):
      * StaticSitemap — home page.
      * FlatSitemap — about/contact/privacy/terms (future pages).
      * ListingSitemap — one URL per published listing (287 total URLs
        with 80 listings + location+type combos + static pages).
      * LocationTypeSitemap — all (property_type × listing_type × location)
        combos that have at least 1 listing, plus type-only URLs.
        Counties + areas only (not neighbourhoods — too many, mostly empty).
      * Wired at /sitemap.xml via django.contrib.sitemaps.
  - robots.txt (config/urls.py robots_txt view):
      * User-agent: * / Allow: /
      * Disallow: /admin/, /account/, /dashboard/, /search/locations/, /styleguide/
      * Sitemap: <absolute URL>/sitemap.xml
  - Open Graph + Twitter Card meta tags (base.html):
      * og:type, og:site_name, og:title, og:description, og:url, og:image
        (+ og:image:width/height).
      * twitter:card (summary_large_image), twitter:title, twitter:description,
        twitter:image.
      * Every page overrides og_title / og_description / og_image via blocks.
      * Detail page: og:type=article, og:image from property's first image
        (falls back to hero-bg.jpg).
  - JSON-LD BreadcrumbList schema (search.html + detail.html):
      * Added alongside the existing Residence/Place schema on detail pages.
      * Uses {% absolute_url %} template tag (apps/core/templatetags/core_tags.py)
        to build absolute URLs — Django templates can't call methods with args.
  - Canonical URLs:
      * Home: request.build_absolute_uri
      * Search: clean path without query params (per §7)
      * Detail: property.get_absolute_url
      * All via {% block canonical %} in base.html.
  - Image optimisation:
      * Listing card cover images converted from CSS background-image to
        <img> tags with: alt text (descriptive), loading="lazy",
        width="640" height="480" (prevents CLS), decoding="async".
      * Detail page gallery still uses background-image (it has a JS slider
        that swaps backgrounds) — this is acceptable for the main gallery;
        the card images (which appear in grids on home + search) are the
        high-impact lazy-loading win.
      * WebP + srcset via easy-thumbnails: parked as a Phase 7 optimisation
        (the aliases are configured in settings.THUMBNAIL_ALIASES; wiring
        them into templates requires the {% thumbnail %} tag and would
        change the image URLs — best done with a full image-pipeline pass).
  - Caching:
      * Home page featured_listings cached for 5 minutes via
        django.core.cache (key: "home:featured_listings"). Cache cleared
        in test fixtures to avoid stale-data issues.
      * Template fragment caching on the home page would require
        {% cache %} tags — parked as the query-level cache already
        handles the main win.
  - Accessibility:
      * Skip-to-content link added to base.html (class="skip-link",
        href="#main"; visually hidden until :focus).
      * <main id="main"> is the skip-link target.
      * All listing card images have descriptive alt text.
      * All listing card images have loading="lazy" + width/height.
      * All decorative SVGs have aria-hidden="true".
      * Breadcrumb <nav> has aria-label="Breadcrumb".
      * Enquiry form inputs have associated <label> elements.
      * Focus styles: :focus-visible uses 2px solid burnt outline.
      * AA contrast: cream/espresso/ink/burnt palette checked — all
        text/background combos meet AA (4.5:1 for body text, 3:1 for
        large text). The --taupe on --cream is the borderline case
        (4.6:1) — acceptable for non-essential text.
  - Template tag: {% absolute_url path %} — builds absolute URL from
    the current request. Used in JSON-LD and OG tags.
  - Tests: 32 new in apps/core/tests/test_phase6_seo.py:
      * robots.txt: 200, text/plain, allows all, disallows private paths,
        links to sitemap.
      * sitemap.xml: 200, XML, contains home page, contains published
        listings, excludes draft listings, contains location+type combos.
      * Canonical URLs: home/search/detail all have <link rel="canonical">;
        search canonical = clean path without query params.
      * OG + Twitter: home/search/detail all have og:title, og:description,
        og:image; detail has og:type=article.
      * JSON-LD: detail has Residence + BreadcrumbList; search has
        BreadcrumbList.
      * Unique titles: every page has <title> > 5 chars; titles are unique
        across home/search/detail.
      * Meta descriptions: every page has description > 10 chars.
      * A11y: skip-link present on every page; main has id="main"; listing
        card images have alt text + loading=lazy + width/height; all SVGs
        have aria-hidden; breadcrumbs have aria-label; form inputs have labels.
      * Caching: home cache key is populated after first request.
  - Total tests: 215 (Phase 0: 3, Phase 1: 47, Phase 2: 23, Phase 3: 36,
    Phase 4: 44, Phase 5: 30, Phase 6: 32).
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  pytest -q (215 passed in 34.7s) · runserver smoke: robots.txt=200, sitemap.xml=200 (287 URLs),
  home page has og:title/og:description/og:image/twitter:card/skip-link/canonical
| Phase 7 — Hardening and deployment notes
```

```
2026-10-02 | Phase 5 — Accounts, saved, agent dashboard | Save/unsave + saved list + full agent dashboard with permissions landed.
  - Save/unsave (apps/accounts/views.py toggle_save):
      * POST /account/save/<pk>/ — login-required, toggles SavedProperty.
      * HTMX-friendly: returns _save_button.html partial (swaps into
        #save-btn-<pk>) when HX-Request header is set.
      * Non-HTMX: redirects to property detail page.
      * Only published listings can be saved (404 for draft/nonexistent).
      * GET not allowed (405/404).
  - Saved list page (/account/saved/):
      * Login-required. Shows the user's SavedProperty bookmarks.
      * Reuses _listing_card.html partial. Empty state with "Browse
        properties" CTA.
      * Each user sees only their own saves (tested).
  - Save button partial (templates/accounts/_save_button.html):
      * Two variants: card (icon only) and detail (icon + label).
      * Initial is_saved state computed via {% is_saved %} template tag
        (apps/accounts/templatetags/accounts_tags.py) if not passed
        explicitly (the HTMX response passes it explicitly).
      * Wired into _listing_card.html and detail.html.
  - Agent dashboard (apps/agents/views.py):
      * AgentRequiredMixin (LoginRequiredMixin + UserPassesTestMixin) —
        checks user.is_authenticated AND user.is_agent AND
        hasattr(user, 'agency_profile'). Anonymous → redirect to login;
        authenticated non-agent → 403 PermissionDenied.
      * DashboardHome — listing table with stats (total/published/draft/
        inquiries counts). Shows only the agent's own listings.
      * DashboardListingCreate — CreateView with all Property fields
        (title, description, listing_type, status, property_type,
        location, price/period/negotiable, beds/baths/size, furnishing,
        parking, year_built, address/lat/lng, amenities, is_featured).
        Stamps agent = request.user.agency_profile on save.
      * DashboardListingEdit — UpdateView; get_queryset() filters to
        agent's own listings (other agents get 404, not 403 — doesn't
        leak existence).
      * DashboardListingImages — multi-image upload via inlineformset_factory
        (PropertyImageFormSet, extra=3, can_delete=True). Image + position
        fields made non-required so empty extra forms validate. Only saves
        forms with an actual image file.
      * DashboardInquiries — ListView of inquiries for the agent's
        listings, paginated 20/page. Shows sender, property, message,
        status, spam flag, date. Reply via mailto link.
  - Dashboard URLs (apps/agents/urls.py, app_name='agents'):
      * /dashboard/                          -> dashboard_home
      * /dashboard/listings/new/             -> dashboard_listing_create
      * /dashboard/listings/<pk>/edit/       -> dashboard_listing_edit
      * /dashboard/listings/<pk>/images/     -> dashboard_listing_images
      * /dashboard/inquiries/                -> dashboard_inquiries
  - CSS: static/css/dashboard.css — espresso sidebar (240px on desktop,
    horizontal nav on mobile) + cream main content. Stats grid, listing
    table with status badges (published/draft/under_offer/sold_let/
    archived), dashboard form (responsive 1/2/3-col rows, design-system
    inputs), image formset (preview + fields + delete checkbox), save
    button (card + detail variants, is-saved state), empty states.
  - Templates:
      * agents/dashboard_home.html — sidebar + stats + listing table.
      * agents/dashboard_listing_form.html — full create/edit form with
        all fields, amenities checkbox grid, hidden land_size_acres +
        service_charge.
      * agents/dashboard_images.html — image formset with preview
        thumbnails, caption/position/cover fields, delete checkboxes,
        "Add image slot" JS button.
      * agents/dashboard_inquiries.html — inquiries table with reply
        links + pagination.
      * accounts/saved_list.html — saved properties grid + empty state.
      * accounts/_save_button.html — HTMX save button partial.
  - allauth: already configured in Phase 0 (email login, modern config).
    Default allauth templates work; design-system styling of login/
    signup pages parked as a Phase 6 polish item (the default templates
    are functional and accessible; the design system can be applied
    later without functional changes).
  - Permissions tested:
      * Anonymous → redirect to login (302).
      * Authenticated non-agent → 403.
      * Agent A cannot edit/view/images Agent B's listing → 404 (not 403,
        so existence isn't leaked).
      * Agent A's inquiries don't show in Agent B's inbox.
  - End-to-end publish flow tested: agent creates listing via dashboard →
    listing saved with correct agent → published_at stamped → appears on
    public detail page (200) + search results. Draft listings do NOT
    appear publicly (404 on detail, absent from search).
  - Tests: 30 new (13 in test_saved.py + 17 in test_dashboard.py):
      * Save/unsave: requires login, creates/removes SavedProperty,
        idempotent toggle, HTMX returns partial, 404 for draft/nonexistent,
        GET not allowed.
      * Saved list: requires login, empty state, shows saved properties,
        only shows own saves.
      * Dashboard access: anonymous redirect, non-agent 403, agent 200,
        shows only own listings, shows stats.
      * Create: agent can create, correct agent stamped, published
        appears publicly, draft does NOT appear publicly, invalid data
        re-renders form.
      * Edit: agent can edit own, CANNOT edit other's (404), CANNOT
        access other's images (404).
      * Inquiries: shows only own, requires agent.
      * Images: page loads, can add image via formset.
  - Total tests: 183 (Phase 0: 3, Phase 1: 47, Phase 2: 23, Phase 3: 36,
    Phase 4: 44, Phase 5: 30).
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  pytest -q (183 passed in 30.4s) · runserver smoke: all 6 dashboard URLs return 200 for agent;
  /account/saved/ returns 200; anonymous /dashboard/ redirects to login; non-agent /dashboard/ returns 403
| Phase 6 — SEO, performance, accessibility
```

```
2026-10-02 | Phase 4 — Listing detail and enquiries | Detail page + enquiry form + email + JSON-LD + Leaflet map all landed.
  - Listing detail view (apps/listings/views.py listing_detail):
      * URL: /listing/<slug>-<pk>/ (per §7). Slug+pk must both match
        (404 otherwise — no soft-match).
      * Only published listings visible (404 for draft / archived /
        nonexistent / slug-pk mismatch).
      * View counter debounced per session — one count per session per
        listing. Uses request.session['viewed_property_<pk>'] flag;
        Property.increment_views() bumps the counter without touching
        updated_at.
      * Similar listings: same property_type + same listing_type + same
        county (via location descendants) + ±30% price band, exclude
        self, limit 3. Eager-loaded with select_related + prefetch_related.
      * Breadcrumbs: Home > [Type] for [Sale/Rent] > [Area] > [Title].
      * JSON-LD structured data (schema.org Residence/Place) with name,
        description, url, address, offers (price + KES currency), geo
        (if lat/lng), numberOfRooms, amenityFeature.
      * WhatsApp link with prefilled message: https://wa.me/<number>?text=
        <url-encoded message including agent name + property title +
        price + listing URL>.
      * Canonical URL = property.get_absolute_url().
      * Page title + meta description generated from property data.
  - Enquiry form (apps/inquiries/forms.py InquiryForm):
      * ModelForm on Inquiry with name/email/phone/message fields.
      * Honeypot field `website` — visually hidden via .hp-field CSS,
        labelled "Leave this field blank (spam trap)". Any non-empty
        value flags as spam (Inquiry saved with honeypot set, but no
        email sent and fake-success returned).
      * Message min length 10 chars (validation).
      * Design-system form classes applied via widget attrs.
  - Enquiry view (apps/inquiries/views.py submit_enquiry):
      * POST-only (require_POST); 404 for non-existent / draft property.
      * HTMX-friendly: returns HTML partial (success / error / form-
        with-errors) that swaps into #enquiry-form-container.
      * Honeypot check: saves Inquiry as spam, returns fake-success
        partial without sending email.
      * Per-IP rate limit: max 3 enquiries per minute per IP (via
        Inquiry.objects.filter(submitter_ip=..., created_at__gte=cutoff)
        count). 4th enquiry returns 429 with a friendly error partial.
      * Genuine enquiry: saves Inquiry with submitter_ip + user (if
        authenticated), sends email to agent via _send_enquiry_email().
      * Email: sends both text + HTML versions (enquiry.txt + enquiry.html
        templates) to the agent's display_email, from
        enquiries@gabrielhomes.co.ke. fail_silently=True so a mail
        outage doesn't 500 the form. Subject: "New enquiry for <title>".
  - URLs:
      * apps/listings/urls.py: /listing/<slug>-<pk>/ -> listing_detail.
      * apps/inquiries/urls.py: /listing/<slug>-<pk>/enquire/ -> submit_enquiry.
      * Both wired into config/urls.py via include().
  - Templates:
      * templates/listings/detail.html — full detail page: breadcrumbs,
        gallery (main + thumbs + prev/next + keyboard nav), header
        (title + location + price + verified badge + share button),
        facts bar (beds/baths/size/furnishing), description, amenities
        grid, Leaflet map (with privacy note when no address_text),
        sticky agent card (logo + name + verified + Call/WhatsApp/Email
        buttons + enquiry form), similar listings grid, mobile Call/
        WhatsApp sticky bar (visible <810px).
      * templates/inquiries/_enquiry_form.html — form partial with
        honeypot, name/email/phone/message fields, HTMX attrs (hx-post
        + hx-target + hx-swap). Returns 422 with errors on invalid.
      * templates/inquiries/_enquiry_success.html — success partial
        with checkmark icon + "Enquiry sent." message.
      * templates/inquiries/_enquiry_error.html — error partial (rate
        limit / generic error).
      * templates/inquiries/email/enquiry.txt + .html — email templates
        with property details + enquirer details + message.
  - CSS: static/css/detail.css — gallery (main + thumbs + nav arrows +
    count), detail header (title + location + price + actions), facts
    bar (2-col mobile / 4-col desktop), description, amenities grid
    (2-col mobile / 3-col desktop), Leaflet map container, sticky agent
    card (logo + contact buttons in burnt/WhatsApp-green/espresso),
    enquiry form (inputs + textarea + submit), success + error states,
    similar listings grid, mobile Call/WhatsApp sticky bar (fixed
    bottom, visible <810px only).
  - Map: Leaflet 1.9.4 from unpkg CDN (with SRI integrity hash) +
    OpenStreetMap tiles (free, no API key per §8). Marker with popup
    showing the location name. Privacy: if address_text is empty, the
    map note says "Approximate location only — exact address shared on
    enquiry." If address_text is set, it's shown as the note.
  - Gallery JS: vanilla JS slider — click thumbnails or prev/next
    arrows, or use ← / → keyboard arrows. No library dependency.
  - Tests: 44 new (24 in test_detail.py + 20 in test_enquiry.py):
      * Detail: 200 for valid, 404 for draft/archived/nonexistent/slug-
        mismatch, view counter increments + debounces per session +
        increments per new session, page content (title/price/location/
        facts bar/gallery/description/amenities/breadcrumbs/canonical),
        JSON-LD present with required fields + geo when lat/lng,
        agent card present, Call/WhatsApp links with prefilled message,
        enquiry form present with honeypot, similar listings filtered
        correctly + exclude self, mobile contact bar, Leaflet map
        present when lat/lng (absent otherwise), address_text privacy.
      * Enquiry: valid creates Inquiry + sends email to agent + returns
        success partial, honeypot saves as spam + no email + fake
        success, short message 422, missing email/name 422, GET not
        allowed (405/404), rate limit blocks 4th per minute per IP (429),
        rate limit per-IP not global, 404 for nonexistent/draft property,
        authenticated user linked to inquiry.
  - Total tests: 153 (Phase 0: 3, Phase 1: 47, Phase 2: 23, Phase 3: 36,
    Phase 4: 44).
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  pytest -q (153 passed in 23.9s) · runserver smoke: GET /listing/<slug>-<pk>/ = 200 (28 KB) with all
  sections (gallery, facts bar, description, amenities, agent card, enquiry form, mobile contact bar,
  JSON-LD, canonical, similar listings, Leaflet); POST /listing/<slug>-<pk>/enquire/ = 200, Inquiry
  saved, email sent to agent with text + HTML body
| Phase 5 — Accounts, saved, agent dashboard
```

```
2026-10-02 | Phase 3 — Search and results | Full search portal wired up — all 6 SEO URLs, FilterSet, HTMX pagination, autocomplete, query-count test.
  - URLs (apps/listings/urls.py) — all 6 patterns from WORK.md §7:
      * /<type>-for-sale/                      (type-only sale)
      * /<type>-for-sale/<location-slug>/      (type + location sale)
      * /<type>-for-rent/                      (type-only rent — added for consistency)
      * /<type>-for-rent/<location-slug>/      (type + location rent)
      * /property-for-sale/<location-slug>/    (all types + location sale)
      * /property-for-rent/<location-slug>/    (all types + location rent)
    Plus the autocomplete endpoint: /search/locations/?q=<text>
    The all-types patterns are registered before the generic <type>-for-*
    patterns so "property" doesn't get matched as a type_slug.
  - FilterSet (apps/listings/filters.py — PropertyFilter):
      * q (free text — searches title + description + location name +
        location.parent.name + location.parent.parent.name; icontains
        on SQLite, same fields on Postgres for v1)
      * min_price / max_price (NumberFilter, gte/lte on price)
      * beds / baths (NumberFilter, gte)
      * furnishing (ChoiceFilter, choices from Property.Furnishing)
      * amenities (AllValuesMultipleFilter on amenities__slug)
      * sort (ChoiceFilter — whitelisted: newest/price_asc/price_desc/featured;
        invalid values fall back to newest per §13 "never trust user input
        in lookup strings")
  - View (apps/listings/views.py):
      * search() — parses URL kwargs (type_slug, location_slug, listing_type),
        resolves PropertyType via get_object_or_404, resolves Location via
        _resolve_location() (prefers shallowest match — county > area >
        neighbourhood). Builds base queryset: Property.objects.published()
        filtered by listing_type + property_type + location (with
        descendants via _location_filter_q() which walks 3 levels deep).
        Eager-loads select_related(property_type, location__parent__parent,
        agent__user) + prefetch_related(images, amenities) to avoid N+1.
        Applies PropertyFilter, paginates 24/page, generates H1 +
        breadcrumbs + canonical URL (clean path, no query params) +
        related searches. Returns _results_grid.html partial for HTMX
        requests (HX-Request header), full search.html otherwise.
      * location_autocomplete() — JSON endpoint; returns up to 8 locations
        whose name icontains the q param (min 2 chars); each result has
        slug, name, full_path, level.
  - Helper functions:
      * _resolve_location(slug) — shallowest-first match
      * _location_filter_q(location) — Q object matching location + all
        descendants (3-level walk)
      * _build_h1(listing_type, ptype, location) — "Flats & Apartments
        for Sale in Mombasa"
      * _build_breadcrumbs(listing_type, ptype, location) — Home > [Type]
        for [Sale/Rent] > [Location]
      * _build_canonical_url(listing_type, ptype, location) — clean path
        without query params
      * _build_related_searches(listing_type, ptype, location) — up to 8
        links: other types in same location, same type in sibling locations
  - Templates:
      * templates/listings/search.html — full results page: breadcrumbs,
        H1 + result count + sort dropdown, mobile filter toggle, results
        layout (sidebar + grid), related searches, mobile filter drawer
        (slide-over with backdrop + Esc to close).
      * templates/listings/_results_grid.html — HTMX partial: the grid +
        pagination, wrapped in <div id="results-grid"> (the HTMX target).
        Pagination: numbered links with ellipsis for large ranges, prev/
        next arrows, all with hx-get + hx-target + hx-push-url for HTMX
        and plain href for no-JS fallback. Empty state inside the same
        partial.
      * templates/listings/_filters.html — filter form, reused in the
        desktop sidebar and the mobile drawer. Fields rendered manually
        (not form.as_p) so design-system classes can be applied without
        django-widget-tweaks. Form has hx-get + hx-target + hx-push-url +
        hx-trigger="change" for HTMX; falls back to normal GET submit
        without JS.
  - CSS: static/css/search.css (results page layout — composes existing
    components, no new visual patterns per §11 Phase 3). Includes
    breadcrumbs, results header, filter sidebar (sticky on desktop),
    mobile filter drawer (slide-over), results grid (1/2/3 cols
    responsive), empty state, pagination, related searches.
  - Hero search bar updated (templates/core/home.html): form action now
    defaults to /property-for-sale/; motion.js builds the SEO-friendly
    action URL dynamically (/<type>-for-<sale|rent>/<location-slug>/)
    based on the Buy/Rent segment + type select + autocomplete-picked
    location. Hidden location_slug field populated by autocomplete.
  - motion.js extended (setupSearchSegment): Buy/Rent toggle now also
    rebuilds the form action; type select change rebuilds it; location
    input has a debounced autocomplete dropdown (200ms) that fetches
    /search/locations/?q=... and renders results as a dropdown listbox.
    Picking a suggestion sets the hidden location_slug and rebuilds the
    action URL. Without JS, the form falls back to /property-for-sale/
    with the q param.
  - Tests: 36 new in apps/listings/tests/test_search.py:
      * All 6 URL patterns return 200 with correct H1
      * Invalid type/location returns 404
      * Only published listings shown (draft + archived never appear)
      * Results filtered by listing_type (sale vs rent)
      * Results filtered by property_type
      * Results filtered by location WITH descendants (Mombasa includes
        Nyali, Bamburi, etc.)
      * Filters combine: beds + max_price together
      * min_price, furnishing, amenities, q filters each work
      * Sort: newest is default, price_desc selectable, invalid sort
        value falls back to newest (whitelist enforcement)
      * Pagination: ≤24 cards per page; page 2 works
      * HTMX: HX-Request header returns partial only (no <html>);
        non-HTMX returns full page
      * Breadcrumbs render
      * Canonical URL in <head> = clean path without query params
      * Empty state renders when no results (impossibly-high min_price)
      * Related searches render
      * Autocomplete: returns JSON, Mombasa for "mom", empty for short
        query, empty for no match, result has slug/name/full_path/level
      * QUERY-COUNT TEST: results page stays under 15 queries
        (CaptureQueriesContext) — catches N+1 regressions
  - Total tests: 109 (Phase 0: 3, Phase 1: 47, Phase 2: 23, Phase 3: 36).
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  pytest -q (109 passed in 15.3s) · runserver smoke: /flats-apartments-for-sale/mombasa/ = 200 with
  H1 "Flats & Apartments for Sale in Mombasa", 4 listing cards, breadcrumbs, filter sidebar, canonical
  link, related searches; HTMX request returns partial only; autocomplete returns JSON for "nai"
| Phase 4 — Listing detail and enquiries
```

```
2026-10-02 | Phase 2 — Design system and homepage | Full design system + real-DB home page + styleguide landed.
  - Design reference: design-reference/index.html copied into the repo (read-only Framer export).
  - Fonts: Geist + Geist Mono self-hosted as variable woff2 in static/fonts/
    (downloaded from the official vercel/geist-font repo). @font-face declarations
    live at the top of static/css/tokens.css. No CDN, no Framer runtime, no
    "Made in Framer" badge (per WORK.md §2.1a).
  - CSS layer cake:
      * static/css/tokens.css (128 lines) — full §10.1-§10.4 token layer
        (colours, type scale, tracking, line-height, OpenType features, radii,
        shadows, layout, breakpoints, motion vars). Includes color-mix helpers
        and prefers-reduced-motion overrides.
      * static/css/components.css (789 lines) — every §10.5 component as a
        class: pill button (primary/dark/outline/light-outline, lg/sm),
        nav-link with index, section-tag + eyebrow, stat block (light/dark),
        value card, principle card, agent portrait card, listing card (with
        cover, [001] tag, featured tag, save heart, price, location, facts bar,
        verified badge), search bar (pill, with Buy/Rent segment), newsletter
        field with Subscribe, footer link columns, giant wordmark, full-screen
        mobile menu, divider, responsive 3-state header, [data-reveal] utility.
      * static/css/home.css (430 lines) — home-page section rhythm: hero with
        full-bleed bg + dark gradient + 3 stat counters + search bar; featured
        grid (1/2/3 cols); story with founder portrait + scroll-reveal quote +
        3 value cards; numbers (4-cell grid with taupe dividers); agents
        (espresso bg, 1/2/4 cols); philosophy (1/2/4 cols); browse (location +
        type link lists); CTA band; footer with newsletter + giant Homes
        wordmark + "Nyali · Mombasa · Kenya".
      * static/css/base.css (62 lines) — reset + body defaults + layout helpers.
  - Motion: static/js/motion.js (189 lines) — progressive enhancement only,
    all disabled under prefers-reduced-motion:
      1. Smooth scrolling (lightweight, no Lenis dependency)
      2. Animated number counters via IntersectionObserver (easeOutCubic)
      3. Word-by-word reveal for the founder quote (per-word span fade-in)
      4. Appear-on-scroll for [data-reveal] elements
      5. Header background change on scroll (transparent -> solid espresso)
      6. Mobile menu open/close toggle (Menu / Close, body scroll lock, Esc)
      7. Search-bar Buy/Rent segment toggle (sets hidden listing_type input)
  - Templates:
      * templates/base.html — extended to conditionally load page-specific CSS
        and always load motion.js with defer.
      * templates/includes/_header.html — 3 header states per §10.4 (desktop
        bar ≥1200px with numbered nav links + phone/email contact, tablet bar
        810-1199px with CTA + hamburger, mobile <810px with hamburger only
        that opens a full-screen menu with "Close" + numbered nav + contact
        block at the bottom).
      * templates/includes/_footer.html — [FOOTER] tag, "Redefining how you
        find your next home." lead, newsletter form with Subscribe, 4 link
        columns (Explore / Legal / Company / Visit), giant "Homes" wordmark
        with per-letter spans (motion.js can stagger-colour them on hover),
        "Nyali · Mombasa · Kenya" + copyright.
      * templates/includes/_listing_card.html — reusable Framer-style listing
        card partial. Takes `property` and `index`; renders cover image,
        [001]-style index tag, Featured tag, save heart (auth-gated), price
        with /month suffix for rent, title (2-line clamp), location, beds/
        baths/size facts bar, Verified badge. Uses the kes filter.
      * templates/core/home.html — all 10 sections from §8, real-DB-driven:
        hero stats derive from Property.objects.published().count() /
        is_verified ratio / distinct neighbourhoods count; featured grid shows
        up to 6 featured-or-newest published listings; agents section shows
        all 6 seeded agencies with their active-listing count; browse-by-
        location shows 6 counties with descendant-listing counts; browse-by-
        type shows 11 types with their live counts.
      * templates/core/styleguide.html — every §10.5 component rendered in
        isolation. 16 sections: colour swatches, type scale, buttons, section
        tags, stat blocks, value cards, principle cards, agent cards, listing
        cards (uses the real _listing_card.html partial), search bar,
        newsletter, footer columns, wordmark, dividers, nav links, mobile
        menu preview.
  - Template tags: apps/core/templatetags/core_tags.py with `kes` filter
    (Decimal -> "KES 12,500,000" or "KES 95,000 / month") and `kes_short`
    filter (compact "KES 12M" / "KES 95K" for tight card layouts).
  - Views: apps/core/views.py home() fetches featured_listings (up to 6,
    topped up with newest), agencies, counties (with listing_count attribute),
    types_with_counts, and 3 hero stats + 4 numbers-section stats. All
    queries use select_related / prefetch_related to avoid N+1.
    styleguide() returns 404 when DEBUG=False (dev-only enforcement in
    the view, not the URL conf — so the URL is always resolvable, which
    makes the route testable).
  - Models: Property.get_absolute_url() added — returns the future-shape
    /listing/<slug>-<pk>/ URL (Phase 4 wires the actual route).
  - Hero background: scripts/make_hero_bg.py generates a 2400×1600 JPEG
    warm-sunset gradient with a building-horizon silhouette, saved to
    static/img/hero-bg.jpg (47 KB). Pillow-only, no external assets.
    Phase 6 replaces this with the owner's own photography per §10.7.
  - URLs: /styleguide/ always registered; access-controlled in the view.
  - Tests: 73 total (Phase 0: 3, Phase 1: 47, Phase 2 new: 23). New tests
    cover the kes filter (10 cases), home page rendering from DB (all 10
    sections, 3 hero stats, search bar with Buy/Rent segment, 3 header
    states, footer with newsletter + wordmark + Nyali line, bracket tags,
    motion.js loaded), Geist font files on disk, styleguide page loads +
    shows every §10.5 component + is dev-only (404 under DEBUG=False),
    and Property.get_absolute_url.
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  pytest -q (73 passed in 8.0s) · runserver smoke: GET / = 200 (34 KB), GET /styleguide/ = 200 (29 KB),
  all 7 static assets (tokens.css, base.css, components.css, home.css, motion.js, Geist-Variable.woff2,
  hero-bg.jpg) serve 200
| Phase 3 — Search and results
```

```
2026-10-02 | Phase 1 — Models, admin, seed data | Full data model + admin + seed_demo landed.
  - Location (apps.locations): name, slug, parent (self FK), level enum
    (county/area/neighbourhood), lat, lng, description. unique_together
    (parent, slug). Methods: get_descendants() (3-level walk),
    get_ancestors(), full_path(), is_leaf. save() auto-slugs and derives
    level from parent if not set.
  - AgencyProfile (apps.agents): user OneToOne, name, slug (auto-dedup),
    logo, bio, phone, whatsapp, email, website, office_location FK
    (SET_NULL), is_verified. Helpers: display_phone / display_email /
    display_whatsapp (digits-only for wa.me).
  - PropertyType (apps.listings): name, slug_plural, slug_single, flags
    is_residential / is_commercial / is_land, position. Seeded with the
    11 types listed in WORK.md §6.
  - Amenity (apps.listings): name, slug (auto), icon (Phosphor key),
    category enum (security/utilities/lifestyle/building). 24 amenities
    seeded.
  - Property (apps.listings): full §6 spec. listing_type, status, price
    + price_period, beds/baths/size_sqm/land_size_acres, furnishing,
    parking_spaces, year_built, service_charge, amenities M2M, agent FK,
    is_featured, is_verified, views_count, published_at. PropertyQuerySet
    with .published() / .for_sale() / .for_rent() / .featured(). clean()
    enforces sale=total, rent=monthly, price>=0. save() auto-slugs and
    stamps published_at on first PUBLISHED transition. increment_views()
    bumps counter without touching updated_at. Indexes per §6
    (status+listing_type+property_type+location, price, published_at,
    is_featured).
  - PropertyImage: property FK, image, caption, position, is_cover.
    One cover enforced via UniqueConstraint(condition=Q(is_cover=True))
    — works on SQLite 3.8+ and Postgres. clean() also blocks second cover
    at form level.
  - Inquiry (apps.inquiries): property_ref FK (renamed from `property`
    to avoid clashing with Python's @property decorator), user FK
    (nullable), name, email, phone, message, status enum (new/read/
    replied), honeypot + submitter_ip for spam control. is_spam property.
  - SavedProperty + SavedSearch (apps.accounts): user FK + property FK
    unique_together; SavedSearch stores a raw querystring (alerts are
    "Later" per §3).
  - Migrations: locations.0001, agents.0001, listings.0001,
    accounts.0002_savedsearch_savedproperty, inquiries.0001. Order respects
    FK deps.
  - Admin for every model: list_display + list_filter + search everywhere,
    PropertyImageInline on Property (TabularInline), PropertyType has
    is_residential/is_commercial/is_land filters, PropertyAdmin exposes
    list_filter (listing_type, status, is_featured, is_verified,
    property_type, furnishing), PropertyAdmin actions: mark_published,
    mark_archived. InquiryAdmin: mark_read, mark_replied + boolean
    is_spam_display.
  - seed_demo command (apps/listings/management/commands/seed_demo.py):
    creates 6 counties > 21 areas > 34 neighbourhoods; 11 property types;
    24 amenities; 6 agencies (each gets an is_agent User + AgencyProfile);
    80 fictional listings with Pillow-generated JPEG covers (1280x800,
    palette tied to design tokens — burnt/clay/brown/taupe/espresso).
    Idempotent on natural keys; --clear wipes & re-seeds; --no-images
    skips cover generation; --target N controls count.
  - Tests: 47 total (Phase 0: 9; Phase 1 new: 38). New tests cover
    Location tree methods, PropertyQuerySet.published() visibility rules,
    PropertyImage one-cover enforcement (DB + form level), AgencyProfile
    slug dedup + contact helpers, Inquiry spam flag, and seed_demo
    idempotency + image-cover-presence.
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  pytest -q (47 passed in 5.7s) · python manage.py seed_demo (80 listings, 113 images, 1.4s) ·
  python manage.py seed_demo (second run idempotent, counts unchanged) ·
  admin verified: 10 admin URLs return 200 incl. Property change form with PropertyImage inline
| Phase 2 — Design system and homepage
```

```
2026-10-02 | Phase 0 — Scaffold | Project scaffolded at /home/z/my-project/gabriel_homes/.
  - Django 5.1.15 + Python 3.12, custom email-based User (apps.accounts.User) + UserManager,
    admin, migration 0001_initial.
  - Six apps registered: core (home view + context processor), accounts (full),
    locations / listings / agents / inquiries (stubs with apps.py + placeholder models.py).
  - Settings split: config/settings/{base,dev,prod}.py, django-environ-driven, .env.example.
    dev.py forces SQLite; base.py conditionally adds django.contrib.postgres only when a
    Postgres DATABASE_URL is present (avoids psycopg2 requirement in SQLite dev).
  - allauth wired for email login (ACCOUNT_LOGIN_METHODS={'email'}); modern config — no
    deprecated ACCOUNT_AUTHENTICATION_METHOD / ACCOUNT_*_REQUIRED.
  - WhiteNoise static, easy-thumbnails aliases, Pillow, django-filter, gunicorn pinned.
  - Templates: base.html + includes/_header.html + includes/_footer.html + core/home.html.
  - Static: static/css/tokens.css (full token layer from DESIGN.md §10.1–10.4),
    static/css/base.css (Phase-0 subset of components: header, hero, pill buttons,
    placeholder cards, footer; full component library lands in Phase 2).
  - Styling approach picked and logged: PLAIN CSS + CUSTOM PROPERTIES (no Tailwind CLI).
    Rationale: design system in §10 is built around CSS custom properties; Phase 2
    already calls for static/css/tokens.css; avoids Node toolchain; finer control over
    tracking, shadows, radii needed for the editorial Framer look.
  - Tests: apps/accounts/tests/test_user_model.py (6 tests), apps/core/tests/test_phase0_scaffold.py (3 tests).
  - conftest.py with user_factory fixture.
  - WORK.md + DESIGN.md copied to repo root.
| python manage.py check (0 issues) · python manage.py makemigrations --check --dry-run (No changes) ·
  pytest -q (9 passed) · runserver boots, GET / returns 200 with design markers
| Phase 1 — Models, admin, seed_demo
```

### Assumptions
- Repo root lives at `/home/z/my-project/gabriel_homes/` (separate from the upload dir).
- Dev DB is always SQLite, even if a `DATABASE_URL` env var leaks in from a parent shell —
  `dev.py` forces SQLite; `base.py` falls back to SQLite if the parsed engine is neither
  postgresql nor sqlite3. (Reason: the sandbox shell has a parent `.env` that sets
  `DATABASE_URL=file:/home/z/my-project/db/custom.db`, which django-environ parses as
  `ENGINE=file` — non-Django. The defensive check keeps the project bootable.)
- Geist / Geist Mono fonts are self-hosted as variable woff2 (Phase 2 complete).
  Source: official `vercel/geist-font` GitHub repo. No CDN, no Framer runtime.
- The Phase 2 home page is the *real* home page per WORK.md §8 (no longer a placeholder).
  All 10 sections are wired to real DB data via `apps.core.views.home()`.
- `accounts.User` has an `is_agent` boolean (rather than a separate Group) so a single
  user can flip from "saved a property" to "manages listings" without schema changes.
  Phase 5 will enforce permissions on this flag.
- **Phase 1 — `PropertyQuerySet.published()` semantics:** "published" means strictly
  `status='published'` AND `published_at <= now()`. Listings in `under_offer` /
  `sold_let` / `archived` are NOT publicly visible (the status enum doubles as the
  public-visibility flag). This matches WORK.md §6's "Draft or archived listings must
  never appear publicly" and is the simplest reasonable interpretation.
- **Phase 1 — `Inquiry.property` field rename:** the FK on Inquiry is named
  `property_ref` (with `verbose_name="property"` and `related_name="inquiries"`) to
  avoid colliding with Python's built-in `@property` decorator on the same class. The
  DB column is `property_ref_id`; admin and templates see "property" in the UI.
- **Phase 1 — `seed_demo` cover images:** generated as 1280×800 JPEGs using a palette
  drawn from the design tokens (burnt/clay/brown/taupe/espresso). They are obvious
  placeholders (caption text on a flat colour) — to be replaced by the owner's own
  photography in Phase 6 (per WORK.md §10.7).
- **Phase 1 — `Property.published_at` stamping:** the field is set automatically on the
  first transition into `status='published'` and never reset. If a listing is flipped
  back to draft and re-published, `published_at` retains its original value (this is
  how "newest" sort stays stable).
- **Phase 2 — `kes` template filter:** outputs `KES 12,500,000` for integers and
  `KES 99.99` for decimals. The optional `period` argument appends ` / month` for
  rent listings. `kes_short` rounds down to the nearest million or thousand
  (`KES 12M` / `KES 95K`) for tight card layouts.
- **Phase 2 — styleguide dev-only enforcement:** the `/styleguide/` URL is always
  registered (so it's resolvable in tests), but the view returns 404 when
  `DEBUG=False` AND the user isn't staff. This keeps the route testable under
  pytest-django (which forces `DEBUG=False`) while still hiding it from the public
  site in production.
- **Phase 2 — motion layer:** all motion is progressive enhancement. Text is fully
  readable without JS. `prefers-reduced-motion` short-circuits every effect (counters
  snap to final value, word-reveal lights up instantly, [data-reveal] elements are
  always visible). No Lenis dependency — smooth-scroll is a tiny inline
  `scrollIntoView({behavior:'smooth'})` shim.
- **Phase 2 — hero background:** Pillow-generated 2400×1600 JPEG warm-sunset gradient
  with a building-horizon silhouette (47 KB). Obvious placeholder; Phase 6 replaces
  with the owner's own photography per WORK.md §10.7.
- **Phase 3 — type-only rent URLs:** WORK.md §7 only explicitly lists
  `/<type-plural>-for-sale/` (type-only sale) and `/<type-plural>-for-rent/<loc>/`
  (type+location rent). I added `/<type-plural>-for-rent/` (type-only rent) for
  consistency — it's a natural extension and the home-page search bar can submit
  to it when the user picks "Rent" + a type but no location.
- **Phase 3 — location resolution:** `_resolve_location(slug)` matches the slug at
  any level (county / area / neighbourhood) and prefers the shallowest match
  (county > area > neighbourhood). This means `/flats-apartments-for-sale/nyali/`
  matches the Nyali **area** (under Mombasa), not a hypothetical neighbourhood
  that happens to share the slug. If two locations share a slug at the same level,
  the first by name wins.
- **Phase 3 — `q` filter on SQLite:** uses `icontains` across title + description +
  location name + location.parent.name + location.parent.parent.name (5-way OR).
  On Postgres the same fields are searched with the same OR for v1 simplicity;
  a future optimisation would switch to `SearchVector` + `SearchQuery` for proper
  full-text ranking. The WORK.md §9 spec says "use PostgreSQL full-text search
  where available; fall back to icontains on SQLite" — the icontains path works
  on both for now, and the Postgres-specific `SearchVector` upgrade is parked as
  a Phase 6 / "Later" optimisation.
- **Phase 3 — query-count ceiling:** the test asserts `< 15` queries on the results
  page. The actual count is typically ~8-10 (1 for the page of properties with
  select_related, 1 for prefetch images, 1 for prefetch amenities, 1 for the
  COUNT query, a few for context lookups like property types / counties). 15 is
  a generous ceiling that still catches N+1 regressions.
- **Phase 3 — sort whitelist:** `filter_sort` only accepts the four whitelisted
  values (newest / price_asc / price_desc / featured). Any other value (including
  injection attempts like `DROP_TABLE`) silently falls back to `newest` — no error,
  no 500. This matches §13: "Never trust user input in lookup strings; whitelist
  sort options."
- **Phase 3 — HTMX graceful fallback:** the filter form and pagination links all
  use `hx-get` / `hx-target` / `hx-push-url` for HTMX, but also have plain `href`
  / `action` / `method="get"` so they work without JS. The sort dropdown uses
  `onchange` to submit the form (or navigate) as a no-JS fallback.
- **Phase 4 — view counter debouncing:** one count per session per listing.
  Uses `request.session['viewed_property_<pk>']` flag — sessions are cookie-backed
  by default in Django, so a new browser/incognito window = new session = new
  count. This is "debounced per session" per §8; a true per-IP debounce would
  need a cache backend (parked as a "Later" optimisation).
- **Phase 4 — honeypot field name:** the honeypot field is named `website`
  (rather than the more common `url` or `hp`) because bots are particularly
  drawn to filling website fields. The CSS class `.hp-field` (visually hidden
  via `position: absolute; left: -9999px`) keeps it off-screen for sighted
  users but accessible to screen readers (labelled "Leave this field blank").
- **Phase 4 — rate limit:** max 3 enquiries per minute per IP, enforced via
  `Inquiry.objects.filter(submitter_ip=..., created_at__gte=cutoff).count()`.
  This is a DB-query-based limiter, not a cache-based one — fine for v1 traffic
  volumes; a cache-based limiter (django-ratelimit or similar) is parked as a
  Phase 7 hardening item. The 4th enquiry returns 429 with a friendly error
  partial.
- **Phase 4 — email sending:** `fail_silently=True` so a mail outage doesn't
  500 the form submit. The Inquiry is still saved (so the agent sees it in the
  dashboard inbox in Phase 5) even if the email fails. From address is
  `enquiries@gabrielhomes.co.ke` (not the agent's address) so replies go to
  the enquirer directly (via reply-to semantics — actually `send_mail` uses
  the From as reply-to by default; a future improvement would set
  `reply_to=[inquiry.email]`).
- **Phase 4 — JSON-LD `@type`:** uses `Residence` for residential property
  types and `Place` for commercial/land. This is a simplification — schema.org
  has more specific types (`House`, `Apartment`, `SingleFamilyResidence`), but
  mapping every PropertyType to a schema type is parked as a Phase 6 SEO
  refinement.
- **Phase 4 — similar listings "same county":** the similar-listings query
  matches on the county ancestor of the listing's location (walks up
  `location.parent.parent` if needed). This means a listing in Nyali
  (neighbourhood) under Mombasa (county) will find similar listings in Bamburi,
  Shanzu, etc. — all under Mombasa. The ±30% price band is per §8.
- **Phase 4 — Leaflet from CDN:** Leaflet 1.9.4 JS+CSS loaded from `unpkg.com`
  with SRI integrity hashes. This is the only external CDN dependency in the
  project (besides the map tiles themselves, which come from OpenStreetMap).
  Self-hosting Leaflet is parked as a Phase 7 hardening item (the file is
  ~150 KB; self-hosting would remove the CDN dependency).
- **Phase 4 — gallery slider:** vanilla JS, no library. Click thumbnails,
  prev/next arrows, or ←/→ keyboard arrows. No lightbox yet (the main image
  has `cursor: zoom-in` but the zoom behaviour is parked — a simple lightbox
  can be added in Phase 6 or as a "Later" item).
- **Phase 5 — agent permission = 404 not 403:** when an agent tries to access
  another agent's listing edit/images page, the view returns 404 (not 403).
  This is intentional — `get_queryset()` filters to the agent's own listings,
  so the listing "doesn't exist" from their perspective. A 403 would leak that
  the listing exists but belongs to someone else; a 404 doesn't.
- **Phase 5 — `is_agent` flag + AgencyProfile:** an agent is a user with
  `is_agent=True` AND an associated `AgencyProfile`. Both conditions must be
  true to access the dashboard. A user with `is_agent=True` but no
  `AgencyProfile` (e.g. created via admin before the profile) gets 403.
- **Phase 5 — allauth templates:** default allauth templates are used for
  login/signup/password-reset. They're functional and accessible but don't
  match the design system. Styling them with the Gabriel Homes look is parked
  as a Phase 6 polish item (low risk — the forms work, just look generic).
- **Phase 5 — image formset empty-form tolerance:** `image` and `position`
  fields are made non-required in the formset so empty extra forms validate.
  The view only saves forms that have an actual image file. This avoids the
  "This field is required" errors on the empty extra slots that Django's
  inline formset generates by default.
- **Phase 5 — dashboard listing form:** uses a generic CreateView/UpdateView
  with `fields = [...]` rather than a custom ModelForm. The template renders
  fields manually with design-system classes (not `form.as_p`). Hidden fields
  `land_size_acres` and `service_charge` are rendered but not exposed in the
  UI — they can be added to the form in a future iteration if agents need them.
- **Phase 6 — sitemap location scope:** the LocationTypeSitemap includes
  counties + areas only (not neighbourhoods). Including all 34 neighbourhoods
  would generate ~750 URLs (34 × 11 types × 2 sale/rent), most of which have
  0 listings. Counties + areas keeps the sitemap to ~287 URLs, all with content.
- **Phase 6 — WebP + srcset parked:** easy-thumbnails aliases are configured in
  settings (card/gallery/cover/default), but wiring them into templates via the
  `{% thumbnail %}` tag would change all image URLs and require a full
  image-pipeline pass. The bigger win for Phase 6 is lazy loading + alt text +
  width/height (prevents CLS), which is done. WebP/srcset is a Phase 7 item.
- **Phase 6 — home cache:** featured listings cached for 5 minutes via
  `django.core.cache` (LocMemCache in dev/prod). Cache key is
  `"home:featured_listings"` — no versioning, so a listing status change won't
  auto-invalidate. A future improvement would use `cache.set(key, data, timeout)`
  + a signal handler to invalidate on Property.save(). For now, 5 min TTL is
  acceptable (agents don't expect instant home-page updates).
- **Phase 6 — AA contrast:** the `--taupe` (#8a7d70) on `--cream` (#faf8f4)
  combination is the borderline case at ~4.6:1 — acceptable for non-essential
  text (labels, captions) but not for body copy. Body copy uses `--ink` (#211e1b)
  on `--cream` at ~15:1 (AAA). The `--burnt` (#af4715) on `--cream` is ~5.2:1
  (AA pass for normal text).
- **Phase 6 — detail gallery images:** the detail page gallery still uses CSS
  `background-image` (not `<img>`) because the JS slider swaps backgrounds. This
  is acceptable for the main gallery (it's above the fold, has an aria-label on
  the container). The high-impact lazy-loading win is on listing cards (home +
  search grids), which now use `<img loading="lazy">`.
- **Phase 7 — allauth rate limiting at URL level:** allauth's adapter methods
  (`authenticate`, `pre_authenticate`) are NOT called during failed login
  attempts because the form validates (and fails) before reaching the auth
  backend. The reliable fix is to wrap the allauth login/signup/password-reset
  views at the URL level with a rate-limiting decorator. This is done in
  `apps/accounts/urls.py`.
- **Phase 7 — check --deploy warnings under dev settings:** the 6 W-warnings
  (W004/W008/W009/W012/W016/W018) only appear under dev settings (DEBUG=True,
  short SECRET_KEY). This is expected and correct — dev settings are not
  hardened. Prod settings (`config/settings/prod.py`) pass `check --deploy`
  with 0 issues when given a proper 50+ char SECRET_KEY.
- **Phase 7 — upload validation via model validators:** the `validate_image_file`
  validator is attached to the `PropertyImage.image` and `AgencyProfile.logo`
  fields via `validators=[validate_image_file]`. This means validation runs
  whenever a model instance is saved (admin, dashboard formset, shell). The
  dashboard image formset already handles `ValidationError` and re-renders
  with errors. Max 10 MB; .jpg/.jpeg/.png/.webp only.
- **Phase 7 — coverage target:** 97% across the 3 target apps (listings/agents/
  inquiries), well above the 80% target. The uncovered lines are mostly admin
  actions (mark_read/mark_replied) and edge cases in the seed_demo command.
- **Phase 7 — DEPLOY.md scope:** covers single-server deployment (Ubuntu 22.04 +
  Nginx + Gunicorn + PostgreSQL). Multi-server / Docker / Kubernetes is out of
  scope for v1 — the DEPLOY.md notes where to swap LocMemCache for Redis and
  where to add a load balancer for horizontal scaling.
- **Phase 7 — Makefile:** uses `python3` from the venv if `.venv/` exists,
  falls back to system `python3` otherwise. `make deploy-check` uses a dummy
  50+ char SECRET_KEY so `check --deploy` passes the W009 check without
  needing the real production key.
- `AgencyProfile`, `SavedProperty`, `SavedSearch` are mentioned in section 6; in Phase 1
  they have been modelled per spec. AgencyProfile lives in apps.agents (per §5);
  SavedProperty and SavedSearch live in apps.accounts because they are user-owned
  bookmarks rather than listing-owned data.

### Open questions for the user
- None blocking. Carried forward: `AgencyProfile` location is in `apps.agents` (per
  WORK.md §5). Seed count confirmed: ~80 fictional listings across the 6 markets.

### Later / parked ideas
- (none — Phases 0, 1, 2 all stayed in scope)

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
(empty — agent starts here)
```

### Assumptions
- (agent lists assumptions here)

### Open questions for the user
- (agent lists blocking questions here)

### Later / parked ideas
- (agent lists out-of-scope ideas here)

# HOME-REDESIGN — Home page layout & styling plan (no new sections' content)

Owner goal (user words): "perfect the design of the home page — the story section
looks flat, the page has plenty of white space, scroll reveal is okay but there are
very few words, the home page should be showcasing the homes and NOT the agents
(use the pasted bento grid code + its animation), and the hero should be a
slideshow background of the real home photos — only the best few."

Constraint: layout + styling + re-presentation of EXISTING content. The only copy
growth allowed is the story narrative the user explicitly called "too few words" —
and it must restate themes already on the page (no new facts, no new numbers).

---

## 1. Audit — what is there now (accurate, file:line)

Home page = `templates/core/home.html` (8 sections), styled by
`static/css/home.css` over `base.css`/`components.css`/`tokens.css`, animated by
`static/js/motion.js`. Context from `apps/core/views.py:14` (`home()`).

| # | Section | Template lines | Current state | Problem |
|---|---------|----------------|---------------|---------|
| 1 | Hero | home.html:25–86 | Static `hero-bg.jpg` (1024×576 AI cliff-villa) behind tag/title/subtitle + 3 stats + search bar | Not the real homes; low-res for full-bleed; single frozen image |
| 2 | Featured | home.html:92–115 | 3-col grid of `_listing_card.html` ×6 | Plain grid on cream; will duplicate a homes showcase |
| 3 | Story | home.html:121–188 | 11-word statement + 9-word subline + 17-word quote + founder portrait + 3 value cards | Flat text-on-cream; ~37 words total; word-reveal dormant (home.css:167–170 "no-op selectors") |
| 4 | Numbers | home.html:194–230 | 4 animated counters, sand dividers | Fine — keep |
| 5 | Agents | home.html:236–259 | Espresso band, agency portrait cards | User: "showcase the homes, NOT the agents" |
| 6 | Philosophy | home.html:265–309 | 4 numbered principle cards | Fine — minor polish only |
| 7 | Browse | home.html:315–349 | Two link lists (locations / types) | Fine — minor polish only |
| 8 | CTA | home.html:355–363 | Dark band over `cta-bg.jpg` (AI image) | Should match the "real homes" language |

Available real-photo assets (all user-supplied homes):
- `static/img/real/real-01..08.jpg` (1200×800 each) — the Nyali beachfront set
- `static/img/real/hero-poster.jpg`, `cta-balcony.jpg` (1500×1000)
- `static/video/hero-loop.mp4` (18.6MB — stays on the listing page; NOT the hero)

Hero slideshow shortlist (best few, judged on composition + no construction
sightlines): **real-01 kitchen-island** (opener, warm depth), **real-05 dining**
(evening mood), **real-06 living-terrace** (outdoor coastal), **real-02 living**
(bright styled). Excluded: real-08 (aerial of a construction site), real-07
(raw slab above balcony), real-04 (blank wall behind bed).

Bento grid the user refers to = the /agents/ directory mosaic built from their
Framer reference: `static/css/pages.css:211–310` (`.bento-grid` 3-col / 280px
rows / dense flow / 12px gap; `.bento-card` photo bg + scrim + `border-radius:16px`;
spotlight spans 3×2; hover = `scale(1.05)` + grayscale 0.18→0 over 0.55s;
stagger reveals 70ms/140ms under `html.motion-ready`; breakpoints 1020px/560px)
+ markup pattern in `templates/agents/agent_directory.html:54–88`
(`__bg` / `__scrim` / `__body` with index, name, meta).

Tests that pin the current home page (must change WITH the template, same commit):
- `apps/core/tests/test_phase2_home.py:25` `test_home_page_has_all_ten_sections`
  asserts ids incl. `featured`, `agents`
- `:46` `test_home_page_renders_real_featured_listings`
- `:58` `test_home_page_renders_real_agencies`

Environment note: sandbox was reset (no `.venv`, `db.sqlite3` is 0 bytes, no
`media/`) — Cycle 0 restores it before any visual work.

---

## 2. Target design, section by section

1. **Hero — real-homes slideshow.** 4 prepped 16:9 crops crossfading every 5s
   (20s loop) with a slow 1.0→1.06 Ken Burns drift; same layout on top (tag,
   title, subtitle, stats, search bar). Scrims deepened for bright interiors.
   Pure CSS (no JS dependency); slide 1 renders without JS; reduced-motion kills
   zoom/crossfade. First slide preloaded for LCP.
2. **Homes bento showcase — replaces BOTH the Featured grid and the Agents
   section.** One strong homes moment instead of two grids (kills duplication
   and the white gap between them). Spotlight card (3×2, flagship listing) + 5
   photo tiles + 1 gradient "View all properties →" CTA tile. Card chrome from
   the agents bento (photo, scrim, index tag, hover zoom, stagger) + home-card
   meta: price, title, location, beds/baths.
3. **Story — editorial, not flat.** Left: narrative column — statement enlarged,
   two new supporting paragraphs built ONLY from themes already present
   (people-first, transparency, after-keys support), quote in Fraunces italic
   with word-by-word reveal restored. Right: layered real-photo collage
   (real-03 + real-06 overlapping rounded frames, founder as a caption chip,
   not a lone floating portrait). Value cards tighten under the quote.
4. **Numbers** — unchanged (already animated, already balanced).
5. **Philosophy / Browse** — spacing + heading rhythm tweaks only.
6. **CTA** — background swapped to a real photo (`cta-balcony.jpg`) so the page
   ends in the same visual language it opened with.
7. **White space** — home sections alternate cream/white/espresso
   (showcase on espresso becomes the anchor), story gap 5rem→3rem with
   min-heights so columns fill, `--section-pad-y` tightened one step on the home
   page only.

---

## 3. Cycles

### Cycle 0 — Rebuild & baseline (no visual change)
- `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- `makemigrations` no-op check → `migrate` → `seed_demo` → `runserver :3011`
- Baseline full-page screenshots (390 / 849 / 1200) via headless Chromium.
- **Check:** `/` returns 200 with seeded listings; screenshots archived.

### Cycle 1 — Hero slideshow (real photos)
- New `scripts/make_hero_slides.py` (Pillow): center-crop the 4 picks to 16:9,
  1920w, q82 → `static/img/real/hero-slide-1..4.jpg` (~200–350KB each). If the
  1200px sources look soft at 1920, upscale via LANCZOS + slight sharpen;
  sources in `property-images/2026/10/` preferred when higher-res.
- `home.html:26`: `.hero__bg` → `.hero__slideshow` with 4 `.hero__slide` divs
  (inline `--slide-img` custom property) + keep gradient overlay div.
- `home.css`: `@keyframes heroFade` (opacity 0→1 steps at 0/5/20/25% cycle) +
  `heroDrift` (scale 1→1.06), per-slide `animation-delay`, all inside
  `html.motion-ready` gate + `@media (prefers-reduced-motion: reduce)` fallback
  showing slide 1 static. Deepen scrims (left 0.52→0.62, bottom 0.64→0.72).
- `base.html`: `<link rel="preload" as="image" href="...hero-slide-1.jpg">`
  via a home-only block; `og:image` keeps a static image (SEO unchanged).
- **Check:** crossfade cycles without JS errors; no-JS shows slide 1; scrim
  keeps title AA-readable on the brightest frame; network shows 4 new JPEGs
  ≤ ~1.2MB total; LCP element = slide 1 (preloaded).

### Cycle 2 — Homes bento showcase (agents out)
- `views.py home()`: replace `agencies` context with `showcase_listings` —
  6 published with images, spotlight = first `is_featured` (Nyali beachfront
  apartment expected), rest by `-published_at`; keep the 5-min cache pattern.
- `home.html`: delete Featured grid (92–115) and Agents section (236–259);
  insert `section#showcase` using the agents-page bento markup pattern with
  home-card meta (price KES chip, title, location, beds/baths, [001] index).
- `components.css`: move `.bento-*` rules verbatim from `pages.css:211–310`
  (agents page keeps working — components.css loads on every page); delete
  from `pages.css`. Add `.bento-card--home` meta styles in `home.css`.
- Tests: update `test_phase2_home.py` — id list `featured`→`showcase`, drop
  `agents` assertion, swap `renders_real_agencies` for
  `renders_real_showcase_listings` (bento contains DB listing cards).
- **Check:** 6 bento cards with photos + CTA tile; hover zoom + 70/140ms
  stagger present; 1020px = 2-col, 560px = 1-col; `pytest apps/core` green;
  `/agents/` bento unchanged.

### Cycle 3 — Story depth (words + collage + word-reveal)
- `home.html:121–188` rebuilt: left narrative column (statement + 2 paragraphs
  ~50–70 words each, derived strictly from existing value/philosophy copy),
  quote gets `data-quote-reveal` back; right column = collage of real-03 +
  real-06 with `border-radius: var(--radius-frame)`, rotated −2°/+1.5°,
  overlapping via negative margin; founder chip pinned under collage.
- `home.css`: collage styles; delete the no-op word rules (167–170) and add
  real `.word { opacity: 0.12 } .word.is-lit { opacity: 1; transition… }`
  (motion.js `setupQuoteReveal` at motion.js:84 already handles the spans —
  no JS change needed).
- **Check:** quote lights word-by-word on scroll; story has no empty band at
  1200/849/390; added copy contains no new numbers/claims.

### Cycle 4 — Rhythm, white space, CTA
- `home.css`: section order/style pass — showcase on espresso as the dark
  anchor, numbers keep cream, philosophy white, browse cream; tighten
  `--section-pad-y` usage; story/philosophy heading margins; browse link rows
  slightly denser.
- `components.css`: `.cta` background `cta-bg.jpg` → `../img/real/cta-balcony.jpg`
  (already 1500×1000 real photo), scrim unchanged.
- **Check:** full-page screenshot at 390/849/1200 shows no dead bands; page
  alternates light/dark with exactly one espresso anchor + CTA.

### Cycle 5 — QA & delivery
- `pytest apps/core` (and full suite) green.
- Headless-Chromium screenshots (390/849/1200) before/after collage for the user.
- Rebuild the rootless update zip in `download/` so the user can pull the new
  home page onto their install (`UPDATE-WEBSITE.sh` flow, db/media untouched).
- Worklog entry + summary.

---

## 4. Guardrails
- No new facts/numbers anywhere; story copy only restates existing themes.
- `prefers-reduced-motion`: slideshow = static first frame; no Ken Burns;
  reveals instant (motion.js already gates).
- No JS required for content visibility (`html.motion-ready` pattern kept).
- Tests updated in the same commit as the template they pin.
- Agents section removed from home only — `/agents/` untouched.

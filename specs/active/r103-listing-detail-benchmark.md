# r103 — Listing Detail Page: Whole-Page Review + Benchmark

Owner ask: "improve the styling of the listing page... where one sees a
particular listing... conduct a whole review of the page... make bench tests
and not loop agents on every micro section on improving every major
component ... score perfectly on the benchmark."

Scope: ONE round, every major component, scored by a committed benchmark
test file. No per-micro-section agent loops — a single continuous pass.

## Review findings (VLM + code audit, 2026-11-15)

Baseline VLM scores: desktop 6/10, mid-page 6/10, lower 4/10, mobile 6/10,
mobile-bottom 2/10. Verified causes:

### Structural (style/robustness)
1. **Bracket labels** — `[ DESCRIPTION ]`, `[ AMENITIES ]`, `[ VIDEO TOUR ]`,
   `[ LOCATION ]` read as unfinished dev syntax, not editorial typography
   (VLM flagged twice on desktop and mobile).
2. **Description rendering** — `{{ property.description }}` raw: newlines
   collapse to one blob; demo copy renders as two-sentence stub. Needs
   `|linebreaks` + drop-cap/editorial styling + graceful empty state.
3. **Facts bar** — label/value contrast weak (11px taupe labels under 16px
   values, nearly same weight); no icons; divider-only layout lacks anchoring.
4. **Amenities grid** — fixed `repeat(2, 1fr)` at desktop: 4 items = 2x2
   stretch that wastes width; checkmark-only icons identical for every
   amenity (no semantic icon variety).
5. **Gallery robustness** — with 1-2 images (current seed), no thumbs strip,
   nav buttons, or counter render: the page's most important element reads
   "broken/placeholder". Also no keyboard access on thumbs (real <button>s —
   ok) but lightbox exists; needs graceful min-image state + richer hero
   treatment (aspect 16/7 letterboxes 4/3 photos).
6. **Similar rail** — 3-col grid with 1 card = stranded 1/3-width orphan;
   no "Browse all" affordance to recover. Needs fluid minmax + closing link.
7. **Sidebar card** — brand contact fields blank (honest-blank by design) but
   leaves NO call/WhatsApp/email: the conversion moment is just a form.
   Sidebar needs: seeded demo brand contacts (Gabriel Homes row), a price
   recap chip, response-time microcopy, and visual hierarchy.
8. **Nearby card copy** — "Sample · about 5 min" placeholder noise shipped in
   presentation listings; note text leaks art direction. Keep honesty, but
   style as quiet mono caption, not same-size body.
9. **Map** — fine bones; heading eyebrow is bracket-adjacent "LOCATION"
   mono; "Approximate location" right span floats unanchored; OSM link is
   mono uppercase — acceptable, keep language, align heading.
10. **Mobile** — intro price/actions row cramped; facts bar 2x2 hairlines
    thin; mobile contact bar absent (brand fields blank); footer dead space
    at 413 (site-wide, out of scope this round — noted).

### Data gaps exposed by styling (fix in seed, demo-only)
- `BrandSettings` phone/whatsapp/email blank → contact buttons + mobile bar
  hidden. Seed the Gabriel Homes demo row: `+254 712 345 678` (the same
  demo number seed_demo already mints for the Gabriel Homes agency profile).
- 1-2 images per listing → gallery thumbs/nav never appear in demo. Bump
  image count for a subset of listings (4-6 photos for the first N).

## The benchmark — 40 criteria, 10 per component group

Committed as `apps/listings/tests/test_r103_detail_bench.py`. Each criterion
is a binary pass/fail assertion; the file prints a scored summary and the
suite FAILS unless the score is 100% (any RED criterion = benchmark not met).

### A. Header/Intro (10)
1. title uses display serif, clamp ≥2.2rem, ≤24ch measure
2. eyebrow = type chip + short-stay chip + verified chip, no bracket syntax
3. price block: strong ≥1.5rem tabular + period + negotiable, baseline row
4. share + save actions present, focus-visible rings
5. breadcrumbs render, last crumb unlinked, aria-current present
6. location line: pin glyph + full path, taupe, 14px+
7. no `[` bracket-label text anywhere in the page
8. intro bottom row wraps cleanly at 375px (no horizontal scroll)
9. h1 exactly one per page
10. og:image absolute when listing has images

### B. Gallery + Facts (10)
1. gallery main aspect between 3/2 and 16/7 (no hard 16/7 letterbox)
2. thumbs render when ≥2 images (buttons, is-active ring)
3. nav buttons + counter when ≥2 images
4. single-image listing: no dead nav/thumbs/counter, hero still fills
5. gallery main tag = property type chip (not "HOUSES" all-caps blob)
6. lightbox: role=dialog, aria-modal, Escape closes (existing L4 — kept)
7. facts bar: icon + label + value per fact (icons semantic: bed/bath/area/sofa)
8. facts labels ≥11px, ≥600 weight, letterspaced; values ≥16px weight 600
9. 4 facts in one row ≥810px, 2x2 with hairlines <810px
10. facts values never wrapped mid-number (white-space nowrap on value+unit)

### C. Body sections (10)
1. description title: editorial eyebrow (mono, burnt, no brackets)
2. description body: |linebreaks rendered (paragraphs), 17px/1.75, ≤68ch
3. description empty state: honest "The owner hasn't added a description"
4. amenities: fluid grid minmax(auto-fill, ≥160px), no fixed 2-col stretch
5. amenity item: icon in tinted squircle + name, 12px radius card, hover lift
6. amenity icons: ≥3 distinct SVG glyphs across the page (semantic variety)
7. nearby: heading + quiet mono caption; "Sample" copy styled as caption
8. nearby cards: icon tile 38px+ tinted, name + type + distance hierarchy
9. map heading aligned with section (same flex language as nearby)
10. video block (when present): rounded, controls, mono eyebrow, no brackets

### D. Sidebar + Similar + Mobile (10)
1. sidebar card: logo/monogram + name + role, price recap chip in header
2. call/WhatsApp/email buttons render when brand fields set (demo: seeded)
3. WhatsApp green ≥4.5:1 contrast on its label (existing r12 rule kept)
4. enquiry form labels mono eyebrow, inputs ≥44px touch height
5. response-time microcopy line under buttons
6. similar rail: fluid grid `repeat(auto-fill, minmax(240px, 1fr))`
7. similar rail never strands an orphan: 1 card fills, 2 cards half, 3 col
8. "Browse all <type>" closing link after the grid
9. mobile contact bar renders when brand phone/whatsapp set (demo: seeded)
10. mobile contact bar contrast + 44px touch targets

## Non-goals
- No per-section agent loops (owner explicitly forbade).
- No footer redesign (site-wide, separate round).
- No map tile restyling (CSP/vendor tiles, DECISIONS.md territory).
- No brand copy invention: real Gabriel Homes contact channels come from the
  owner's BrandSettings form; demo seed uses the agency demo number already
  minted by seed_demo (same value, clearly demo).

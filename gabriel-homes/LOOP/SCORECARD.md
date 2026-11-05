# SCORECARD.md — one row per work item

Scoring per RUBRIC.md (D1-D8, 0-4; evidence E1/E2/E3). Priority formula per
PROTOCOL.md. Statuses: TODO, WIP, READY-FOR-AUDIT, MET-T1, MET-T2, REGRESSED,
BLOCKED. Binary checks and the proving test for each item are specified below the
table — a builder ships the item only when every binary check passes and the
proving test exists and is green.

| ID | Item | W | needs | target | status | self D1-D8 | aud D1-D8 | evid | att | last | next step |
|----|------|---|-------|--------|--------|------------|-----------|------|-----|------|-----------|
| F1 | Token integrity | 5 | — | T1 | MET-T1 | 3,n/a,n/a,n/a,3,n/a,3,3 | 3,n/a,n/a,n/a,3,n/a,3,4 | E2 | 0 | r18 | MET — frozen; WATCH re-runs ratchets via scripts/f1_token_survey.py (expect 44/236) |
| F2 | Capability gate | 5 | — | T1 | MET-T1 | 3,n/a,n/a,3,3,n/a,3,3 | 3,n/a,n/a,3,3,3,4,4 | E2+E3 | 1 | r17 | MET — frozen; WATCH spot-checks; E3 artifacts LOOP/audit-screens/r17-e3-*.png |
| F3 | Image & video diet | 4 | — | T1 | TODO | – | – | – | 0 | r15 | NEXT BUILD (r21): measure static/ baseline table, Pillow WebP pass, hero video gating; FOLDS HYG-1 dead home.css purge (D-LOOP-20c) |
| F4 | Motion vocabulary | 4 | — | T1 | TODO | – | – | – | 0 | r15 | Write docs/DESIGN-ADDENDUM.md (≤6 effects + archetypes), then map shipped effects |
| F5 | Smooth scroll (Lenis) | 3 | F2 | T1 | TODO | – | – | – | 0 | r15 | Vendor Lenis under hygiene rules after F2 lands |
| H1 | Home order & diet | 5 | — | T1 | MET-T1 | 3,3,n/a,3,3,3,3,3 | 3,3,n/a,3,3,3,3,3 | E2+E3 | 0 | r19 | MET — frozen; WATCH spot-checks; D6 desktop-only E3 — batched OWNER_NEEDS mobile eyeball |
| H2 | Hero | 5 | F2,F3 | T1 | TODO | – | – | – | 0 | r15 | After F3 — two ordered slices in one row (D-LOOP-20b): H2.a structure (one gesture, frosted pill + segment, stats from BrandSettings, LCP preload) then H2.b motion (split-text mask headline, video under fx=rich; folds BACKLOG P4-1) |
| H3 | Mobile bento | 5 | F2 | T1 | MET-T1 | 3,3,3,3,3,3,3,3 | 3,3,3,3,3,3,3,3 | E2+E3 | 0 | r20 | MET — frozen; WATCH spot-checks; E3: scripts/r20_e3_h3_audit.py 21/21 (snap rail, keyboard walk 0→1470, JS-blocked D-MOTION-SAFE, desktop untouched), LOOP/audit-screens/r20-e3-h3-*.png |
| H4 | Section rhythm | 3 | H1 | T1 | TODO | – | – | – | 0 | r15 | After H1: archetype tags on sections + rhythm test |
| G1 | Floating pill nav | 4 | F2 | T1 | TODO | – | – | – | 0 | r15 | Hide/return on scroll under fx lite+rich; move mobile-menu inline styles to CSS |
| G2 | Shared-element transitions | 5 | F2 | T1 | TODO | – | – | – | 0 | r15 | r22 candidate (D-LOOP-20a): @view-transition behind @supports + per-listing names; uniqueness test; unblocks L4 |
| G3 | Scroll-linked effects | 3 | F2,F4 | T1 | TODO | – | – | – | 0 | r15 | animation-timeline: view() behind @supports; IO fallback kept |
| G4 | Pointer polish | 2 | F2,F4 | T1 | TODO | – | – | – | 0 | r15 | Cursor View bubble + magnetic CTAs, fx=rich + fine pointer only |
| L1 | Map & list sync | 5 | — | T1 | TODO | – | – | – | 0 | r15 | Two-way highlight (row↔pin), keyboard operable, aria-live count, Map pill |
| L2 | Basemap palette | 4 | — | T1 | TODO | – | – | – | 0 | r15 | setPaintProperty token recolour with guarded layer list; pin font fix |
| L3 | Row conversion & density | 4 | — | T1 | TODO | – | – | – | 0 | r15 | WhatsApp primary icon action; row ≤320px; desc ≤28 words |
| L4 | Detail gallery | 3 | G2 | T1 | TODO | – | – | – | 0 | r15 | Read detail-gallery.js first; swipe + lightbox focus trap + shared-element |
| Q1 | Perf budget (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r15 | Record measurement method; home first-view ≤400KB, JS deferred, CLS 0; r18 constraint: results-page query budget baseline 14 / ceiling 15 — page chrome stays query-free |
| Q2 | Accessibility (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r15 | Reduced-motion parity test per effect; 4.5:1; visible focus; keyboard |
| Q3 | Resilience (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r15 | All content visible with JS blocked and under fx=none |
| Q4 | Docs (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r15 | PROTOCOL matches practice; addendum current; DECISIONS entries made |

Priorities recomputed at the r20 retrospective (D-LOOP-20a; untouched bonus +1 live from r20):
**L1 16 · G2 16 · F3 13 · F4 13 · G1 13 · L2 13 · L3 13 · F5 10 · H4 10 · G4 7\***
(* blocked: H2→F3 would be 16, G3→F4 would be 10, L4→G2 would be 10).
Build order: r21 WATCH overlay + F3 (folds HYG-1) → r22 G2 → L1. MET share 4/17 (24%) after H3's r20 audit.

---

## Binary checks & proving tests (builder contract per item)

**F1 Token integrity (5)** — proving test `apps/core/tests/test_f1_token_integrity.py`
1. pytest fails on any `var(--x)` in static/css/*.css with no definition in tokens.css (or component :root block) and no fallback.
2. `--font-body` is gone (uses `--font-sans`); `--paper` is defined in tokens.css.
3. No `font-size` under 13px outside a documented allowlist (allowlist lives in tokens.css comment + DECISIONS entry).
4. Hard-coded hex count outside tokens.css recorded as a baseline constant in the test; count may only go down (ratchet).

**F2 Capability gate (5)** — proving test `apps/core/tests/test_f2_capability_gate.py`
1. One small deferred script sets `html[data-fx]` ∈ {rich, lite, none} from: prefers-reduced-motion ⇒ none; Save-Data ⇒ no richer than lite; hardwareConcurrency or deviceMemory ≤ 4 ⇒ lite; coarse pointer / no hover ⇒ pointer-driven effects off.
2. Every shipped effect keys off `[data-fx]`; none behaves exactly like today's reduced-motion behaviour.
3. With data-fx="none", no effect runs (decision-table test + static check that motion JS gates on data-fx).
4. D-MOTION-SAFE: without JS (no data-fx attr) all content visible, effects off.

**F3 Image & video diet (4)** — proving test `apps/core/tests/test_f3_media_diet.py`
1. No static image > 250KB (test walks static/, lists offenders).
2. WebP/AVIF + srcset where practical (Pillow script scripts/; hero + listing photos first).
3. Every <img> in shipped templates carries width and height.
4. static/video/hero-loop.mp4 loads only under fx=rich and not Save-Data, with a poster; (it is currently unreferenced — either wire it under this gate or the item documents its removal).

**F4 Motion vocabulary (4)** — proving test `apps/core/tests/test_f4_motion_vocabulary.py`
1. docs/DESIGN-ADDENDUM.md names ≤6 effects (mask-reveal, clip-reveal, parallax, spotlight-shift, cursor-view, magnetic) each with purpose, where used, tier, and the "max 2 at once per viewport" rule.
2. Every shipped effect in static/js/*.js maps to an addendum entry (test parses effect IDs, greps the JS).
3. Rule enforced: an effect that does not orient, confirm or earn its keep gets cut, logged in DECISIONS.

**F5 Smooth scroll (3) [needs F2]** — proving test `apps/core/tests/test_f5_smooth_scroll.py`
1. Lenis self-hosted under static/vendor/lenis/ per hygiene rules (no sourceMappingURL; pinned SRI if tag-loaded; hygiene test covers it).
2. Initialises only under fx=rich; off for touch.
3. Anchors, find-in-page, focus and keyboard scrolling still work; scrollIntoView hack replaced.

**H1 Home order & diet (5)** — proving test `apps/core/tests/test_h1_home_order.py`
1. Top-level section id order exactly: hero, bento, recommended, nearby (test asserts the id sequence).
2. ≤ 7 top-level sections on home.
3. Trust ("five checks") message appears in ≤ 2 places.
4. About/Services/Commitments/FAQ/Browse/Newsletter content MOVED (About→/about/, Services→/services/, Commitments→about or checks, FAQ→its page or footer, Browse→nav/footer links, Newsletter→footer) — test finds each block on its destination; nothing silently deleted.

**H2 Hero (5) [needs F2,F3]** — proving test `apps/core/tests/test_h2_hero.py`
1. One gesture (the search pill CTA); no competing hero CTAs.
2. Video only under fx=rich && !Save-Data; else slide-1 image.
3. Split-text mask headline (mask-reveal in addendum).
4. Frosted floating search pill keeps the Buy/Rent segment.
5. Stats row removed, or every stat resolves from BrandSettings (no "Kenya" filler).
6. LCP image preloaded in <head>.

**H3 Mobile bento (5) [needs F2]** — proving test `apps/core/tests/test_h3_mobile_bento.py`
1. Under 1021px or on touch: horizontal scroll-snap carousel, centred card scaled up (CSS only).
2. Swipe (native) and keyboard (focusable cards) work; scrolls with JS blocked.
3. Desktop shape-shift and its existing tests untouched (they stay green).

**H4 Section rhythm (3) [needs H1]** — proving test `apps/core/tests/test_h4_section_rhythm.py`
1. ≥ 3 archetypes (full-bleed, type-led, edge strip) documented in the addendum and used on home.
2. Never more than 2 consecutive sections share one archetype.

**G1 Floating pill nav (4) [needs F2]** — proving test `apps/core/tests/test_g1_pill_nav.py`
1. Hides on scroll-down, returns on scroll-up; active under fx lite or rich.
2. Full nav from 1024px up.
3. Mobile-menu inline styles moved to CSS.
4. Escape closes the menu; skip link present and first focusable.

**G2 Shared-element transitions (5) [needs F2]** — proving test `apps/core/tests/test_g2_view_transitions.py`
1. `@view-transition { navigation: auto }` inside `@supports`.
2. Unique per-listing view-transition-name on card/row image and detail hero (test renders list + detail; names present and unique).
3. Off under fx=none; HTMX pagination unaffected (pagination tests stay green).

**G3 Scroll-linked effects (3) [needs F2,F4]** — proving test `apps/core/tests/test_g3_scroll_linked.py`
1. `animation-timeline: view()` behind `@supports` for parallax/clip reveals on collage, services, nearby.
2. Falls back to the existing IntersectionObserver reveal; no layout shift (transform/clip-path/opacity only).

**G4 Pointer polish (2) [needs F2,F4]** — proving test `apps/core/tests/test_g4_pointer_polish.py`
1. Cursor "View" bubble on listing rows/cards + magnetic primary CTAs; fx=rich and fine pointer only; hidden for keyboard users; no hover-only information.

**L1 Map & list sync (5)** — proving test `apps/core/tests/test_l1_map_list_sync.py`
1. Owner layout kept: map on top, three filter cards, alternating rows.
2. Two-way highlight: row hover → pin highlight; pin click → scroll to + flash row.
3. Keyboard operable (pins focusable/activable, rows reachable); aria-live result count; floating "Map" pill returns to the map.

**L2 Basemap palette (4)** — proving test `apps/core/tests/test_l2_basemap_palette.py`
1. After style load, land/water/roads/labels recoloured to tokens via getMaplibreMap().setPaintProperty with a guarded layer list that skips missing ids.
2. SVG fallback and the single attribution copy unchanged; pin font fixed (F1 dependency).
3. r13/r14 map tests stay green.

**L3 Row conversion & density (4)** — proving test `apps/core/tests/test_l3_row_density.py`
1. WhatsApp primary action (icon), Call and Email secondary, via existing brand-channel logic (hidden when unfilled).
2. Row min-height ≤ 320px desktop; description ≤ 28 words; alternating sides kept; stacks on mobile.

**L4 Detail gallery (3) [needs G2]** — proving test `apps/core/tests/test_l4_gallery.py`
1. Builder reads detail-gallery.js FIRST and extends it (no rewrite).
2. Swipe; lightbox with focus trap + keyboard control; shared-element transition name wired.

**Q1-Q4 (cross-cutting, WATCH-graded)** — enforced on every item: Q1 home
first-view CSS+JS+fonts+LCP ≤ 400KB, new JS deferred, CLS 0, measurement method
recorded · Q2 reduced-motion parity test per effect, 4.5:1 contrast on new text,
visible focus, carousel/map keyboard operable · Q3 all content visible with JS
blocked and under fx=none · Q4 PROTOCOL matches practice, addendum current,
DECISIONS entries made.

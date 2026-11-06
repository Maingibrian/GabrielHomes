# SCORECARD.md — one row per work item

Scoring per RUBRIC.md (D1-D8, 0-4; evidence E1/E2/E3). Priority formula per
PROTOCOL.md. Statuses: TODO, WIP, READY-FOR-AUDIT, MET-T1, MET-T2, REGRESSED,
BLOCKED. Binary checks and the proving test for each item are specified below the
table — a builder ships the item only when every binary check passes and the
proving test exists and is green.

| ID | Item | W | needs | target | status | self D1-D8 | aud D1-D8 | evid | att | last | next step |
|----|------|---|-------|--------|--------|------------|-----------|------|-----|------|-----------|
| F1 | Token integrity | 5 | — | **T2** (raised r35 retro) | MET-T1 | 3,n/a,n/a,n/a,3,n/a,3,3 | 3,n/a,n/a,n/a,3,n/a,3,4 | E2 | 0 | r34 | MET-T1 — frozen at T1; T2 lift needs 4s on D1/D5/D7/D8 with evidence (the two ratchet baselines are already tightened to true counts 211/43 — a further tokenisation pass over the 10 search.css hexes is the natural T2 proof) |
| F2 | Capability gate | 5 | — | **T2** (raised r35 retro) | **MET-T2 (r37 audit — first T2 in the project)** | 4,n/a,n/a,4,4,4,4,4 | **4**,n/a,n/a,**4**,**4**,**4**,**4**,**4** | E2+E3 | 1 | r37 | r37 audit from scratch: 14/14 test_f2_capability_gate.py + matrix re-run on a FRESH server **53/53 ALL PASS** (correction: r36's ledger said 52 — true count is 53: NOJS 8 + NONE 10 + LITE 13 + RICH 15 + TOUCH 7) + D-LOOP-36a verified against code + 5 hashed screenshots eyeballed — zero gaps, aud=self all-4s. WATCH re-runs 14/14 + scripts/r36_e3_f2_matrix.py expect ALL PASS |
| F3 | Image & video diet | 4 | — | T1 | MET-T1 | 3,3,n/a,3,3,3,3,4 | 3,3,n/a,4,3,3,3,4 | E2+E3 | 0 | r24 | MET — frozen; WATCH re-runs 6 F3 tests + exact bytes ratchet **4,191,687** (re-pinned r24 D-LOOP-24b: +6,642 B owner portrait, sanctioned) + f1 survey expect **43**/211 + smoke expect PASS |
| F4 | Motion vocabulary | 4 | — | T1 | MET-T1 | 3,n/a,3,3,n/a,3,4,4 | 3,n/a,3,n/a,n/a,3,4,3 | E2 | 0 | r26 | MET — frozen; WATCH re-runs 7/7 test_f4_motion_vocab.py; r26 audit finding fixed in-audit: gallery-count-bump → M5, manage-card-in declared portal-scoped, SHIPPED_TOKENS tightened (D-LOOP-26a); archetypes verified rendering (hero/marquee/featured__header) |
| F5 | Smooth scroll (Lenis) | 3 | F2 | T1 | MET-T1 | 3,n/a,3,3,3,3,3,4 | 3,n/a,3,3,3,3,3,4 | E2+E3 | 0 | r30 | MET — frozen; WATCH re-runs 6/6 test_f5_smooth_scroll.py + scripts/r29_e3_f5.py expect ALL PASS; r30 audit from scratch: 6/6 + E3 re-run 19/19 (rich smoothing curve 0→661→958→1196, G1 hide/return under Lenis, L1 pin 5→886 + flash, fx=none/touch/lite native with helper defined) + SRI recomputed from bytes = base.html tag + 16,731 B + LICENSE kept + no sourceMappingURL + M5 addendum entry covers fx-aware smooth scroll + D-LOOP-29a verified line-by-line — zero gaps |
| H1 | Home order & diet | 5 | — | **T2** (raised r35 retro) | MET-T1 | 3,3,n/a,3,3,3,3,3 | 3,3,n/a,3,3,3,3,3 | E2+E3 | 0 | r19 | MET-T1 — frozen at T1; T2 lift needs 4s incl. the batched D6 mobile eyeball (OWNER_NEEDS L3) |
| H2 | Hero | 5 | F2,F3 | **T2** (raised r35 retro) | **MET-T2 (r38 audit — second T2 in the project)** | **4**,**4**,n/a,**4**,**4**,**4**,4,4 | **4**,**4**,**4**,**4**,**4**,**4**,**4**,**4** | E2+E3 | 0 | r38 | r38 audit from scratch on a FRESH server: 10/10 test_h2_hero.py + scripts/r37_e3_h2_t2.py **24/24 ALL PASS** (R7+L8+M5+MR2+RM2; wire accounting reproduced byte-for-byte: css 173,559 + js 52,033 + fonts 290,180 + LCP 119,000; video 0 B on all off-rich legs) + D-LOOP-37a verified against code (preload fetchpriority=high in head, video hidden-by-default contract comment, 0 data-count in hero) + git working tree proves r37 evidence-only (only LOCKS + 2 regenerated screenshots) + 3 screenshots eyeballed (rich-1280 settled mask headline; mobile-390 stacked pill; mobile-rich-390 shows a DIFFERENT video frame = touch handover fired). aud=self all-4s, lower wins → MET-T2. WATCH re-runs: 10/10 test_h2_hero.py + scripts/r37_e3_h2_t2.py expect ALL PASS |
| H3 | Mobile bento | 5 | F2 | T1 | MET-T1 | 3,3,3,3,3,3,3,3 | 3,3,3,3,3,3,3,3 | E2+E3 | 0 | r20 | MET — frozen; WATCH spot-checks; E3: scripts/r20_e3_h3_audit.py 21/21 (snap rail, keyboard walk 0→1470, JS-blocked D-MOTION-SAFE, desktop untouched), LOOP/audit-screens/r20-e3-h3-*.png |
| H4 | Section rhythm | 3 | H1 | T1 | MET-T1 | 3,3,n/a,n/a,n/a,3,3,4 | 3,3,n/a,n/a,n/a,3,3,4 | E2+E3 | 0 | r31 | MET — frozen; WATCH re-runs 6/6 test_h4_section_rhythm.py + scripts/r30_e3_h4.py expect ALL PASS; r31 audit from scratch: 6/6 + E3 re-run 6/6 (fresh server after pkill — OPS lesson applied) + D-LOOP-30a verified against code (5 tags byte-match the documented mapping) + 390px screenshot eyeballed (hamburger nav, stacked pill, hero intact) + D-LOOP-30c doc wart fixed — zero gaps |
| G1 | Floating pill nav | 4 | F2 | T1 | MET-T1 | 3,3,3,4,4,3,4,4 | 3,3,3,4,4,3,4,4 | E2+E3 | 0 | r28 | MET — frozen; WATCH re-runs 6/6 test_g1_pill_nav.py + scripts/r27_e3_g1.py expect PASS; r28 audit from scratch: 6/6 + E3 re-run 10/10 + D-LOOP-27a claims verified line-by-line + 1280px visible/hidden screenshots eyeballed (r28-g1-header-*.png) — zero gaps; D6 tablet-band (1024–1199 nav handover) eyeball batched OWNER_NEEDS L4 |
| G2 | Shared-element transitions | 5 | F2 | **T2** (raised r35 retro) | MET-T1 | 3,3,3,3,3,3,4,4 | 3,3,3,3,3,3,4,4 | E2+E3 | 0 | r23 | MET-T1 — frozen at T1; T2 lift needs 4s on D1-D6 (real-browser transition capture would be the exemplary evidence) |
| G3 | Scroll-linked effects | 3 | F2,F4 | T1 | MET-T1 | 3,n/a,3,3,3,3,4,4 | 3,n/a,3,3,3,3,4,4 | E2+E3 | 0 | r32 | MET — frozen; WATCH re-runs 9/9 test_g3_scroll_linked.py + scripts/r31_e3_g3.py expect ALL PASS; r32 audit from scratch: 9/9 + E3 re-run ALL PASS on a fresh server (pkill first) + implementation read line-by-line against D-LOOP-31a (transition:none sole ownership, fail-closed :not([data-fx]), triple kill fx=none/reduced-motion/no-JS, bento untouched, M1 extension no new family) + r31-g3-services.png eyeballed (media frame renders, no shift) — zero gaps |
| G4 | Pointer polish | 2 | F2,F4 | T1 | MET-T1 | 3,3,3,3,3,3,4,4 | 3,3,4,3,3,3,4,4 | E2+E3 | 0 | r35 | MET — frozen; WATCH re-runs 7/7 test_g4_pointer_polish.py + scripts/r34_e3_g4.py expect ALL PASS; r35 audit from scratch: 7/7 + E3 re-run 18/18 (fresh server) + D-LOOP-34a verified against code (brace balance 279/279, dead fragment gone, 7/7 gate needles, M5/M6 rows correct, bento exclusion documented) + both screenshots eyeballed — zero gaps |
| L1 | Map & list sync | 5 | — | **T2** (raised r35 retro) | MET-T1 | 3,3,3,3,3,3,4,4 | 3,3,3,3,3,3,4,4 | E2+E3 | 0 | r25 | MET-T1 — frozen at T1; T2 lift needs 4s incl. the batched D6 mobile eyeball (OWNER_NEEDS L3) |
| L2 | Basemap palette | 4 | — | T1 | MET-T1 | 3,3,n/a,4,3,3,4,4 | 3,3,n/a,4,3,3,4,4 | E2+E3 | 0 | r27 | MET — frozen; WATCH re-runs 6/6 test_l2_basemap_palette.py + scripts/r26_e3_l2.py expect PASS; r27 audit from scratch: 6/6 + E3 7/7 live tiles re-run + D-LOOP-26b verified line-by-line against the code + screenshot eyeballed (vintage-atlas; taupe-on-paper label contrast computed 5.4:1) — zero gaps found; D6 desktop-E3 only (batched OWNER_NEEDS L3 row) |
| L3 | Row conversion & density | 4 | — | T1 | MET-T1 | 3,3,n/a,3,3,3,3,4 | 3,3,n/a,3,3,3,3,4 | E2+E3 | 0 | r29 | MET — frozen; WATCH re-runs 6/6 test_l3_row_density.py + scripts/r29_e3_l3_audit.py expect ALL PASS (live 24-row render: hierarchy, 16px icon, 445px content-driven heights, ≤28 content words — ellipsis is punctuation, mobile stack, zero errors); r29 audit from scratch: 6/6 + git-diff proves brand→agent channel conditions byte-identical + agent-fallback branch E3-rendered (brand unfilled in demo data) + r28-l3-row.png eyeballed — zero gaps |
| L4 | Detail gallery | 3 | G2 | T1 | MET-T1 | 3,3,3,3,4,3,4,4 | 3,3,3,3,4,3,4,4 | E2+E3 | 0 | r33 | MET — frozen; WATCH re-runs 9/9 test_l4_gallery.py + scripts/r32_e3_l4.py expect ALL PASS; r33 audit from scratch: 9/9 + E3 re-run ALL PASS on a fresh server (pkill-first) + D-LOOP-32a verified against code (JS-built overlay, G2 name unique on gallery main, .lightbox__main view-transition-name:none, Lenis stop/start via the F5 public API, M2 extension no new family) + both screenshots verified — zero gaps |
| Q1 | Perf budget (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r37 | r37 recorded the FIRST real wire measurement (r37_e3_h2_t2.py Leg L, content-length sums at networkidle, no scroll): home first-view css 173,559 + js 52,033 + fonts 290,180 + LCP 119,000 = **634,772 B** — ABOVE the ≤400KB budget; fonts are the biggest lever (290 KB), then CSS (173 KB); images 2.83 MB total incl. below-fold (lazy loading keeps them out of first-view cost but not the transfer total). Next WATCH/Q1 run: font subsetting (fewer weights) + CSS trim are the levers; method recorded here |
| Q2 | Accessibility (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r15 | Reduced-motion parity test per effect; 4.5:1; visible focus; keyboard |
| Q3 | Resilience (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r15 | All content visible with JS blocked and under fx=none |
| Q4 | Docs (WATCH) | — | all | T1 | TODO | – | – | – | 0 | r15 | PROTOCOL matches practice; addendum current; DECISIONS entries made |

Priorities recomputed at the r20 retrospective (D-LOOP-20a; untouched bonus +1 live from r20):
**L1 16 · G2 16 · F3 13 · F4 13 · G1 13 · L2 13 · L3 13 · F5 10 · H4 10 · G4 7\***
(* blocked: H2→F3 would be 16, G3→F4 would be 10, L4→G2 would be 10).
Build order: r35 (AUDIT G4 + WATCH + RETRO D-LOOP-35a) → r36 = BUILDER F2 T2 lift (matrix, D-LOOP-36a) → **r37 (done): AUDITOR F2 T2 claim → MET-T2 (first T2; 53/53 correction) + BUILDER H2 T2 lift (24/24, D-LOOP-37a)**. **r38 = AUDITOR**: audit the H2 T2 claim from scratch (10/10 test_h2_hero.py + re-run scripts/r37_e3_h2_t2.py expect ALL PASS + D-LOOP-37a re-read + r37-h2-*.png eyeball) → MET-T2 or demote; then BUILDER the next T2 lift (G2 real-browser transition capture, or F1 tokenisation pass over the 10 search.css hexes). WATCH rows Q1-Q4 remain cross-cutting — Q1 now has a real baseline (634,772 B) and a named lever (fonts).

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

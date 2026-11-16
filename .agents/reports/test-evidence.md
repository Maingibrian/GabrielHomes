# test-evidence.md — last real verification output

Rule (AGENTS.md done-when): no claim of completion without a pasted receipt.
Replace this file's content at the end of every session that runs the gate.

---

## 2026-11-13 · r92 — dashboard visual polish on the r91 board

Working tree at verification time: HEAD `e88c1b6a` + r92 changes
(`templates/manage/home.html`, `static/css/manage.css`,
`apps/manage/tests/test_r92_dashboard_polish.py` NEW).

### `manage.py check`
```
System check identified no issues (0 silenced).
```

### Full suite — `.venv/bin/python -m pytest -q` (real output, tail)
```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1118 passed, 620 warnings in 134.57s (0:02:14)
PYTEST_EXIT:0
```
(1112 r91 baseline + 6 new r92 tests. First run caught r91's
`test_kpi_strip_has_four_tiles_with_hints` counting the exact attribute
string `class="manage-kpi"` — broken by the hero tile's longer class
list; fixed to a word-boundary regex count, then full suite green.)

### `bash scripts/gate.sh` (real output, tail)
```
==> G-DEPLOY check --deploy
System check identified no issues (0 silenced).
==> G-SAFE |safe allowlist
==> G-CDN third-party hosts
==> G-STATIC collectstatic (prod)
==> G-COV coverage 80
==> coverage
GATE GREEN
GATE_EXIT:0
```

### Live DOM + VLM screenshot review (through gateway :81)
- Desktop 1440×900 full-page: `.manage-kpi--hero` ×1, `.manage-check--dark` ×1,
  `.manage-kpi__spark` ×1 (now under the enquiry KPI it measures). VLM: hero
  tile dark with sparkline, other three KPI tiles white; espresso checklist
  anchor with cream "Start here" box + orange button; compact site-content/SEO
  tiles; "Mark as done" buttons readable on espresso (btn--light-outline);
  no overlap/misalignment/unreadable text.
- Mobile 390×844 full-page: sidebar `none`, topbar `flex` (r91 mobile stack
  untouched), hero + dark anchor render additively; VLM: 2×2 KPI grid, chips,
  checklist readable, no clipped text.

---

## 2026-11-13 · r91 — owner-portal desktop dashboard (sidebar + board)

Working tree at verification time: HEAD `21f4745b` + r91 changes
(`templates/manage/_nav.html` NEW, `base.html`, `home.html`,
`static/css/manage.css`, `apps/manage/tests/test_r91_desktop_dashboard.py` NEW).

### `manage.py check`
```
System check identified no issues (0 silenced).
```

### r91 pins + design-stack guards (focused run)
```
.venv/bin/python -m pytest apps/manage/tests/test_r91_desktop_dashboard.py apps/manage/tests/test_portal_design_stack.py -q
14 passed, 11 warnings in 2.33s
```

### Full suite — `.venv/bin/python -m pytest -q` (real output, tail)
```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1112 passed, 617 warnings in 145.15s (0:02:25)
EXIT:0
```
1112 = 1102 baseline (r90) + 10 new r91 tests. No regressions.

### Live visual check (via gateway :81, logged in as owner)
- DOM (1440×900): `.manage-side` display `flex`, `.manage-nav` display `none`,
  `.manage-board` present with 8 zone elements.
- DOM (390×844): `.manage-side` display `none`, topbar + chip nav `flex`
  (mobile layout unchanged).
- VLM review of screenshots (desktop top/mid, mobile): numbered espresso
  sidebar (01–05, badge 3, account tools at foot), 4 KPI tiles with hint lines
  + sparkline, 12-col board (chart 8/pipe 4, top-viewed 8/recent 4), no
  overlap, no blank zones, no misalignment. Mobile: 2-col KPI grid, chip nav
  scrollable as designed (pre-existing r73 behavior).
- Screenshots: `/tmp/r91_shots/` (session-local; screenshots are not repo
  artifacts in this project).

NOT RUN this session: `bash scripts/gate.sh` end-to-end (check + pytest cover
its core stages; G-DEPLOY/G-STATIC/G-COV unchanged by a template/CSS-only
round); `manage.py makemigrations --check` (no model changes — verified no
new migrations needed via the full suite, which runs its own checks).

---

## 2026-11-13 · coordination-layer retrofit session

Working tree at verification time: HEAD `a3dd47fe` + uncommitted new
coordination files (AGENTS.md, AGENTS-COLLAB.md, .agents/**, specs/**,
loops/**, one 2-line append to docs/AGENT-BRIEF.md).

### `manage.py check` (from gabriel-homes-advanced-r64/gabriel-homes/)
```
System check identified no issues (0 silenced).
```

### Full suite — `.venv/bin/python -m pytest -q` (real output, tail)
```
apps/accounts/tests/test_saved.py::test_save_requires_login
apps/accounts/tests/test_saved.py::test_save_requires_login
apps/accounts/tests/test_saved.py::test_save_requires_login
apps/accounts/tests/test_saved.py::test_save_requires_login
  /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes/.venv/lib/python3.12/site-packages/django/db/models/fields/__init__.py:1148: RemovedInDjango60Warning: The default scheme will be changed from 'http' to 'https' in Django 6.0. Pass the forms.URLField.assume_scheme argument to silence this warning, or set the FORMS_URLFIELD_ASSUME_HTTPS transitional setting to True to opt into using 'https' as the new default scheme.
    return form_class(**defaults)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1102 passed, 611 warnings in 138.96s (0:02:18)
PYTEST_EXIT:0
```

1102 passed matches the r90 baseline (`19f67359`) exactly — the coordination
layer changed no application behavior, as intended.

NOT RUN this session: `bash scripts/gate.sh` end-to-end (its stages duplicate
manage.py check + pytest + deploy/static/coverage checks already covered
above); live preview login (no application change to verify live).

### Earlier in the same session (access-restoration work, commits `914d257a` + `33018bba`)
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:81/` → 200 (gateway)
- Public URL `https://preview-chat-32c380a6-f37c-48b2-a3b0-ee41938bc50c.space-z.ai/account/login/` → 200
- Playwright end-to-end through the public URL: owner login → `/manage/` portal (nav: Home / Enquiries / Listings / Site content / SEO), enquiries screen rendering seeded rows, homepage Portal link visible; no JS errors.

## r93 — listings edit pages (2026-11-15)

- `.venv/bin/python manage.py check` → `System check identified no issues (0 silenced).`
- RED phase (before fixes): `apps/agents/tests/test_r93_listing_edit_pages.py` → 6 failed on the real bugs: amenities wiped (`assert [] == [20, 18, 1, 5]`), marketing `<footer>` in editor HTML, orphan `<option>` tags, select missing from manage.css rule, no width cap on .dashboard-form, visible land/service inputs.
- After fixes: `9 passed` (edit pages) + `3 passed` (listings screen) = 12 new r93 tests.
- Full suite: `.venv/bin/python -m pytest -q` → `1130 passed, 628 warnings in 137.84s` · EXIT:0 (1118 r92 baseline + 12 new)
- `bash scripts/gate.sh` → `GATE GREEN` · EXIT:0 (stages: check / makemigrations --check / pytest 1130 / G-DEPLOY / G-SAFE / G-CDN / G-STATIC / G-COV)
- Live DOM via :81 + :8000: wizard selects computed style `rgb(250,248,244)` bg / 8px radius / appearance:none / custom chevron (was `rgb(239,239,239)` / 0px / native). Editor: 24 amenity checkboxes (0 before), 0 `<footer>`, 5 section fieldsets. Listings: 20/20 rows with thumbs at desktop; `.manage-row__thumb` base `display:none` (mobile stack unchanged — verified in stylesheet rules; headless window min 1280px prevented a pixel screenshot at 390px).
- VLM screenshot review (desktop): listings rows "compact single-line-plus-meta cards… scannable", editor "selects match the inputs… no duplicated labels… no marketing footer", no overlap/misalignment/broken areas.

## r94 — front-page motion (2026-11-15)

- Owner asks: palms stagnant; phone bento scroll-triggered leftward card motion; "gabriel/homes" flank words alive in place (no up/down); gutter white space gets a 3-image upward carousel.
- RED first: NEW `apps/core/tests/test_r94_front_page_motion.py` → 10 failed on exactly the intended changes (sway present, no drift, no breathe, script loaded, no reels).
- After fixes: r94 suite 14 passed. Retired pins updated: `test_c1_palm_sentinels.py` (r62 wind tests → stagnant tests), `test_r44_bento_unpack.py` (parallax script contract → in-place animation contract).
- Full suite (after final reel CSS fix): `.venv/bin/python -m pytest -q` → `1144 passed, 628 warnings in 194.31s` · EXIT:0 (1130 r93 baseline + 14 new).
- `bash scripts/gate.sh` → `GATE GREEN` · EXIT:0.
- Live DOM (1920×1080, data-fx=rich): `.bento-flank__word` animationName `r94-flank-breathe`; `.flank-reel__film` animationName `r94-reel-rise`, reels 180px wide × 544px (fixed a zero-width bug: flank wrappers are zero-width so percentage widths collapse — reel now uses `clamp(7.5rem, calc(50vw - 47rem), 11.25rem)`).
- Mobile (iPhone 14 emulation, 413px): rail `h3-rail-drift` with `animation-timeline: scroll()`; measured transform −6.6px at section entry → −42.6px near page end (monotonic leftward drift driven by page scroll); reels/words display:none below 1440px.
- Reduced motion (media emulation): rail, reels, and words all `animation: none`.
- VLM (1920px): reels visible in both gutters, soft-faded edges, no overlap with bento cards or words; layout intact.

## r95 — reel execution + bento polish (2026-11-15)

- Owner asks: blur before/after on the carousel; rectangular (not square) images; infinite loop (r94 "currently ends"); better bento card presentation.
- Root cause of the "ending" reel: r94 shipped ONE set of 3 frames while the keyframe translated a full loop height — the window emptied, then snapped. Fix: set shipped twice in markup (6 frames/reel) + loop distance = exactly one set height.
- RED first: NEW `apps/core/tests/test_r95_reel_bento_polish.py` → 8 failed on the intended changes.
- Geometry hardened in CSS vars: `--reel-w` (gutter clamp) → `--reel-frame-h = w × 2/3` (the 3/2 rectangle) → `--reel-set-h = 3 frames + 3 gaps` (window AND loop distance — they share the var, so they can never drift). Caught live: the first pass used `aspect-ratio: 3/2` + a separate hardcoded 8.5rem var — frames rendered 120px while the loop assumed 136px (would still jump); the derived-height fix makes drift impossible.
- Blur strips: `.flank-reel__blur--top/--bottom`, backdrop-filter blur(7px) with their own fading masks — the frames dissolve through blur entering and leaving the window.
- Bento polish: resting espresso shadow + cream hairline ring (outline, offset -1px); hover lift `translate: 0 -4px` (the SEPARATE `translate` property — bento-shift.js FLIP owns `transform`, they cannot clobber); bed/bath facts → frosted glass chips (fact dropped from the shared middot ::before; location keeps it); price up to ~21.3px sand; index smaller + 0.78 opacity.
- Full suite: `pytest -q` → `1153 passed, 628 warnings in 183.70s` · `bash scripts/gate.sh` → `GATE GREEN` · EXIT:0. (An earlier gate run failed transiently: the geometry edit landed mid-run and pytest read the file mid-write; the clean re-run above is the receipt.)
- Live DOM 1920px: frames 180×120 (ratio 1.500), film 780px = 2 sets, window/loop 396px = set height (loop == set ⇒ seamless), blur top+bottom `blur(7px)`, drift −55px over 4s ≈ 396px/30s. VLM: both reels show rectangular filmstrips dissolving through blur at the edges; cards show soft drop shadows; mobile shows bed/bath pills and prominent price, rail drift intact (`h3-rail-drift`), reels hidden below 1440px. Hover lift mechanism proven by injected-rule test (`translate: 0px -4px` applied) — the real rule is `(hover:hover)`-gated, correct for touch devices.

## r96 — the reels hug their words (2026-11-15)

- Owner ask: "the carousels are way too far from the words" (measured live: gabriel→reel 234px, homes→reel 303px @1920). Root cause: r94/r96-prior reels were pinned to the SECTION's far edges (bottom/top: 6rem) while the words anchor from the OPPOSITE ends (gabriel top:7.5rem, homes bottom:7.5rem) — the gap grew with section height.
- Fix: each flank becomes a flex COLUMN (word static in flow, reel static in flow, --reel-hug: 1.75rem between them); the word keeps its exact anchor via the flank's own padding (7.5rem); gabriel stacks word→reel, homes stacks reel→word (justify-content: flex-end) — identical visual order as before.
- RED first: NEW apps/core/tests/test_r96_reel_hug.py — 4 failing on the intended change (1 keep-pin passed from the start).
- Live: gaps now exactly 28px BOTH sides, at 1920 and 1512; horizontal pins identical to the old right:0/left:0 pins; mobile (<1440px) flanks+reels hidden, 6 cards intact; fx=none → 28px hug holds, film static. VLM: "filmstrip sits close below the gabriel word... reading as one cohesive decorative unit"; no overlap with cards/header; no breakage.
- Full suite: pytest -q → 1158 passed, 628 warnings (143.41s); bash scripts/gate.sh → GATE GREEN, exit 0. No edits during the run.
- Login verification this round: owner login via the real chain (caddy :81) — POST /account/login/ → 302 /manage/ + sessionid cookie. NOTE the allauth field name is `login`, not `email` (cost two debug cycles). CSRF: the Origin/Referer must be the :81 origin the browser uses.

## r97 — the reels run word→section edge (2026-11-15)

- Owner ask: "the carousel should also run from the words all the way to edge of the section". r96 left the reel a fixed 3-frame window (276px) beside the word with dead space to the edge.
- Fix: .flank-reel drops `height: var(--reel-set-h)` for `flex: 1` + `min-height: calc(3 * var(--reel-frame-h) + 2 * var(--reel-gap))` (the floor doubles as the flex-item min-height override so the 21-frame film can never force the flank taller than the section). Films grew from 6 to 21 frames (7 sets) via scripts/r97_expand_films.py — loop distance unchanged (exactly one set, r95 pin).
- Coverage math: worst case @1440 window 1138px + set 276px = 1414px ≤ 7 sets (1920px). @1920: window 772 + set 464 = 1236 ≤ 7 sets (2760px).
- RED first: NEW apps/core/tests/test_r97_reel_span.py (2 RED on the intended change, 3 keep-pins green). Rewrote two superseded pins deliberately: test_r96 template-shape pin 12→42 frames; test_r95 film-duplication pin 6→21 frames (both with reasons in their docstrings).
- Live: gabriel reel_bottom→section_bottom = 0px, homes reel_top→section_top = 0px (both 1920 AND 1440); hug 28px both sides both breakpoints; mid-animation film covers window (transform -38px / -197px into cycle, covers:true); mobile 413px 0 reels visible, 6 cards; fx=none static with span held. VLM: "filled edge-to-edge... no empty band where a card is missing" both sides.
- Full suite: pytest -q → 1163 passed, 628 warnings (180.73s); bash scripts/gate.sh → GATE GREEN, exit 0. No edits during the run.

## r98 — "Full sale list" tile upgrade (2026-11-15)

- Owner ask: the full sale list card in "Homes for the way you want to move." needs its styling upgraded, building on the style it has. Target: .market-rail__more (group 01's closing tile, 460×417 @1920 — the plainest tile in the section).
- Direction: its sibling closer (.market-stay--more, group 03) already carried the r18.1 language — ghost group-numeral watermark, sand keyline over the eyebrow, chip affordance. The sale tile got the same language on its existing espresso base; NO markup change, no redesign.
- Changes (static/css/home.css only): position:relative+overflow:hidden on the tile (watermark clip); ::before ghost "01" top-right (clamp 5–6.5rem, rgba(250,248,244,.07), mono); small gains border-top 1px rgba(217,162,126,.45) + padding-top 14px; the arrow span becomes a 40px circular outlined chip (34px ≤900px) that fills var(--burnt) on hover keeping the translateX(5px) nudge; radial warm glow rgba(217,162,126,.14→.2) layered over the kept espresso gradient at 12%/100% (bottom-left); content now justify-content:flex-end + align-items:flex-start (bottom-anchored like the sibling); mobile block: numeral clamp(3.5rem,9vw,5rem) tucked top:6px right:10px.
- RED first: NEW apps/core/tests/test_r98_sale_tile_upgrade.py — 6 RED on the change + 1 markup keep-pin green from the start. Helpers: _strip_media (nested-brace-safe) + _media_blocks (brace-walker). 7 green after.
- Live: keyline 1px rgba(217,162,126,.45) + padding 14px; chip 40px/999px/rgba(238,207,174,.4) border; glow layered both states; 1440 numeral 93.6px contained; mobile 413px: numeral 56px @ top 6px, chip 34px, tile 161px overflow hidden; fx=none: all styles static-present. VLM: all five elements confirmed, "no clipping, overlap, or cramped spacing".
- Full suite: pytest -q → 1170 passed, 628 warnings (189.46s); bash scripts/gate.sh → GATE GREEN, exit 0. No edits during the run.

## r99 — sale tile elevation + reveal-vs-hover defect fix (2026-11-15)

- Owner ask: "the card is well styled but not that great" — r98's detailing was correct but the tile read flat. r99 = elevation pass, CSS-only, markup untouched, all r98 pins kept.
- Elevation (static/css/home.css): resting presence — ambient espresso shadow 0 16px 44px rgba(28,21,17,.16) + inset hairline ring rgba(250,248,244,.04) (r95 bento language) + fine diagonal grain weave (repeating-linear-gradient 115deg, .045 alpha, 1px/5px — tuned with VLM until faintly visible but not stripes; .012 and .02 were sub-visible); hover sheen sweep — one ::after carries grain + a 115deg band, ships scaleX(0), hover sweeps to scaleX(1) translateX(8%) (transform-only, no repaint); ghost numeral gains life — hover translate(6px,-10px) + color warms .07→.12; chip gains glow ring — 0 0 0 5px rgba(175,71,21,.18) + 0 0 22px rgba(217,162,126,.35) joining the burnt fill; keyline brightens .45→.75 on hover; serif cap 1.5→1.65rem.
- DEFECT found live during verification (D-REVEAL-LIFT): html.motion-ready [data-reveal].is-visible (0,3,1) pins transform:translateY(0) and out-specifies every revealed card's :hover (0,2,0) — ALL home-page market/nearby card hover lifts were dead under motion-ready (live-verified identity matrix while hovered; masked because box-shadow still changed). Fix: html.motion-ready … .is-visible:hover overrides (0,4,1+) for market-feature/-banner/-rail__card/-stay/-stay--more/-rail__more + nearby-card img, each mirroring its own lift/shadow. Live after: tile -4, feature -4, stay -5, nearby img -5.
- RED first: 6 elevation tests + 1 defect pin, all RED before the CSS, 14/14 green after (suite grew to 1177).
- Live battery: 1920 hover (sheen matrix(1,0,0,1,36.6,0), numeral (6,-10), tile -4, chip burnt+glow, keyline .75); 1440 (serif 24.48px, numeral 93.6px contained); iPhone 413 (numeral 56px top 6px, chip 34px, band 161px, overflow hidden, hover:none so no sticky hover); fx=none (shadow+ring+grain rest, no animation). VLM resting review: "premium, ~8/10" → after grain fix: "quiet material texture rather than stripes".
- Full suite: pytest -q → 1177 passed, 628 warnings (136.69s); bash scripts/gate.sh → GATE GREEN, exit 0. No edits during the run.

## r100 — hero slideshow + mobile hero + sale tile (2026-11-15)

- Owner asks (round seventeen): retire the "not the best" background video for a world-class image slideshow; fix the mobile hero; the tile still isn't world class.
- SLIDESHOW (Ken Burns, CSS-only): <video> tag + motion.js setupHeroVideo + .hero__video/.is-video flip CSS all RETIRED (1.5MB mp4 no longer ships even on rich devices; f3's contract already accepts the unreferenced end state). Each .hero__slide declares its own --kb-from/--kb-to transform pair (four distinct pan/zoom characters: push-in on the sea, pull-back over the arches, terrace drift, counter-drift) consumed by shared hero-fade/hero-drift keyframes; cycle 24s→80s (20s per slide, director pace; beginner shows restate every 6s); crossfade overlap compressed to 0-1.25%/25-27.5%; opacity+transform only (compositor-friendly).
- MOBILE HERO: poster window 46vh letterbox → clamp(380px, 62svh, 560px) portrait window with per-slide --slide-pos crop anchors in the template (VLM before: "raw phone snapshot"; after: "premium... designed boutique property site, not a template"); caption plate simplified to gap-only separation (VLM: "three devices doing one job").
- TILE (bold move): the tall middle that read empty for two rounds now carries a fanned polaroid trio of the sale group's own photos (cream frames + chin, committed tilts -8/+1.5/+8deg, deep shadows, z-stack, fully inside the tile — VLM-verified containment after an initial crop ambiguity) + a live count stat ("43 homes for sale right now", view-computed sale_count, white bold number) + full-measure sand keyline (alpha .45→.55, superseding r98 pin with reason) + tightened headline→chip gap. Polaroid polish came from two VLM review rounds (first pass: "three rectangles, tilt not legible" → committed motif pass: "tactile and intentional").
- RED first: 8 new tests in test_r100_hero_slideshow_tile.py (video retired, per-slide direction, director pace, fx-safe slideshow, taller cover window, plate simplification, fan presence, live count, fan fx-safe containment) — all RED before implementation; 2 superseded H2 pins rewritten with reasons (video contract → removal pin; JS boundary marker setupHeroVideo → setupPointerPolish); 1 superseded r98 pin (keyline .45→.55 full measure).
- Live battery: 1920 (4 slides, no video element, 80s cycle, s1 mid-drift matrix scale 1.12; crossfire sample s1_op 0 → s2_op 1 handover clean; hover: tile -4, fan straightens rotate(-1.5deg), sheen sweeps, chip burnt); 1440 (drift live, fan inside, serif 24.48px); iPhone 413 (fan 306px inside 355px tile, hover:none touch-safe); fx=none (slide 1 static visible, others 0, tile+fan+count present).
- VLM verdicts: desktop hero "world-class-leaning... bespoke feel"; mobile hero "premium... not a template" (crop praised, caption tidy); tile "excellent execution; one interaction/rhythm refinement from world-class" → that refinement (hover liveness) already existed and the rhythm gap was tightened; final check confirmed all three polaroids fully inside.
- DEFECT found + fixed en route (D-RNG-POLLUTION): the first two full-suite runs failed on r65's coast-chip test (location page with zero listings) — deterministic in full-suite order, green in isolation. Root cause: seed_demo's RNG was seeded at MODULE level, so its state depended on how many earlier suites had run seed_demo in the same process; the random spread of listings across neighbourhoods differed by call order and could starve a chip location (Shanzu/Mtwapa). Fix: random.seed(42) moved into Command.handle() so every invocation is deterministic on its own; polluted pairs verified green, then the full suite.
- Also en route (F1 latent bug): the count font's first pass used 12.5px — below the 13px floor — and the F1 allowlist test's int(px) crashed on the decimal before it could report it. Font raised to 13px AND the test's allowlist comparison made decimal-safe (round(float(px))).
- Final receipts: pytest -q → 1186 passed, 631 warnings (206.19s); bash scripts/gate.sh → GATE GREEN, exit 0. No edits during the final runs.

## r105 — 2026-11-16 (agencies cleanup + edit-page pin picker)
- `manage.py check`: 0 issues (0 silenced)
- `pytest apps/agents apps/manage -q`: 291 passed (1 label-pin updated: test_owner_inquiries_see_all_agencies asserts "All inquiries" — the "[ ALL AGENCIES ]" bracket label was retired; behaviour unchanged)
- FULL SUITE `pytest -q`: **1227 passed, 672 warnings in 156.53s (0:02:36)** — 0 failed
- `scripts/gate.sh`: GATE GREEN
- Live through :81 (scripts/r105_live_verify.py): 16/16 PASS — agencies UI absent from dashboard + all-listings, /dashboard/agencies/ still 200, edit page pin-map div + pin-picker.js + rendered canvas, map click fills id_lat/id_lng with Mombasa-range coords, Studio↔workspace cross-links both directions, mobile 413 map renders
- Public chain (browser UA): login 200 → /dashboard/; edit page has pin-map; dashboard has Studio link, no Agencies label

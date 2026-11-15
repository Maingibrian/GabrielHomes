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

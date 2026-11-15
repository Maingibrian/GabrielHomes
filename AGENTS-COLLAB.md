# AGENTS-COLLAB.md — live handoff layer (not history)

Update this file at the END of every session. Keep it short enough to read
in under 3 minutes together with AGENTS.md.

## Current state
- **Last updated:** 2026-11-15 (r99 session)
- **Active branch:** `main` (remote `Maingibrian/GabrielHomes`, GitHub)
- **HEAD before this session's commit:** `8e49aa05` (r98)
- **Last dev round:** r99 — sale-tile elevation (presence, sheen, drift, glow) + D-REVEAL-LIFT defect fix (all revealed home cards' hover lifts were dead under motion-ready)
- **PAT note:** the owner's PAT (supplied r96 session) works; r93–r99 all on GitHub. If push 401s, ask for a new PAT (do NOT store it in any file — pass inline only, never commit it).
- **Known recurring cost:** sandbox recycle wipes `db.sqlite3`/`.venv`/daemon between sessions (restore recipe: `.agents/memory/lessons.md`)
- **Preview:** up on ports 3000/81 inside the sandbox; public URL `https://preview-chat-32c380a6-f37c-48b2-a3b0-ee41938bc50c.space-z.ai` works only while this sandbox instance lives

## Active decisions (in-flight)
- Preview env vars (`CSRF_TRUSTED_ORIGINS`, `EXTRA_ALLOWED_HOSTS`) are set in repo-root `scripts/launch_preview.py`, NOT in Django settings — deliberate: preview/gateway concern, keeps plain local runs unaffected.
- `loops/plan-execute-verify.md` is the operating loop for non-trivial changes; small fixes may skip it but must still paste a verification receipt.
- Coordination files live at git root; the Django tree keeps its own `docs/AGENT-BRIEF.md` protocol — both apply, AGENTS.md reading order first.
- r91: portal desktop shell keys on `body.page-manage` at `min-width: 64rem`; mobile chrome (topbar + chip nav) stays in the DOM and is only hidden by CSS. Both nav variants render from `templates/manage/_nav.html` — edit that one file, never one variant alone.
- r92: the dashboard's visual hierarchy is expressed with additive classes on the r91 zones — `manage-kpi--hero` (first KPI, espresso, owns the 30-day sparkline because `stats.per_day` counts ENQUIRIES) and `manage-check--dark` (espresso anchor). Mobile keeps the r91 stack: these classes restyle, they do not move DOM. Undo buttons inside the dark card use `btn--light-outline`.
- r93: `PropertyFormMixin.get_form_class()` now passes `widgets` through `modelform_factory` — Django's `ModelFormMixin.get_form_class()` silently ignores a class-level `widgets` attr when only `fields` is set; any future widget on that form goes in `PropertyFormMixin.widgets`, never as a bare class attr. The dashboard editor/create/images templates override `header`/`footer`/`scripts` blocks to empty — backend screens must not grow marketing chrome again. `.manage-field select` styling is pinned by test; new portal form controls get it for free.

## Traps (do not repeat)
- POST forms 403 through any gateway unless its Origin is in `CSRF_TRUSTED_ORIGINS` → traps.md #1
- Public preview URL 400s unless `.space-z.ai`/`.fcapp.run` are allowed hosts → traps.md #2
- Verifying through localhost only can mask the Host-header bug → traps.md #2
- Raw XFF as rate-limit key = attacker bucket rotation → traps.md #3
- `seed_demo` without `--with-enquiries` = silently empty portal inbox → traps.md #4
- Sandbox recycle wipes DB/venv/daemon; unpushed work is lost → traps.md #5
- `media/demo-photos/` must stay tracked ("cards are back", 3×) → traps.md #6
- Background shells here start at repo root, not the Django dir — use absolute paths or `cd` inside the command → traps.md #7

Full detail: `.agents/memory/traps.md`

## Agent roster
| agent | role | current task | status |
|---|---|---|---|
| zgo/glm-5.3 (ZCode) | full-stack + coordination | retrofit agent coordination layer | done — see handoff below |

## Handoff block template
```
### Handoff — <date> · <agent>
What I did:
What I verified (command + output):
What I did NOT do:
Next concrete step:
```

### Handoff — 2026-11-15 · ZCode (r99 — sale-tile elevation + reveal-lift defect fix)
What I did:
- Owner round sixteen: "the card is well styled but not that great" → elevation pass on the same tile, CSS-only: resting ambient espresso shadow + inset hairline ring + VLM-tuned grain weave; hover sheen sweep (transform-only, no repaint); ghost-numeral drift + warm; chip glow ring; keyline brightens .45→.75; serif cap 1.65rem. All r98 pins kept.
- DEFECT (D-REVEAL-LIFT) found live and fixed: `html.motion-ready [data-reveal].is-visible` (0,3,1) pinned translateY(0) over every revealed card's :hover (0,2,0) — ALL home market + nearby card hover lifts were dead under motion-ready since the reveal system landed. Added reveal-proof `html.motion-ready … .is-visible:hover` overrides (6 card families + nearby img). Live-verified: tile -4, feature -4, stay -5, nearby img -5.
What I verified (command + output):
- `pytest -q` → `1177 passed, 628 warnings in 136.69s` · `bash scripts/gate.sh` → `GATE GREEN` · FINAL_EXIT:0.
- Live: 1920 real-mouse hover (sheen swept, numeral (6,-10), tile -4, chip burnt + glow ring); 1440 + iPhone 413 (contained, hover:none safe) + fx=none (presence rests, nothing animates). VLM: resting "premium, ~8/10"; grain confirmed visible after tuning (.045 alpha, 1px/5px).
What I did NOT do:
- No markup/JS changes; other sections' cards (hero, bento) untouched — their hover patterns were audited and unaffected (listing-card never pairs with data-reveal).
Next concrete step:
- Owner preview review (hard-refresh); if the sheen should be brighter/slower or the grain quieter, each is one value in the r99 block of home.css.

### Handoff — 2026-11-15 · ZCode (r98 — "Full sale list" tile upgrade)
What I did:
- Owner round fifteen: the full sale list card (.market-rail__more) styling upgraded, building on its espresso base. It now speaks the same language as its sibling closer (group 03's stay tile): contained ghost "01" numeral, sand keyline over the eyebrow, circular arrow chip that fills burnt on hover, warm radial glow in the bottom-left, bottom-anchored content. CSS only — template markup untouched. Mobile band sized down (numeral 3.5–5rem, chip 34px).
What I verified (command + output):
- `pytest -q` → `1170 passed, 628 warnings in 189.46s` · `bash scripts/gate.sh` → `GATE GREEN` · FINAL_EXIT:0.
- Live: keyline 1px rgba(217,162,126,.45), chip 40px/999px, glow layered; 1440 numeral 93.6px contained; mobile 413px numeral 56px @top 6px + overflow hidden; fx=none all styles present. VLM: all five elements confirmed, "no clipping, overlap, or cramped spacing".
What I did NOT do:
- No markup/JS changes; the rent group's tiles were not in scope.
Next concrete step:
- Owner preview review; if the glow should be warmer/stronger or the numeral bigger, both are single-value tweaks in the r98 block of home.css.

### Handoff — 2026-11-15 · ZCode (r97 — reels run word→section edge)
What I did:
- Owner round fourteen: "the carousel should also run from the words all the way to edge of the section" — the reel window dropped its fixed 3-frame height for flex:1 + a 3-frame min-height floor (the floor doubles as the flex-item min-height override so the 21-frame film can't force the flank taller than the section). Films: 6→21 frames per reel (7 sets; loop distance still exactly one set). Generated by scripts/r97_expand_films.py at repo root.
- Rewrote two superseded pins with reasons in their docstrings: r96 template-shape (12→42 frames total), r95 film-duplication (6→21 per reel).
What I verified (command + output):
- `pytest -q` → `1163 passed, 628 warnings in 180.73s` · `bash scripts/gate.sh` → `GATE GREEN` · FINAL_EXIT:0.
- Live: gabriel reel-bottom→section-bottom 0px, homes reel-top→section-top 0px (1920 AND 1440); hug 28px everywhere; mid-animation film covers window (covers:true at -38px/-197px into cycle); mobile 413px: 0 reels, 6 cards; fx=none: span holds, film static. VLM: "filled edge-to-edge... no empty band".
What I did NOT do:
- Nothing outstanding. Owner: hard-refresh the preview to see the span.
Next concrete step:
- Owner preview review; if the spaced-stack look should become a solid run (no gaps between frames), that is a tokens-only tweak (--reel-gap).

### Handoff — 2026-11-15 · ZCode (r96 — reels hug their words + push unblocked)
What I did:
- Owner round thirteen: "the carousels are way too far from the words" — measured 234px/303px @1920. Root cause: reels pinned to the section's far edges while words anchor from the opposite ends; gap grew with section height. Fix: flanks are flex columns now (word static, reel static, --reel-hug 1.75rem between them), words keep their exact anchors via flank padding (7.5rem), gabriel stacks word→reel, homes reel→word. Gap: fixed 28px both sides, all viewports.
- Scope discipline per owner ask: only home.css placement rules + the new test file; template untouched (pinned by test: 12 frames, 4 blur divs unchanged).
- Backend password: set a fresh temp password on the owner account (admin@gabrielhomes.co.ke) and verified the login through the real chain (302 → /manage/, sessionid). NOTE: allauth login field is `login`, not `email`.
What I verified (command + output):
- `pytest -q` → `1158 passed, 628 warnings in 143.41s` · `bash scripts/gate.sh` → `GATE GREEN` · FINAL_EXIT:0.
- Live: gaps exactly 28px @1920 and 1512; 1439px cutoff holds (flanks hidden); mobile 413px: flanks/reels hidden, 6 cards intact; fx=none: 28px hug + static film. VLM: filmstrip "sits close below the gabriel word... one cohesive decorative unit"; no overlap/breakage.
- Login: POST /account/login/ → `302 redirect: http://127.0.0.1:81/manage/` + sessionid cookie.
What I did NOT do:
- Nothing outstanding. (Screenshots reviewed at mid-scroll + section-top; both fine.)
Next concrete step:
- Owner: sign in with the temp password (change it under Studio → Change password), review the hug on the preview, hard-refresh.

### Handoff — 2026-11-15 · ZCode (r95 — reel execution + bento polish)
What I did:
- Owner round twelve. (1) INFINITE REEL: root cause of "it currently ends" — r94 shipped one set of 3 frames but the keyframe translated a full loop height, so the window emptied then snapped. The set now ships TWICE (6 frames/reel) and the loop distance = exactly one set height. (2) BLUR BEFORE/AFTER: `.flank-reel__blur--top/--bottom` strips, backdrop-filter blur(7px) + fading masks — frames dissolve through blur entering and leaving. (3) RECTANGLES: 3/2 landscape; frame height DERIVED from reel width (`--reel-frame-h: calc(var(--reel-w) * 2 / 3)`) so ratio + loop math share one source. (4) BENTO POLISH: resting shadow + hairline ring, hover lift on the `translate` property (FLIP-safe; bento-shift.js owns `transform`), bed/bath glass chips (middot retired for facts only), price enlarged/sand, index quieter.
- Live-caught geometry bug: first pass used `aspect-ratio: 3/2` + hardcoded 8.5rem loop var — frames rendered 120px, loop assumed 136px (would still jump every cycle). Derived-height fix makes drift structurally impossible; window and keyframe both read `--reel-set-h`.
- Preview daemon restarted mid-session (stale template); fresh daemon serves 12 frames + 4 blur strips.
What I verified (command + output):
- `pytest -q` → `1153 passed, 628 warnings in 183.70s` · `bash scripts/gate.sh` → `GATE GREEN` · EXIT:0. (One earlier gate run failed transiently — my CSS edit landed while pytest was mid-run; clean re-run above is the receipt.)
- Live 1920px: frames 180×120 (ratio 1.500), film 780px = 2 sets, window/loop 396px = set height ⇒ seamless; blur strips `blur(7px)` top+bottom; rise −55px/4s. VLM: both reels rectangular + blur-dissolved edges, cards show shadows; iPhone 413px: bed/bath pills + prominent price + rail drift intact, reels hidden. Hover lift proven via injected-rule test (`translate: 0px -4px` applies); real rule is `(hover:hover)`-gated — correct for touch.
What I did NOT do:
- Real-pointer hover screenshot (headless browser reports `(hover: hover)` false) — verified via CSSOM + injected rule instead.
- Push NOT RUN successfully — PAT still 401. r93+r94+r95 sit on local main only.
Next concrete step:
- Owner reviews preview (hard-refresh). Fresh PAT → push three rounds.

### Handoff — 2026-11-15 · ZCode (r94 — front-page motion)
What I did:
- Owner round eleven, four front-page asks. (1) Palms STAGNANT: deleted the r62 wind sway/flutter block from search.css — trees, sticky placement, fx gate untouched (the SVG is generator-owned, never edited). (2) Phone bento: the H3 swipe rail now also drifts LEFT as the page scrolls (`h3-rail-drift`, animation-timeline: scroll(), @supports-gated; native swipe + snap untouched as fallback; reduce block stops it). (3) "gabriel"/"homes" flank words ALIVE IN PLACE: `r94-flank-breathe` (letter-spacing + skew lean, NO translate of any kind) replaces the vertical parallax; js/bento-flank.js no longer loads (file kept for history). (4) Gutter white space: `flank-reel` vertical carousels — 3 soft-masked coastal photos rising (`r94-reel-rise`) below "gabriel" and above "homes", ≥1440px only, decorative.
- Bug caught in live verify: flank wrappers are ZERO-WIDTH, so the reel's percentage width collapsed to 0px — now `clamp(7.5rem, calc(50vw - 47rem), 11.25rem)`.
- Belt-and-braces reduce block added: reels + words stop under prefers-reduced-motion even when the fx gate is emulated.
- Tests: NEW test_r94_front_page_motion.py (14, RED first); retired/rewrote the r62 wind pins in test_c1_palm_sentinels.py and the r44 parallax-script pin in test_r44_bento_unpack.py.
What I verified (command + output):
- `pytest -q` → `1144 passed, 628 warnings in 194.31s` · EXIT:0 · `bash scripts/gate.sh` → `GATE GREEN` · EXIT:0
- Live DOM 1920px fx=rich: word animationName `r94-flank-breathe`, reel `r94-reel-rise`, reels 180×544px both gutters (VLM: stacks visible, no overlap, no breakage). iPhone 413px: rail drift measured −6.6px → −42.6px across section travel. Reduced-motion emulation: rail/reels/words all `animation: none`.
What I did NOT do:
- The reel shows 2 fully-visible frames + 2 dissolving at the mask edges by design (3-frame window with 18% top/bottom fade); if the owner wants 3 crisp frames, raise the mask stops from 18%/82% to ~8%/92%.
- Push NOT RUN successfully — PAT still 401. r93+r94 sit on local main only.
Next concrete step:
- Owner reviews the preview (same URL, hard-refresh for new CSS). Fresh PAT → push both rounds.

### Handoff — 2026-11-15 · ZCode (r93 — listings edit pages)
What I did:
- Owner: "iterate to improve only the listings page edit in the back end.. the page end page of listings page looks horrible". Audited every screen in the flow (wizard steps, /manage/listings/, the row Edit target /dashboard/listings/<pk>/edit/) with screenshots + VLM + computed styles.
- Fixed a DATA BUG first: the editor's amenities were a SelectMultiple iterated as checkboxes in the template → orphan <option> tags ("Lift Lift") and no amenities key in the POST → every Save silently wiped amenities. Fix: `PropertyFormMixin.widgets = {amenities: CheckboxSelectMultiple, land_size_acres/service_charge: HiddenInput}` + `get_form_class()` override (Django's ModelFormMixin.get_form_class() IGNORES a class-level widgets attr — it must pass through modelform_factory). Hidden fields now ride along hidden instead of rendering as two unlabeled inputs.
- Editor visuals: header/footer/scripts blocks emptied (no marketing chrome on backend screens), form capped at 56rem, fields grouped into 5 labelled section fieldsets, selects get custom chevron matching inputs, amenities as readable checkbox tiles, sticky save bar.
- Portal-wide: `.manage-field select` added to the shared control rule (wizard step 1's four raw OS dropdowns now match the inputs; computed style went native gray/0px → cream/8px/chevron).
- /manage/listings/ desktop: rows get cover thumbnails (prefetched covers, to_attr=cover_images, no N+1; pinned by a query-count test), 72rem board cap, tools column flattened, tighter rows. Mobile stack untouched (thumb base rule display:none, verified in stylesheet rules).
- NEW tests: apps/agents/tests/test_r93_listing_edit_pages.py (9) + apps/manage/tests/test_r93_listings_screen.py (3), written RED first — 6 initial failures were the real bugs (amenities `assert [] == [20, 18, 1, 5]`, `<footer` present, select missing from CSS, no width cap).
What I verified (command + output):
- `manage.py check` → `System check identified no issues (0 silenced).`
- `pytest -q` → `1130 passed, 628 warnings in 137.84s` · EXIT:0 (1118 r92 baseline + 12 new)
- `bash scripts/gate.sh` → `GATE GREEN` · EXIT:0
- Live DOM: editor 24 amenity checkboxes (0 before), 0 `<footer>`; wizard select cream/8px/appearance:none; listings 20/20 rows with thumbs; mobile thumb rule display:none. VLM: "selects match the inputs… no duplicated labels… compact single-line-plus-meta cards… scannable".
What I did NOT do:
- Did not touch the wizard's own flow/views (only its CSS); did not restyle enquiries/SEO screens; the listings row action links stay text links (a future round could button-ize them).
- Mobile screenshots at 390px NOT RUN in pixels — headless window floors at 1280px; mobile safety verified via stylesheet rule inspection + the CSS-only mobile-first diff instead.
Next concrete step:
- Owner reviews the preview (same URL). If the empty-thumb placeholder reads odd, the fallback is hiding `.manage-row__thumb--empty` (one CSS line) — no template change.

### Handoff — 2026-11-13 · ZCode (r92 — dashboard visual polish)
What I did:
- Owner asked for better dashboard design. r92 = layout-only polish on the r91 zones: `manage-kpi--hero` (first KPI becomes the espresso hero tile and owns the 30-day sparkline — it moved from "Listing views" because `stats.per_day` counts enquiries, not views), `manage-check--dark` (setup checklist becomes the espresso anchor: cream text, ember pills, cream "Start here" box), manual-item undo buttons switched to `btn--light-outline` for contrast, quick-action cards compacted on desktop, welcome card flattened into the page at ≥64rem, KPI hover lift with `prefers-reduced-motion` off-switch. Tokens only, no JS, mobile stack untouched.
- NEW `apps/manage/tests/test_r92_dashboard_polish.py` (6 tests: hero+sparkline placement, dark anchor, compact tiles, CSS pins, token existence, no-JS/mobile guarantees). Updated r91's KPI count pin to a word-boundary regex (the hero's class list grew).
What I verified (command + output):
- `manage.py check` → `System check identified no issues (0 silenced).`
- `pytest -q` → `1118 passed, 620 warnings in 134.57s` · EXIT:0 (1112 baseline + 6 new)
- `bash scripts/gate.sh` → `GATE GREEN` · EXIT:0
- Live DOM via :81 + VLM full-page screenshots (desktop 1440 + mobile 390): hero/dark/compact all confirmed, sidebar + 2×2 mobile KPI grid intact, no overlap/clipping/unreadable text. First full-suite run caught the r91 pin break (see above) — fixed, rerun green.
What I did NOT do:
- Did not touch views/stats/checklist logic (`stats.py` shapes stay pinned); did not restyle other portal screens; mobile layout unchanged by design.
Next concrete step:
- Owner reviews the preview (same URL); if the espresso anchor reads too heavy, the fallback is a single CSS token swap (`.manage-check--dark` background → cream) — no template change needed.

### Handoff — 2026-11-13 · ZCode (r91 — desktop dashboard, design→plan→execute loops)
What I did:
- Ran the full loop protocol from `loops/plan-execute-verify.md`: DESIGN (audit + spec), PLANNING (ordered task list, pin review), EXECUTION, VERIFY.
- Root cause of "simplistic": `manage.css:79` capped every portal screen at `max-width: 44rem` and no sidebar existed, while DESIGN.md §9 mandated "espresso sidebar" — never built.
- r91 changes: NEW `templates/manage/_nav.html` (one partial renders both nav variants); `base.html` adds the espresso sidebar shell (brand, numbered 01–05 nav, account tools, sign-out) before the untouched mobile topbar/chip-nav; `home.html` restructured into a 12-column board (`manage-board` zones: welcome/KPI strip, chart 8 + pipe 4, top-viewed 8 + recent 4, checklist 7 + quick 5) with KPI hint lines and a CSS-only sparkline; `manage.css` +~250 lines (desktop shell at ≥64rem, board grid, KPI tiles — all tokens, mobile untouched); NEW `test_r91_desktop_dashboard.py` (10 tests).
- Spec landed → `specs/done/owner-portal-desktop-dashboard.md`; receipts → `.agents/reports/test-evidence.md`.
What I verified (command + output):
- `manage.py check` → `System check identified no issues (0 silenced).`
- `pytest -q` → `1112 passed, 617 warnings in 145.15s (0:02:25)` · EXIT:0 (1102 baseline + 10 new)
- Live DOM via gateway :81 — desktop 1440×900: sidebar `flex`, chip nav `none`, board 8 zones; mobile 390×844: sidebar `none`, topbar+chip nav `flex` (unchanged). VLM screenshot review: professional layout, no overlap/blank/broken zones.
What I did NOT do:
- Did not touch views/URLs/models/stats (layout-only round; `stats.py` shapes stay pinned by test_dashboard_graphs).
- Did not run `bash scripts/gate.sh` end-to-end (check + full pytest cover its core stages for a template/CSS-only round) — stated NOT RUN in test-evidence.md.
- Did not restyle other portal screens' internals (enquiries/listings/SEO keep the 44rem column on desktop; only the sidebar shell applies there — a future round can board them out).
Next concrete step:
- r92 candidate: extend the desktop treatment to the enquiries/listings screens (wider table rows, column view at ≥64rem) — same `body.page-manage` shell already applies; and/or run `bash scripts/gate.sh` once for a full-stage receipt.
- Also: rotate the GitHub PAT that was pasted in chat (see final reply).

### Handoff — 2026-11-13 · ZCode (retrofit session)
What I did:
- Created the coordination layer: AGENTS.md, AGENTS-COLLAB.md, .agents/memory/{traps,lessons,decisions}.md, .agents/handoffs/ (with .gitkeep), .agents/reports/test-evidence.md, specs/active/README.md, loops/plan-execute-verify.md.
- Wired the reading-order line into docs/AGENT-BRIEF.md (the repo's existing agent-instruction file; no AGENTS.md/CLAUDE.md/.cursorrules existed) and restated it at the top of AGENTS.md.
- No application source, migrations, settings values, or templates were modified.
What I verified (command + output):
- `.venv/bin/python manage.py check` → `System check identified no issues (0 silenced).`
- `.venv/bin/python -m pytest -q` → `1102 passed, 611 warnings in 138.96s (0:02:18)` · PYTEST_EXIT:0 (matches the r90 baseline exactly)
- Full paste incl. warnings context: `.agents/reports/test-evidence.md`
- `git status --short` before commit → only the new coordination files + the 2-line AGENT-BRIEF append (nothing under apps/, config/, templates/, migrations)
What I did NOT do:
- Did not run `bash scripts/gate.sh` end-to-end (its stages duplicate manage.py check + pytest + collectstatic checks; suite + check were run instead — gate NOT RUN, stated here per rules).
- Did not create any spec in specs/active/ (no non-trivial code change was made in this session; README explains the convention).
Next concrete step:
- Next dev round (r91) picks up from docs/STATUS.md / LOOP/ runbook; read AGENTS.md reading order first; consider a specs/active/ entry for any non-trivial r91 change.

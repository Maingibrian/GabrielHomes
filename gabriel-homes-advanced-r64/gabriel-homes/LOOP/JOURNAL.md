Run 70 | BUILDER (owner round, off-loop) | 2026-11-11 ~16:20-17:10 +03:00 | items:
(1) **OWNER ASK — "Asses the animations and resolve the glitches ...
when the listing animation occurs ..the parralax effect drops down and
up... ensure you take in to calculations everything."** MEASURED, not
guessed: a 12s per-frame recorder (rAF cadence, scrollY, six block
geometries above the band, band rect, computed --palms-y) installed
live on /properties/ and driven through eight stepped 500px scrolls
across the row animations. Trace scripts:
scripts/r70_analyze_trace.py (before) + r70_analyze_after.py (after).
(2) DIAGNOSIS — layout was INNOCENT: bandTop 966.7 / bandH 12349
constant across all 323 before-frames (map box clamp-reserved,
filters min-height-reserved, every row image carries width/height so
lazy loads never shift; the r69 "±35px lazy-load creep" note was a
measurement artifact of sampling a still-chasing lerp). The glitch
was TIME: frame cadence collapsed 59fps -> 10-12fps exactly while
the rows glided in and their images decoded (main-thread decode
bursts), and the r69 chase stepped a fixed fraction PER FRAME
(EASE 0.14/rAF tick) — frame-rate dependent, so the dip made it ~5x
slower in wall clock: every scroll stop left the field 180-230px
behind target and it kept sinking 600-800ms+ after the user stopped
("settled 95%: NEVER"). That post-stop drift around each row glide
IS the owner's "drops down and up".
(3) FIX (two files, pins in a third) — motion.js setupPalmParallax
rewritten: the chase is now a TIME-CONSTANT exponential
k = 1 - exp(-dt / TAU), TAU=70ms (felt weight kept, settle bounded
~200-300ms at ANY fps — 10fps low-end dip or 120hz flagship);
measure() runs INSIDE frame() (target = live geometry, never a
stale kick snapshot); dt clamped at MAXDT=400ms (background-tab
stall = one bounded step, no catch-up mega jump); SNAP=0.25px ends
the loop. DRIFT stays 0.5 (half speed — the owner's r69 middle),
anchor semantics, htmx:afterSwap re-resolve, fxNone fail-closed and
the 0px fallback all unchanged. _results_grid.html row images gain
decoding="async" (the cards already had it) — decode off the main
thread so the row glide stops starving rAF.
(4) GATES — check 0 · makemigrations 0 · **880 passed** (+2: NEW
test_parallax_chase_is_frame_rate_independent pins TAU 20-200 band,
the exp form, the MAXDT clamp, in-frame measure(), the SNAP
threshold, and BANS `var EASE =` outright so the frame-fraction
chase can't return; NEW test_results_grid_images_decode_async pins
decoding=async + the reserved 760x520 box. r68/r69 pins rewritten
in place only where they described the lerp).
(5) E3 (agent-browser, live /properties/, same 12s recorder, same
eight stepped scrolls): frame cadence 59fps FLAT (the dip is gone);
gap at stops 8-30px (was 180-230px); 95% settle at every stop
167/200/234/233/300/266/250/250ms (was NEVER); worst 300ms; overall
ratio palms/scroll = 0.501 over 3989px — half speed exact. No
console errors; VLM on the mid-band screenshot: palms even on both
edges, cards/images/actions intact, no glitches. Deliverable:
download/r70-listings-after-fix.png.
FOR THE NEXT RUN: preview bootstrap is scripts/start_preview.sh
(self-healing after sandbox recycles). Owner's cloud PAT still
"Later" — push when provided, delete after use.

Run 69 | BUILDER (owner round, off-loop) | 2026-11-11 ~14:00-15:10 +03:00 | items:
(1) **OWNER ASK — "the palms are stagnant they need to move ...but not
to slow they look stagnant and not to fast they move together with the
listings."** Diagnosis: the r68 pass pinned the field to the VIEWPORT
(background-attachment: fixed) — speed 0, "the deepest tier" on paper,
but on screen the field never moves: stagnant (and iOS/Android ignore
fixed attachment outright, so phones never saw even that). The owner's
words define a middle: palms must MOVE under scroll, slower than the
listings — not 0 (stagnant), not 1:1 (glued to the rows). HALF SPEED
is that middle.
(2) MECHANISM — motion.js setupPalmParallax() (NEW, called from init
after setupRowSlides): writes --palms-y on .listings-band; search.css
.listings-band::before now reads background-position:
0 var(--palms-y, 0px). DRIFT=0.5 (pattern px per scrolled px → field
speed exactly half), EASE=0.14 lerp — the chase carries weight: during
a fast fling the field hangs back a touch and eases in once the scroll
settles, never snaps. Anchored at the scroll where the band's top
enters the viewport (exactly static on arrival, drifts while any part
of the band is on screen, freezes after it passes — no wasted work in
the footer); scroll/resize kicks passive; htmx:afterSwap + isConnected
guard re-resolves a swapped band and restarts the chase from the
static pose. The tile repeats, so the drift never seams; the
box-relative 84% mask stays anchored (dissolve lands exactly at the
band's end); no stacking changes (r62 root-negative contract intact —
the drift moves paint inside the ::before, never the box).
background-attachment: fixed is BANNED from search.css by test pin so
the stagnant pin cannot return.
(3) GATING — D-FX-GATE as the row slides: rich + lite drift (a
position shift costs no data); fx=none (prefers-reduced-motion — the
WCAG 2.3.3 vestibular ask) and the attribute-less document (scripts
blocked, fails closed) never write the var: the 0px fallback scrolls
the exact static r65 tile. No media query re-checked (the gate owns
it). Band markup untouched (r65 markup pin stands).
GATES: check 0 · makemigrations 0 · **878 passed** (2 obsolete r68
parallax pins rewritten in place — fixed-gated-rich+lite +
scroll-default-fails-closed → half-speed-drift-not-viewport-pinned +
js-half-speed-gated-fail-closed; test docstring updated; r65
scroll-attachment pin, r65-contract and home-keeps-r46 pins untouched
and green).
E3 (agent-browser, live /properties/): data-fx=rich confirmed; the
drift var settles at EXACTLY 0.5× in-band travel at four readings
(1040.19 / 1595.80 / 2063.87 / 2546.29 — computed ::before
backgroundPosition reads the var live); back-to-back 1000px scroll →
var delta 482 (0.48 with ±35px lazy-load layout creep above the band);
PIXEL PROOF at 1600×1000 (sentinels off <1620px → clean gutters):
both gutters cross-correlate the PAINTED field 450px UP against the
cards' full 1000px — half speed, nowhere near stagnant (0) or 1:1
(1000); VLM A/B read: "pattern shifted… much less than cards…
parallax confirmed". Fail-closed live: var removed → computed
background-position 0px 0px, attachment scroll (the exact static
pose); the fxNone early-return is the same gate mechanism live-verified
four-tier in r68 (route-abort of fx-gate.js not matchable via the
agent-browser CLI — noted). Desktop VLM: palms visible, even, cards
readable, nothing broken; mobile 390px: "coherent repeating botanical
texture, no areas too heavy" (one earlier "clumped" read at a single
phase disproved by a second neutral read — a 390px window shows less
than half the tile, so one phase can look sparse; the structural
one-centroid-per-cell pin governs).
Deliverables in download/: r69-parallax-proof.png (A|B with the
measurements), r69-listings-drift-desktop.png,
r69-listings-drift-mobile.png; E3 script scripts/r69_parallax_proof.py.
FOR THE NEXT RUN: preview bootstrap is scripts/start_preview.sh
(self-healing after sandbox recycles). Owner's cloud PAT still
"Later" — push when provided, delete after use.

Run 68 | BUILDER (owner round, off-loop) | 2026-11-11 ~11:40-12:40 +03:00 | items:
(1) **OWNER ASK — "the listings page palms need to be spread out
evenly to look less bushy in some areas than others and maximise the
parallax effect they give out."** Diagnosis first, measured: the r46
hand-tuned tile (12 fronds, seed 46) clumps — sand-composited per-cell
wash coverage ran 1.2%–9.9% across a 4×4 grid, an 8.06× spread (top
band arches into a heavy clump, mid-right nearly bare). EVEN TILE:
static/img/palm-field-even.svg (NEW asset, scripts/
r68_palm_field_even.py, deterministic seed 868 — best of a 12-seed
sweep measured on the shipped pipeline): one frond per cell of a
jittered 5×5 grid (±0.16 cell), ink CENTROID anchored on each cell
centre (base offset opposite the aim — without this the arch bleeds
all its ink into the aimed neighbour and the grid comes back as
stripes), golden-angle aim (i×137.508° ± 12° — consecutive fronds
never push ink the same way), checkerboard layers (13 back 14% /
12 front 26% — the strong wash never shares an edge), scales back
0.66–0.82 / front 0.60–0.76. Measured result: 4.6%–6.6% per cell,
1.43× spread, 16/16 cells within ±30% of the mean; mean coverage
4.5%→5.6% (same total ink now reaching everywhere instead of stacking
in clumps; busiest even cell 6.6% still under the old clump peak
9.9%). Frond art, washes, tile size, wrap pass: r46 lineage verbatim.
VLM tile bake-off (old vs 2 candidates): old = "heavy dark clumps
with large bare gaps"; winner = "uniformly distributed… subtlest,
most professional backdrop". Home keeps palm-field.svg untouched (the
ask was listings; test_r46/r66 pins green).
(2) **PARALLAX — background-attachment: fixed** on .listings-band::
before, gated html[data-fx="rich"] + [data-fx="lite"]: the field
anchors to the VIEWPORT, rows/chips/pagination slide over a still
palm field — the deepest tier a background layer can give (sentinels
already hold the stagnant tier r62, content 1:1, field now at
infinity). A compositing mode, not a keyframed effect: no JS, no
data cost. Scroll stays the default (fails closed): scripts blocked
(no attribute), fx=none (prefers-reduced-motion — scroll-linked
parallax is what WCAG 2.3.3 asks sites to spare vestibular-sensitive
visitors), and every engine that ignores fixed (iOS Safari, most
Android Chrome) all keep the exact r65 look. Box-relative mask
unaffected — the 84% dissolve still lands at the band's end. No
stacking changes (r62 root-negative-layer contract intact).
(3) Measurement lesson for future vision passes: cairosvg renders
SVG backgrounds TRANSPARENT; PIL convert('L') maps alpha-transparent
pixels to BLACK — an un-composited "ink" heat-map silently inverts
(watermark reads as bare, bare reads as ink). Always pass
background_color=<sand> (or composite) before measuring tone-on-tone
tiles. First heatmap also mis-read the old clump's LOCATION (inverted)
— the evenness conclusion held, the map did not.
GATES: check 0 · makemigrations 0 · **878 passed** (r67 baseline
868; +10 — NEW test_r68_even_palm_field.py: dimensions/washes, one-
centroid-per-cell (reconstructed from the SVG by inverting the
centroid anchor — bases wander cells by design), checkerboard-front-
never-adjacent, scale band, wrapped-copies-exist, generator==
asset byte-pin, fixed-gated-rich+lite, scroll-default-fails-closed,
r65-contract-carried, home-keeps-r46; 1 obsolete r65 pin rewritten in
place: "same asset as home" → the even tile + scroll default; comment
prose gotcha — the word "animation:" inside a CSS comment tripped
test_c1's ungated-animation regex, reworded to "keyframed effect").
test_r46/r66/c1 green untouched. E3 (agent-browser 1920x1080,
data-fx=rich verified live): computed backgroundAttachment = fixed
under rich AND lite, scroll under fx=none AND attribute-removed
(fails closed) — all four tiers exercised browser-side. PARALLAX
PIXEL PROOF: screenshots 1300px apart in the band — field regions
(both gutters) mean|diff| = 0.00/max 0 (pixel-identical, the deepest
parallax a background can show) while the card grid moved
(mean|diff| 82). Evenness on-page: gutter wash coverage by vertical
third 56.7/53.8/47.8 (left) and 58.3/42.7/47.1 (right) — 1.2-1.4x
swing, matching the tile's intrinsic spread; a leading-question VLM
read ("mid gutters bare") was disproved by measurement (42-54% wash
coverage there) — neutral re-asks + crop reads came back "denser
toward the middle and lower half… purely decorative tropical
background" and mobile 390px "subtle, evenly distributed without
striping, cards readable". Footer dissolve measured in 120px slices:
22.5% -> 2.1% -> 0.1% at the footer line (84% mask lands exactly);
sentinel handoff at the footer is the known r62 design (footer
scrolls up over the still trees), sentinel CSS untouched. Home
market re-shot: "tone-on-tone… subtle and unaltered", r46 tile kept.
Deliverables in download/: r68-tile-before-after.png,
r68-parallax-proof.png, r68-listings-even-field.png,
r68-listings-mobile.png, r68-home-market-unchanged.png.
FOR THE NEXT RUN: preview bootstrap is scripts/start_preview.sh
(self-healing after sandbox recycles). Owner's cloud PAT still
"Later" — push when provided, delete after use.

Run 67 | BUILDER (owner round, off-loop) | 2026-11-10 ~21:00-22:30 +03:00 | items:
(1) **OWNER ASK — "looks bad"** (on the delivered r66 values redesign,
both the white-panel accordion and its stripped collapsed pose).
The 001/002/003 principles are now PHOTO EXPANDER COLUMNS: each card
a tall coast photograph, object-fit cover, deliberately UNSHADED (the
carousel complaint was the scrim crushing pictures — the only veil is
the bottom gradient the copy sits on), with numeral (ember Fraunces)
+ bracket tag + title (white Fraunces) + body (cream, text-base)
riding a bottom-anchored panel over an espresso gradient. Markup:
photos with honest alt text + intrinsic sizes, aria-hidden scrim
span, icons + spine GONE, tabindex=0 kept (keyboard parity via
:focus-within). CSS: base = equal grid of 30rem-tall panels (26rem
under 810px), all copy visible — phones/touch/no-JS/print render
exactly this; gate @media (hover:hover) and (pointer:fine) and
(min-width:811px) = flex row 32rem, hovered/focused card flex-grow
1→2.8 (0.55s ease-out), detail (fixed 24rem, no reflow) fading in at
0.16s behind the panel; reduced-motion kills all transitions, keeps
states; reveal-stagger delays unchanged (5-value list, transition
list specificity (0,3,0) still outranks html.motion-ready
[data-reveal] (0,2,1)). Shared components.css card frame killed in
scope (padding:0 — the panel owns the inset; transform:none — a
photo column must not bounce on hover).
(2) **E3 drove five visual passes.** pass-1 VLM on the r66 state:
white boxes "floating on a textureless void, no real-estate warmth"
→ photo columns. pass-2: scrim too weak (numerals fighting pool
water), kitchen photo MLS-grade → gradient deepened, 003→dining,
002 crop weighted down. pass-3: baselines ragged + 002 still thin →
detail block became a bottom-anchored flex column with min-height
11rem (measured result: all three stacks identical — num top 180px,
body bottom 29px), mid-scrim to 55%. pass-4: contact sheet of 8
candidate photos graded A/B/C by VLM → 002 real-09-golden-hour
(A-tier, "the only frame that feels like coastal Kenya", back with
the stronger scrim + object-position center 62%), 003
real-10-sea-light (A-tier, "your first morning here"); rejected
real-02-living (AC unit hero, blown-out walls) and real-05-dining
(range hood behind text). pass-5: text zone (bottom 6-62% of card)
deepened to 84-62% espresso, top fifth stays clean — final VLM:
"all text comfortably readable", "one coherent warm editorial set",
expanded state "intentional… no bugs", mobile 390px "strong
contrast… no bugs", full page "polished, cohesive component",
card→founder spacing "reasonable" (bottom padding halved).
Section bottom padding halved (dead zone), intro text-wrap:balance
(orphan rag), num margin 0.7→0.95rem.
GATES: check 0 · makemigrations 0 · **868 passed** (r66 baseline
865; +3 net — test_r66_about_focus.py rewritten to pin the photo
expander (13→16 tests: unshaded-photo pin, cream-on-photo pin,
base-panels pin; spine pins retired with the spine); r52 icon pin →
photo pin, r53 white-panel pin → espresso-frame pin, both rewritten
in place per the r64 precedent). Wave field + closing-CTA pins
carried over untouched; listings palm untouched (r65 contract).
E3: base/expanded/mobile/full-page verdicts above; geometry
measured browser-side; headless gotcha — Chromium reports
(hover:none)(pointer:none) so the gate was verified by injecting the
gate's cssRules unconditionally + .focus() (678px vs 243px
siblings); mobile scrollWidth>clientWidth is the known marquee
phantom (scrollX 0). Deliverables in download/:
r67-values-final.jpg, r67-values-expanded.jpg,
r67-values-mobile.jpg.
FOR THE NEXT RUN: preview bootstrap is scripts/start_preview.sh
(self-healing after sandbox recycles). Owner's cloud PAT still
"Later" — push when provided, delete after use.

Run 66 | BUILDER (owner round, off-loop) | 2026-11-10 11:35-11:55 +03:00 | items:
(1) **OWNER ASK — "remove the carousel — Homes worth crossing town
for — it doesn't look good, the background and images are shaded."**
The closing band's shaded bento photo strip (three scrimmed real-* photos,
captions, proof note) left the page ENTIRELY — markup and every
.cta__proof/.about-tile rule in pages.css. The shared .cta band
(components.css §15, untouched) now carries the close alone: [ THE
COLLECTION ] tag, the taste-led headline, one Explore button. Quiet
espresso close after a textured page.
(2) **OWNER ASK — "the cards above should get better styling... cards
stacked in columns that you hover and they expand and reveal more
info."** The 001/002/003 principles are now tall WHITE PANELS in an
accordion row over the new wave field: base state = equal grid, every
card fully readable (phones/touch/no-JS/print render exactly this);
inside @media (hover:hover) and (pointer:fine) and (min-width:811px)
the row becomes flex, panels collapse to numeral+tag strips, and
:hover/:focus-within blooms the panel (flex-grow 1→4.2, 0.55s
ease-out) with the .value-card__detail (title+body, fixed 26rem — no
mid-expand reflow) fading in at 0.16s behind the panel. Pass-2 (VLM):
collapsed strips first read as "loading content" → added
.value-card__spine: an aria-hidden vertical-rl mono book-spine label
per card (its title), top-aligned at 13.5rem, crossfading out on
expand; base display:none keeps it out of every non-gate context.
Keyboard parity via tabindex=0 + :focus-within (verified browser-side:
hover 736px / siblings 219px, detail opacity 1). D-MOTION-SAFE:
prefers-reduced-motion kills all three transitions, keeps the states;
the reveal-stagger delays grew to five values so hover never lags.
Transition list specificity (0,3,0) documented to outrank the
html.motion-ready [data-reveal] rule (0,2,1).
(3) **OWNER ASK — "remove the palm tree background in the about us
page... maybe some waves patterns."** .about-values::before now tiles
wave-field.svg (NEW asset, scripts/r66_wave_field.py): nine sine rows
x bright+dim tone pair (the palm's #e7d9cd/#dcc6b8), wavelength 250
(4 cycles/1000px — horizontal seam-exact), row step 700/9 (multiple of
3 — phase rotation tiles cleanly), 1000x700 native grain, same
z-index:-1 / pointer-events:none / 78% bottom-fade contract as the r65
palm before it. The palm itself is untouched on home + listings.
GATES: check 0 · makemigrations 0 · **865 passed** (r65 baseline 852;
+13 new test_r66_about_focus.py pins; 9 obsolete pins rewritten in
r53/r55/r63/r64/r65 to pin the NEW contract — r64 precedent).
E3: VLM pass-3 verdicts — collapsed "consistent and deliberately
designed, cohesive system"; expanded "balanced and readable, no
clipping"; waves "genuinely subtle and attractive"; mobile 390px cards
fully readable, spine correctly display:none, zero actual horizontal
scroll (scrollWidth phantom = marquee track, clipped, scrollX 0);
0 console errors, 0 broken images. Spine alignment verified
pixel-exact (all three top:495px) after a VLM false-positive.
Deliverables in download/: r66-values-accordion.jpg (collapsed+hover),
r66-cta-band-after.jpg, about-page-r66-{desktop,mobile}.png.
FOR THE NEXT RUN: preview server bootstrap is scripts/start_preview.sh
(self-healing: reinstall deps, recreate .env, reseed, setsid runserver
+ bridge :3000 — the sandbox recycle wipes gitignored state).
# JOURNAL.md — append-only, newest first

Run 65 | BUILDER (owner round, off-loop) | 2026-11-10 12:10-13:05 +03:00 | items:
(1) **OWNER ASK — "add the pine background image seen in the home page
to the listings page to add some depth; don't remove any other thing."**
`.listings-band::before` in search.css: the r46 palm-field tile
(palm-field.svg, generator seed 46, unchanged asset) repeating across the
results band with the home bottom-fade mask (84%→100%), 1400px 1600px
desktop grain / 860px 985px under 1020px — the exact home treatment.
ONE deliberate difference, documented in-file: NO isolation:isolate on the
band (home's .home-market isolates) — the palm sentinels must keep painting
in the ROOT negative layer so the footer scrolls up over them (r62);
the ::before simply joins them at z-index:-1 (tree order: field, then
trees). CSS-only, zero markup touched on the page, token-only (D-LOOP-38a
zero-hex holds), no motion (D-MOTION-SAFE trivially satisfied). VLM
verified at 1920px (field visible in gutters/gaps, cards fully readable,
sentinels intact, no seams) + 390px (finer grain clean); fade verified
pixel-wise — gutter variance 12.0 mid-band → 3.4-6.0 near the bottom →
0 at the footer seam.
(2) **OWNER ASK — the About remodel ("study why it's boring, remodel it,
Editorial+").** Diagnosis (VLM, images loaded): cream/beige stripe rhythm
with no colour break after the hero, interchangeable 001-003 grid on flat
cream, empty espresso quote band, no location storytelling ("Nyali to
Shanzu is just a text chip"), no motion beyond data-reveal. Four additive
fixes, zero pinned copy/components touched: (a) the coast ticker after the
hero — home's .hv2-marquee component reused with about-specific mood
phrases; pass-2 gave it its own voice (Fraunces-italic mood spans via
.hv2-marquee__mood in pages.css, towns stay mono caps; home ribbon
untouched); (b) ghost "10" in the quote band (aria-hidden span +
.about-quote__ghost; pass-2 raised 8%→13% cream and enlarged after the
VLM read pass-1 as "a smudge"); (c) the coast strip — full-bleed dhow
(coast-dhow.jpg) under espresso color-mix scrims, "From Nyali to
Shanzu." + six neighbourhood chips into REAL location pages (each
verified 200 with live listings at seed: Nyali 10, Bamburi 9, Mtwapa 6,
Tudor 7, Shanzu 5, Mkomani 4); (d) the palm field behind the principles
row (860px grain, 78% bottom fade) + the home head-veil geometry behind
values-head (pass-2 widened to -4rem -8rem). VLM final: 8.5/10 "real
editorial rhythm", mobile 390px clean (no overflow/clipping).
NEW test file apps/core/tests/test_r65_owner_remodel.py — 19 pins
(field contract incl. the no-isolation stacking guard, additive-only
markup check, ticker placement/voice, ghost numeral, coast strip order
+ parametrized live-chip resolution, values field + veil, asset
identity). Suite 833 → **852 passed** (drivers psycopg/gunicorn/mysqlclient
installed to green the 4 pre-existing prod-config skips-fails; those were
environment, not code).
| score: n/a (owner round, off-SCORECARD) | evidence: E2+E3 (VLM passes
x4 + pixel variance + computed-style probes) | gates: start — check 0,
makemigrations 0, 833 passed (after env fix); end — check 0,
makemigrations 0, **852 passed** | ratchets: search.css hex **0** (held);
no new tokens/colours (color-mix of existing espresso/cream only, no
DECISIONS entry needed) | decisions: none | FOR THE NEXT RUN: owner
review of the about remodel + listings field; optional VLM follow-ups
queued — ghost numeral at 15-16% on dim screens, marquee left-edge
dissolve is the shared r55 cap behaviour (left as-is) | blockers: none |

Run 38 | AUDITOR→BUILDER | 2026-11-06 07:15-08:05 +03:00 | items:
(1) **AUDIT H2 T2 claim from scratch — verdict MET-T2 (the project's second
Tier-2 item).** Baseline gates green (check 0, makemigrations 0, 655);
fresh server (pkill-first); 10/10 test_h2_hero.py; scripts/r37_e3_h2_t2.py
re-run **24/24 ALL PASS** (R7+L8+M5+MR2+RM2; lite-leg wire accounting
reproduced byte-for-byte: css 173,559 + js 52,033 + fonts 290,180 + LCP
119,000; video 0 B on every off-rich leg); D-LOOP-37a verified against
code (preload fetchpriority=high in home.html head, video hidden-by-default
with the rich && !Save-Data contract at the reference site, zero
[data-count] in hero) + git tree proves r37 evidence-only (LOCKS + 2
regenerated screenshots only); 3 screenshots eyeballed (rich-1280 settled
mask headline + ONE gesture; mobile-390 stacked pill; mobile-rich-390
shows a DIFFERENT video frame = touch handover fired). aud=self all-4s,
lower wins → H2 MET-T2. (2) **BUILDER F1 T2 lift** — the tokenisation pass:
search.css carried exactly 10 hex (`#fff` ×8 + `#e7e4df` ×2, test regex);
8× #fff → var(--white) (pre-existing token, identical value) + 2× #e7e4df
→ NEW token **--map-stage** (tokens.css, D-LOOP-38a sanction, used nowhere
else); hex ratchet **211 → 201** re-pinned; NEW test
test_search_css_is_fully_tokenised (suite 655 → **656**); **computed-style
A/B proof** scripts/r38_e3_f1_ab.py: 13 probes on /properties/ captured
BEFORE and AFTER the edit → **13/13 identical** (render-invisible by
construction); WCAG D5: all five text pairs ≥ 4.5:1 (16.59 / 5.62 / 16.59
/ 16.59 / 13.48); search-page screenshot eyeballed clean. F3's WATCH
needle updated 211 → 201.
| score: H2 READY-FOR-AUDIT → **MET-T2** (aud=self 4s) · F1 MET-T1 →
**READY-FOR-AUDIT (T2 claim; T1 intact)** self 4,n/a,n/a,n/a,4,n/a,4,4
(was 3,n/a,n/a,n/a,3,n/a,3,4) | evidence: E2+E3 | gates: start — check 0
issues, makemigrations no changes, **655 passed**; end — check 0,
makemigrations 0, **656 passed** | ratchets: sub-13px **43**, hex **211 →
201** (legitimate drop: 10 search.css hex tokenised), image bytes
4,191,687 — untouched | decisions: **D-LOOP-38a** | FOR THE NEXT RUN:
r39 = AUDITOR — audit the F1 T2 claim (9/9 test_f1_token_integrity.py
incl. the new search-css pin, re-run scripts/r38_e3_f1_ab.py before/after
on a FRESH server expect 13/13 identical, verify --map-stage in
tokens.css, re-read D-LOOP-38a, eyeball r38-f1-search-after.png; verdict
MET-T2 or demote naming the checks); then BUILDER the next T2 lift deeply
(G2 real-browser transition capture, or L1/H1 evidence pack); suite ≥ 656
| blockers: none |


Run 37 | AUDITOR→BUILDER | 2026-11-06 05:45-06:35 +03:00 | items:
(1) **AUDIT F2 T2 claim from scratch — verdict MET-T2 (the project's first
Tier-2 item).** Baseline gates green (check 0, makemigrations 0, 655);
fresh server (pkill-first); 14/14 test_f2_capability_gate.py; scripts/
r36_e3_f2_matrix.py re-run **ALL PASS** (three times total this run, once
for the count audit); D-LOOP-36a verified against code (five legs, byte
fact 1,507,333 B, M-table aligned row-for-row, screenshots hash-verified
+ eyeballed). **Bookkeeping correction: the matrix is 53/53, not 52/52**
(NOJS 8 + NONE 10 + LITE 13 + RICH 15 + TOUCH 7, counted via rg -c;
r36's prose undercounted by one; all green either way; D-LOOP-22a
precedent). From-scratch grading: D1/D4/D5/D6/D7/D8 all 4 with E2+E3 →
aud=self all-4s, lower wins → **F2 MET-T2**. (2) **BUILDER H2 T2 lift**
(evidence-only, zero shipped-code changes): scripts/r37_e3_h2_t2.py —
**24/24 ALL PASS** across 5 legs. D1: ONE gesture live (1 submit CTA,
0 competing anchors, stats gone) + LCP preload fetchpriority=high
honoured (119,000 B); D2: settled screenshots eyeballed (rich-1280,
mobile-390, mobile-rich-390); D4: video 0 B lite/none/no-JS + LCP
119 KB; D5: keyboard walk — skip link first, Enter flips Rent + hidden
input + action URL → /property-for-rent/; D6: zero horizontal overflow
at 390px, hamburger + stacked pill, video handover pointer-independent
on touch. Script fixes en route: ?v= query on the preload href (assert
the path), keyboard walk lands on Buy first (Rent = one more Tab),
1.2s settle before mobile screenshots (r34 lesson). **Q1 datapoint**
(first real wire accounting, recorded on the Q1 WATCH row): css
173,559 + js 52,033 + fonts 290,180 + LCP 119,000 = **634,772 B** >
400KB aspiration — fonts are the lever; NOT an H2 defect (site-wide).
| score: F2 READY-FOR-AUDIT → **MET-T2** (aud=self 4s) · H2 MET-T1 →
**READY-FOR-AUDIT (T2 claim; T1 intact)** self 4,4,n/a,4,4,4,4,4 (was
3,3,n/a,3,3,3,4,4) | evidence: E2+E3 | gates: start — check 0 issues,
makemigrations no changes, **655 passed**; end — re-run below (docs +
E3 scripts only) | ratchets: sub-13px 43, hex 211, image bytes
4,191,687 — untouched (no CSS/static changes) | decisions:
**D-LOOP-37a** | FOR THE NEXT RUN: r38 = AUDITOR — audit the H2 T2
claim (10/10 test_h2_hero.py, re-run scripts/r37_e3_h2_t2.py expect
ALL PASS on a FRESH server, re-read D-LOOP-37a, eyeball r37-h2-*.png;
verdict MET-T2 or demote naming the checks); then BUILDER the next T2
lift deeply (G2 real-browser transition capture, or F1 tokenisation
pass over the 10 search.css hexes); suite ≥ 655 | blockers: none |


Run 36 | BUILDER (T2 lift) | 2026-11-06 05:15-06:05 +03:00 | items:
**F2 capability gate — the keystone T2 lift (evidence-only; no shipped code
touched)**. Chose F2 over H2 per r35's fork: a gate lift is read-only on the
17 frozen MET items, so zero regression risk. Read PROTOCOL/STATE/SCORECARD/
LOCKS/last-5-journal first; baseline gates green (check 0, makemigrations 0,
655); claimed F2 T2 lift in LOCKS; read test_f2_capability_gate.py (14 tests),
fx-gate.js, motion.js, smooth-scroll.js, bento-shift.js, the G3 @supports
block and the addendum M-table, then built scripts/r36_e3_f2_matrix.py — the
five-leg live decision-table matrix on home: RICH (spoofed hc=8/dm=8) · LITE
(hc=2) · NONE (reduced-motion) · TOUCH (390×844, is_mobile+has_touch, spoofed
rich, coarse pointer) · NOJS (java_script_enabled=False). **52/52 ALL PASS,
zero console/page errors**: tier half (split lite+rich never none/no-JS; video
rich && !Save-Data; Lenis rich+fine; nav auto-hide lite+rich; g3 scroll-linked
lite+rich and animation:none under none/no-JS; reveals instant under none,
visible no-JS) AND pointer half (TOUCH: data-fx=rich but no data-fine → no
bubble, bento never is-live, native scroll). Byte fact (D4): hero loop =
1,507,333 B under rich/touch, exactly **0 B** under lite/none/no-JS.
Reduced-motion parity (D5) + D-MOTION-SAFE (D7) proven live. Addendum M-table
matches the observed table row-for-row — no doc drift, F4 freeze untouched.
Screenshots r36-f2-{rich,nojs,none,lite,touch}-*.png eyeballed (video frame +
settled mask headline; static marquee with header never hidden; mobile stacked
pill, no pointer decorations). E3 lesson: under Lenis autoRaf, native
window.scrollTo(0,0) is overridden next frame — use window.__lenis.scrollTo(0).
| score: F2 MET-T1 → **READY-FOR-AUDIT (T2 claim; T1 baseline intact)**, self
4,n/a,n/a,4,4,4,4,4 (was 3,n/a,n/a,3,3,3,4,4) | evidence: E2+E3 (52/52 matrix
+ 14 F2 tests within the 655 + 5 screenshots + printed decision table) |
gates: start — check 0 issues, makemigrations no changes, **655 passed**; end —
re-run below (docs+script only after the matrix) | ratchets: sub-13px 43, hex
211, image bytes 4,191,687 — untouched (no CSS/static changes this run) |
decisions: **D-LOOP-36a** | FOR THE NEXT RUN: r37 = AUDITOR — audit the F2 T2
claim from scratch (14/14 test_f2_capability_gate.py, re-run
scripts/r36_e3_f2_matrix.py expect ALL PASS on a fresh server (pkill-first),
re-read D-LOOP-36a, eyeball r36-f2-rich/none/touch pngs; verdict MET-T2 or
demote naming the checks); then BUILDER the next T2 lift deeply (H2 five
3s→4s with the r33/r24 harness, or G2 real-browser transition capture); suite
≥ 655 | blockers: none |


Run 35 | AUDITOR→PLANNER (+WATCH overlay) | 2026-11-06 04:19-05:05 +03:00 | items:
(1) AUDIT G4 from scratch — gates 655, 7/7 test_g4_pointer_polish.py; E3
scripts/r34_e3_g4.py re-run **18/18 ALL PASS** on a FRESH server (pkill-first);
D-LOOP-34a verified against the code (brace balance 279/279 + dead fragment
gone, 7/7 gate needles in setupPointerPolish, M5 data-cursor-view / M6
data-magnetic rows correct, cap 6 intact, bento exclusion documented); both
fresh screenshots eyeballed → **G4 MET-T1**, aud=self 3,3,4,3,3,3,4,4, zero
gaps — **all 17 work items now MET-T1**. (2) WATCH overlay (r20 precedent):
35 mod 16 = 3 → **F5 spot-check** 6/6 test_f5_smooth_scroll.py + r29_e3_f5.py
ALL PASS; F1 drift re-surveyed **211/43 held**; nothing REGRESSED.
(3) RETRO (r35 = multiple of 5, docs-only): read r30-r34 — five builders, five
first-attempt audit passes, 0 failed attempts, no stuck items to split, no
duplicates, no new item earned its keep (F4 rule); per §5 raised the six
weight-5 items (F1, F2, H1, H2, G2, L1) to **Tier 2**; fixed the ledger's
off-by-one denominator — canonical count is **17** (SCORECARD work rows), so
MET share is **17/17 (100%) at T1**; bookkeeping rationale + T2 plan logged as
D-LOOP-35a. | score: G4 READY-FOR-AUDIT→MET-T1 (aud=self); targets raised for
F1/F2/H1/H2/G2/L1 | evidence: E2+E3 (G4 7/7 + 18/18; F5 6/6 + ALL PASS; survey
211/43) | gates: start — check 0 issues, makemigrations no changes, **655
passed**; end — unchanged, docs-only after the audits (no code touched this
run) | ratchets: sub-13px 43, hex 211, image bytes 4,191,687 — all held |
decisions: **D-LOOP-35a** | FOR THE NEXT RUN: r36 = BUILDER — take ONE T2 lift
deeply (suggested H2: five 3s → 4s with evidence, richest existing E3 harness
r33_e3_h2b.py + r24_e3_h2a_audit.py; or F2 the keystone gate); every T2 claim
then needs a different-run audit to become MET-T2; suite must stay ≥ 655 |
blockers: none |


Run 34 | AUDITOR→BUILDER | 2026-11-06 03:46-04:55 +03:00 | items: (1) AUDIT H2.b
from scratch — gates 648, 10/10 test_h2_hero.py; E3 scripts/r33_e3_h2b.py re-run
**18/18 ALL PASS** on a FRESH server (pkill-first); D-LOOP-33a verified
line-by-line against motion.js/home.css/home.html (fxNone skips the split,
splitText(parent, textNode) keeps whitespace verbatim, em accent survives,
sole-owner hv2-rise removal, rich && !Save-Data video gate with
hidden+preload=none+poster, .is-video crossfade); r33-h2b-hero-rich-1280.png
eyeballed (loop playing, headline settled, descenders intact) → **H2 full
MET-T1** (a r25 + b r34), aud 3,3,4,3,3,3,4,4, zero gaps. (2) BUILDER G4
(pointer polish — the last remaining item) — test_g4_pointer_polish.py FIRST
(7 tests, red 7), then motion.js setupPointerPolish: cursor "View" bubble
JS-built (aria-hidden, textContent, pointer-events none, fixed +
transform-positioned) following the pointer over .listing-row +
.nearby-card via --cx/--cy; magnetic primary CTAs (hero search submit,
header Enquire, detail WhatsApp primary) via clamped ±8px --mx/--my;
gate = data-fx=rich AND (pointer: fine) AND (hover: hover); keyboard users
never trigger it (pointer events only); bento cards deliberately excluded
(M4 bento-shift owns the pointer there — test-pinned); cursor-view → M5
confirm, magnetic → M6 invite (variant mapping, cap stays 6),
SHIPPED_TOKENS extended. E3 scripts/r34_e3_g4.py **18/18 ALL PASS**;
screenshots r34-g4-row-cursor.png + r34-g4-magnet.png eyeballed.
**Defect found + repaired (D-LOOP-34a)**: components.css ended (pre-existing,
in HEAD) in a dead rule fragment (orphan declarations + stray `}`) — after
the G4 append the browser's error recovery dropped the FOLLOWING rule
(.cursor-view never applied: computed opacity 1, position static);
diagnosed by brace-balancing the served CSS in-browser (276 opens / 277
closes); dead text removed — it carried 3 hex literals, so hex ratchet
legitimately fell **214→211** (HEX_BASELINE re-pinned; SUB13 44→43 aligned
with the r22-recorded count). E3 lessons: scroll_into_view before hovering
below-fold rows (map pushes rows under the fold); text-transform uppercase
→ assert inner_text .lower(); adjacent rows re-trigger pointerenter — leave
to a no-target area; 1.2s settle before evidence screenshots.
| score: H2.b audit (no move — MET-T1 confirmed, H2 full) · G4 n/a→READY-FOR-AUDIT
self 3,3,3,3,3,3,4,4 | evidence: E2+E3 | gates: start — check 0 issues,
makemigrations no changes, **648 passed**; end — check 0 issues, makemigrations
no changes, **655 passed** (+7 G4) | ratchets: sub-13px **43** (constant
re-pinned), hex **211** (re-pinned, legitimate drop), image bytes
**4,191,687** — held | decisions: **D-LOOP-34a** | FOR THE NEXT RUN: AUDITOR —
audit G4 (mechanical: 7/7 test_g4_pointer_polish.py, re-run
scripts/r34_e3_g4.py expect ALL PASS, re-read D-LOOP-34a, eyeball
r34-g4-row-cursor.png + r34-g4-magnet.png); then PLANNER retrospective (r35
is a multiple of 5 — re-weight/split/add/prune; if G4 passes, every work
item is MET-T1 → raise targets per §5); suite must stay ≥ 655 | blockers:
none |


Run 33 | AUDITOR→BUILDER | 2026-11-06 05:15-06:05 +03:00 | items: (1) AUDIT L4
from scratch — gates 645, 9/9 test_l4_gallery.py; E3 scripts/r32_e3_l4.py
re-run **ALL PASS** on a FRESH server (pkill-first); D-LOOP-32a verified
against code (JS-built overlay, G2 name unique on the gallery main,
.lightbox__main view-transition-name:none, Lenis stop/start via the F5
public API, M2 extension with no new family); both screenshots re-verified
→ **L4 MET-T1**, aud=self 3,3,3,3,4,3,4,4, zero gaps. (2) BUILDER H2.b
(hero motion slice, weight-5 item) — split-text mask headline: motion.js
word-splits the h1 client-side (DOM APIs only, whitespace runs preserved
verbatim, em accent kept, h1's own hv2-rise handed over — sole-owner rule
per D-LOOP-31a; fxNone skips the split entirely = plain visible h1),
CSS mask rise transform-only with 45ms stagger + descender allowance,
reduced-motion kill; hero-loop.mp4 now referenced: hidden + preload="none"
+ poster, motion.js flips it live ONLY under html[data-fx=rich] &&
!Save-Data (D-LOOP-21a), crossfades over the slides via .hero__bg.is-video
— lite/none/SaveData/JS-blocked never load a byte; gate contract documented
at the reference site (multiline {% comment %}) and pinned by tests;
addendum M1 (mask headline) + M2 (video handover) extended, cap stays 6.
test_h2_hero.py 7→**10/10**; E3 scripts/r33_e3_h2b.py **18/18 ALL PASS**
(mask split/stagger/text-intact-vs-JS-blocked-baseline, rich hand-over
playing t>0.9s, lite/none/JS-blocked h1 plain + video hidden, zero errors);
r33-h2b-hero-rich-1280.png eyeballed (loop playing, headline settled).
Failures fixed en route: splitText appendChild on a text node (take
parent+textNode), whitespace verbatim preservation, headless-fx spoof via
add_init_script, and the **multiline {# #} Django comment leak** (r24
D-LOOP-24c lesson hit again — 4 test_p0/phase2 failures → {% comment %}
block, suite re-run green). | score: L4 audit (no move, MET-T1 confirmed)
· H2.b n/a→READY-FOR-AUDIT self 3,3,n/a,3,3,3,4,4 (+D3 4 with E3) |
evidence: E2+E3 | gates: check OK · makemigrations OK · **645 → 648
passed** (+3 H2.b) · hex **214** held | decisions: D-LOOP-33a | FOR THE
NEXT RUN: audit H2.b (10/10 + r33_e3_h2b.py ALL PASS + D-LOOP-33a re-read
+ rich-hero screenshot), then BUILDER G4 (pointer polish — the last
remaining item) | blockers: none

Run 32 | AUDITOR→BUILDER | 2026-11-06 04:45-05:25 +03:00 | items: (1) AUDIT G3
from scratch — gates 636, 9/9 test_g3_scroll_linked.py; E3 scripts/r31_e3_g3.py
re-run **ALL PASS** on a FRESH server (pkill-first OPS lesson applied);
implementation read line-by-line against D-LOOP-31a (transition:none sole
ownership, fail-closed :not([data-fx]), triple kill fx=none/reduced-motion/
no-JS, bento untouched, M1 extension with no new family); r31-g3-services.png
eyeballed (media frame renders rounded, text readable, no layout shift) →
**G3 MET-T1**, aud=self 3,n/a,3,3,3,3,4,4, zero gaps. (2) BUILDER L4 (detail
gallery, 10) — read detail-gallery.js FIRST, extended in place (crossfade/
ring/bump/swipe/arrows survive — test-asserted); JS-built lightbox: role=
dialog + aria-modal, real focus trap (Tab/Shift+Tab cycle, Escape, focus
restored to opener), arrows advance + gallery syncs, backdrop click closes,
JS-injected "Enlarge photo" control (no dead control without JS), scroll
lock html.lb-open + Lenis stop/start via the F5 public API (smooth-scroll.js
untouched), G2 name stays on gallery main and .lightbox__main sets
view-transition-name:none (D-LOOP-32a), single-image fallback (no-thumbs
listings get the viewer too), fx=none + reduced-motion parity kills.
test_l4_gallery.py **9/9**; E3 scripts/r32_e3_l4.py **24/24 ALL PASS**
(dialog/trap/keys/backdrop/swipe/fx=none/JS-blocked/single-image, zero
errors); screenshots r32-l4-lightbox-1280.png + r32-l4-lightbox-single-1280.png
eyeballed (88 listing renders a real photo end-to-end; demo covers are
espresso-dark Pillow art avg RGB 32,23,18 — dark frame = correct rendering,
probed and documented). E3 lessons: 480ms crossfade settle before reading
the gallery main bg; ~700ms settle before screenshots (mid-smooth-scroll
compositor frames offset fixed layers). | score: G3 audit (no move, MET-T1
confirmed) · L4 n/a→READY-FOR-AUDIT self 3,3,3,3,4,3,4,4 | evidence: E2+E3 |
gates: check OK · makemigrations OK · **636 → 645 passed** (+9 L4) · hex
ratchet **214 held** (survey re-run) | decisions: D-LOOP-32a | FOR THE NEXT
RUN: audit L4 (9/9 + r32_e3_l4.py ALL PASS + D-LOOP-32a re-read + both
screenshots), then BUILDER ONE item deeply — G4 (pointer polish, 7) or
H2.b (hero motion slice); suite ≥ 645 | blockers: none

Run 31 | AUDITOR→BUILDER | 2026-11-06 02:18-03:20 +03:00 | items: (1) AUDIT H4 from scratch — gates 627, 6/6 test_h4_section_rhythm.py; E3 scripts/r30_e3_h4.py re-run **6/6 ALL PASS** on a FRESH server (pkill first — r30 OPS lesson applied; stale-cache trap avoided); D-LOOP-30a verified against code (5 data-archetype tags byte-match the documented mapping; addendum Home mapping pins hold); r30-h4-home-390.png eyeballed (hamburger nav, stacked search pill, hero intact); D-LOOP-30c duplicated-clause doc wart fixed → **H4 MET-T1**, aud=self 3,3,n/a,n/a,n/a,3,3,4, zero gaps. (2) BUILDER G3 (scroll-linked, 10) — test_g3_scroll_linked.py FIRST (9 tests: @supports+view() gate, live-surface targeting, transform/clip-path/opacity-only keyframes, no layout-shift props, IO fallback intact, motion-ready scoping, fx=none kill, bento never targeted, surfaces render), then ONE @supports block in components.css 12b: reversible scroll-driven g3-rise on nearby cards + services rows, g3-clip on services media, rise on the about collage figure; IO fallback untouched; E3 scripts/r31_e3_g3.py **12/12 ALL PASS** with a natural-scroll methodology (rAF-ticked instant steps — same-task timeline reads are stale; two-arg scrollTo inherits the global scroll-behavior:smooth): nearby op **0→0.57→1**, svc-row 0→1, media clip inset(10% 7%)→inset(0%), about figure ViewTimeline attached, fx=none kill rules hold, JS-blocked fully visible, zero console errors; r31-g3-services.png eyeballed (003 row media mid-clip, text readable, no layout shift). Architecture lessons banked in D-LOOP-31a: g3 elements set transition:none (a running CSSTransition sits ABOVE animations in the cascade and would snap the reveal mid-range); fail-closed :not([data-fx]) kill; bento deliberately untouched (H3/M4 frozen); parallax DEFERRED honestly (dormant .story collage, bg-image media box — no clipped inner layer exists; fake parallax rejected); "collage" mapped to the live about figure; addendum M1 row extended (no new family, cap 6). | score before to after (self): H4 READY-FOR-AUDIT→MET-T1 (aud 3,3,n/a,n/a,n/a,3,3,4); G3 TODO→READY-FOR-AUDIT (self 3,n/a,3,3,3,3,4,4) | evidence tier: E2+E3 | gates: start — check 0 issues, makemigrations no changes, **627 passed**; end — check 0 issues, makemigrations no changes, **636 passed** (+9 G3; re-verified after the addendum M1 edit) | ratchets: sub-13px 43, hex 214, image bytes 4,191,687 — all held (CSS additions use tokens/one var() fallback only) | decisions: **D-LOOP-31a** (scroll-timeline sole ownership + parallax deferral + collage mapping + E3 scroll-timeline measurement method) | FOR THE NEXT RUN: AUDITOR — audit G3 (mechanical: 9/9 test_g3_scroll_linked.py, re-run scripts/r31_e3_g3.py expect ALL PASS, re-read D-LOOP-31a, eyeball r31-g3-services.png); then BUILDER ONE item deeply: L4 (detail gallery, 10 — read detail-gallery.js FIRST, swipe + lightbox focus trap + keyboard + shared-element) or G4 (pointer polish, 7); suite must stay ≥ 636 | blockers: none |

Run 30 | AUDITOR→BUILDER | 2026-11-06 00:47-01:25 +03:00 | items: (1) AUDIT F5 from scratch — gates 621, 6/6 test_f5_smooth_scroll.py; E3 scripts/r29_e3_f5.py re-run **19/19 ALL PASS** (rich smoothing curve 0→661→958→1196, G1 hide/return under Lenis, L1 pin 5→886 + flash, anchor click, fx=none/touch/lite native with helper defined, zero errors); SRI recomputed from vendored bytes == base.html tag (sha384-v5v9…SCUK), 16,731 B, LICENSE kept, no sourceMappingURL, load order fx-gate→motion→lenis→smooth-scroll all defer; D-LOOP-29a verified line-by-line (ghScrollTo unconditional, rich+fine-pointer+hover guards, anchors:false/autoRaf, D-LOOP-16a no re-check honoured, base.css 3 lenis classes, motion.js/search-map.js call sites routed with native fallback kept); M5 addendum entry covers fx-aware smooth scroll (cap intact) → **F5 MET-T1**, aud=self 3,n/a,3,3,3,3,3,4, zero gaps. (2) BUILDER H4 (section rhythm, 10) — test_h4_section_rhythm.py FIRST (6 tests: addendum docs + home mapping pins, tag order, ≥3 archetypes, ≤2 consecutive), then 5 attribute-only data-archetype tags on home bands in flow order (#hero full-bleed → #checks edge-strip → #bento full-bleed → #recommended type-led → #nearby type-led; rationale D-LOOP-30a — bento is a media band, not type-led, else 3 type-led in a row), addendum archetype section corrected (marquee double-listing resolved; F4 M-table untouched), E3 scripts/r30_e3_h4.py **6/6 ALL PASS** (5 bands DOM-order at 1280px AND 390px, marquee text intact, zero console errors; screenshots r30-h4-home-{1280,390}.png eyeballed — hero pixel-identical). OPS lesson: a stale --noreload server from r29 still held port 8765 and served cached pre-edit templates (E3 failed oddly) — killed it, re-ran clean; future runs: pkill before starting the detached server. Hex ratchet bisected (D-LOOP-30c): 215→214 landed in the r29 L3 commit (search.css primary-action `color:#fff` tokenised); HEX_BASELINE re-pinned 214, survey regex aligned with the test counter, F1 8/8 re-green. | score before to after (self): F5 READY-FOR-AUDIT→MET-T1 (aud 3,n/a,3,3,3,3,3,4); H4 TODO→READY-FOR-AUDIT (self 3,3,n/a,n/a,n/a,3,3,4) | evidence tier: E2+E3 | gates: start — check 0 issues, makemigrations no changes, **621 passed**; end — check 0 issues, makemigrations no changes, **627 passed** (+6 H4; F1 re-pinned constant re-verified 8/8) | ratchets: sub-13px **43**, hex **214** (re-pinned), image bytes **4,191,687** — all held | decisions: **D-LOOP-30a** (archetype mapping + marquee resolution + F4-freeze scope), **D-LOOP-30c** (hex re-pin 214 + survey regex alignment) | FOR THE NEXT RUN: AUDITOR — audit H4 (mechanical: 6/6 test_h4_section_rhythm.py, re-run scripts/r30_e3_h4.py expect ALL PASS, re-read D-LOOP-30a, eyeball r30-h4-home-1280.png); then BUILDER ONE item deeply: G3 (animation-timeline behind @supports, 10 — collage/services/nearby parallax+clip reveals, IO fallback kept, transform/clip/opacity only) or L4 (detail gallery, 10 — read detail-gallery.js first, swipe + lightbox focus trap + shared-element); suite must stay ≥ 627 | blockers: none |

Run 29 | AUDITOR→BUILDER | 2026-11-05 23:50-2026-11-06 00:45 +03:00 | items: (1) AUDIT L3 from scratch — gates 615, 6/6 test_l3_row_density.py; git-diff HEAD~1 on _results_grid.html + search.css proves the brand→agent channel conditions (`{% if brand.x %}…{% elif property.agent.x %}`) byte-identical — only class/aria/`?text=` prefill/SVG added, Call now shows the number, View dropped to a quiet last link; E3 scripts/r29_e3_l3_audit.py **16/16 ALL PASS** on the live page (24 rows, agent-fallback branch exercised because brand channels are unfilled in demo data): order WhatsApp>Call>Email>View in EVERY row, wa.me+?text=+svg+aria everywhere, no primary class on secondary actions, rendered heights 410–448px content-driven (CSS min 320), descriptions ≤28 content words — the 29-token rows are Django's truncatewords " …" suffix (punctuation, not a word; audit script fixed, contract met), 16×16 icon, ink/cream tokens, keyboard-focusable, mobile 390px stacks 1-col, zero console/page errors; r28-l3-row.png eyeballed vs my fresh r29-l3-row-audit.png — identical, no regression → **L3 MET-T1**, aud=self 3,3,n/a,3,3,3,3,4, zero gaps. (2) BUILDER F5 (smooth scroll, 10) — test_f5_smooth_scroll.py FIRST (6 tests), then lenis@1.3.11 vendored at static/vendor/lenis/ (16,731 B after sourceMappingURL strip, MIT LICENSE kept, sha384 SRI pinned in base.html and RECOMPUTED from bytes by the test), loaded deferred fx-gate→motion→lenis→smooth-scroll; new static/js/smooth-scroll.js defines `window.ghScrollTo(el, block)` UNCONDITIONALLY (lite/none/touch safety — bare call sites would ReferenceError where the guards return early; lenis.scrollTo when `__lenis` exists, else native fx-aware scrollIntoView honouring scroll-margin-top), Lenis constructed only under data-fx=rich AND fine-pointer+hover (touch off), anchors:false (motion.js owns anchors), autoRaf:true, NO prefers-reduced-motion re-check (my initial defence-in-depth line violated D-LOOP-16a — removed in-build); motion.js anchor handler routes through the helper with native fallback (+3 lines), search-map.js 2 call sites (pin→row, Map pill) routed and its dead local smoothOk() removed — frozen-file touches justified by the F5 contract, logged D-LOOP-29a; base.css gains the 3 official Lenis classes (native scroll-behavior stands down only while lenis-smooth is set). E3 scripts/r29_e3_f5.py **19/19 ALL PASS** (fx=rich faked via init-script hardware spoof: smoothing curve 0→661→932→1196 across samples, html.lenis-smooth set while driving, G1 nav hide/return under Lenis, L1 pin click scrolled 5→886 + flash fired, anchor click clean, zero errors; reduced-motion→none, touch, and default-headless-lite all refuse Lenis with the helper still defined). Frozen-neighbour re-verification: r27_e3_g1.py re-run **PASS** | score: L3 → MET-T1 (aud=self); F5 → READY-FOR-AUDIT (self 3,n/a,3,3,3,3,3,4 · E2+E3); MET share **11/18 (61%)** + H2.a slice | evidence: E2 (6 L3 + 6 F5 tests, full 621) + E3 (r29_e3_l3_audit.py 16/16; r29_e3_f5.py 19/19; r27_e3_g1.py re-run PASS) | gates: start — check 0 issues, makemigrations no changes, **615 passed**; end — check 0 issues, makemigrations no changes, **621 passed** (+6 F5) | ratchets: sub-13px 43, hex 215, image bytes 4,191,687 — all held (no new px font-sizes, no new hex, no images; F1 test pins exact counts) | decisions: **D-LOOP-29a** (vendored Lenis hygiene+SRI; unconditional ghScrollTo; init guards; frozen-file touch justification; truncatewords ellipsis ≠ word) | FOR THE NEXT RUN: AUDITOR — audit F5 (mechanical: 6/6 test_f5_smooth_scroll.py, re-run scripts/r29_e3_f5.py expect ALL PASS, re-read D-LOOP-29a, sanity-check base.html SRI tag); then BUILDER ONE item deeply: H4 (archetype tags + rhythm test, 10) or G3 (animation-timeline behind @supports, 10) — L4 also unblocked; suite must stay ≥ 621 | blockers: none |

Run 28 | AUDITOR→BUILDER | 2026-11-05 22:45-23:15 +03:00 | items: (1) AUDIT G1 from scratch — gates 609, 6/6 test_g1_pill_nav.py, re-ran scripts/r27_e3_g1.py **10/10 PASS** (hide-on-down/return-on-up incl. focusin return, fx=none never hides, JS-blocked header visible), re-read D-LOOP-27a line-by-line against the code (fx-gated call, rAF throttle, 4px hysteresis, 160px depth, transform-only, focusin — all verified), captured 1280px visible/hidden header screenshots (r28-g1-header-*.png; hidden state shows header fully off-viewport) → **G1 MET-T1**, aud=self 3,3,3,4,4,3,4,4, zero gaps. (2) BUILDER L3 (row conversion & density, 13) — test_l3_row_density.py FIRST (6 tests, red 3), then _results_grid.html actions rebuilt: WhatsApp = ink primary pill with ORIGINAL inline SVG glyph (bubble+handset, currentColor — not copied) on BOTH brand and agent branches, wa.me now prefills ?text=listing title, Call shows the number, Email unchanged, "View property" drops to a quiet borderless link (title+image still link to detail); brand→agent channel fallback logic byte-identical, channels stay hidden when unfilled; aria-label="WhatsApp about {{ title }}"; truncatewords 34→28; search.css: row height 500px fixed → auto / min-height 320px, padding clamp 42→32, h2 clamp max 3.3→2.7rem, new .listing-row__whatsapp (ink bg, cream text, 16px svg) + .listing-row__view (transparent) rules, .listing-row__primary rule retired; alternating reverse + mobile 1fr stack untouched (now test-pinned). E3 smoke: rendered row 445px (content-driven; CSS min-height 320 ≤ 320 check passes), WhatsApp pill + svg visible, Call/Email secondary, zero page errors, screenshot r28-l3-row.png — hierarchy reads WhatsApp > Call/Email > View exactly per contract | score: G1 → MET-T1 (aud=self); L3 → READY-FOR-AUDIT (self 3,3,n/a,3,3,3,3,4 · E2+E3); MET share **10/18 (56%)** + H2.a slice | evidence: E2 (6 G1 + 6 L3 tests, full 615) + E3 (r27_e3_g1.py 10/10 re-run; G1 header screenshots; L3 row smoke + screenshot) | gates: start — check 0 issues, makemigrations no changes, **609 passed**; end — check 0 issues, makemigrations no changes, **615 passed** (+6 L3) | ratchets: sub-13px 43, hex 215, image bytes 4,191,687 — all held (no new px font-sizes, no new hex; icon is currentColor) | decisions: none new — L3 implemented per the SCORECARD contract (seed item sanctioned WhatsApp-primary); no addendum change (row actions are not motion effects) | FOR THE NEXT RUN: AUDITOR — audit L3 (mechanical: 6/6 test_l3_row_density.py, re-render a search page and check the action hierarchy + row height yourself, verify brand-channel logic unchanged, eyeball r28-l3-row.png); then BUILDER F5 (Lenis, 10 — vendor under hygiene rules, fx=rich only, off touch, replaces scrollIntoView hack) or H4 (archetype tags, 10); suite must stay ≥ 615 | blockers: none |
Run 27 | AUDITOR→BUILDER | 2026-11-05 21:45-22:25 +03:00 | items: (1) AUDIT L2 from scratch — gates 603, 6/6 test_l2_basemap_palette.py, re-ran scripts/r26_e3_l2.py **7/7 PASS with live tiles** (canvas + 3 pins, zero console/page errors, pin-click flash + scroll intact), re-read D-LOOP-26b line-by-line against search-map.js (ordered rule list, first-match-wins per paint property, getLayer+try/catch guards, runtime getComputedStyle token reads — all match), eyeballed r26-e3-l2-map-region.png (vintage-atlas confirmed: sand ocean/creeks, paper land, cream roads, taupe labels, single attribution, pins clean) + computed label contrast taupe #6b5e53 on paper #f3eee6 = **5.4:1** (≥4.5 Q2) + verified all 4 tokens exist in tokens.css and the SVG fallback untouched (mtime Nov 1) → **L2 MET-T1**, aud scores identical to self (3,3,n/a,4,3,3,4,4), zero gaps found. (2) BUILDER G1 (floating pill nav, 13) — test_g1_pill_nav.py FIRST (6 tests, red 5), then: motion.js setupNavAutoHide (fx-gated call if(!fxNone), rAF-throttled passive scroll, 4px hysteresis, 160px depth, JS-only nav--hidden class, focusin always returns); components.css (header transition + transform, .site-header.nav--hidden translateY(-100%), breakpoints 1200→1024 for nav AND hamburger handover, new .mobile-menu__index/.mobile-menu__signout/.mobile-menu brand-accent classes); _header.html 6 inline styles → classes. Escape-close + skip-link pre-existing — now test-pinned. E3 scripts/r27_e3_g1.py **10/10 PASS**: hide after scroll-down, return on scroll-up AND on focusin, fx=none never hides, JS-blocked header visible (D-MOTION-SAFE); harness note: headless Chromium gates to lite (low hwConcurrency) — assertion accepts lite|rich per the binary check | score: L2 → MET-T1 (aud=self); G1 → READY-FOR-AUDIT (self 3,3,3,4,4,3,4,4 · E2+E3); MET share **9/18 (50%)** + H2.a slice | evidence: E2 (6 L2 + 6 G1 tests, full 609) + E3 (r26_e3_l2.py 7/7 re-run; r27_e3_g1.py 10/10) | gates: start — check 0 issues, makemigrations no changes, **603 passed**; end — check 0 issues, makemigrations no changes, **609 passed** (+6 G1) | ratchets: sub-13px **43**, hex **215**, image bytes 4,191,687 — all held (survey re-run: em sizes are not px literals, so the inline→CSS move is ratchet-neutral) | decisions: D-LOOP-27a nav hide/return = functional nav UI (no addendum family — 6-family cap intact), breakpoint 1024 is a media constant not a token, px-only survey rule | FOR THE NEXT RUN: AUDITOR — audit G1 (mechanical: 6/6 test_g1_pill_nav.py, re-run scripts/r27_e3_g1.py expect PASS, re-read D-LOOP-27a, eyeball hide/return yourself at 1280px); then ONE item deeply (MET share hit 50% per protocol): BUILDER L3 (row conversion, 13) — WhatsApp primary icon via brand-channel logic, row ≤320px, desc ≤28 words — or F5 (Lenis, 10) if L3 looks too template-wide for one box; suite must stay ≥ 609 | blockers: none |

Run 26 | AUDITOR→BUILDER | 2026-11-05 20:45-21:15 +03:00 | items: (1) AUDIT F4 from scratch — gates 597, 7/7 test_f4_motion_vocab.py, then an exhaustive effect hunt: 9 @keyframes in CSS + all JS animation surfaces enumerated. FINDING: addendum mapped 7 hooks but missed detail.css `gallery-count-bump` (public detail page → must map) and manage.css `manage-card-in` (portal, silent). Fixed IN-AUDIT per D-LOOP-22a precedent (2-line doc edit; demote+rebuild would churn 2 runs): gallery-count-bump → M5 confirm row, manage-card-in declared portal-scoped under Cut/dormant, test SHIPPED_TOKENS tightened with both hooks so the gap cannot reopen; archetypes verified against the rendered home (hero=full-bleed, hv2-marquee=edge strip, featured__header=type-led); anchor smooth-scroll considered and excluded (F5's territory, not a vocabulary effect) → **F4 MET-T1** (aud D8 3 for the caught gap, lower-wins D8=3; D-LOOP-26a). (2) BUILDER L2 (basemap palette, 13) — test_l2_basemap_palette.py FIRST (6 tests, red 4), then search-map.js: ordered rule list (regex over loaded style ids, enumerated live from the positron style JSON — 55 layers) applied in the map load handler; first-match-wins per paint property; every application guarded by getLayer + try/catch (missing ids / missing paint props skipped, never fatal); colours read at RUNTIME via getComputedStyle from tokens.css (--paper land, --sand water/buildings/casings/railways, --cream roads, --taupe labels+boundaries, --paper text-halo) — zero hex in JS; positron style JSON enumerated to confirm id scheme (background/water/landcover_*/building/highway_*_casing|inner/railway*/label_*/boundary_*); SVG fallback mombasa-map.svg untouched, single attributionControl untouched, pin font pinned to var(--font-sans). Harness fix: the token-read assertion was too literal for the cached-reader shape (asserts getPropertyValue + ≥4 '--token' refs now). E3 scripts/r26_e3_l2.py **7/7 PASS with live tiles**: canvas + 3 pins draw after recolour, pin click still flashes + scrolls its row (L1 sync intact), ZERO console/page errors (incl. zero setPaintProperty errors), screenshots r26-e3-l2-palette.png + r26-e3-l2-map-region.png — vintage-atlas Mombasa verified visually: sand ocean/creeks, paper land, cream roads, taupe labels, single attribution line; the positron blue/grey clash is gone | score: F4 → MET-T1; L2 → READY-FOR-AUDIT (self 3,3,n/a,4,3,3,4,4 · E2+E3); MET share **8/18 (44%)** | evidence: E2 (7 F4 + 6 L2 tests) + E3 (r26_e3_l2.py 7/7 live tiles + 2 screenshots; r23/r24 E3 suites remain green in the full run) | gates: start — check 0 issues, makemigrations no changes, **597 passed**; end — check 0 issues, makemigrations no changes, **603 passed** (+6 L2) | ratchets: sub-13px 43, hex 215, image bytes 4,191,687 — all held (JS reads tokens at runtime; no CSS hex, no image changes) | decisions: D-LOOP-26a F4 audit correction (M5 + portal-scope declaration + test tightening); D-LOOP-26b L2 palette (rule-list = the "guarded layer list": regex rules over the loaded style, first-match-wins per paint property, getLayer+try/catch guards, runtime token reads, vintage-atlas mapping) | FOR THE NEXT RUN: AUDITOR — audit L2 (mechanical: 6/6 test_l2_basemap_palette.py, re-run scripts/r26_e3_l2.py expect PASS, re-read D-LOOP-26b, eyeball r26-e3-l2-map-region.png); then BUILDER G1 (floating pill nav, 13 — hide/return on scroll under fx lite+rich, full nav from 1024px, mobile-menu inline styles → CSS, Escape closes, skip link) or L3 (row conversion, 13 — WhatsApp primary icon, row ≤320px, desc ≤28 words); suite must stay ≥ 603 | blockers: none

Run 25 | AUDITOR→BUILDER | 2026-11-05 17:47-18:07 +03:00 | items: (1) AUDIT L1 from scratch — gates 590, 12/12 test_l1_map_list_sync.py, implementation re-read (delegated hover wiring survives HTMX swaps, popup-owns-focus, fx-gated scroll, Q3-safe hidden pill, escapeHtml on every popup interpolation), D-LOOP-23a re-read, E3 re-run scripts/r23_e3_l1_audit.py **15/15 with live tiles** (identity 21/21, pin→scroll+flash, popup focus, hover→hot→clear, pill reveal/return/hide, JS-blocked Q3 21 rows) → **L1 MET-T1** (aud 3,3,3,3,3,3,4,4 — lower-wins equals self). (2) AUDIT H2.a from scratch — 7/7 test_h2_hero.py, D-LOOP-24a/b re-read, template+CSS slices re-read (stats gone, cue `(max-width: 809px), (hover: none)`, marquee mask colour-keywords, components.css r24 block token-only), E3 re-run scripts/r24_e3_visual.py **15/15** AND the SCORECARD-mandated superset scripts/r24_e3_h2a_audit.py **18/18** (adds desktop-1280 cue-visible + pill-radius-100px checks and reduced-motion mask parity) → **H2 MET-T1 (a-slice)** (aud 3,3,n/a,3,3,3,4,4 — lower-wins equals self; H2.b motion slice stays TODO). (3) BUILDER F4 (motion vocabulary, 13) — test_f4_motion_vocab.py FIRST (7 tests, red 7), then docs/DESIGN-ADDENDUM.md: 6-entry vocabulary M1 rise / M2 crossfade / M3 marquee / M4 spotlight / M5 confirm / M6 invite, each row purpose + where-used + tier + reduced-motion/none behaviour; stacking rule (max 2 per viewport — ambient + gesture slots, hero is the only ambient site); 3 archetypes (full-bleed, type-led, edge strip); every shipped hook maps (hv2-rise, data-reveal, view-transition, hero-fade+hero-drift, hv2-marquee, bento-shift, h3-card-grow, is-flashed, data-map-return, hv2-scroll); data-count declared DORMANT (no template usage — motion.js counter must not return without an entry); no hex in docs (D-LOOP-25a) | score: L1 → MET-T1; H2 → MET-T1 (a-slice); F4 → READY-FOR-AUDIT (self 3,n/a,3,3,n/a,3,4,4 · E2 docs+tests); MET share **7/18 (39%)** + H2.a slice | evidence: E2 (12 L1 + 7 H2 + 7 F4 tests) + E3 (r23_e3_l1_audit.py 15/15 live tiles; r24_e3_visual.py 15/15; r24_e3_h2a_audit.py 18/18; LOOP/audit-screens/r23-e3-l1-*.png + r24-e3-*.png refreshed this run) | gates: start — check 0 issues, makemigrations no changes, **590 passed**; end — check 0 issues, makemigrations no changes, **597 passed** (+7 F4) | ratchets: sub-13px 43, hex 215, image bytes 4,191,687 — all held (docs+tests only, zero CSS/image edits) | decisions: D-LOOP-25a addendum vocabulary consolidation (hero-fade/drift → M2 crossfade; bento-shift + h3-card-grow → M4 spotlight; data-count dormant) | FOR THE NEXT RUN: AUDITOR — audit F4 (mechanical: 7/7 test_f4_motion_vocab.py, read the addendum against the code — confirm every shipped hook maps, nothing exceeds 6 rows, archetypes match rendered sections); then BUILDER L2 (basemap palette, 13 — test_l2_basemap_palette.py first, setPaintProperty token recolour with guarded layer list, pin font fix, r13 map tests stay green) or G1 (floating pill nav, 13) if L2 looks too tile-dependent for one box; suite must stay ≥ 597 | blockers: none

Run 24 | BUILDER (owner-directed, resumed after interruption) | 2026-11-05 17:20-17:55 +03:00 | items: (1) REPAIR — the r24-owner session was cut mid-run leaving an unreleased lock and a half-applied tree; gates red at resume (4 failed / 586 passed): ONE root cause, the r16/r18 bug class again — a multi-line `{# … #}` comment in about.html (Django template comments are single-line); single-line fix → green. No other defect; no completed edit reverted (D-LOOP-24c). (2) Completion of the interrupted scope — H2.a hero structure slice (owner 390px screenshots): hero stats row (2026 / 5 checks / Kenya) REMOVED (BrandSettings has no stat fields; "Kenya" is named filler in the H2 spec — D-LOOP-24a); touch-meaningless mouse-wheel scroll cue hidden under `(max-width: 809px), (hover: none)`; marquee edge `mask-image` fade (colour keywords, no hex); mobile search card `--radius-card` + Buy/Rent segment shrunk + submit stretched (components.css r24 block). test_h2_hero.py FIRST (7 tests) + test_phase2_home three-stat contract superseded in place (count preserved). (3) Founder portrait — owner upload → scripts/r24_founder_portrait.py → 240×240 WebP 6,642 B → /about/ founder card 60px circle (width/height, real alt, lazy); "GO" monogram gone; test_founder_portrait.py (2 tests). (4) Ratchets re-pinned: image bytes 4,185,045 → **4,191,687** (+6,642 B sanctioned content addition, D-LOOP-24b); hex tightened 217 → **215** (stat--light removal carried 2 hex out); sub-13px 43 held; HEX_BASELINE constant 217→215, IMAGE_BYTES_BASELINE re-pinned — both documented | score: H2 → READY-FOR-AUDIT (a-slice; self 3,3,n/a,3,3,3,4,4 · E2+E3); MET share 6/18 (33%) | evidence: E2 (7 H2.a + 2 portrait + 8 F1 + 6 F3 green) + E3 (scripts/r24_e3_visual.py **15/15** first pass + scripts/r24_e3_h2a_audit.py **18/18** superset — adds desktop 1280 pill/cue checks and reduced-motion mask parity — at 390×844: header top-0, stats absent, cue display:none, marquee mask, card radius 20px, segment start, submit stretch, no x-overflow; portrait decoded naturalWidth 240 in 60px circle + alt + monogram gone; LOOP/audit-screens/r24-e3-{mobile-hero,about-founder,hero-mobile-390,hero-desktop-1280,about-portrait-390}.png) | gates: start — check 0 issues, makemigrations no changes, **586 passed / 4 failed** (comment leak); end — check 0 issues, makemigrations no changes, **590 passed** | decisions: D-LOOP-24a one-gesture hero / stats removed + mobile fixes; D-LOOP-24b portrait + ratchet re-pins; D-LOOP-24c interrupted-run-completion mechanics | FOR THE NEXT RUN: AUDITOR — audit L1 (mechanical: re-run gates, 12/12 test_l1_map_list_sync.py, re-run scripts/r23_e3_l1_audit.py expect PASS — live tiles reachable, re-read D-LOOP-23a) AND audit H2.a (7/7 test_h2_hero.py, re-run scripts/r24_e3_visual.py expect PASS, re-read D-LOOP-24a/b); then BUILDER F4 (motion vocabulary, 13 — docs/DESIGN-ADDENDUM.md ≤6 effects, map the G2 pair + L1 flash/scroll + hv2-rise/marquee, unblocks G3+G4); suite must stay ≥ 590 | blockers: none

Run 23 | AUDITOR→BUILDER | 2026-11-05 16:15-16:45 +03:00 | items: (1) AUDIT G2 from scratch — gates 569, 7/7 test_g2_view_transitions.py, E3 re-run 14/14 (CSSOM proves the @supports-nested @view-transition rule; lite names on; reduced-motion + JS-blocked fail-closed), D-LOOP-22b re-read, implementation surfaces re-grepped (5 named surfaces + hero; _listing_card intentionally unnamed) → **G2 MET-T1** (aud 3,3,3,3,3,3,4,4 — equals self, lower wins). (2) BUILDER L1 (map & list sync, 16) — test_l1_map_list_sync.py FIRST (12 tests, red 10), then: rows carry id=listing-row-<pk> + data-listing-pk; map JSON gains "id"; search-map.js adds delegated row→pin .is-hot hover, pin→row scroll+is-flashed (behaviour reads html[data-fx], no motion-preference query per D-LOOP-16a), IntersectionObserver Map pill (hidden in markup — no dead control JS-blocked, Q3), map region tabindex=-1 + pill returns focus to it; #results-count aria-live=polite + HTMX partial re-sends it hx-swap-oob (count was outside the swap target — stale on filter changes; fixed); search.css appends flash/is-hot/pill (tokens only; pin is-hot reuses the existing hover language; flash killed under reduced-motion AND fx=none). E3 first pass 12/15: (a) flashRow's link.focus fought maplibre's popup focusAfterOpen — REMOVED, popup owns focus (that IS the keyboard path, D-LOOP-23a); (b) pill-return assertion assumed scrollY=0 but the map shell sits at y≈594 — assert map-in-viewport instead; (c) get_attribute('hidden') returns "" for boolean attrs — harness fix. E3 re-run **15/15 with live tiles** | score: G2 → MET-T1; L1 → READY-FOR-AUDIT (self 3,3,3,3,3,3,4,4 · E2+E3); MET share **6/18 (33%)** | evidence: E2 (12 L1 tests + 7 G2) + E3 (scripts/r23_e3_l1_audit.py 15/15: identity 21/21, canvas+3 pins, click→scroll+flash, popup-focus, hover→hot→clear, pill reveal/return/hide cycle, JS-blocked pill never appears + 21 rows visible; LOOP/audit-screens/r23-e3-l1-{map,flash}.png) | gates: start — check 0 issues, makemigrations no changes, 569 passed; end — check 0 issues, makemigrations no changes, **581 passed**; ratchets: sub-13px 43, hex 217, image bytes 4,185,045 — all held (no CSS hex added; rgba pulses are F1-exempt per existing precedent) | decisions: D-LOOP-23a L1 sync design (delegated wiring survives HTMX swaps; oob live count; popup-owns-focus rule; pill Q3-safe) | FOR THE NEXT RUN: AUDITOR — audit L1 (mechanical: re-run gates, 12/12 test_l1_map_list_sync.py, re-run scripts/r23_e3_l1_audit.py expect PASS — needs live tiles, they ARE reachable from this sandbox, re-read D-LOOP-23a); then BUILDER F4 (motion vocabulary, 13 — docs/DESIGN-ADDENDUM.md ≤6 effects + archetypes, map shipped effects incl. the G2 pair and L1 flash/scroll, unblocks G3+G4) or the H2.a structure slice (D-LOOP-20b, 16) if the addendum looks too small for a box — suite must stay ≥ 581 | blockers: none

Run 22 | AUDITOR→BUILDER | 2026-11-05 15:15-15:55 +03:00 | items: (1) AUDIT F3 from scratch — gates 562, 6/6 test_f3_media_diet.py, independent byte walk (35 images, 4,185,045 B exact, zero >250KB), width/height re-verified 12/12 across all templates incl. the multi-line _listing_card tag (Python [^>]* crosses newlines — test is sound), E3 smoke re-run 13/13 PASS, D-LOOP-21a/b/c rationale re-read. SIDE-FINDING: survey prints sub-13px **43** not the recorded 44 — regexes identical to the F1 test counter; HYG-1 carried one sub-13px line out AFTER the r21 WATCH count → ratchet DOWN = compliant, F1 ceiling constant stays 44, SCORECARD F1/F3 expectations corrected 44→43 (D-LOOP-22a — same stale-expectation class as r20's 44/238) → **F3 MET-T1** (aud 3,3,n/a,4,3,3,3,4; D6 visual-unverified → OWNER_NEEDS L2). (2) BUILDER G2 — test_g2_view_transitions.py FIRST (7 tests, red 6), then: base.css @supports block (@view-transition nav:auto + fail-closed `html { view-transition-name: none }` + rich/lite re-enable + inline-name override); inline `prop-<pk>` names on _results_grid row imgs, _home_card_{feature,rail,banner,stay}, detail .gallery__main (image AND poster branches); _listing_card deliberately UNNAMED (similar-listings on detail would duplicate the hero's name — test guards it); fixture generates in-memory PIL images because the suite's no_images=True convention strips the <img> elements the names ride on (found via 0-names red, fixed in fixture) | score: F3 → MET-T1; G2 → READY-FOR-AUDIT (self 3,3,3,3,3,3,4,4 · E2+E3); MET share **5/18 (28%)** | evidence: E2 (7 G2 + 6 F3 + 8 F1 tests) + E3 (scripts/r22_e3_g2_audit.py 14/14: CSSOM proves the @supports-nested @view-transition rule parses in Chromium; lite → root name active + card prop-88 with width/height; reduced-motion → fx=none → root none + inline name neutralised; JS-blocked → no attr, everything off, rows visible (Q3); LOOP/audit-screens/r22-e3-g2-{lite,none}.png) | gates: start — check 0 issues, makemigrations no changes, 562 passed; end — check 0 issues, makemigrations no changes, **569 passed**; ratchets: sub-13px **43** (expectation corrected), hex 217 held, image bytes 4,185,045 exact held | decisions: D-LOOP-22a sub-13px 44→43 correction (docs-only, ceiling constant unchanged); D-LOOP-22b G2 CSS-only double fail-closed + _listing_card exclusion rule | FOR THE NEXT RUN: AUDITOR — audit G2 (mechanical: re-run gates, 7/7 test_g2_view_transitions.py, re-run scripts/r22_e3_g2_audit.py expect PASS, re-read D-LOOP-22b); then BUILDER L1 (map & list sync, 16) or the H2.a structure slice (D-LOOP-20b) if L1 looks too big for one box; suite must stay ≥ 569; ALSO QUEUED: HYG-2 delete orphaned _home_property_card.html (BACKLOG, zero includers since r18) | blockers: none

Run 21 | WATCH→BUILDER | 2026-11-05 14:15-14:45 +03:00 | items: (1) WATCH overlay (D-LOOP-20e) — deterministic spot-check 21 mod 4 = 1 → F2: 22/22 (test_f2 14 + test_f1 8), r17 E3 artifacts present, F1 drift held — clean, no REGRESSED. (2) BUILDER F3 (image & video diet, folds HYG-1) — test_f3_media_diet.py FIRST (6 tests, red: cap/bytes/dimensions/webp/purge), then: market-filter cards 1600px→900px WebP q82 (green-apartments 660→146KB, mombasa-villa 602→162KB, pool-villa-night 436→87KB) + width/height attrs (CLS); hero slides 1-4 → WebP q85 native 1920 (slide-1 preload kept, LCP; 258→183KB worst); seed sources nyali-apartment/ocean-bedroom RE-ENCODED in place (293→149, 400→188KB) because seed_demo.py + seed_mombasa_showcase.py copy them at seed time (deleting would break fresh-DB seeding); 7 JPGs deleted after ref updates; hero-loop.mp4 deferred to H2 via contract test (unreferenced OK; any future ref must carry fx=rich && !Save-Data + poster, D-LOOP-21a); HYG-1 executed — dead hv2 rule test: rule dies when ANY hv2 token has no template usage; removed commit/collage/faq/cta/cards-card/about/services/btn-light/link/h2--light + 3 dead stagger lines + dead lines in 3 media blocks (.hv2-split selector reduced to live part; reduced-motion block lost only its 2 dead lines); home.css 1461→1342 lines | score: F3 → READY-FOR-AUDIT (self 3,3,n/a,3,3,3,3,4 · E2+E3); suite 556→562 | evidence: E2 (6 F3 tests + F1 suite green after constant tighten) + E3 (scripts/r21_render_smoke.py 13/13: hero-slide-1.webp decodes 1920w, bento grid renders post-purge, marquee still styled, 3 market WebPs load at 391px; r21-{home,search}-after-diet.png) | gates: start — check 0 issues, makemigrations no changes, 556 passed; end — check 0 issues, makemigrations no changes, 562 passed; ratchets: hex 236→217 (dead rules carried 19 hex; F1 HEX_BASELINE 240→217 with history), sub-floor 44 held, static image bytes 6,161,625→4,185,045 (new ratchet, exact) | decisions: D-LOOP-21a video deferral + contract test; 21b diet split (WebP marketing art vs re-encoded seed sources); 21c HYG-1 boundary rule (any-dead-token ⇒ dead rule; keyframe names excluded) | FOR THE NEXT RUN: AUDITOR — audit F3 (mechanical: re-run gates, 6/6 F3 tests, f1_token_survey expect 44/217, re-run r21_render_smoke.py expect PASS); then BUILDER takes G2 (shared-element transitions, priority 16, unblocks L4; test_g2_view_transitions.py first) or L1 (16, map/list sync) — G2 recommended per D-LOOP-20a build order; H2 (16) also unblocked now F3 is built — if H2, build slice H2.a structure only (D-LOOP-20b); suite must stay ≥ 562 | blockers: none

Run 20 | PLANNER→AUDITOR | 2026-11-05 13:50-14:14 +03:00 | items: (1) RETROSPECTIVE over r15-r19 — untouched bonus +1 live from r20 (leaders: L1 16, G2 16, F3 13, F4 13, G1/L2/L3 13, F5/H4 10; H2/G3/G4/L4 needs-blocked); F3 sequenced next despite the nominal tie (unblocks H2 at 16, page-weight win, HYG-1 folds into the same diet pass); H2 pre-split into two ordered slices in one row (H2.a structure / H2.b motion, planning-only — attempts stay 0); pruned cross-file overlap: BACKLOG P4-1→H2, HYG-1→F3, P5-3 focus/contrast→Q2; P4-4 vs frozen H1 order → DECISIONS-FIRST reconciliation rule; WATCH made an explicit r21+ overlay with a deterministic MET spot-check by run number; SCORECARD F1 line corrected (expect 44/236 — was stale 44/238; survey re-run confirmed 44/236). (2) AUDIT H3 from scratch — 5/5 test_h3_mobile_bento.py, then new E3 suite scripts/r20_e3_h3_audit.py (4 Playwright contexts, 21 checks, verdict PASS): mobile 390px = flex rail / overflow-x auto / snap x-mandatory / scroll-padding 9% / snap-align centre / 82%+88% bases / scrollable 1825>355 / bento-shift NOT live / keyboard walk reaches all 7 cards scrolling 0→1470; reduced-motion → animation none + transitions zeroed; JS-aborted → rail still flex + scrollable + fully visible (D-MOTION-SAFE); desktop 1280 rich+fine shim → data-fx=rich, is-live set, display grid (mobile block did not hijack desktop) → H3 MET-T1 (aud 3,3,3,3,3,3,3,3; equals self, lower wins) | score: H3 → MET-T1; MET share 4/17 (24%) | evidence: E2 (5 H3 tests) + E3 (21/21; LOOP/audit-screens/r20-e3-h3-{mobile-rail,mobile-reduced,desktop-untouched}.png, owner copy download/preview-screenshots/r20-mobile-bento-audit.jpg) | gates: start — check 0 issues, makemigrations no changes, 556 passed; end — identical (docs + audit only, zero product-code edits); ratchets 44/236 held (survey re-run) | decisions: D-LOOP-20a..e (DECISIONS "Loop 20") | FOR THE NEXT RUN: WATCH overlay FIRST per D-LOOP-20e (deterministic spot-check: 21 mod 4 = 1 → F2 from the sorted MET list [F1,F2,H1,H3] — re-run test_f2_capability_gate.py + verify r17 E3 artifacts exist; mandatory F1 drift test; any failure ⇒ REGRESSED and pre-empts the build), then BUILDER F3 (image & video diet, priority 13; folds HYG-1: measure static/ baseline table FIRST, Pillow WebP pass, hero-loop.mp4 gated fx=rich && !Save-Data with poster or documented removal, width/height on every img) — G2 (16) is the r22 candidate | blockers: none

Run 19 | AUDITOR→BUILDER | 2026-11-05 13:20-13:50 +03:00 | items: (1) AUDIT H1 from scratch — gates 551 green, 11/11 H1 tests, exactly 4 sections, E3 destination audit via Playwright visibility checks (9/9: /checks/ commitments, footer FAQ/newsletter/CTA/browse, /about/ philosophy+fee) → H1 MET-T1 (D6 desktop-only E3 → batched one OWNER_NEEDS mobile-eyeball line per §4). (2) BUILDER H3 — test_h3_mobile_bento.py first (5 tests incl. two guards: desktop shape-shift rules untouched, plain .bento-grid not hijacked), then home.css: <1021px .bento-grid--shift becomes a flex scroll-snap rail (cards 82%/88% snap-align center, clamp height, hidden scrollbar); centre-card scale-up = scroll-driven animation-timeline: view(inline) behind @supports (0.92→1, animation-range entry 40%→cover 50%); reduced-motion block now kills the grow animation; ZERO JS added (bento-shift.js untouched, grep-guarded) | score: H1 → MET-T1 (aud=self 3,3,n/a,3,3,3,3,3); H3 → READY-FOR-AUDIT (self 3,3,3,3,3,3,3,3 · E2+E3); suite 551→556 | evidence: E2 (5 H3 tests) + E3 (390px mobile emulation: computed flex/auto/x-mandatory/center, 7 cards, scrollable, bento-shift correctly NOT live; keyboard focus walk scrollLeft 0→493; r19-mobile-bento-carousel.jpg in download/preview-screenshots) | gates: start — check 0 issues, makemigrations no changes, 551 passed; end — check 0 issues, makemigrations no changes, 556 passed; ratchets held (44/236) | decisions: D-LOOP-19a mobile bento carousel is CSS-only — snap rail + @supports-guarded scroll-driven centre scale; bento-shift.js and the >1020px desktop rules untouched; one audit-tool bug self-caught (a verdict line tested 'x' in overflowX='auto'; re-ran with fixed logic → clean PASS) | FOR THE NEXT RUN: AUDITOR — audit H3 (re-run gates + test_h3_mobile_bento.py; E3: re-check the rail at 390px incl. snap and keyboard walk); then BUILDER takes F3 (image & video diet, priority 12, unblocked, pairs with the HYG-1 dead-CSS purge) or L1 (15, map/list sync) — F3 recommended because H2 needs it and it shrinks the page | blockers: none

Run 18 | AUDITOR→BUILDER | 2026-11-05 12:30-13:05 +03:00 | items: (1) AUDIT F1 from scratch — gates re-run (540), ratchets recomputed via scripts/f1_token_survey.py (sub-floor 44, hex 238 — exact), --font-body gone / --paper #f3eee6 verified in files, 8/8 F1 tests → F1 MET-T1 (aud D8=4: documented counting rules, pair-level no-growth baselines, value pinning; lower-wins = 3s). (2) BUILDER H1 — test_h1_home_order.py first (11 tests), then: home.html restructured 569→~347 lines, top-level sections 12→4 (exactly hero, bento, recommended, nearby; showcase id→bento, hero id=top→hero); talk-to-us band → channels strip inside recommended (honest-blank kept: renders only when the brand row has a channel); about philosophy + fee lines → /about/; services cards already duplicated on /services/ (dedup removal); commitments → /checks/; FAQ + newsletter + closing CTA → footer site-wide (details/summary, same form action, /#newsletter anchor now in footer); browse → curated footer hub links. Two failed attempts en route (root causes in JOURNAL): (a) the EXACT r16 multi-line {#…#} comment-leak bug class — 5 new multi-line template comments leaked, fixed single-line (rule re-learned: grep BEFORE committing); (b) the footer browse column first built LIVE (context processor, 7 queries/request incl. a bad location__path FieldError) broke the results-page query budget (21 > 15; baseline is 14, ceiling 15, zero headroom) → replaced with curated query-free hubs, processor deleted | score: F1 → MET-T1; H1 → READY-FOR-AUDIT (self 3,3,n/a,3,3,3,3,3 · E2+E3: rendered home verified — 4 nearby cards, footer rows, honest-blank strip); suite 540→551 | evidence: E2 (11 H1 tests + updated phase2 markers) + E3 (r18-home-desktop.jpg, r18-checks-commitments.jpg in download/preview-screenshots) | gates: start — check 0 issues, makemigrations no changes, 540 passed; MID-RUN RED — 17 failed (comment leaks + query budget + F1 attribution shifts); end — check 0 issues, makemigrations no changes, 551 passed; ratchets: hex 238→236 (--light variant + orphan var(--bg) lines removed), sub-floor 44 (pairs re-attributed home→components for the moved form label) | decisions: D-LOOP-18a home = hero/bento/recommended/nearby exactly, talk strip inside recommended with honest-blank; 18b footer browse = curated static hubs, query-free (live version broke the budget); 18c FAQ/newsletter/CTA footer site-wide, home.html 12→4 sections | FOR THE NEXT RUN: AUDITOR — audit H1 (re-run gates + test_h1_home_order.py; check destinations with E3: /checks/ commitments, footer rows, /about/ lines); then BUILDER takes F3 (image & video diet, priority 12, unblocked) or H3 (mobile bento, priority 15, needs F2 ✓ MET) — H3 recommended; suite must stay ≥ 551; ALSO QUEUED: dead home.css purge (hv2-commit/faq/cta/cards/collage rules orphaned by H1 — noted in BACKLOG, do with F3/F4) | blockers: none

Run 17 | AUDITOR→BUILDER | 2026-11-05 11:58 +03:00 | items: (1) AUDIT F2 from scratch — gates re-run, code re-read, closed the open E3 step with a real-browser Playwright suite (scripts/r17_e3_fx_audit.py): reduced-motion emulation → real gate sets fx=none, bento stays off, ALL 57 reveals visible instantly; gate request blocked → attribute null (fail-closed holds), content visible; rich+fine shim → fx=rich and bento grid becomes is-live; this container's real hardware grades lite and bento correctly stays off there; screenshots LOOP/audit-screens/r17-e3-{rich-bento-live,none}.png → F2 MET-T1 (aud 3,n/a,n/a,3,3,3,4,4; lower-wins vs self 3s). (2) BUILDER F1 — test_f1_token_integrity.py first (8 tests: undefined-var scan counting css declarations + template inline styles + JS setProperty as definition sources; --font-body gone; --paper defined; 13px-floor allowlist 12 pairs with reasons + no-growth pair baselines; hex ratchet), then fixes: search.css price-pin var(--font-body)→var(--font-sans) (the r13-era "probably breaks the pin font" finding CONFIRMED — undefined var silently invalidated the declaration), detail.css font-body fallback→--font-sans, tokens.css defines --paper:#f3eee6 + allowlist comment, both --paper inline fallbacks removed | score: F2 → MET-T1; F1 → READY-FOR-AUDIT (self 3,n/a,n/a,n/a,3,n/a,3,3); suite 532→540 | evidence: E2+E3 for F2 (browser-verified), E2 for F1 (zero visual delta by construction: --paper value = the old fallback verbatim) | gates: start — check 0 issues, makemigrations no changes, 532 passed; end — check 0 issues, makemigrations no changes, 540 passed; ratchets: hex 240→238, sub-floor 44 (held) | decisions: D-LOOP-17a --paper single-sourced #f3eee6 (value pinned by test); 17b inline/JS custom properties count as definitions (home.html --bg pattern is intentional); 17c 13px floor = allowlist + ratchets (44/240 recorded, hex already down to 238) | FOR THE NEXT RUN: AUDITOR — audit F1 (mechanical: re-run gates, run scripts/r17_f1_survey.py, expect 44/238 and 8/8 F1 tests); then BUILDER takes H1 (home order & diet, priority 15, now the biggest unblocked user-visible item; test_h1_home_order.py first) — L1 is the alternative if H1 looks too big for one box; suite must stay ≥ 540 | blockers: none

Run 16 | BUILDER | 2026-11-05 09:58 +03:00 | items: F2 capability gate (static/js/fx-gate.js new; motion.js + bento-shift.js re-gated on data-fx/data-fine; base.html loads gate outside scripts block; test_f2_capability_gate.py 14 tests) | score: F2 — to self 3,3,n/a,3,3,n/a,3,3 (READY-FOR-AUDIT); suite 518→532 | evidence: E2 (pytest mirror + Node execution of computeFx, 10/10 cases incl. boundaries; harness gotcha: Node's read-only global navigator) | gates: start — check 0 issues, makemigrations no changes, 518 passed; MID-RUN RED — 12 failed (multi-line {#…#} template comment leak, known run-4 bug class, root cause in NOTES/F2.md); end — check 0 issues, makemigrations no changes, 532 passed | decisions: D-LOOP-16a fx-gate.js single decision point (only JS allowed to mention prefers-reduced-motion); D-LOOP-16b fail-closed both ways (JS blocked → no attrs → no effects; gate missing → "none"); D-LOOP-16c bento shape-shift rich+fine only, no instant-promote under none | FOR THE NEXT RUN: AUDITOR — audit F2 (re-run gates, grade from scratch, lower score wins); after auditing, BUILDER takes F1 (token-integrity ratchet, priority 15, unblocked) | blockers: none

Run 15 | PLANNER | 2026-11-05 08:52 +03:00 | items: plan-only — created RUBRIC.md, PROTOCOL.md, SCORECARD.md (17 seed items + Q1-Q4, binary checks + proving-test specs), LOCKS.md; reconciled old backlog cadence | score: n/a (all items seeded TODO, self-score —) | evidence: E1 (docs) | gates: start — check 0 issues, makemigrations no changes, 518 passed; end — identical (plan-only, re-run after doc writes) | decisions: D-LOOP-15a design-loop runbook is the operative protocol, old "r15=P2-3" next-slice superseded (P2-3 stays queued in BACKLOG.md, revisit at r20 retrospective); D-LOOP-15b OWNER_NEEDS 5-line rule applies to lines loop runs add (existing A1-A8 table grandfathered); D-LOOP-15c run numbering follows STATE.md — last run was r14, so this is r15 (cron note said r13, STATE wins) | FOR THE NEXT RUN: BUILDER — build F2 (capability gate fx-gate.js + test_f2_capability_gate.py) first, then F1 (token integrity ratchet test) — together they unblock 7 of 17 items | blockers: none

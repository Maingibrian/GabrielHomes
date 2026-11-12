"""r68 — owner round twelve: the EVEN palm field + parallax on listings.

Owner ask: "the listings page palms need to be spread out evenly to
look less bushy in some areas than others and maximise the parallax
effect they give out."

Two moves, both CSS/asset-only (the band markup is untouched —
test_r65_owner_remodel.test_listings_band_markup_unchanged_additive_only
still stands):

1. EVEN TILE — static/img/palm-field-even.svg (generator seed 868,
   scripts/r68_palm_field_even.py). Measured against the r46 tile it
   replaces: sand-composited per-cell wash coverage 4.6%–6.6% (1.43×
   spread) versus the r46 hand-tuned tile's 1.2%–9.9% (8.06×). The
   evenness here is pinned STRUCTURALLY: one frond base per cell of
   the 5×5 grid, checkerboard layers, golden-angle aim — a future
   regeneration that clumps again fails these pins.

2. PARALLAX — r69 (owner round thirteen, second pass): "the palms
   are stagnant they need to move ...but not to slow they look
   stagnant and not to fast they move together with the listings."
   The r68 fixed-attachment pin (speed 0 — stagnant, and ignored by
   iOS/Android anyway) is gone; motion.js now advances the field at
   HALF the scroll rate. Fail-closed: scripts blocked
   (no attribute) and fx=none (prefers-reduced-motion, WCAG 2.3.3)
   never write the var — the 0px fallback scrolls the tile exactly
   like r65.

   r70 (owner round fourteen): "when the listing animation occurs
   the parallax effect drops down and up." Measured 12s per-frame
   trace: the r69 chase stepped a fixed fraction PER FRAME while the
   row glide + image decode collapse the frame rate 59->10-12fps, so
   the field sank 180-230px behind and kept drifting 600-800ms after
   every scroll stop. The chase is now a TIME-CONSTANT exponential
   (1 - exp(-dt/TAU)) — same ~200ms settle at any frame rate — with
   live measure() per frame and a clamped dt; the rows' images gained
   decoding="async" to keep decode off the main thread. Pinned here.

   r71 (owner round fifteen): "ensure the movements are smooth." A
   compositor-transform drift (translate3d + will-change on the
   ::before) was built, proven pixel-identical in-band — and then
   REJECTED on live evidence: Chrome hoists the composited
   ROOT-NEGATIVE layer over the static footer (the footer vanished
   behind the field) and the extended masked box leaked faint fronds
   below the band. The r62 paint contract wins; the drift stays on
   background-position (repaint cost measured at a FLAT 59fps in the
   r70 trace). The rejection is PINNED — transform/will-change on
   the ::before is banned by test — so it can't be retried blind.

Home keeps the r46 tile — pinned here so the "spread them out" ask
can never leak into the home market section unnoticed.
"""
import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EVEN_SVG = (REPO / "static" / "img" / "palm-field-even.svg").read_text()
OLD_SVG = (REPO / "static" / "img" / "palm-field.svg").read_text()
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text()
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text()
MOTION_JS = (REPO / "static" / "js" / "motion.js").read_text()
GRID_HTML = (REPO / "templates" / "listings" / "_results_grid.html").read_text()

W, H = 1400.0, 1600.0
GRID = 5
FROND_LEN = 520.0
CENTROID = (0.48, -0.55)   # local ink centroid, units of L·scale


def _placements():
    """Reconstruct (centroid_x, centroid_y, scale, layer) per frond.

    The SVG only stores BASE points (wrapped copies at ±W/±H), but the
    generator anchors each frond's ink CENTROID on its cell centre and
    pushes the base the opposite way — so the base can sit in a
    neighbouring cell or outside the tile entirely. Inverting the
    offset (rotation and scale parse straight out of the transform)
    recovers the cell centres, which is what the evenness grid is
    built on. Wrapped copies collapse: they differ only by whole-tile
    offsets, so normalising x/y into [0, W) × [0, H) and de-duplicating
    leaves exactly one entry per placement.
    """
    seen = {}
    for layer, wash in (("back", "#e7d9cd"), ("front", "#dcc6b8")):
        block = EVEN_SVG.split(f'<g fill="{wash}">', 1)[1].split("</g>", 1)[0]
        for m in re.finditer(
            r"translate\((-?\d+),(-?\d+)\) rotate\(([-\d.]+)\) "
            r"scale\(([\d.]+)\)",
            block,
        ):
            x, y = float(m[1]) % W, float(m[2]) % H
            rot, s = float(m[3]), float(m[4])
            key = (round(x, 1), round(y, 1))
            if key in seen:
                continue
            a = math.radians(rot)
            cxd = CENTROID[0] * FROND_LEN * s
            cyd = CENTROID[1] * FROND_LEN * s
            # the centroid is periodic with the tile: a frond pushed
            # across an edge carries its ink into the neighbouring tile
            # period, so the reconstruction mods into [0, W) × [0, H)
            # exactly like the generator's cell centres
            cx = (x + cxd * math.cos(a) - cyd * math.sin(a)) % W
            cy = (y + cxd * math.sin(a) + cyd * math.cos(a)) % H
            seen[key] = (cx, cy, s, layer)
    return list(seen.values())


# ---------------------------------------------------------------------------
# 1. The even tile — even by construction
# ---------------------------------------------------------------------------
def test_even_tile_dimensions_and_washes():
    """Same canvas and the same two clay washes as the r46 lineage —
    the evenness is placement, not a new palette."""
    assert 'width="1400" height="1600"' in EVEN_SVG
    assert 'viewBox="0 0 1400 1600"' in EVEN_SVG
    for wash in ("#e7d9cd", "#dcc6b8"):
        assert wash in EVEN_SVG, f"wash {wash} missing"
    # no third colour sneaks in (token discipline, D-LOOP-38a in css)
    assert set(re.findall(r"#[0-9a-fA-F]{6}", EVEN_SVG)) == {
        "#e7d9cd", "#dcc6b8"}


def _cells():
    """(row, col, layer) of the cell each frond's CENTROID lands in."""
    return [
        (int(cy // (H / GRID)), int(cx // (W / GRID)), layer)
        for cx, cy, _s, layer in _placements()
    ]


def test_even_tile_one_centroid_per_grid_cell():
    """THE evenness pin: 25 fronds, exactly one ink centroid inside
    every cell of the 5×5 grid. The r46 clump (8.06× per-cell coverage
    spread) came from hand-tuned bases drifting together; one centroid
    per cell makes clumping structurally impossible."""
    placements = _placements()
    assert len(placements) == GRID * GRID, (
        f"expected {GRID * GRID} placements, found {len(placements)}"
    )
    cells = {(row, col) for row, col, _layer in _cells()}
    assert len(cells) == GRID * GRID, (
        f"only {len(cells)}/{GRID * GRID} grid cells hold a frond "
        "centroid — the field can clump again"
    )


def test_even_tile_layers_checkerboard_front_never_adjacent():
    """The stronger 26% front wash is the 'bushy' read — the generator
    checkerboards it, so no two front fronds share a grid edge."""
    fronts = [(row, col) for row, col, layer in _cells()
              if layer == "front"]
    assert len(fronts) == 12, "5×5 checkerboard carries 12 front fronds"
    for c1 in fronts:
        for c2 in fronts:
            if c1 != c2:
                dr, dc = abs(c1[0] - c2[0]), abs(c1[1] - c2[1])
                assert (dr, dc) not in {(0, 1), (1, 0)}, (
                    f"front fronds adjacent at {c1}/{c2} — the strong "
                    "wash clumps"
                )


def test_even_tile_scales_stay_in_the_tuned_band():
    """Back 0.66–0.82 (faint, fills), front 0.60–0.76 (strong,
    punctuates) — the band the seed sweep measured evenest. A scale
    drift re-clumps or over-densifies the field."""
    for _cx, _cy, s, layer in _placements():
        lo, hi = (0.66, 0.82) if layer == "back" else (0.60, 0.76)
        assert lo - 0.005 <= s <= hi + 0.005, (
            f"{layer} scale {s} outside [{lo}, {hi}]"
        )


def test_even_tile_seamless_wrapped_copies_exist():
    """Anything crossing an edge is redrawn at ±W/±H — the wrap pass
    that makes the tile repeat invisibly. No wrapped copies, visible
    seams every 1400/1600px."""
    offs = re.findall(
        r'translate\((-?\d+),(-?\d+)\)',
        EVEN_SVG,
    )
    assert any(float(x) < 0 or float(x) >= W or float(y) < 0
               or float(y) >= H for x, y in offs), (
        "no wrapped copies — the tile would seam when repeated"
    )


def test_even_tile_is_generated_not_hand_edited():
    """The generator and the asset stay in lockstep: re-running the
    script must reproduce the shipped file byte-for-byte (deterministic
    seed 868). A hand-edited SVG would drift from the lineage."""
    import subprocess
    import sys
    gen = REPO / "scripts" / "r68_palm_field_even.py"
    out = subprocess.run(
        [sys.executable, str(gen)], capture_output=True, text=True,
        cwd=REPO, timeout=60,
    )
    assert out.returncode == 0, out.stderr
    regenerated = (REPO / "static" / "img" / "palm-field-even.svg").read_text()
    assert regenerated == EVEN_SVG, (
        "the shipped tile differs from the generator output — regenerate "
        "or update both together"
    )


# ---------------------------------------------------------------------------
# 2. The parallax — r69 pass: HALF-SPEED drift, not the stagnant pin
# ---------------------------------------------------------------------------
def test_parallax_field_is_stagnant_not_drifting():
    """r89 (owner round: "the palms in the listings page should be
    stagnant"). The r69-r88 half-speed drift is retired: the band
    field's background-position is frozen at 0 0 — the r85 sticky box
    alone pins the tile to the viewport, so the fronds hold dead
    still beside the scrolling rows. The drift var is gone from the
    CSS entirely (no writer exists in motion.js); fixed attachment
    stays banned (iOS/Android silently kill it, and the sticky box
    is the sanctioned stillness)."""
    assert "background-attachment: fixed" not in SEARCH_CSS, (
        "fixed attachment silently dies on iOS/Android — the sticky "
        "box is the sanctioned stagnation mechanism"
    )
    rule = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
    assert rule, ".listings-band::before rule missing"
    body = re.sub(r"/\*.*?\*/", "", rule.group(0), flags=re.S)
    assert "background-position: 0 0" in body, (
        "the field must be frozen at 0 0 — stagnant per the r89 ask"
    )
    assert "var(--palms-y" not in body, (
        "the drift var is retired with the r69-r88 engine; a frozen "
        "position cannot ride a var nothing writes"
    )
    assert "background-attachment: scroll" in body, (
        "scroll stays the declared safe default"
    )


def test_parallax_js_engine_is_gone_fail_closed():
    """The r89 retirement, JS side: setupPalmParallax no longer exists,
    so no visitor tier gets scroll-linked field motion — not rich, not
    lite, not anything. Stillness is pure CSS (the sticky box), so
    scripts-blocked and fx=none see the identical field by
    construction (D-MOTION-SAFE / D-FX-GATE: there is no motion left
    to gate)."""
    assert "function setupPalmParallax" not in MOTION_JS, (
        "the drift engine must stay deleted — the palms are stagnant "
        "(r89); reintroducing it needs a fresh owner ask"
    )
    assert '"--palms-y"' not in MOTION_JS, (
        "nothing in motion.js may write the retired drift var"
    )
    assert "setupPalmParallax();" not in MOTION_JS, (
        "init() must not arm a drift that does not exist"
    )


# ---------------------------------------------------------------------------
# r89: the drift engine is RETIRED — the chase pins below were the
# r70 contracts for an engine motion.js no longer carries. Their
# history (frame-rate-independent exponential, clamped dt, snap
# threshold) is preserved in LOOP/JOURNAL.md r70/r89 and the motion.js
# r89 comment block, so a future owner ask can rebuild from the
# lesson, not from scratch. The r71 compositor-transform ban below
# STAYS: it guards the ::before regardless of what drives it.
# ---------------------------------------------------------------------------


def test_results_grid_images_decode_async():
    """r70: the row images carry decoding="async" (the listing cards
    already did). During the row glide the browser was decoding a
    burst of listing photos on the main thread — the measured frame
    rate collapsed 59fps -> 10-12fps exactly when the rows animated
    in, which is what exposed the parallax chase lag. Async decode
    keeps that work off the critical path; the width/height pair
    (already present) keeps the layout box reserved so nothing
    shifts either."""
    assert 'decoding="async"' in GRID_HTML, (
        "the results-grid row images must decode off the main thread — "
        "the r70 trace showed decode bursts dipping the frame rate "
        "during the row glide"
    )


def test_parallax_compositor_transform_is_banned():
    """r71 (owner round fifteen): "ensure the movements are smooth."
    A compositor-transform drift was BUILT and measured live — pixel-
    identical to the background-position drift in-band (same-session
    A/B diff 0.012%, and one-tile-period wrap verified seamless) —
    but REJECTED on two live defects no refactor can dodge:

      1. Chrome HOISTS a composited ROOT-NEGATIVE layer over later
         in-flow content: with translate3d + will-change on the
         ::before, the static footer vanished behind the field
         (measured: hiding the ::before revealed the dark footer;
         showing it painted cream fronds across the footer's rows).
         The r62 paint contract (field + sentinels root-negative so
         the footer scrolls over them) only holds while the ::before
         is NOT layerized by a transform.
      2. The extended masked box (the translation needs one tile of
         slack) leaked faint fronds below the band end — the mask's
         out-of-bounds region does not render fully transparent under
         compositing.

    The drift therefore STAYS on background-position: it repaints on
    the main thread, but the r70 trace measured a FLAT 59fps through
    the row animations — smooth, and contract-safe. This pin BANS
    transform/will-change on the ::before so the experiment cannot
    be retried without reading LOOP/JOURNAL.md r71 first."""
    rule = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
    assert rule, ".listings-band::before rule missing"
    # comments are documentation; ban the PROPERTIES, not the words
    body = re.sub(r"/\*.*?\*/", "", rule.group(0), flags=re.S)
    assert "inset: 0" in body, (
        "the ::before must stay exactly the band box — any extension "
        "exists only to feed a transform drift (banned, see r71)"
    )
    for banned in ("translate3d", "will-change", "mask-size",
                   "mask-position", "mask-repeat", "transform:"):
        assert banned not in body, (
            f"'{banned}' on .listings-band::before is the r71 "
            "compositor drift — REJECTED live: Chrome hoists the "
            "composited root-negative layer over the static footer "
            "and the extended masked box leaks below the band "
            "(LOOP/JOURNAL.md r71). The drift belongs on "
            "background-position."
        )


def test_parallax_keeps_the_r65_field_contract():
    """The depth change must not disturb the r65 guardrails: the band
    still is not a stacking context (sentinels paint in the root
    negative layer), the mask still dissolves the last stretch, and
    the tile sizes still match the home grain."""
    base = re.search(r"\.listings-band \{[^}]*\}", SEARCH_CSS).group(0)
    assert "isolation" not in base and "z-index" not in base
    rule = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
    assert "84%" in rule.group(0) and "transparent 100%" in rule.group(0)
    assert "background-size: 1400px 1600px" in rule.group(0)
    finer = re.search(
        r"@media \(max-width: 1020px\) \{[^@]*\.listings-band::before "
        r"\{[^}]*\}",
        SEARCH_CSS,
    )
    assert finer and "860px 985px" in finer.group(0)


# ---------------------------------------------------------------------------
# 3. Home keeps the r46 tile — the ask was listings-only
# ---------------------------------------------------------------------------
def test_home_market_keeps_the_r46_tile():
    """The 'spread them out' round must not leak into the home market
    section: home.css still points at the r46 hand-tuned tile, and the
    r46 asset itself is untouched on disk."""
    m = re.search(r"\.home-market::before \{[^}]*\}", HOME_CSS)
    assert m, ".home-market::before rule missing"
    assert 'url("../img/palm-field.svg")' in m.group(0), (
        "home still carries the original r46 field"
    )
    assert 'palm-field-even' not in HOME_CSS, (
        "the even tile is the listings band's, not home's"
    )
    # the r46 lineage comment survives (test_r46_palm_field pins more)
    assert "seed 46" in OLD_SVG

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
   HALF the scroll rate via --palms-y (lerped for weight). Fail-closed:
   scripts blocked (no attribute) and fx=none (prefers-reduced-motion,
   WCAG 2.3.3) never write the var — the 0px fallback scrolls the
   tile exactly like r65.

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
def test_parallax_half_speed_drift_not_viewport_pinned():
    """r69 (owner round thirteen): "the palms are stagnant they need to
    move ...but not too slow they look stagnant and not too fast they
    move together with the listings." The r68 pass pinned the field to
    the viewport (background-attachment: fixed — speed 0, stagnant; it
    also silently dies on iOS/Android). The band now drifts: the
    ::before's background-position Y rides var(--palms-y, 0px), which
    motion.js advances at half the scroll rate — the field visibly
    climbs while the listings slide past twice as fast. Fixed
    attachment is banned outright so the stagnant pin can't return."""
    assert "background-attachment: fixed" not in SEARCH_CSS, (
        "fixed attachment pins the field to the viewport — stagnant; "
        "the r69 half-speed drift replaces it"
    )
    rule = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
    assert rule, ".listings-band::before rule missing"
    assert "background-position: 0 var(--palms-y, 0px)" in rule.group(0), (
        "the field must ride the drift var, with a 0px fallback for "
        "every visitor the gate excludes"
    )
    assert "background-attachment: scroll" in rule.group(0), (
        "scroll stays the declared safe default (fail-closed)"
    )


def test_parallax_js_half_speed_gated_fail_closed():
    """The drift engine: exactly HALF speed (midway between stagnant 0
    and 1:1 with the listings — the owner's "not too slow / not too
    fast" band), lerped so it carries weight, armed only under a gate
    tier. fx=none and the attribute-less document (scripts blocked)
    never write the var, so the 0px fallback keeps the static field
    (D-MOTION-SAFE, D-FX-GATE: the gate owns reduced motion, no media
    query is re-checked here)."""
    setup = re.search(
        r"function setupPalmParallax\(\) \{(.*?)\n  \}",
        MOTION_JS,
        re.S,
    )
    assert setup, "setupPalmParallax missing from motion.js"
    body = setup.group(1)
    # fail closed: the gate's none/missing decision stops it first
    assert re.search(r"if \(fxNone\) return;", body), (
        "the drift must never run under fx=none or without the gate "
        "attribute (scripts blocked)"
    )
    # exactly half speed: DRIFT 0.5 pattern px per scrolled px
    drift = re.search(r"var DRIFT = ([\d.]+);", body)
    assert drift and abs(float(drift.group(1)) - 0.5) < 1e-9, (
        "the drift rate must stay 0.5 — half speed: visibly moving, "
        "never moving with the listings"
    )
    # it drives the CSS var, never the attachment (the hyphenated word
    # may appear in comments; the JS APIs to set it may not)
    assert '"--palms-y"' in body, "the engine must write --palms-y"
    assert "backgroundAttachment" not in MOTION_JS, (
        "JS must not touch attachment — the drift is a position shift"
    )
    assert 'setProperty("background-attachment' not in MOTION_JS
    # the gate owns reduced motion — no media query is re-checked here
    assert "matchMedia" not in body, "D-FX-GATE: the gate decides, not the setup"
    assert "prefers-reduced-motion" not in body
    # armed from init, like every other setup
    init_block = MOTION_JS.split("function init", 1)[1]
    assert "setupPalmParallax();" in init_block


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

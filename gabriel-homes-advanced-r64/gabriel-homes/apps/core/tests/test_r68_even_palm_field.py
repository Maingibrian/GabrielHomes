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

2. PARALLAX — .listings-band::before opts into
   background-attachment: fixed under html[data-fx="rich"] and
   html[data-fx="lite"] only. Scroll stays the default so scripts
   blocked (no attribute — fails closed), prefers-reduced-motion
   (fx=none, WCAG 2.3.3) and engines that ignore fixed-attachment
   keep the exact r65 look.

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
# 2. The parallax — deepest tier, gated like every other effect
# ---------------------------------------------------------------------------
def _gate_rules():
    """Every rule setting background-attachment on the band."""
    return re.findall(
        r"[^{}]*\.listings-band::before[^{}]*\{[^}]*background-attachment:"
        r"[^;}]*[^{}]*\}",
        SEARCH_CSS,
    )


def test_parallax_fixed_only_for_fx_tiers_that_opted_in():
    gates = re.findall(
        r"(html\[[^\]]*\][^{]*)\{\s*background-attachment: fixed;\s*\}",
        SEARCH_CSS,
    )
    assert gates, "no gated fixed-attachment rule — the parallax vanished"
    selectors = " ".join(gates)
    assert 'data-fx="rich"' in selectors, "rich tier must get the parallax"
    assert 'data-fx="lite"' in selectors, (
        "fixed attachment costs no data — lite keeps it"
    )
    assert 'data-fx="none"' not in selectors, (
        "reduced-motion visitors must NOT get scroll-linked parallax "
        "(WCAG 2.3.3)"
    )


def test_parallax_scroll_default_fails_closed():
    """No attribute (scripts blocked) means no parallax — the D-FX-GATE
    contract: html:not([data-fx]) must never unlock fixed."""
    rule = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
    assert rule, ".listings-band::before rule missing"
    assert "background-attachment: scroll" in rule.group(0), (
        "the safe default must be the scroll attachment"
    )
    # and nothing reopens fixed for the attribute-less document
    for m in re.finditer(
        r"html:not\(\[data-fx\]\)[^{]*\{[^}]*\}", SEARCH_CSS
    ):
        assert "fixed" not in m.group(0), (
            "html:not([data-fx]) must never set fixed — fails closed"
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

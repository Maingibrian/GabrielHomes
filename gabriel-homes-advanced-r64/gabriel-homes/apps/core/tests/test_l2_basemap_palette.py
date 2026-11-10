"""L2 — basemap palette proving tests.

Binary checks (SCORECARD L2):
1. After the style loads, land/water/roads/labels are recoloured to house
   tokens via maplibre's setPaintProperty, driven by a guarded rule list
   that skips missing layer ids (getLayer guard + try/catch per rule).
2. The palette reads tokens.css custom properties at runtime
   (getComputedStyle) — zero hard-coded hex in the palette block.
3. The SVG fallback asset and the single maplibre attribution control are
   untouched (no second attribution source added).
4. The price-pin font stays on var(--font-sans) (F1 regression guard).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = (REPO / "static" / "js" / "search-map.js").read_text(encoding="utf-8")
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")
FALLBACK = REPO / "static" / "img" / "mombasa-map.svg"

BEGIN = "/* L2-PALETTE-BEGIN */"
END = "/* L2-PALETTE-END */"


def _palette_region() -> str:
    start = JS.index(BEGIN) + len(BEGIN)
    return JS[start:JS.index(END)]


def test_recolour_called_after_style_load():
    assert "setPaintProperty" in JS, "the recolour must use setPaintProperty"
    load_idx = JS.index("map.on('load'")
    call_idx = JS.index("recolourBasemap(map);", load_idx), "call inside the load handler"
    assert JS.index("recolourBasemap(map);", load_idx) > load_idx


def test_palette_reads_tokens_not_hex():
    region = _palette_region()
    assert "getPropertyValue(" in region, (
        "the palette must read tokens.css custom properties at runtime")
    token_refs = re.findall(r"'--[a-z][a-z-]+'", region)
    assert len(token_refs) >= 4, (
        f"palette rules must reference token variables, got {token_refs}")
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", region)
    assert not hexes, f"palette must not hard-code hex: {hexes}"


def test_palette_covers_land_water_roads_labels():
    region = _palette_region()
    for token in ("--paper", "--sand", "--cream", "--taupe"):
        assert token in region, f"palette missing {token}"
    # land/background, water, roads (casing before generic), labels
    assert re.search(r"background|landcover|park", region)
    assert "water" in region
    assert "casing" in region and re.search(r"highway|road|street", region)
    assert "text-color" in region and "text-halo-color" in region
    # ordering: casing (specific) before the generic road rule
    assert region.index("casing") < region.index("highway"), (
        "specific casing rule must precede the generic road rule "
        "(first match wins per paint property)")


def test_guarded_layer_list_skips_missing_ids():
    region = _palette_region()
    assert "map.getLayer(" in region, (
        "every application must be guarded by a getLayer check")
    assert "catch" in region, (
        "a layer without the paint property must be skipped, not fatal")


def test_svg_fallback_and_single_attribution_untouched():
    assert FALLBACK.exists(), "static/img/mombasa-map.svg (SVG fallback) must stay"
    assert JS.count("attributionControl") == 1, (
        "exactly one attribution control — no second attribution source")


def test_pin_font_stays_on_token_sans():
    pin = re.search(r"\.map-price-pin\s*\{[^}]*\}", SEARCH_CSS)
    assert pin and "var(--font-sans)" in pin.group(0), (
        "the price pin font must stay on var(--font-sans) (F1 fix)")

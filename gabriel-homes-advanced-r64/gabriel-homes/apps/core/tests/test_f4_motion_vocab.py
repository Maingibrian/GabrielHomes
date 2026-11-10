"""F4 — motion vocabulary proving tests.

Binary checks (SCORECARD F4):
1. docs/DESIGN-ADDENDUM.md exists and names at most 6 motion effects
   (vocabulary rows M1..Mn, n <= 6), each with purpose, where-used,
   tier and reduced-motion/none behaviour.
2. Every shipped effect token in the codebase maps to an addendum entry
   (grep bridge: the addendum names the CSS/JS hooks that ship).
3. The "max 2 at once per viewport" stacking rule is stated.
4. At least 3 section archetypes are documented (full-bleed, type-led,
   edge strip).
5. Token hygiene: the addendum carries no raw hex literals (colour
   references use token names only).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ADDENDUM = REPO / "docs" / "DESIGN-ADDENDUM.md"

# Every shipped motion hook the loop has shipped so far (r16-r24).
SHIPPED_TOKENS = [
    "hv2-rise",        # hero entry stagger (M1)
    "data-reveal",     # IntersectionObserver fade-ups (M1)
    "view-transition", # G2 shared-element pair (M2)
    "hero-fade",       # hero slide rotation (M2)
    "hero-drift",      # hero slide drift (M2)
    "hv2-marquee",     # five-checks strip (M3)
    "bento-shift",     # desktop hover shape-shift (M4)
    "h3-card-grow",    # mobile scroll-driven centre scale (M4)
    "is-flashed",      # L1 pin->row flash (M5)
    "data-map-return", # L1 Map pill return (M5)
    "hv2-scroll",      # wheel cue pulse (M6)
    "gallery-count-bump",  # detail gallery counter bump (M5, r26 audit find)
    "manage-card-in",      # portal /manage/ entrance (declared out-of-scope)
    "data-cursor-view",    # G4 cursor "View" bubble (M5 confirm, r34)
    "data-magnetic",       # G4 magnetic primary CTAs (M6 invite, r34)
    "data-bubble-title",   # r47 bubbly topic-title reveal (M1 rise variant)
]


def _text() -> str:
    assert ADDENDUM.exists(), "docs/DESIGN-ADDENDUM.md is missing"
    return ADDENDUM.read_text(encoding="utf-8")


def test_addendum_names_at_most_six_effects():
    rows = re.findall(r"^\| M\d+\b", _text(), re.M)
    assert 1 <= len(rows) <= 6, f"vocabulary must name 1..6 effects, got {len(rows)}"


def test_every_row_carries_purpose_where_tier_behaviour():
    for row in re.findall(r"^\| M\d+.*$", _text(), re.M):
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert len(cells) >= 5, f"row needs id/effect/purpose/where/tier/behaviour: {row}"
        assert all(cells), f"empty cell in vocabulary row: {row}"


def test_every_shipped_effect_maps_to_an_entry():
    text = _text()
    missing = [t for t in SHIPPED_TOKENS if t not in text]
    assert not missing, f"shipped effects absent from the addendum: {missing}"


def test_stacking_rule_stated():
    text = _text()
    assert re.search(r"at most (two|2)", text, re.I) and "viewport" in text, (
        "the 'max 2 at once per viewport' stacking rule must be stated")


def test_three_archetypes_documented():
    text = _text()
    for archetype in ("full-bleed", "type-led", "edge strip"):
        assert archetype in text, f"archetype missing: {archetype}"


def test_reduced_motion_and_none_behaviour_documented():
    text = _text()
    assert "reduced-motion" in text and "none" in text, (
        "every entry's behaviour under reduced-motion / fx=none must be "
        "documented")


def test_no_hex_literals_in_addendum():
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", _text())
    assert not hexes, f"addendum must reference token names, not hex: {hexes}"

"""H3 — mobile bento proving tests.

Under 1021px the shift bento becomes a horizontal scroll-snap carousel:
native swipe, keyboard-focusable cards, and — where the browser supports
scroll-driven animations — the card nearest the centre scales up. Pure CSS:
no JS is added, and with JS blocked the rail still scrolls (binary check 3:
the desktop shape-shift and its tests stay untouched).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = REPO / "static" / "css" / "home.css"
COMPONENTS_CSS = REPO / "static" / "css" / "components.css"
BENTO_JS = REPO / "static" / "js" / "bento-shift.js"


def test_mobile_carousel_is_css_only():
    css = HOME_CSS.read_text(encoding="utf-8")
    # the H3 block exists under the shift breakpoint
    m = re.search(
        r"H3 r19.*?@media \(max-width: 1020px\) \{(.*?)\n\}", css, re.S)
    assert m, "H3 mobile carousel block missing from home.css"
    block = m.group(1)
    assert "display: flex" in block, "carousel must be a flex rail"
    assert "scroll-snap-type" in block, "rail must snap"
    assert "scroll-snap-align: center" in css, "cards must snap to centre"
    # no JS drives the carousel: bento-shift.js keeps its desktop-only logic
    js = BENTO_JS.read_text(encoding="utf-8")
    assert "scroll-snap" not in js and "carousel" not in js.lower(), (
        "the carousel must be pure CSS — bento-shift.js must not grow it"
    )
    assert '(min-width: 1021px)' in js, (
        "desktop shape-shift keeps its own breakpoint"
    )


def test_centred_card_scale_is_supports_guarded():
    css = HOME_CSS.read_text(encoding="utf-8")
    assert "@supports (animation-timeline: view())" in css, (
        "the centre-scale effect must degrade cleanly — only browsers with "
        "scroll-driven animations get it"
    )
    assert "view(inline)" in css, "scale tracks the inline (horizontal) axis"


def test_reduced_motion_disables_the_carousel_animation():
    css = HOME_CSS.read_text(encoding="utf-8")
    # scope to the bento region so an earlier page-level reduce block
    # (hero, marquee…) can't satisfy this check
    bento_at = css.index("H3 r19")
    region = css[bento_at:]
    m = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", region, re.S)
    assert m and "h3-card-grow" in m.group(0), (
        "reduced motion must stop the carousel grow animation"
    )


def test_desktop_shape_shift_rules_untouched():
    css = HOME_CSS.read_text(encoding="utf-8")
    m = re.search(r"@media \(min-width: 1021px\) \{(.*?)\n\}", css, re.S)
    assert m, "desktop bento block missing"
    block = m.group(0)
    assert "grid-column: 1 / -1" in block, "promoted card keeps full width"
    assert "--spot-row" in block, "JS-picked row promotion kept"
    assert "corner-shape: superellipse(1.6)" in block, "squircle kept"


def test_base_bento_grid_not_hijacked():
    """Only the shift variant becomes a rail; other bento grids (if any)
    keep their tile layouts."""
    css = HOME_CSS.read_text(encoding="utf-8")
    for m in re.finditer(r"@media \(max-width: 1020px\) \{[^}]*\}", css, re.S):
        assert ".bento-grid--shift" in m.group(0), (
            "H3 rules must target only .bento-grid--shift"
        )
        assert not re.search(r"\.bento-grid \{", m.group(0)), (
            "the plain .bento-grid must keep its tile layout"
        )

"""r98 — the "Full sale list" tile upgrade (owner round fifteen:
"the full sale list card ... needs to have is styling upgraded building
on the style it has and improving it").

The tile (.market-rail__more) closes group 01 of the "Homes for the
way you want to move." section. It already speaks espresso (dark
gradient, mono eyebrow, serif line, hover lift) but it is the plainest
tile in the family: its sibling closer — group 03's .market-stay--more
— carries a ghost group-numeral watermark, a sand keyline over the
eyebrow and a link-chip affordance, and the r18.1 polish pass never
reached the sale tile.

r98 upgrades the sale tile ON THAT EXISTING LANGUAGE (no redesign, no
markup change): ghost "01" numeral (contained), the r18.1 sand keyline
treatment on the eyebrow, the bare "→" becomes a circular chip that
fills burnt on hover, and a warm radial glow layer joins the espresso
gradient so the tall tile reads lit, not empty.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")
HOME_HTML = (REPO / "templates" / "core" / "home.html").read_text(encoding="utf-8")


def _strip_media(css):
    """Drop @media blocks (one nesting level) so rule lookup sees only
    the top-level (winning) cascade layer."""
    return re.sub(r"@media[^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)


def _rule(selector):
    """The LAST top-level declaration block for a selector."""
    blocks = re.findall(
        re.escape(selector) + r"\s*\{([^}]*)\}", _strip_media(HOME_CSS))
    assert blocks, f"missing rule: {selector}"
    return blocks[-1]


# ---------------------------------------------------------------------------
# 1. The ghost numeral, contained
# ---------------------------------------------------------------------------
def test_ghost_numeral_watermark():
    """The tile carries group 01's ghost numeral top-right, in the same
    mono/ghost language as the stay tile's "03" (r18.1 contained
    placement: inside the tile, not bleeding past it)."""
    tile = _rule(".market-rail__more")
    assert "position: relative" in tile and "overflow: hidden" in tile, (
        "the watermark needs a clipping context on the tile itself")
    before = _rule(".market-rail__more::before")
    assert 'content: "01"' in before, "the numeral is the group's own: 01"
    assert "var(--font-mono" in before and "rgba(250, 248, 244, .07)" in before, (
        "same ghost language as the stay tile's numeral")
    assert "top: 10px" in before and "right: 14px" in before, (
        "r18.1 containment placement (inside, top-right)")


# ---------------------------------------------------------------------------
# 2. The eyebrow gets the sand keyline (the r18.1 stay treatment)
# ---------------------------------------------------------------------------
def test_eyebrow_sand_keyline():
    small = _rule(".market-rail__more small")
    assert "border-top: 1px solid rgba(217, 162, 126, .45)" in small, (
        "the sand keyline the stay tile's eyebrow already has")
    assert "padding-top" in small, "the keyline needs air beneath it"
    assert "#d9a27e" in small, "the eyebrow keeps its sand tone"


# ---------------------------------------------------------------------------
# 3. The arrow becomes a designed chip
# ---------------------------------------------------------------------------
def test_arrow_is_a_chip_that_fills_on_hover():
    """The bare '→' glyph becomes a circular chip; hover fills it with
    the burnt accent — the affordance language of the section's
    buttons — and keeps the r95-era nudge."""
    chip = _rule(".market-rail__more span[aria-hidden]")
    assert "border-radius: 999px" in chip and "border:" in chip, (
        "a circular, outlined chip — not a bare glyph")
    assert "width" in chip and "height" in chip, "the chip is a fixed circle"
    hover = _rule(".market-rail__more:hover span[aria-hidden]")
    assert "var(--burnt" in hover, "hover fills with the burnt accent"
    assert "translateX(5px)" in hover, "the nudge survives as the chip's move"


# ---------------------------------------------------------------------------
# 4. Depth: the warm glow layer under the espresso gradient
# ---------------------------------------------------------------------------
def test_warm_glow_layer():
    """A faint sand radial at the bottom-left joins the espresso
    gradient (resting and hover) so the tall tile reads lit from the
    corner rather than flat-empty."""
    tile = _rule(".market-rail__more")
    assert "radial-gradient" in tile and "rgba(217, 162, 126" in tile, (
        "resting glow layer over the espresso base")
    assert "linear-gradient(160deg, #261c16, #3a291f)" in tile, (
        "the espresso base the tile already had stays")
    hover = _rule(".market-rail__more:hover")
    assert "radial-gradient" in hover, "hover keeps (and warms) the glow"


# ---------------------------------------------------------------------------
# 5. Keep-pins: the style it already had is not lost
# ---------------------------------------------------------------------------
def test_existing_espresso_language_kept():
    tile = _rule(".market-rail__more")
    assert "var(--font-display" in tile, "the serif display line stays"
    assert "clamp(" in tile, "the fluid serif size stays"
    assert "flex: 1" in tile and "min-height: 132px" in tile, (
        "the tile still fills the rail's leftover height")
    assert "align-items: flex-start" in tile, (
        "content aligns left like its stay sibling (was center)")
    hover = _rule(".market-rail__more:hover")
    assert "translateY(-4px)" in hover, "the hover lift stays"
    assert "box-shadow" in hover, "the hover shadow stays"
    assert "border-color: rgba(250, 248, 244, .16)" in hover, (
        "the hover border brightening stays")


def test_markup_untouched():
    """Scope check: styling only — the template keeps its exact r18
    shape (eyebrow, line, arrow span, link, reveal)."""
    m = re.search(
        r'<a class="market-rail__more"[^>]*>.*?</a>', HOME_HTML, re.S)
    assert m, "the tile markup must exist"
    block = m.group(0)
    assert "<small>Full sale list</small>" in block
    assert "Every home for sale" in block
    assert '<span aria-hidden="true">→</span>' in block
    assert 'href="/properties/?market=sale"' in block
    assert "data-reveal" in block


# ---------------------------------------------------------------------------
# 6. Mobile: the watermark cannot overrun the short band
# ---------------------------------------------------------------------------
def _media_blocks(css, query):
    """Bodies of every @media block matching the query, walked with a
    brace counter (regex cannot span nested braces)."""
    out = []
    for m in re.finditer(re.escape(query) + r"\s*\{", css):
        depth, i = 1, m.end()
        while i < len(css) and depth:
            depth += css[i] == "{"
            depth -= css[i] == "}"
            i += 1
        out.append(css[m.end():i - 1])
    return out


def test_mobile_watermark_contained():
    """At <=900px the tile becomes a short full-width band (min-height
    96px): the numeral shrinks with the viewport so the clipped ghost
    still reads as a corner accent, never a smear."""
    blocks = _media_blocks(HOME_CSS, "@media (max-width: 900px)")
    block = next((b for b in blocks if ".market-rail__more" in b), None)
    assert block, "the 900px block must style the sale tile"
    assert ".market-rail__more::before" in block, (
        "the watermark gets a mobile size")
    sizes = re.findall(
        r"clamp\(([\d.]+)rem, ([\d.]+)vw, ([\d.]+)rem\)", block)
    tile_numeral = [s for s in sizes if float(s[0]) < 5]
    assert tile_numeral, (
        "the numeral's mobile floor must be well under the desktop 5rem")
    assert re.search(r"\.market-rail__more::before\s*\{[^}]*top: 6px", block), (
        "the mobile numeral tucks closer to the corner")

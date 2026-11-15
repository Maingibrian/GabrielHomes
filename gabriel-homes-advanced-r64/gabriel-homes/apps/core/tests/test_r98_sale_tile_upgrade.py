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

r99 (owner round sixteen: "the card is well styled but not that
great") elevates the same tile from detailed to premium, still
CSS-only and markup-untouched: resting presence (ambient shadow +
inset hairline ring + grain weave over the espresso), a diagonal
sheen sweep on hover, the ghost numeral drifting alive, a glow ring
joining the chip fill, the keyline brightening, and a larger serif
cap so the tall tile's line carries its weight.
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
    # SUPERSEDED r100 (VLM polish pass): resting alpha .45 -> .55 and
    # the rule spans the full measure (align-self: stretch) — the r98
    # stub read as leftover decoration. The sand tone + air remain.
    assert "border-top: 1px solid rgba(217, 162, 126, .55)" in small, (
        "the sand keyline (r100: alpha .55, full measure)")
    assert "align-self: stretch" in small, (
        "r100: the keyline spans the tile's content measure")
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


# ===========================================================================
# r99 — owner round sixteen: "the card is well styled but not that great".
# The r98 detailing was correct but the tile read flat next to its
# photographed siblings: no resting shadow, a static light, a dead
# surface. These pins hold the elevation pass.
# ===========================================================================

def test_resting_presence():
    """Every sibling card in the section casts a resting shadow; the
    tile now does too (r98 shipped none). Plus the r95 bento treatment:
    an inset hairline ring so the dark surface has an edge to catch
    light, and a faint grain weave so the espresso reads material."""
    tile = _rule(".market-rail__more")
    assert "box-shadow" in tile and "rgba(28, 21, 17" in tile, (
        "ambient espresso-tinted resting shadow")
    assert "inset" in tile, "the inner hairline ring (r95 bento language)"
    grain = _rule(".market-rail__more::after")
    assert "repeating-linear-gradient" in grain, "the grain weave layer"
    assert "pointer-events: none" in grain, "the weave never eats clicks"
    assert grain.count("position: absolute") == 1, (
        "the weave is pinned inside the tile (clipped by its overflow)")


def test_hover_sheen_sweep():
    """A diagonal sheen band sweeps across the tile on hover — the
    classic premium-card cue. It lives on the existing ::after grain
    element (no markup), as a transform-only overlay band so the sweep
    animates without repaint; the grain stays as the resting surface."""
    grain = _rule(".market-rail__more::after")
    assert "linear-gradient" in grain and "115deg" in grain, (
        "a diagonal sheen band on the tile's own pseudo")
    assert "scaleX(" in grain, (
        "the band ships pre-scaled flat, ready for a transform-only sweep")
    hover = _rule(".market-rail__more:hover::after")
    assert "scaleX(" in hover and "translateX(" in hover, (
        "hover sweeps the band across by transform alone")
    assert "transition" in grain, "the sweep eases"
    for rule in (grain, hover):
        assert "rotate(" not in rule, "no rotation — band stays diagonal"


def test_numeral_gains_life():
    """The ghost numeral is the tile's signature; on hover it drifts
    up-and-out (transform-only, clipped by the tile's overflow:hidden
    so it reads as dissolving past the corner) and gains a whisper of
    warmth. A transition joins it so the drift eases."""
    before = _rule(".market-rail__more::before")
    assert "transition" in before, "the numeral's drift eases"
    hover = _rule(".market-rail__more:hover::before")
    assert "translate(" in hover and "-1" in hover, (
        "hover sends the numeral drifting up/out")
    assert "rgba(250, 248, 244" in hover and ".12" in hover, (
        "the ghost warms a step (from .07) while it drifts")


def test_chip_gains_a_glow_ring():
    """Hover on the chip now pairs the burnt fill with a soft outer
    glow ring — the tile's own mini sunrise — and the fill keeps the
    r98 nudge."""
    hover = _rule(".market-rail__more:hover span[aria-hidden]")
    assert "box-shadow" in hover and "0 0" in hover, (
        "a soft outer glow joins the fill")
    assert "var(--burnt" in hover, "the burnt fill stays"
    assert "translateX(5px)" in hover, "the nudge stays"


def test_keyline_and_weight():
    """On hover the sand keyline brightens (its rgba alpha steps up)
    and the serif line gets a larger cap (1.5rem -> 1.65rem) so the
    tall tile's promise carries its weight."""
    hover = _rule(".market-rail__more:hover small")
    assert "rgba(217, 162, 126" in hover and ".45" not in hover, (
        "the keyline brightens on hover")
    tile = _rule(".market-rail__more")
    assert "clamp(1.2rem, 1.7vw, 1.65rem)" in tile, (
        "the serif cap grows to carry the tall tile")


def test_elevation_is_fx_safe():
    """Everything r99 adds must be static-safe: under fx=none (and
    reduced motion via the site-wide gate) the tile keeps its resting
    presence — shadow, ring, grain — and simply does not animate.
    Nothing may rely on animation to be visible."""
    tile = _rule(".market-rail__more")
    assert "animation" not in tile, "no keyframe dependencies on the tile"
    grain = _rule(".market-rail__more::after")
    assert "animation" not in grain, "the sheen is hover-only, never looping"
    before = _rule(".market-rail__more::before")
    assert "animation" not in before, "the numeral drifts only on hover"


def test_hover_lifts_survive_the_reveal_system():
    """DEFECT (found live in r99 verification): the site-wide reveal
    rule `html.motion-ready [data-reveal].is-visible` (0,3,1) pins
    transform: translateY(0) and out-specifies every revealed card's
    :hover lift (0,2,0) — under motion-ready the home page's market
    cards + nearby cards never actually lift (verified identity in the
    live DOM while hovered). Each card needs an override that starts
    with html.motion-ready (>= 0,4,1) and carries its own lift amount."""
    lifts = {
        ".market-feature": "-4px",
        ".market-banner": "-4px",
        ".market-rail__card": "-3px",
        ".market-stay": "-5px",
        ".market-rail__more": "-4px",
    }
    for sel, lift in lifts.items():
        override = re.findall(
            r"(html\.motion-ready\s+" + re.escape(sel)
            + r"\.is-visible:hover)\s*\{([^}]*)\}", _strip_media(HOME_CSS))
        assert override, (
            f"missing reveal-proof hover override for {sel}")
        body = override[-1][1]
        assert f"translateY({lift})" in body, (
            f"{sel} override must carry its own lift {lift}")
    # nearby-card's hover lifts its img (not itself) — the override
    # must carry that same translateY(-5px) on the img.
    nearby = re.findall(
        r"html\.motion-ready\s+\.nearby-card\.is-visible:hover\s+img\s*\{([^}]*)\}",
        _strip_media(HOME_CSS))
    assert nearby and "translateY(-5px)" in nearby[-1], (
        "missing reveal-proof hover override for .nearby-card img")

"""r95 — reel execution + bento presentation polish (owner round twelve).

The owner reviewed the r94 reels and cards live and asked for four
things, pinned here RED-first:

1. INFINITE REEL — "that carousel should be infinite, it currently
   ends". r94 shipped only one set of three frames per reel while the
   keyframe translated a full loop height, so the window visibly
   emptied and snapped. r95 duplicates the set in markup (A B C A B C)
   and the translate must equal exactly one set height so the loop is
   seamless.

2. BLUR BEFORE AND AFTER — the reel edges must dissolve through a
   blurred strip, not a bare linear mask.

3. RECTANGULAR FRAMES — "the images should not be square but
   rectangular". The 180×173px near-square frames become landscape
   3/2 rectangles.

4. BENTO PRESENTATION — "the cards should have a better presentation
   of the style": a resting shadow, a hover lift (FLIP-safe: the
   `translate` property, never `transform` — bento-shift.js owns
   transform), the bed/bath facts as glass chips, a stronger price,
   a quieter index, and a hairline ring for definition.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")
HOME_HTML = (REPO / "templates" / "core" / "home.html").read_text(encoding="utf-8")
COMPONENTS_CSS = (REPO / "static" / "css" / "components.css").read_text(
    encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Infinite reel
# ---------------------------------------------------------------------------
def _reel_block(html):
    """Each flank-reel block's inner HTML from the template."""
    return re.findall(
        r'<div class="flank-reel__film">(.*?)</div>', html, re.S)


def test_reel_frames_duplicated_for_infinite_loop():
    """Six frames per reel: the set appears twice so the rise can wrap
    seamlessly (r94 shipped three — the reel 'ended')."""
    for block in _reel_block(HOME_HTML):
        n = block.count("flank-reel__frame")
        assert n == 6, f"reel must carry 6 frames (set x2), found {n}"


def test_reel_translate_covers_exactly_one_set():
    """The loop distance = one SET (3 frames + their gaps). With the set
    duplicated underneath, frame 1 re-appears where frame 4 was — the
    wrap is invisible. CSS vars so the frame height and the keyframe
    can never drift apart again."""
    assert "--reel-frame-h" in HOME_CSS, (
        "frame height must live in a custom property")
    assert "--reel-set-h" in HOME_CSS, (
        "the loop distance must live in a custom property")
    # the set height is defined as exactly 3 frames + 3 gaps
    m = re.search(r"--reel-set-h:\s*([^;]+);", HOME_CSS)
    assert m, "--reel-set-h must be defined"
    assert "3" in m.group(1), "the set is three frames (plus their gaps)"
    # and the keyframe uses the var — no hardcoded drift possible
    kf = HOME_CSS[HOME_CSS.index("@keyframes r94-reel-rise"):]
    kf = kf[:kf.index("\n}") + 2]
    assert "var(--reel-set-h)" in kf, (
        "the rise must translate exactly var(--reel-set-h)")
    assert re.search(r"translateY\(calc\(-1 \* var\(--reel-set-h\)\)\)", kf), (
        "the rise must move UP by one set height")


def test_reel_window_shows_three_frames():
    """The window height equals 3 frames + 2 gaps — three on screen."""
    m = re.search(r"\.flank-reel\s*\{[^}]*\}", HOME_CSS)
    assert m and "var(--reel-frame-h)" in m.group(0), (
        "the window height must be derived from the frame height")


# ---------------------------------------------------------------------------
# 2. Blur dissolve at the edges
# ---------------------------------------------------------------------------
def test_reel_edges_blur_before_and_after():
    """Blur strips at both ends of the reel window."""
    assert "flank-reel__blur" in HOME_HTML, (
        "the blur strip markup must exist in the template")
    assert "backdrop-filter" in HOME_CSS and "flank-reel__blur" in HOME_CSS, (
        "the blur strips must backdrop-blur whatever passes beneath")
    # one strip pinned to the top, one to the bottom
    assert re.search(r"\.flank-reel__blur--top", HOME_CSS)
    assert re.search(r"\.flank-reel__blur--bottom", HOME_CSS)


# ---------------------------------------------------------------------------
# 3. Rectangular frames
# ---------------------------------------------------------------------------
def test_reel_frames_are_landscape_rectangles():
    """Frames are 3/2 landscape rectangles, not squares. The height
    DERIVES from the reel width (x 2/3) — stronger than aspect-ratio
    because the same var feeds the loop math, so the rectangle and the
    seamless loop can never drift apart (caught live in r95: aspect-ratio
    rendered 120px while the loop var assumed 136px)."""
    m = re.search(r"\.flank-reel__frame\s*\{[^}]*\}", HOME_CSS)
    assert m, "frame rule missing"
    assert "height: var(--reel-frame-h)" in m.group(0), (
        "frame height must come from --reel-frame-h")
    d = re.search(r"--reel-frame-h:\s*calc\(var\(--reel-w\) \* 2 / 3\)",
                  HOME_CSS)
    assert d, "the frame height must be derived as 2/3 of the reel width"
    # and the shipped markup carries matching intrinsic dimensions
    for tag in re.findall(r"<img[^>]*flank-reel__frame[^>]*>", HOME_HTML):
        w = int(re.search(r'width="(\d+)"', tag).group(1))
        h = int(re.search(r'height="(\d+)"', tag).group(1))
        assert w / h == 3 / 2, f"markup dimensions must be 3/2, got {w}x{h}"


# ---------------------------------------------------------------------------
# 4. Bento presentation polish
# ---------------------------------------------------------------------------
def test_bento_cards_have_resting_shadow_and_ring():
    """A quiet resting elevation + hairline ring so cards read as
    objects, not cut-outs."""
    region = HOME_CSS[HOME_CSS.index("3c. Homes bento"):]
    assert "box-shadow" in region, "resting shadow missing"
    assert "box-shadow: none" not in region, "shadow must not be disabled"
    assert "outline:" in region or "outline " in region, (
        "hairline ring missing")


def test_bento_hover_lift_is_flip_safe():
    """The hover lift uses the `translate` property — bento-shift.js
    animates `transform` for the FLIP move, so the two can never
    clobber each other. Scoped to the r95 LIFT rule itself (the only
    rule that hovers the .bento-card--home card directly; the older
    r44 drawer rules hover INNER elements and legitimately use
    transform on them)."""
    region = HOME_CSS[HOME_CSS.index("r95 — bento presentation polish"):]
    lift = re.findall(
        r"\.bento-grid--shift[^{]*\.bento-card--home:hover[^{]*\{[^}]*\}",
        region)
    assert lift, "a hover lift rule must exist for the shift cards"
    joined = "\n".join(lift)
    assert "translate: 0 -4px" in joined, (
        "the lift must use the `translate` property (FLIP-safe)")
    assert "transform:" not in joined, (
        "the lift must NOT touch `transform` (bento-shift.js owns it)")


def test_bento_facts_are_glass_chips():
    """Bed/bath facts render as glass chips (they were plain text with
    a middot separator)."""
    # exact selector + body (not ::before), and it must set the chip
    m = re.search(r"\.bento-card__fact\s*\{[^}]*\}", HOME_CSS)
    assert m, "the fact chip rule must exist"
    rule = m.group(0)
    assert "backdrop-filter" in rule, "chips must be glassy"
    assert "border-radius" in rule
    # the middot ::before separator is retired for facts (chips separate
    # themselves); the location keeps its middot
    loc = re.search(r"\.bento-card__loc::before,\s*\.bento-card__fact::before",
                    HOME_CSS)
    assert not loc, (
        "the fact must drop out of the shared middot ::before rule")
    # and the location keeps ITS middot
    assert re.search(r"\.bento-card__loc::before\s*\{", HOME_CSS), (
        "the location keeps its middot separator")


def test_bento_price_emphasis_and_quieter_index():
    """The price stands up (bigger, brighter), the index eyebrow
    recedes (smaller, dimmer)."""
    price = re.search(r"\.bento-card--home[^{]*__price\s*\{[^}]*\}", HOME_CSS)
    assert price, "price rule missing"
    assert "font-size" in price.group(0), "price must be re-sized"
    idx = re.search(r"\.bento-card--home[^{]*__index\s*\{[^}]*\}", HOME_CSS)
    assert idx, "index rule missing"
    assert ("opacity" in idx.group(0) or "color-mix" in idx.group(0)), (
        "index must be visually quieter")

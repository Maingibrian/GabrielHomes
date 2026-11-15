"""r94 — front-page motion, owner round eleven.

Four asks, all pinned here RED-first:

1. PALMS STAGNANT — the owner wants the palm sentinels on the front
   page to stand still ("make the palm leaves svg just stagnant").
   The r62 wind sway (palm-sway/palm-flutter keyframes and every
   animation on them) must be gone from search.css. The trees
   themselves, their sticky placement and the fx gate stay.

2. MOBILE BENTO SCROLL DRIFT — on the phone the bento is a horizontal
   swipe rail and the cards start off-screen ("those cards go off
   screen and one has to scroll to see them"). Scrolling the PAGE
   down must move the cards left (a scroll-driven horizontal drift),
   while the native swipe rail keeps working as the fallback.

3. FLANK WORDS ALIVE IN PLACE — "the gabriels homes part next to the
   bento should be animated... not moving up or down but just have
   animated motion". The old bento-flank.js translated the words
   vertically; that goes. The words get an in-place CSS animation
   (letter-spacing / weight "breathing"), gated on the fx gate, and
   bento-flank.js becomes unnecessary on the page.

4. GUTTER IMAGE REELS — the white space below "gabriel" and above
   "homes" gets a vertical carousel: three images visible at a time,
   moving upwards, decorative only.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")
HOME_HTML = (REPO / "templates" / "core" / "home.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Palms stand still
# ---------------------------------------------------------------------------
def test_palm_wind_sway_removed():
    """No sway/flutter keyframes or animations on the palms any more."""
    assert "@keyframes palm-sway" not in SEARCH_CSS, (
        "the r62 sway keyframe must be gone — the owner wants the palms "
        "stagnant")
    assert "@keyframes palm-flutter" not in SEARCH_CSS
    # no animation of any kind may target the palm tree parts
    for sel in (".palm-tree", ".palm-frond--mid", ".palm-frond--front"):
        for m in re.finditer(re.escape(sel) + r"\s*\{[^}]*\}", SEARCH_CSS):
            assert "animation" not in m.group(0), (
                f"{sel} must not carry an animation")


def test_palm_placement_kept():
    """The trees themselves stay: sticky sentinels, gated visibility."""
    assert ".palm-sentinel" in SEARCH_CSS
    assert "position: sticky" in SEARCH_CSS
    assert "palm-sentinel--left" in SEARCH_CSS
    assert "palm-sentinel--right" in SEARCH_CSS


# ---------------------------------------------------------------------------
# 2. Mobile bento: page scroll drifts the rail leftwards
# ---------------------------------------------------------------------------
def test_mobile_bento_scroll_drift_present():
    """A scroll-driven horizontal drift exists for the phone rail."""
    assert "h3-rail-drift" in HOME_CSS, (
        "the scroll-driven rail drift keyframe must exist")
    assert "animation-timeline: scroll()" in HOME_CSS, (
        "the drift must be driven by the page scroll timeline")


def test_mobile_bento_drift_is_supports_gated():
    """Browsers without scroll-driven animations keep the plain rail."""
    assert re.search(
        r"@supports \(animation-timeline: scroll\(\)\)",
        HOME_CSS), "drift must sit behind a @supports guard"


def test_mobile_bento_drift_reduced_motion_safe():
    """prefers-reduced-motion stops the drift (rail still swipes)."""
    bento_at = HOME_CSS.index("h3-rail-drift")
    region = HOME_CSS[bento_at:]
    m = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", region, re.S)
    assert m, "a reduce block must follow the drift rules"


def test_mobile_bento_rail_still_snaps():
    """The native swipe rail is untouched as the fallback."""
    m = re.search(
        r"H3 r19.*?@media \(max-width: 1020px\) \{(.*?)\n\}", HOME_CSS, re.S)
    assert m
    assert "scroll-snap-type" in m.group(1)


# ---------------------------------------------------------------------------
# 3. Flank words: alive in place (no vertical travel)
# ---------------------------------------------------------------------------
def test_flank_words_have_inplace_animation():
    """An in-place CSS animation exists for the flank words."""
    assert "r94-flank-breathe" in HOME_CSS, (
        "the in-place flank animation keyframe must exist")


def test_flank_words_animation_gated():
    """The breathing runs only under the rich fx gate."""
    assert re.search(
        r'html\[data-fx="rich"\][^{]*\.bento-flank__word[^{]*\{[^}]*r94-flank-breathe',
        HOME_CSS), "the flank animation must be gated on data-fx=rich"


def test_flank_words_no_vertical_travel():
    """No keyframe may translate the words along Y any more."""
    for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
                         HOME_CSS):
        name, body = m.group(1), m.group(2)
        if "flank" in name:
            assert not re.search(r"translate[XYd]*\(", body), (
                f"{name} must not translate the words")


def test_flank_parallax_script_gone():
    """The vertical parallax script is retired from the page (no script
    tag loads it any more)."""
    assert '<script src="{% staticv \'js/bento-flank.js\' %}"' not in HOME_HTML, (
        "bento-flank.js (vertical word travel) must no longer load")


# ---------------------------------------------------------------------------
# 4. Gutter reels: vertical image carousels in the flanks
# ---------------------------------------------------------------------------
def test_gutter_reels_in_template():
    """Each flank carries a reel of images (3 visible, decorative)."""
    assert 'class="flank-reel"' in HOME_HTML or "flank-reel" in HOME_HTML, (
        "the flank reel markup must exist in home.html")
    assert HOME_HTML.count("flank-reel__frame") >= 6, (
        "two reels x three visible frames minimum")


def test_gutter_reel_images_have_dimensions():
    """Every reel <img> carries width/height (F3 CLS rule)."""
    reel_at = HOME_HTML.find("flank-reel")
    region = HOME_HTML[reel_at:]
    for m in re.finditer(r"<img[^>]*>", region[:6000]):
        tag = m.group(0)
        assert "width=" in tag and "height=" in tag, (
            f"reel img missing dimensions: {tag}")


def test_gutter_reels_move_upwards_gated():
    """The reel rises (upward translate) under the rich gate only."""
    assert "r94-reel-rise" in HOME_CSS, "the reel rise keyframe must exist"
    assert re.search(
        r'html\[data-fx="rich"\][^{]*flank-reel__film[^{]*\{[^}]*r94-reel-rise',
        HOME_CSS), "reel motion must be gated on data-fx=rich"
    # moving UP means the film translates to negative Y (scan the
    # whole keyframe block text, not a per-frame regex — calc() math
    # makes per-frame matching brittle)
    kf = HOME_CSS[HOME_CSS.index("@keyframes r94-reel-rise"):]
    kf = kf[:kf.index("\n}") + 2]
    assert re.search(r"translateY\((?:calc\()?-", kf), (
        "the reel must move upwards (negative Y)")


def test_gutter_reels_only_desktop():
    """The reels only exist where the flanks do (>=1440px)."""
    assert re.search(
        r"\.flank-reel\s*\{[^}]*display:\s*none", HOME_CSS), (
        "reels must be display:none in the mobile-first base rule")

"""H2 — hero proving tests (a-slice r24, b-slice r33).

The a-slice covers the structural binary checks of H2:
  1. one gesture — the search pill is the hero's only CTA;
  2. the search pill keeps the Buy/Rent segment;
  3. the LCP image is preloaded in <head>;
  4. no stats filler row (every stat would have to resolve from
     BrandSettings, which has no stat fields — see D-LOOP-24a);
  5. mobile hero defects from the owner's 390px screenshots are fixed:
     marquee edge fade, scroll cue hidden on touch, card radius sane,
     segment no longer a full-width cream band.

The b-slice (r33, D-LOOP-33a) covers the motion binary checks:
  6. split-text mask headline — motion.js word-splits the h1 into
     overflow-hidden masks (DOM APIs, em accent preserved), the h1's own
     hv2-rise is removed on hand-over, fxNone skips the split entirely
     (plain visible h1 — D-MOTION-SAFE), and the mask animates
     transform-only under html.motion-ready;
  7. hero-loop.mp4 loads only under fx=rich && !Save-Data (D-LOOP-21a):
     hidden + preload=none + poster in the template, motion.js flips it
     live and crossfades it over the slides via .hero__bg.is-video.
"""
import re
from pathlib import Path

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = REPO / "static" / "css" / "home.css"
COMPONENTS_CSS = REPO / "static" / "css" / "components.css"
HOME_HTML = REPO / "templates" / "core" / "home.html"
MOTION_JS = REPO / "static" / "js" / "motion.js"


def _body():
    return Client().get("/").content.decode()


def test_hero_has_one_gesture_and_no_stats_row():
    """The hero section holds exactly one form (the search pill), no
    button-styled CTA links, and no stats markup."""
    body = _body()
    hero = body.split('class="hero"', 1)[1].split("</section>", 1)[0]
    assert hero.count("<form") == 1, "hero must carry exactly one gesture"
    assert "btn--" not in hero, "no competing CTA buttons inside the hero"
    assert "stat__number" not in hero and "hero__stats" not in hero


def test_search_pill_keeps_buy_rent_segment():
    body = _body()
    assert 'data-segment="sale"' in body
    assert 'data-segment="rent"' in body
    assert 'id="hero-search-form"' in body


def test_lcp_image_is_preloaded_in_head():
    head = _body().split("</head>", 1)[0]
    m = re.search(
        r'<link rel="preload" as="image" href="([^"]+)"[^>]*'
        r'fetchpriority="high"', head)
    assert m, "hero LCP image must be preloaded with high priority"
    assert "hero-slide-1" in m.group(1)


def test_marquee_has_edge_fade_mask():
    """The five-checks ticker must dissolve at the edges (mask), not be
    sliced mid-word — owner mobile screenshot defect. Colour keywords
    only, so the F1 hex ratchet is untouched."""
    css = HOME_CSS.read_text(encoding="utf-8")
    rule = re.search(r"\.hv2-marquee \{(.*?)\}", css, re.S)
    assert rule, ".hv2-marquee rule missing"
    body = rule.group(1)
    assert "mask-image: linear-gradient" in body
    assert "-webkit-mask-image" in body
    assert "transparent" in body
    # the fade is expressed with colour keywords — the F1 hex ratchet
    # (global count may only go down) is guarded by test_f1_token_integrity


def test_scroll_cue_hidden_on_touch_and_small_screens():
    css = HOME_CSS.read_text(encoding="utf-8")
    m = re.search(
        r"@media \(max-width: 809px\), \(hover: none\) \{(.*?)\}",
        css, re.S)
    assert m, "touch/small-screen media block missing"
    assert ".hv2-scroll" in m.group(1) and "display: none" in m.group(1)


def test_search_card_uses_card_radius_on_mobile():
    """Below 810px the stacked card is tall; the 100px pill radius clamps
    into a blob. The mobile block must switch to --radius-card and shrink
    the Buy/Rent segment to its buttons."""
    css = COMPONENTS_CSS.read_text(encoding="utf-8")
    blocks = re.findall(
        r"@media \(max-width: 809px\) \{(.*?)\n\}", css, re.S)
    assert blocks, "no max-width: 809px blocks in components.css"
    ok = any(
        "border-radius: var(--radius-card)" in b
        and ".search-bar__segment { justify-self: start; }" in b
        for b in blocks)
    assert ok, (
        "mobile search-card block must set --radius-card and shrink the "
        "segment (owner mobile screenshot defects)")


def test_hero_slides_and_preload_still_static_faded():
    """The slideshow structure survives the a-slice untouched (video and
    split-text arrive with H2.b under the fx gate)."""
    html = HOME_HTML.read_text(encoding="utf-8")
    assert html.count('class="hero__slide"') == 4
    assert "hero-slide-1.webp" in html


# ---------------------------------------------------------------------------
# H2.b — split-text mask headline (r33, D-LOOP-33a)
# ---------------------------------------------------------------------------
def test_split_text_mask_headline_contract():
    html = HOME_HTML.read_text(encoding="utf-8")
    js = MOTION_JS.read_text(encoding="utf-8")
    css = HOME_CSS.read_text(encoding="utf-8")
    # The template only marks the h1; the words are built by JS.
    assert "data-hero-headline" in html
    assert "hero__w" not in html, "word spans must be JS-built, not templated"
    assert 'class="hero__title" data-hero-headline' in html or \
        re.search(r'class="hero__title[^"]*"[^>]*data-hero-headline', html)
    # motion.js splits via DOM APIs (no innerHTML), preserves the em,
    # removes the h1's own hv2-rise on hand-over, and skips under fxNone.
    assert "setupHeroHeadline" in js
    fn = js[js.index("function setupHeroHeadline"):
            js.index("function setupHeroVideo")]
    assert "innerHTML" not in fn, "word spans must use DOM APIs, not innerHTML"
    assert 'createElement("span")' in fn and 'className = "hero__w-in"' in fn
    assert 'fxNone) return' in fn, "fx=none must keep the h1 plain (D-MOTION-SAFE)"
    assert 'classList.remove("hv2-rise")' in fn, \
        "the mask animation must be the sole owner of the h1 entrance"
    assert "--d" in fn, "words need a stagger index"
    # CSS: masks scope under html.motion-ready, animate transform only,
    # keep descenders readable, and die under reduced-motion.
    assert re.search(r"html\.motion-ready \.hero__w\s*\{[^}]*overflow:\s*hidden", css, re.S)
    assert re.search(r"html\.motion-ready \.hero__w-in\s*\{[^}]*animation:\s*hero-mask-rise", css, re.S)
    kf = re.search(r"@keyframes hero-mask-rise\s*\{(.*?)\n\}", css, re.S)
    assert kf, "hero-mask-rise keyframes missing"
    props = set(re.findall(r"([a-z-]+)\s*:", kf.group(1)))
    assert props <= {"transform"}, f"mask keyframes animate non-transform props: {props}"
    assert "112%" in kf.group(1), "the mask must rise from fully below the mask"
    assert re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{[^@]*\.hero__w-in[^{]*\{[^}]*animation:\s*none", css, re.S)


def test_headline_text_survives_the_split():
    """Rendering splits nothing server-side: the served h1 still carries
    the exact BrandSettings words (JS splits client-side only)."""
    html = Client().get("/").content.decode()
    m = re.search(r'<h1 class="hero__title[^"]*"[^>]*>(.*?)</h1>', html, re.S)
    assert m, "hero h1 missing"
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    assert text, "h1 must keep its words"
    assert "<em" in m.group(1), "the accent em must survive"


# ---------------------------------------------------------------------------
# H2.b — hero video under fx=rich && !Save-Data (D-LOOP-21a)
# ---------------------------------------------------------------------------
def test_hero_video_gated_and_progressive():
    html = HOME_HTML.read_text(encoding="utf-8")
    js = MOTION_JS.read_text(encoding="utf-8")
    css = HOME_CSS.read_text(encoding="utf-8")
    m = re.search(r'<video[^>]*data-hero-video[^>]*>', html)
    assert m, "hero video tag missing"
    tag = m.group(0)
    assert "hidden" in tag, "video must ship hidden (no load without the gate)"
    assert 'preload="none"' in tag, "preload=none is the second belt"
    assert "muted" in tag and "loop" in tag and "playsinline" in tag
    assert "hero-poster.jpg" in tag, "poster required (F3/D-LOOP-21a)"
    assert "hero-loop.mp4" in tag
    # motion.js: rich AND !Save-Data only; anything else leaves it hidden.
    fn = js[js.index("function setupHeroVideo"):js.index("function init")]
    assert 'getAttribute("data-fx") === "rich"' in fn
    assert "saveData" in fn
    assert "hidden = false" in fn and 'classList.add("is-video")' in fn
    # CSS: the flip crossfades the loop over the slides.
    assert re.search(r"\.hero__bg\.is-video \.hero__video\s*\{[^}]*opacity:\s*1", css)
    assert re.search(r"\.hero__bg\.is-video \.hero__slide\s*\{[^}]*opacity:\s*0", css)

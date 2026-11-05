"""H2.a — hero structure slice (r24, D-LOOP-20b order: a then b).

The a-slice covers the structural binary checks of H2:
  1. one gesture — the search pill is the hero's only CTA;
  2. the search pill keeps the Buy/Rent segment;
  3. the LCP image is preloaded in <head>;
  4. no stats filler row (every stat would have to resolve from
     BrandSettings, which has no stat fields — see D-LOOP-24a);
  5. mobile hero defects from the owner's 390px screenshots are fixed:
     marquee edge fade, scroll cue hidden on touch, card radius sane,
     segment no longer a full-width cream band.

H2.b (split-text mask headline, video under fx=rich) ships in a later
run and extends this file.
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

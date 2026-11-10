"""r64 — owner round twelve: the wordmark returns + vision critic pass.

The owner asked for two things: bring the giant "Homes" footer
wordmark BACK (removed in r63), and run a vision critic over the About
page. The critic pass surfaced eight verified defects (every claim was
measured or pixel-checked before fixing — the VLM misread several,
including input/button heights that were already identical):

1. CTA band: near-white photo patches (luma 240) behind the RIGHT half
   of the centered "Homes worth crossing town for." headline — cream
   text vanished in spots. Shared band: home/contact fixed too.
2. The restored wordmark had only 8px of air below before KENYA.
3. The newsletter heading inherited the footer body colour
   (cream at 80%) and read muted next to the full-cream FAQ heading.
4. The founder quote ended on a two-word orphan ("that feeling.").
5. The quote band kicker orphaned "OURSELVES." alone on line two.
6. The what-we-look-for hairlines stopped 85px short of the story
   paragraphs' measure (54ch vs 62ch).
7. The bento strip left 180px of dead photo per side of the container.
8. The FAQ grid stopped 285px short of the container's right edge.
"""
import re
from pathlib import Path

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
PAGES_CSS = (REPO / "static" / "css" / "pages.css").read_text()
COMPONENTS_CSS = (REPO / "static" / "css" / "components.css").read_text()
FOOTER = (REPO / "templates" / "includes" / "_footer.html").read_text()


def _page(path):
    return Client().get(path).content.decode()


# ---------------------------------------------------------------------------
# 0. The wordmark is back (owner's explicit ask)
# ---------------------------------------------------------------------------
def test_wordmark_is_back_in_the_footer():
    assert 'class="wordmark wordmark--footer"' in FOOTER
    assert FOOTER.count('class="wordmark__letter"') == 5
    # and its styles survived the round trip
    for sel in (r"\.wordmark \{", r"\.wordmark--footer \{",
                r"\.wordmark__letter \{", r"\.wordmark__letter:hover \{"):
        assert re.search(sel, COMPONENTS_CSS), f"{sel} must exist"


# ---------------------------------------------------------------------------
# 1. CTA band — text-zone protection over the photo
# ---------------------------------------------------------------------------
def test_cta_band_shadows_the_text_zone():
    rule = re.search(r"\.cta \{.*?\n\}", COMPONENTS_CSS, re.S)
    assert rule, "the .cta rule must exist"
    css = rule.group(0)
    # the radial rides first (top layer) over the text zone
    radial = re.search(r"radial-gradient\([^)]*\)", css)
    assert radial and "50% 44%" in radial.group(0), (
        "a centred radial must shadow the headline/button zone"
    )
    assert css.index("radial-gradient") < css.index("linear-gradient"), (
        "the radial must layer ABOVE the linear scrim"
    )
    # the linear mid stays at the r55-pinned 0.60 (test_r53 pins it
    # <= 0.62 — the owner wants the photo to read, not mud); the
    # radial carries the text-zone protection on its own.
    assert "rgba(42,33,28,0.60) 50%" in css


# ---------------------------------------------------------------------------
# 2. Wordmark breathing room
# ---------------------------------------------------------------------------
def test_wordmark_row_gives_the_signature_air():
    rule = re.search(r"\.site-footer__wordmark-row \{[^}]*\}", COMPONENTS_CSS)
    assert rule
    assert "gap: 1.25rem" in rule.group(0), (
        "0.5rem jammed KENYA against the 9rem baseline (8px measured)"
    )


# ---------------------------------------------------------------------------
# 3. Newsletter heading — full cream like the FAQ heading
# ---------------------------------------------------------------------------
def test_newsletter_heading_is_full_cream():
    rule = re.search(
        r"\.site-footer__newsletter \.featured__title \{[^}]*\}",
        COMPONENTS_CSS,
    )
    assert rule and "var(--cream)" in rule.group(0), (
        "it inherited cream-at-80% body colour and read muted/disabled"
    )


# ---------------------------------------------------------------------------
# 4 + 5. Orphan lines — balanced, copy untouched
# ---------------------------------------------------------------------------
def test_quote_and_kicker_balance_their_rags():
    quote = re.search(r"\.about-founder__quote \{[^}]*\}", PAGES_CSS)
    assert quote and "text-wrap: balance" in quote.group(0), (
        "the quote ended on the two-word orphan 'that feeling.'"
    )
    kicker = re.search(r"\.about-quote__kicker \{[^}]*\}", PAGES_CSS)
    assert kicker and "text-wrap: balance" in kicker.group(0), (
        "'OURSELVES.' sat alone on line two of the caps kicker"
    )


# ---------------------------------------------------------------------------
# 6. Taste list measure matches the story copy
# ---------------------------------------------------------------------------
def test_taste_list_matches_the_story_measure():
    rule = re.search(r"\.about-story__taste \{[^}]*\}", PAGES_CSS)
    assert rule and "max-width: 62ch" in rule.group(0), (
        "54ch hairlines stopped 85px short of the 62ch paragraphs' rag"
    )


# ---------------------------------------------------------------------------
# 7. Bento owns the band — r66 (owner round): the strip left the page
#    ("remove the carousel... the background and images are shaded").
#    The pin now guards the removal, not the geometry.
# ---------------------------------------------------------------------------
def test_bento_strip_left_the_band():
    assert ".cta__proof-strip" not in PAGES_CSS, (
        "the shaded photo strip's CSS must stay gone with its markup"
    )
    assert ".about-tile" not in PAGES_CSS, "no orphaned tile rules"


# ---------------------------------------------------------------------------
# 8. FAQ grid closes flush with the container edge
# ---------------------------------------------------------------------------
def test_faq_grid_fills_the_footer_row():
    rule = re.search(r"\.footer-faq__list \{[^}]*\}", COMPONENTS_CSS)
    assert rule
    assert "max-width" not in rule.group(0), (
        "the 60rem cap left ~285px of dead dark on the right"
    )

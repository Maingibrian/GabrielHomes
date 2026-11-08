"""r63 — About page redesign (owner round eleven), fix pass.

The first r63 pass shipped the new markup but left five defects that
this file pins so they can never silently return:

1. Bento tiles kept the UA default <figure> margin (1em 40px) — every
   tile was inset 40px per side and the small-tile captions clipped on
   phones. The old filmstrip CSS carried `margin: 0`; the bento rewrite
   forgot it.
2. The facts rail's 4-column rule sat BELOW the r52-era ≤900px 2-column
   rule in the stylesheet, so source order won and phones rendered four
   76px slivers with clipped labels.
3. The founder band went side-by-side at ≤560px (an r52 leftover),
   squeezing the copy into a 212px column. The owner's brief asks for
   stacking on mobile.
4. The founder caption sat ON the offset sand frame line (17px overlap).
5. The footer's new .site-footer__meta-row had no CSS (the wordmark
   rule it replaced was the only styling), and the newsletter form kept
   its stacked desktop layout (owner goal 7: input + button on one
   line, consent smaller underneath).

Also pinned: the FAQ summary chevrons clipping off-screen at 375px
(list-style-position: outside with no room at phone padding).
"""
import re
from pathlib import Path

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
PAGES_CSS = (REPO / "static" / "css" / "pages.css").read_text()
COMPONENTS_CSS = (REPO / "static" / "css" / "components.css").read_text()


def _page(path):
    return Client().get(path).content.decode()


# ---------------------------------------------------------------------------
# 1. Bento tiles — the UA figure margin must be reset
# ---------------------------------------------------------------------------
def test_about_tile_resets_the_ua_figure_margin():
    rule = re.search(r"\.about-tile \{[^}]*\}", PAGES_CSS)
    assert rule, "the .about-tile rule must exist"
    assert re.search(r"margin:\s*0", rule.group(0)), (
        "without margin: 0 the UA default (1em 40px) shrinks every tile "
        "and clips the small-tile captions on phones"
    )


def test_about_tiles_are_real_images_with_dimensions():
    body = _page("/about/")
    cta = body.split('class="section cta"', 1)[1].split("</section>", 1)[0]
    for attr in ("loading=\"lazy\"", "width=\"1200\"", "height=\"800\""):
        assert cta.count(attr) == 3, f"{attr} must be on all three tiles"


# ---------------------------------------------------------------------------
# 2. Facts rail — the 2×2 phone rule must win the cascade
# ---------------------------------------------------------------------------
def test_rail_two_column_rule_comes_after_the_four_column_rule():
    four_col = PAGES_CSS.index("grid-template-columns: repeat(4, minmax(0, 1fr))")
    responsive = re.search(
        r"@media \(max-width: 900px\) \{[^@]*?\.about-founder__rail \{[^}]*"
        r"repeat\(2, minmax\(0, 1fr\)\)",
        PAGES_CSS,
    )
    assert responsive, "a ≤900px 2-column rail rule must exist"
    assert responsive.start() > four_col, (
        "the responsive rule must be declared AFTER the 4-column rule — "
        "equal specificity means source order decides, and phones got "
        "four 76px slivers when the old rule lost"
    )


# ---------------------------------------------------------------------------
# 3. Founder band — phones stack, per the owner's brief
# ---------------------------------------------------------------------------
def test_founder_band_stacks_on_phones():
    # ANY ≤560px block may own the phone layout — scan them all
    blocks = PAGES_CSS.split("@media (max-width: 560px)")[1:]
    founder = None
    for block in blocks:
        m = re.search(r"\.about-founder \{[^}]*\}", block)
        if m:
            founder = m
    assert founder, "a ≤560px .about-founder rule must exist"
    assert "grid-template-columns: 1fr" in founder.group(0), (
        "phones stack (portrait above, copy full width) — the r52 "
        "side-by-side squeezed the copy into a 212px column"
    )
    assert "auto minmax(0, 1fr)" not in founder.group(0), (
        "the old side-by-side track must be gone at phone width"
    )


# ---------------------------------------------------------------------------
# 4. Founder caption — must clear the offset frame line
# ---------------------------------------------------------------------------
def test_founder_caption_clears_the_offset_frame():
    rules = re.findall(r"\.about-founder__caption \{[^}]*\}", PAGES_CSS)
    assert rules, "the caption rule must exist"
    desktop = next((r for r in rules if "font-family" in r), rules[0])
    assert "calc(16px + 1.05rem)" in desktop, (
        "the frame extends 16px below the photo — 0.85rem sat ON the line"
    )
    mobile = next((r for r in rules if "calc(10px" in r), None)
    assert mobile, "the ≤560px caption rule keeps its 10px frame clearance"


# ---------------------------------------------------------------------------
# 5. Footer meta row + newsletter (owner goals 7 + 8)
# ---------------------------------------------------------------------------
def test_footer_meta_row_is_styled():
    rule = re.search(r"\.site-footer__meta-row \{[^}]*\}", COMPONENTS_CSS)
    assert rule, "the meta row needs its own rule (the wordmark row it replaced was the only styling)"
    for prop in ("justify-content: space-between", "flex-wrap: wrap"):
        assert prop in rule.group(0)
    # the dead wordmark styles went with the markup
    assert ".wordmark--footer" not in COMPONENTS_CSS


def test_newsletter_button_shares_the_input_line_on_desktop():
    block = re.search(
        r"@media \(min-width: 561px\) \{.*?\n\}",
        COMPONENTS_CSS,
        re.S,
    )
    assert block, "a ≥561px newsletter layout rule must exist"
    css = block.group(0)
    assert "minmax(0, 1fr) auto" in css, "input takes the line, button follows it"
    assert "grid-column: 2" in css, "the button sits beside the input (owner goal 7)"
    assert "grid-column: 1 / -1" in css, "the label spans the full row"
    consent = re.search(r"\.newsletter-form__consent \{[^}]*\}", COMPONENTS_CSS)
    assert consent and "font-size: 13px" in consent.group(0), (
        "consent is smaller (13px — the r59 readability floor, never below)"
    )


# ---------------------------------------------------------------------------
# 6. FAQ chevrons — room at phone width
# ---------------------------------------------------------------------------
def test_faq_chevrons_get_room_on_phones():
    block = re.search(
        r"@media \(max-width: 560px\) \{[^}]*?\.footer-faq__list summary \{[^}]*\}",
        COMPONENTS_CSS,
    )
    assert block, "a ≤560px FAQ summary rule must exist"
    css = block.group(0)
    assert "list-style-position: inside" in css, (
        "the outside marker clipped off-screen at 375px — padding alone "
        "cannot make room for it; the hanging indent does"
    )
    assert "text-indent: -1.3rem" in css
    assert "padding-left: 1.3rem" in css

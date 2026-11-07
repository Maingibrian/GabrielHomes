"""r53 — About styling round two + phone header diet (owner round five).

Two owner asks drive this revision:

1. "THE NAV BAR IN THE PHONE IS TOO LONG" — at 390px the actions box
   (Enquire + "Menu") overflowed its grid track and wrapped into a
   second row: a 98px bar. Phones now get an icon-only hamburger (the
   word drops; the aria-label keeps the name) plus compact paddings.
2. "THE ABOUT PAGE STILL COULD DESERVE MORE STYLING" — the second
   vision-critique pass found a 90%-cream page with no dark rhythm,
   SaaS-radius value cards, a buried philosophy line, a top-heavy
   founder band with a dead right half, and a muddy closing band.
   Fixes pinned here: the espresso quote band, the de-SaaS'd value
   cards, the three-column founder lockup with its fact rail, the
   CTA proof triptych, and the shared-band scrim rebalance.
"""
import re
from pathlib import Path

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
PAGES_CSS = (REPO / "static" / "css" / "pages.css").read_text()
COMPONENTS_CSS = (REPO / "static" / "css" / "components.css").read_text()
HEADER = (REPO / "templates" / "includes" / "_header.html").read_text()


def _page(path):
    return Client().get(path).content.decode()


# ---------------------------------------------------------------------------
# 1. Phone header — one compact row (was 98px / two rows at 390px)
# ---------------------------------------------------------------------------
def test_header_hamburger_label_is_hideable_span():
    """The "Menu" word lives in its own span so ≤480px can drop it for an
    icon-only button — the aria-label keeps the accessible name."""
    assert '<span class="site-header__hamburger-label">Menu</span>' in HEADER
    assert 'aria-label="Open menu"' in HEADER


def test_phone_header_compact_rules_exist():
    """The ≤480px block must exist and carry the compact pins directly —
    nested braces make block-extraction regexes brittle, so each needle is
    asserted against the stylesheet as a whole."""
    m = re.search(
        r"@media \(max-width: 480px\) \{", COMPONENTS_CSS)
    assert m, "a ≤480px header media block must exist"
    for needle in (
        ".site-header__inner {\n    padding-block: 0.55rem",
        ".site-header__hamburger-label { display: none; }",
        "min-width: 40px",
        "min-height: 40px",
        ".site-header__hamburger {\n    padding: 0.5rem 0.4rem",
    ):
        assert needle in COMPONENTS_CSS, f"compact header rules must pin {needle!r}"


# ---------------------------------------------------------------------------
# 2. About — the philosophy line becomes the mid-point espresso band
# ---------------------------------------------------------------------------
def test_about_quote_band_is_espresso_display_quote():
    body = _page("/about/")
    band = body.split('class="section about-quote"', 1)[1].split("</section>", 1)[0]
    # the blockquote keeps its r52 class inside the new band
    assert 'class="about-story__pull"' in band
    assert "[ THE STANDARD ]" in band
    # the story column no longer carries the pull
    story = body.split('class="about-story__copy"', 1)[1].split("</section>", 1)[0]
    assert "about-story__pull" not in story, "the pull-quote left the story column"
    # the band sits between the story and the values band
    assert body.index("about-quote") < body.index("about-values")
    css = re.search(r"\.about-quote \{[^}]*\}", PAGES_CSS)
    assert css and "var(--espresso)" in css.group(0), "the band is espresso"
    pull_css = re.search(r"\.about-quote \.about-story__pull \{[^}]*\}", PAGES_CSS)
    assert pull_css and "var(--cream)" in pull_css.group(0), "display quote in cream"


# ---------------------------------------------------------------------------
# 3. About — value cards de-SaaS'd (scoped to the about values band)
# ---------------------------------------------------------------------------
def test_about_value_cards_are_restyled_in_scope():
    body = _page("/about/")
    assert 'class="section about-values"' in body
    # articles keep the shared class (r52 regex-safe)
    assert len(re.findall(r'<article class="value-card"', body)) == 3
    scoped = re.search(r"\.about-values \.value-card \{[^}]*\}", PAGES_CSS)
    assert scoped, "the about values band has its own card rules"
    css = scoped.group(0)
    assert "border-top: 3px solid var(--burnt)" in css, "burnt top rule"
    assert "border-radius: var(--radius-card);" in css, "the 40px app radius is gone (house 20px card radius)"


# ---------------------------------------------------------------------------
# 4. About — founder band: caption, bigger quote, mono fact rail
# ---------------------------------------------------------------------------
def test_about_founder_band_carries_caption_and_rail():
    body = _page("/about/")
    assert 'class="about-founder__caption"' in body
    assert "[ FOUNDER — MOMBASA ]" in body
    rail = body.split('class="about-founder__rail"', 1)[1].split("</ul>", 1)[0]
    for fact in ("2026", "Mombasa · Kenya", "Every home walked through"):
        assert fact in rail, f"the rail must state {fact!r}"
    css = re.search(r"\.about-founder \{[^}]*\}", PAGES_CSS)
    assert css, "the .about-founder grid rule must exist"
    assert "minmax(170px, 210px)" in css.group(0), "three-column lockup: rail track"
    assert "align-items: start" in css.group(0), "quote tops out with the portrait"


# ---------------------------------------------------------------------------
# 5. About — closing band proof triptych + shared scrim rebalance
# ---------------------------------------------------------------------------
def test_about_cta_carries_proof_strip():
    body = _page("/about/")
    cta = body.split('class="section cta"', 1)[1].split("</section>", 1)[0]
    assert 'class="cta__proof-strip"' in cta
    # r55: real-08-aerial read as an unfinished construction site (vision
    # pass) — the triptych closes on real-03-bedroom-garden instead.
    imgs = re.findall(r'src="[^"]*real-(\d+)-', cta)
    assert imgs == ["01", "05", "03"], "three real listing photos"
    assert "honest photography" in cta


def test_shared_cta_scrim_is_rebalanced():
    """The vision pass called the old scrim muddy — the middle thins so the
    photo reads warm, while top/bottom deepen for the tag and proof strip."""
    m = re.search(
        r"\.cta \{[^}]*linear-gradient\(180deg,\s*"
        r"rgba\(28,21,17,([\d.]+)\) 0%,\s*rgba\(42,33,28,([\d.]+)\) 50%,\s*"
        r"rgba\(28,21,17,([\d.]+)\) 100%\)",
        COMPONENTS_CSS, re.S)
    assert m, "the shared .cta band must carry the 180deg scrim"
    assert float(m.group(1)) >= 0.85, "top scrim deepened"
    assert float(m.group(2)) <= 0.62, "mid scrim thinned (was 0.68)"
    assert float(m.group(3)) >= 0.90, "bottom scrim deepened (carries the strip)"


# ---------------------------------------------------------------------------
# 6. About — mobile hero clears the fixed header
# ---------------------------------------------------------------------------
def test_about_mobile_hero_clears_the_header():
    m = re.search(
        r"@media \(max-width: 560px\) \{[^@]*\.page-hero \{[^}]*\}",
        PAGES_CSS)
    assert m and "calc(var(--section-pad-y) + 3rem)" in m.group(0), (
        "the phone hero needs real clearance below the fixed header")

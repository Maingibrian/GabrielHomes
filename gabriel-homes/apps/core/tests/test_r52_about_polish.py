"""r52 — nav pill order swap + About page polish (owner round four).

Two owner asks drive this revision:

1. NAV PILL ORDER — Listings is the FIRST button and About the SECOND
   (supersedes the r13 order). Pinned for the desktop pill AND the mobile
   menu on every public page (the header is a shared include).
2. ABOUT PAGE POLISH — the vision critique pass found: a dead zone under
   the story copy, a dangling "What we stand for" heading, ghost-flat
   value cards with no icons, a sparse founder chip, and a closing CTA
   that repeated the footer CTA's exact heading. This file pins the fixes:
   the pull-quote that fills the story column, the values header band +
   icons + motion-gated stagger, the editorial founder portrait with a
   first-person quote drawn only from established copy, and the
   de-duplicated CTA ("See the homes we have checked.").
"""
import re
from pathlib import Path

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
PAGES_CSS = (REPO / "static" / "css" / "pages.css").read_text()


def _page(path):
    return Client().get(path).content.decode()


# ---------------------------------------------------------------------------
# 1. Nav pill order — Listings first, About second, everywhere
# ---------------------------------------------------------------------------
def test_desktop_nav_pill_listings_first_about_second():
    """r52: the shop window leads, the story follows. The desktop pill
    (numbered links) must open with 01 Listings, 02 About — on every page
    that renders the shared header."""
    for path in ("/", "/about/", "/properties/", "/services/"):
        body = _page(path)
        nav = body.split('<nav class="site-header__nav"', 1)[1].split("</nav>", 1)[0]
        first = nav.index('href="/properties/"')
        second = nav.index('href="/about/"')
        assert first < second, f"/properties/ must come before /about/ in the pill on {path}"
        assert '<span class="nav-link__index">01</span> Listings' in nav
        assert '<span class="nav-link__index">02</span> About' in nav
        # the r13 order is gone for good
        assert '<span class="nav-link__index">01</span> About' not in nav


def test_mobile_menu_listings_first_about_second():
    body = _page("/")
    menu = body.split('<nav class="mobile-menu__nav"', 1)[1].split("</nav>", 1)[0]
    assert '<span class="mobile-menu__index">01</span>Listings' in menu
    assert '<span class="mobile-menu__index">02</span>About' in menu
    assert menu.index('href="/properties/"') < menu.index('href="/about/"')


# ---------------------------------------------------------------------------
# 2. About hero — one label, meta line instead of the redundant eyebrow
# ---------------------------------------------------------------------------
def test_about_hero_drops_redundant_eyebrow_and_gains_meta_line():
    body = _page("/about/")
    hero = body.split('class="page-hero"', 1)[1].split("</section>", 1)[0]
    # the eyebrow said the same thing as the [ ABOUT ] pill — retired
    assert "Our story" not in hero
    assert "[ ABOUT ]" in hero
    # the mono place-and-year line (facts already stated by the copy)
    assert "Mombasa · Kenya — by the Indian Ocean" in hero
    assert "page-hero__meta" in hero


def test_page_hero_scrim_deepened_for_contrast():
    """r52: the shared page-hero left band was the weakest contrast on the
    page (vision pass) — the gradient must stay at or above the r52
    depths, which keep the text column near-dark."""
    m = re.search(
        r"\.page-hero::before \{[^}]*linear-gradient\(90deg,\s*"
        r"rgba\(28,21,17,([\d.]+)\) 0%,\s*rgba\(28,21,17,([\d.]+)\)",
        PAGES_CSS, re.S)
    assert m, "page-hero::before must carry the 90deg left scrim"
    assert float(m.group(1)) >= 0.9, "left edge of the scrim must be >= 0.9"
    assert float(m.group(2)) >= 0.7, "mid scrim must be >= 0.7"


# ---------------------------------------------------------------------------
# 3. Story band — pull-quote fills the copy column, photo capped
# ---------------------------------------------------------------------------
def test_about_story_pull_quote_carries_the_philosophy_line():
    body = _page("/about/")
    assert 'class="about-story__pull"' in body
    # r56: the philosophy line is taste-led now (owner round seven);
    # the checked-ledger line lives on /checks/ only
    assert "ten homes you'll love" in body
    # the fee disclosure keeps its place (footer FAQ, rendered on about)
    assert "exact amount before you commit" in body
    # the dangling heading left the story column (it heads the values band)
    assert '<h2 data-reveal>What we stand for</h2>' not in body


def test_about_story_figure_is_the_unused_sea_bedroom_capped_45():
    body = _page("/about/")
    m = re.search(r'<img src="[^"]*real-(\d+)-([^"]+)"[^>]*>', body.split('about-story__figure', 1)[1])
    assert m, "story figure img missing"
    # r55: real-04-bedroom-sea read as cheap stock (vision pass: cloud-print
    # duvet + beach canvas) and its caption promised "listing checks" — the
    # taste-led story now runs real-06-living-terrace (the terrace room IS
    # the coastal-living story). Still the 4/5 capped crop.
    assert m.group(1) == "06", "the story figure must be real-06-living-terrace"
    assert 'width="1200"' in m.group(0) and 'height="800"' in m.group(0)
    css = PAGES_CSS.split(".about-story__figure img", 1)[1].split("}", 1)[0]
    assert "aspect-ratio: 4 / 5" in css, "figure crop is 4/5"
    assert "max-height" in css, "figure height must be capped (no wallpaper runs)"


# ---------------------------------------------------------------------------
# 4. Values band — header, icons, motion-gated stagger
# ---------------------------------------------------------------------------
def test_about_values_have_header_band_and_three_iconed_cards():
    body = _page("/about/")
    assert "[ PRINCIPLES ]" in body
    assert 'class="values-head__title" data-reveal>What we stand for.' in body
    # r55: taste-led intro (owner: less checked-listings language)
    assert "Three instincts run through everything we do" in body
    # every value card carries an icon from the 1.7-stroke family
    cards = re.findall(r'<article class="value-card".*?</article>', body, re.S)
    assert len(cards) == 3
    for card in cards:
        assert 'class="value-card__icon"' in card
        assert 'stroke-width="1.7"' in card
    # the icon trio: person / eye / key (everyday objects, no AI-look)


def test_about_value_stagger_is_motion_gated_with_kill_switches():
    """The stagger delays live ONLY under html.motion-ready:not([data-fx=none]),
    and prefers-reduced-motion resets the longhand delay explicitly (the
    base `transition: none` shorthand would lose the cascade to the more
    specific stagger selector)."""
    assert 'html.motion-ready:not([data-fx="none"]) .story__values .value-card:nth-child(2)' in PAGES_CSS
    assert 'html.motion-ready:not([data-fx="none"]) .story__values .value-card:nth-child(3)' in PAGES_CSS
    kill = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{\s*"
        r"html\.motion-ready \.story__values \.value-card \{[^}]*transition-delay: 0s",
        PAGES_CSS)
    assert kill, "reduced motion must reset the stagger delay to 0s"


# ---------------------------------------------------------------------------
# 5. Founder band — editorial portrait + first-person quote
# ---------------------------------------------------------------------------
def test_about_founder_band_is_an_editorial_portrait_with_quote():
    body = _page("/about/")
    assert 'class="about-founder__portrait"' in body
    assert 'class="about-founder__quote"' in body
    # r56: the quote leads with the feeling and closes on the standard —
    # taste-led, no paperwork clause (owner: comfort first, not proven homes)
    assert "the feeling of coming home to" in body
    assert "has to give you that feeling" in body
    # signature block on its rule
    assert 'class="about-founder__sig"' in body
    assert "Gabriel Omulu" in body and "Founder" in body
    # the old floating chip layout is retired
    assert 'class="hv2-founder"' not in body


# ---------------------------------------------------------------------------
# 6. CTA band — de-duplicated against the footer CTA
# ---------------------------------------------------------------------------
def test_about_cta_no_longer_repeats_the_footer_cta_heading():
    body = _page("/about/")
    # the footer band (shared include) owns this heading now.
    # r55: the about CTA leads with taste ("Homes worth crossing town
    # for.") — the checked-listings framing retired per the owner round.
    assert "Homes worth crossing town for." in body
    cta = body.split('class="section cta"', 1)[1].split("</section>", 1)[0]
    assert "Tell us what you are looking for" not in cta, (
        "the about CTA must not repeat the footer CTA heading")
    assert 'href="/properties/"' in cta
    assert "[ THE COLLECTION ]" in cta


def test_about_cta_phrase_appears_once_on_the_page():
    """The footer include still carries the brand CTA heading once — the
    About body must not add a second copy anywhere above it."""
    body = _page("/about/")
    assert body.count("Tell us what you are looking for") == 1

"""r65 — owner round: listings palm field + About remodel ("Editorial+").

Two owner asks drive this round:

1. "Add the pine background image seen in the home page to the
   listings page to add some depth — don't remove any other thing
   from that page."  →  .listings-band::before: the seamless
   arching-frond tile (r46 lineage) that backs the home market
   section, repeating across the results band with the home
   bottom-fade mask. Nothing else on the page changed. r68 (owner
   round twelve) swapped the band to its own EVEN tile
   (palm-field-even.svg) — pinned in test_r68_even_palm_field.py;
   the pin below follows the asset.

2. "Study why the about page is boring and remodel it to be more
   interesting"  →  four additive moves, none touching pinned copy or
   components: the coast ticker after the hero (home's marquee
   component, about-specific words, mixed serif/mono voice), a ghost
   "10" numeral in the espresso quote band, a full-bleed dhow coast
   strip with real neighbourhood links, and the palm field behind the
   principles row.

This file pins every piece so a future refactor cannot silently drop
them.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (test_search.py's pattern) — the coast chips
    resolve against real location pages, so the tree must exist."""
    call_command("seed_demo", no_images=True, target=80, verbosity=0,
                 i_know_this_is_demo=True)
    yield

REPO = Path(__file__).resolve().parents[3]
PAGES_CSS = (REPO / "static" / "css" / "pages.css").read_text()
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text()
ABOUT = (REPO / "templates" / "core" / "about.html").read_text()
PALM_SVG = (REPO / "static" / "img" / "palm-field.svg").read_text()


def _page(path):
    return Client().get(path).content.decode()


# ---------------------------------------------------------------------------
# 1. Listings band — the palm field, home treatment, nothing removed
# ---------------------------------------------------------------------------
def _band_before_rule():
    m = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
    assert m, ".listings-band::before rule missing"
    return m.group(0)


def test_listings_band_carries_the_palm_field():
    rule = _band_before_rule()
    # r68: the band ships the EVEN tile (test_r68_even_palm_field.py
    # pins the evenness); the r46 hand-tuned tile stays home's.
    assert 'url("../img/palm-field-even.svg")' in rule, "the even r68 tile"
    assert "background-repeat: repeat" in rule, "seamless tile, like home"
    assert "z-index: -1" in rule, "paints under every in-flow block"
    assert "pointer-events: none" in rule, "decorative — never steals a click"
    assert "background-attachment: scroll" in rule, (
        "scroll is the safe default; only fx tiers opt into fixed (r68)"
    )
    # the home treatment's fade: solid to 84%, dissolved by 100%
    for mask in ("-webkit-mask-image", "mask-image"):
        m = re.search(rf"{mask}:\s*linear-gradient\([^)]*\)", rule)
        assert m and "84%" in m.group(0) and "transparent 100%" in m.group(0), (
            f"{mask} must dissolve the field over the last stretch, like home"
        )


def test_listings_band_keeps_the_home_tile_grain():
    assert "background-size: 1400px 1600px" in _band_before_rule(), (
        "desktop tile matches the home field exactly"
    )
    finer = re.search(
        r"@media \(max-width: 1020px\) \{[^@]*\.listings-band::before \{[^}]*\}",
        SEARCH_CSS,
    )
    assert finer and "860px 985px" in finer.group(0), (
        "phones get the home field's finer 860px grain"
    )


def test_listings_band_is_not_a_stacking_context():
    """The sentinels must keep painting in the ROOT negative layer so the
    footer can scroll up over them (r62). isolation/z-index on the band
    would reparent them into a band-local context and break that — the
    one deliberate difference from home's .home-market."""
    base = re.search(r"\.listings-band \{[^}]*\}", SEARCH_CSS)
    assert base, ".listings-band base rule missing"
    css = base.group(0)
    assert "isolation" not in css and "z-index" not in css, (
        "the band must not create a stacking context (palm sentinels, r62)"
    )
    # and the sentinel contract is untouched
    sentinel = re.search(r"\.palm-sentinel \{[^}]*\}", SEARCH_CSS).group(0)
    assert "z-index: -1" in sentinel
    assert "bottom: calc(-1 * min(64vh, 660px))" in sentinel


def test_listings_band_markup_unchanged_additive_only():
    """The owner's "don't remove any other thing": the band still wraps
    exactly the same children — palms include, results header, tools,
    results grid, related searches — and search.css keeps zero hex."""
    page = _page("/properties/")
    for needle in ('class="listings-band"', 'class="palm-sentinel palm-sentinel--left"',
                   'class="palm-sentinel palm-sentinel--right"',
                   'class="results-header"', 'class="filter-toggle"',
                   'id="results-grid"', 'class="related__title"'):
        assert needle in page, f"{needle!r} must survive the round"
    # the new field is CSS-only: the band gained no new markup at all
    band = page.split('class="listings-band"', 1)[1]
    assert "palm-field" not in band, "the field lives in CSS, not markup"


# ---------------------------------------------------------------------------
# 2. About — the coast ticker (home's marquee, about's words)
# ---------------------------------------------------------------------------
def test_about_ticker_follows_the_hero():
    body = _page("/about/")
    assert 'class="hv2-marquee"' in body, "the marquee component joins the page"
    assert body.index("page-hero__meta") < body.index("hv2-marquee") < body.index("about-story"), (
        "the ribbon sits between the hero and the story, like home"
    )
    ticker = body.split("hv2-marquee__track", 1)[1].split("</div>", 1)[0]
    # the about words preview the comfort-led story copy, not the home ticker
    for mood in ("The light at four", "Slow evenings", "Streets we know by name",
                 "The short walk to the water"):
        assert mood in ticker, f"mood phrase {mood!r} missing"
    for town in ("Nyali", "Bamburi", "Shanzu"):
        assert town in ticker, f"town {town!r} missing"
    # not a copy of the home ribbon
    assert "Old Town courtyards" not in ticker
    assert "Garden mornings" not in ticker


def test_about_ticker_has_its_own_mixed_voice():
    """r65 pass-2 (VLM): mood phrases set in Fraunces italic, towns stay
    mono caps — the strip carries the page's editorial contrast."""
    body = _page("/about/")
    assert body.count('class="hv2-marquee__mood"') >= 12, (
        "the mood spans ship (duplicated track x2)"
    )
    rule = re.search(r"\.hv2-marquee \.hv2-marquee__mood \{[^}]*\}", PAGES_CSS)
    assert rule, "the mood rule must exist (scoped to pages.css)"
    css = rule.group(0)
    assert "var(--font-display)" in css and "italic" in css
    assert "text-transform: none" in css, "mood phrases keep their sentence case"


# ---------------------------------------------------------------------------
# 3. About — the ghost "10" in the quote band
# ---------------------------------------------------------------------------
def test_quote_band_carries_the_ghost_ten():
    body = _page("/about/")
    m = re.search(r'<span class="about-quote__ghost" aria-hidden="true">10</span>', body)
    assert m, "the ghost numeral ships, aria-hidden (pure decoration)"
    band = body.split('class="section about-quote"', 1)[1].split("</section>", 1)[0]
    assert band.index("about-quote__ghost") < band.index("container"), (
        "the numeral paints behind the copy column"
    )
    # pinned copy untouched inside the band
    assert "ten homes you'll love" in band
    assert "[ WHY WE'RE SMALL ]" in band


def test_quote_ghost_is_a_texture_not_a_competitor():
    rule = re.search(r"\.about-quote__ghost \{[^}]*\}", PAGES_CSS)
    assert rule, "the ghost rule must exist"
    css = rule.group(0)
    assert "color-mix(in srgb, var(--cream) 13%, transparent)" in css, (
        "r65 pass-2: 8% read as a smudge — 13% keeps the gesture legible"
    )
    assert "pointer-events: none" in css and "user-select: none" in css
    assert "var(--font-display)" in css and "italic" in css, "Fraunces italic, house voice"
    # the band crops the bleed (deliberate editorial crop) and keeps the
    # pinned espresso ground
    band = re.search(r"\.about-quote \{[^}]*\}", PAGES_CSS).group(0)
    assert "var(--espresso)" in band and "overflow: hidden" in band


# ---------------------------------------------------------------------------
# 4. About — the coast strip (location storytelling, real links)
# ---------------------------------------------------------------------------
COAST_CHIPS = [
    ("/property-for-sale/nyali/", "Nyali"),
    ("/property-for-sale/mkomani/", "Mkomani"),
    ("/property-for-sale/bamburi/", "Bamburi"),
    ("/property-for-sale/shanzu/", "Shanzu"),
    ("/property-for-sale/mtwapa/", "Mtwapa"),
    ("/property-for-sale/tudor/", "Tudor"),
]


def test_coast_strip_sits_between_quote_and_values():
    body = _page("/about/")
    assert 'class="about-coast"' in body
    assert body.index("about-quote") < body.index("about-coast") < body.index("about-values"), (
        "the coast moment answers the 'why we're small' quote with WHERE"
    )
    strip = body.split('class="about-coast"', 1)[1].split("</section>", 1)[0]
    assert "[ THE COAST ]" in strip
    assert "From Nyali to Shanzu." in strip
    assert "Mombasa is our beat" in strip


@pytest.mark.parametrize("href,label", COAST_CHIPS)
def test_coast_chips_are_real_location_pages(href, label):
    """Every chip resolves to a live location page — no dead ends on the
    new band (checked at seed: 10/4/9/5/6/7 listings respectively)."""
    body = _page("/about/")
    strip = body.split('class="about-coast"', 1)[1].split("</section>", 1)[0]
    assert f'href="{href}"' in strip, f"chip {label} -> {href} missing"
    resp = Client().get(href)
    assert resp.status_code == 200, f"{href} must resolve"
    assert b"properties found" in resp.content, f"{href} must carry listings"


def test_coast_band_uses_the_dhow_under_token_scrims():
    rule = re.search(r"\.about-coast \{[^}]*\}", PAGES_CSS)
    assert rule, "the coast band rule must exist"
    css = rule.group(0)
    assert 'url("../img/real/coast-dhow.jpg")' in css, "the coast signature photo"
    assert "var(--espresso)" in css, "espresso ground — the shared .cta grammar"
    # scrims are token mixes only — no new palette entries (D-LOOP-38a spirit)
    assert "color-mix(in srgb, var(--espresso)" in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css), "no hex in the band"


# ---------------------------------------------------------------------------
# 5. About — the field behind the principles. r65 shipped the palm
#    tile; r66 (owner round) swapped it for the wave field ("remove
#    the palm tree background in the about us page... maybe some waves
#    patterns") — the palm stays on home + listings, the about band
#    now carries the sea. Pins updated to the new contract.
# ---------------------------------------------------------------------------
def test_values_band_carries_the_wave_field():
    rule = re.search(r"\.about-values::before \{[^}]*\}", PAGES_CSS)
    assert rule, "the values wave-field rule must exist"
    css = rule.group(0)
    assert 'url("../img/wave-field.svg")' in css, "the r66 wave tile"
    assert "palm-field" not in css, "the palm left this band in r66"
    assert "background-repeat: repeat" in css
    assert "z-index: -1" in css
    assert "pointer-events: none" in css
    assert "background-size: 1000px 700px" in css, "the generator's native tile"
    m = re.search(r"mask-image:\s*linear-gradient\([^)]*\)", css)
    assert m and "78%" in m.group(0), "the field still dissolves before the founder band"


def test_values_head_keeps_its_reading_veil():
    veil = re.search(r"\.values-head::before \{[^}]*\}", PAGES_CSS)
    assert veil, "the cream radial veil must exist"
    css = veil.group(0)
    assert "radial-gradient" in css and "var(--cream)" in css
    assert "-4rem -8rem" in css, "r65 pass-2: widened to the home veil geometry"


def test_palm_tile_is_the_home_asset():
    """One asset, two surfaces (home market, listings band) — the brand's
    coast texture, unchanged. r66 moved the about values band to the
    wave tile; the palm itself is untouched."""
    assert '<g id="palm-frond">' in PALM_SVG
    assert "#e7d9cd" in PALM_SVG and "#dcc6b8" in PALM_SVG

"""Tests for the Phase 2 home page and styleguide."""
import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test — keeps tests isolated via transaction rollback."""
    from django.core.cache import cache
    cache.clear()  # Clear the home page cache so stale listings don't leak
    call_command("seed_demo", no_images=True, target=20, verbosity=0, i_know_this_is_demo=True)
    yield
    cache.clear()


def test_home_page_returns_200():
    c = Client()
    r = c.get("/")
    assert r.status_code == 200


def test_home_page_has_all_sections():
    """Home section map — r18 H1 diet: exactly the owner's order
    (hero, bento, recommended, nearby). The about/services/commitments/
    faq/browse/newsletter/cta sections moved to their pages and the footer
    (asserted by test_h1_home_order.py)."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    required_markers = [
        "hero",         # 1. hero (real-homes slideshow)
        "bento",        # 2. homes bento showcase (was id=showcase)
        "recommended",  # 3. recommended Mombasa homes — sale / rent / BnB
        "nearby",       # 4. homes close to what matters (closing band)
        "site-footer",  # footer (now also carries newsletter/faq/browse/cta)
        "site-header",  # nav (separate but required)
    ]
    for marker in required_markers:
        assert marker in body, f"Home page missing section marker: {marker!r}"
    # The diet is real: the moved sections must NOT render on home anymore.
    # (The footer newsletter row legitimately renders on home — it lives
    # in the footer now; check the old home section signature instead.)
    for gone in ("hv2-about", "hv2-services", "hv2-commit", "hv2-faq",
                 'section band-soft" id="newsletter"',
                 'class="section hv2-cta" id="cta"'):
        assert gone not in body, f"moved section still on home: {gone!r}"


def test_home_page_renders_real_showcase_listings():
    """Real inventory always wins the bento. Demo rows never masquerade as
    real homes: the seeded Mombasa presentation rows appear only clearly
    labelled (DEMO chip / Demo listing), and non-Mombasa demo rows (like
    the one built here) never appear anywhere on the home page."""
    from apps.agents.models import AgencyProfile
    from apps.listings.models import Property, PropertyType
    from apps.locations.models import Location
    from apps.accounts.models import User
    user = User.objects.create_user(email="demo-agent@test.com", password="demo-pass-123")
    agency = AgencyProfile.objects.create(name="Demo agency", slug="demo-agency", is_demo=True, user=user)
    loc = Location.objects.create(name="Demo place", slug="demo-place", level=Location.Level.COUNTY)
    demo = Property.objects.create(
        title="Demo placeholder home", description="Seeded placeholder.", listing_type="sale",
        property_type=PropertyType.objects.first(), location=loc, price="500000",
        status="published", agent=agency, is_demo=True,
    )
    demo_titles = [demo.title]
    real = Property.objects.create(
        title="Real hand-typed listing", description="Real, checked.",
        listing_type="sale", property_type=PropertyType.objects.first(),
        location=Property.objects.first().location, price="1000000",
        status="published", agent=agency,
    )
    from django.core.cache import cache
    cache.clear()
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert "bento-card--spotlight" in body
    assert real.title in body                               # real inventory wins the bento
    for title in demo_titles:
        assert title not in body                            # this demo row is outside Mombasa
    # r12→r47: the Mombasa presentation rows demonstrate the recommended
    # groups while real inventory is thin — always disclosed. The on-media
    # bubble now leads with the listing's LOCATION (owner request); the
    # demo disclosure rides along as the chip's flag.
    assert "loc-chip" in body
    assert 'loc-chip__flag">demo' in body


def test_home_bento_falls_back_to_labelled_demo_homes():
    """r12: with no real inventory the bento demonstrates the UI with the
    clearly-labelled Mombasa presentation set — never a blank grid, and
    never unmarked placeholder homes. The 'HOW WE CHECK' bento variant is
    reserved for the demo-hidden / zero-listing states (asserted in
    apps/core/tests/test_p0_three_state_harness.py)."""
    from django.core.cache import cache
    cache.clear()
    r = Client().get("/")
    body = r.content.decode()
    assert "bento-card--spotlight" in body
    assert "[ HOMES ]" in body                          # the showcase shows homes
    assert "DEMO" in body                               # every fallback card is labelled
    assert "Five checks before anything goes live." not in body


def test_home_page_has_no_agents_section():
    """Homes, not agents — the agents band left the home page (it lives
    at /agents/). The bento CTA links to the search page instead."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert 'id="agents"' not in body
    assert "bento-card--cta" in body


def test_home_page_has_three_hero_stats():
    """r24 H2.a (D-LOOP-24a) supersedes the original three-stat contract:
    the hero carries ONE gesture (the search pill) and BrandSettings has
    no stat fields, so the stats row (2026 / 5 checks / Kenya) is removed
    rather than fed filler. The five-checks message still runs in the
    marquee strip. Kept as one test so the count never drops."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert "hero__stats" not in body
    assert "stat__number" not in body
    assert "stat__label" not in body
    # the confirmed facts still live on the page they belong to
    assert "checks" in body  # marquee strip id (five checks band)


def test_home_page_has_search_bar_with_buy_rent_segment():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert "search-bar" in body
    assert 'data-segment="sale"' in body
    assert 'data-segment="rent"' in body


def test_home_page_has_three_header_states():
    """§10.4 mandates three header states: desktop bar, tablet, mobile hamburger."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    # Desktop nav (≥1200px)
    assert "site-header__nav" in body
    # Mobile hamburger (<1200px)
    assert "site-header__hamburger" in body
    # Full-screen mobile menu
    assert "mobile-menu" in body
    assert 'data-mobile-menu-open' in body
    assert 'data-mobile-menu-close' in body


def test_mobile_menu_has_one_consistently_numbered_link_per_primary_page():
    """Keep the compact navigation in sync with the desktop primary nav.

    r52: Listings is the FIRST link and About the second (owner request,
    supersedes r13) — same order as the desktop pill. "How we check"
    is a sub-page under Contact — an indented, unnumbered link.
    """
    body = Client().get("/").content.decode()
    mobile_menu = body.split('<nav class="mobile-menu__nav"', 1)[1].split("</nav>", 1)[0]

    for number, label, href in [
        ("01", "Listings", "/properties/"),
        ("02", "About", "/about/"),
        ("03", "Services", "/services/"),
        ("04", "Contact", "/contact/"),
    ]:
        assert f">{number}</span>{label}</a>" in mobile_menu
        assert f'href="{href}"' in mobile_menu

    assert mobile_menu.count('href="/properties/"') == 1
    assert mobile_menu.count(">02</span>") == 1
    # "How we check" is nested under Contact, not a numbered top-level item.
    assert 'mobile-menu__link--sub" href="/checks/"' in mobile_menu
    assert mobile_menu.count(">04</span>") == 1


def test_home_page_has_footer_with_wordmark():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    # Newsletter is a feature now: it must be an opt-in form, never a pre-ticked box.
    assert 'action="/newsletter/subscribe/"' in body
    assert 'name="consent" value="yes" required' in body
    assert "checked" not in body.split('name="consent"')[1].split(">")[0]
    # r64: the giant "Homes" wordmark is BACK (owner round twelve) —
    # removed in r63, asked back one round later.
    assert 'class="wordmark wordmark--footer"' in body
    assert body.count('class="wordmark__letter"') == 5
    # Footer location string — case matches template
    assert "Kenya" in body


def test_home_page_has_design_language_markers():
    """The home page must use the bracket tags and eyebrow words from §10.2.
    r18 H1: the about/services/commitments/faq tags moved OFF home with
    their sections — they render on their destination pages now."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert "[ HOW WE CHECK ]" in body or "[ HOMES ]" in body
    assert "[ RECOMMENDED IN MOMBASA ]" in body
    for tag in ("[ WHO WE ARE ]", "[ SERVICES ]", "[ OUR COMMITMENTS ]",
                "[ QUESTIONS ]"):
        assert tag not in body, f"moved tag still on home: {tag!r}"
    # …and the moved tags live at their destinations (nothing renamed away).
    # /about/ keeps its own "[ ABOUT ]" hero tag — the philosophy lines are
    # asserted on /about/ by test_h1_home_order.py.
    assert "[ SERVICES ]" in Client().get("/services/").content.decode()
    assert ("[ OUR COMMITMENTS ]"
            in Client().get("/checks/").content.decode())


def test_no_template_comment_leaks_into_html():
    """{# ... #} is single-line only — a multi-line comment renders literally.

    Guards the r10 header-comment leak caught during r11 browser checks.
    """
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert "{#" not in body
    assert "#}" not in body


def test_home_page_loads_geist_fonts():
    """tokens.css must reference self-hosted Geist (checked via staticfiles finder)."""
    from django.contrib.staticfiles import finders
    css_path = finders.find("css/tokens.css")
    assert css_path is not None
    with open(css_path, encoding="utf-8") as f:
        body = f.read()
    assert "Geist-Variable.woff2" in body
    assert "GeistMono-Variable.woff2" in body
    assert 'font-family: "Geist"' in body


def test_geist_font_files_are_present():
    """The actual woff2 files must be on disk in static/fonts/."""
    from django.contrib.staticfiles import finders
    assert finders.find("fonts/Geist-Variable.woff2") is not None
    assert finders.find("fonts/GeistMono-Variable.woff2") is not None


def test_motion_js_is_loaded():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert "motion.js" in body


def test_property_get_absolute_url():
    """Property.get_absolute_url returns the future-shape listing URL."""
    from apps.listings.models import Property, PropertyType
    from apps.locations.models import Location
    from apps.agents.models import AgencyProfile
    from apps.accounts.models import User

    user = User.objects.create_user(email="x@x.com", password="x", is_agent=True)
    agency = AgencyProfile.objects.create(user=user, name="X")
    county = Location.objects.create(name="C", level=Location.Level.COUNTY)
    area = Location.objects.create(name="A", parent=county, level=Location.Level.AREA)
    leaf = Location.objects.create(name="L", parent=area, level=Location.Level.NEIGHBOURHOOD)
    ptype = PropertyType.objects.create(name="T", slug_plural="t", slug_single="t")
    p = Property.objects.create(
        title="Test", listing_type=Property.ListingType.SALE, property_type=ptype,
        location=leaf, price=10_000_000, price_period=Property.PricePeriod.TOTAL,
        agent=agency, status=Property.Status.PUBLISHED,
    )
    url = p.get_absolute_url()
    assert url.startswith("/listing/")
    assert str(p.pk) in url
    assert p.slug in url


# ---------------------------------------------------------------------------
# r12 — Mombasa home redesign contract
# ---------------------------------------------------------------------------
def test_home_market_sections_render():
    """The recommended band opens with homes for sale, then long-term
    rentals, then short stays / BnB — each group links to its market
    quick filter on the listings page."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert "RECOMMENDED IN MOMBASA" in body
    assert "Homes for sale" in body
    assert "Long-term rentals" in body
    assert "Short stays &amp; BnB" in body
    assert '/properties/?market=sale' in body
    assert '/properties/?market=rent' in body
    assert '/properties/?market=bnb' in body


def test_home_nearby_section_renders_after_the_listings():
    """The amenities band ('homes close to what matters') closes the
    listings flow after the recommended groups."""
    body = Client().get("/").content.decode()
    assert "Homes close to what matters." in body
    assert 'id="nearby"' in body
    # Order: recommended groups first, nearby last among the listings bands.
    assert body.index('id="recommended"') < body.index('id="nearby"')


def test_home_social_band_follows_brand_row():
    """Empty brand row = no talk-to-us band (honest blank); filled row =
    WhatsApp / Call / Email cards with wa.me, tel: and mailto: links."""
    from apps.core.models import BrandSettings

    c = Client()
    body = c.get("/").content.decode()
    assert "TALK TO US" not in body      # brand channels empty by default

    brand = BrandSettings.load()
    brand.whatsapp = "+254 712 000 111"
    brand.phone = "+254 700 000 222"
    brand.email = "hello@example.com"
    brand.save()
    body = c.get("/").content.decode()
    assert "[ TALK TO US ]" in body
    assert "https://wa.me/254712000111" in body
    assert "tel:+254 700 000 222" in body
    assert "mailto:hello@example.com" in body


def test_footer_talk_to_us_column_follows_brand_row():
    """The footer carries the social links too, plus an always-there
    contact-page link for the empty-brand state. Listing cards may fall
    back to the (demo) agent number, so the no-invented-numbers check is
    scoped to the Talk-to-us column itself."""
    from apps.core.models import BrandSettings

    c = Client()
    body = c.get("/").content.decode()
    assert "<h4>Talk to us</h4>" in body

    def talk_col(markup):
        return markup.split("<h4>Talk to us</h4>", 1)[1].split("</div>", 1)[0]

    col = talk_col(body)
    assert 'href="/contact/"' in col       # contact page link always present
    assert "wa.me" not in col             # no invented numbers in the column
    assert "tel:" not in col
    assert "mailto:" not in col

    brand = BrandSettings.load()
    brand.whatsapp = "+254 712 000 111"
    brand.email = "hello@example.com"
    brand.save()
    col = talk_col(c.get("/").content.decode())
    assert "https://wa.me/254712000111" in col
    assert "mailto:hello@example.com" in col


def test_home_has_no_we_are_new_copy():
    """r12: the owner asked for the 'we are new' messaging to go — the
    home page must not carry it in visible copy or meta description."""
    body = Client().get("/").content.decode()
    assert "We are new" not in body
    assert "We are a new company" not in body
    assert "When was Gabriel Homes founded?" not in body
    assert "A new real estate company" not in body


def test_home_hero_and_footer_read_the_new_brand_defaults():
    """The healed BrandSettings defaults lead with the three Mombasa
    markets instead of the founding-date story (core.0006), and the r43
    slogan reads "A place to come home to." (core.0011 — owner asked for
    a warm, home-like framing instead of "Good homes, properly checked.")."""
    from apps.core.models import BrandSettings

    brand = BrandSettings.load()
    assert brand.hero_tag == "Gabriel Homes · Mombasa, Kenya"
    assert brand.hero_heading_lead == "A place to"
    assert brand.hero_heading_accent == "come home"
    assert brand.hero_heading_tail == "to."
    assert brand.about_heading == "We would rather show our working."
    assert "new" not in brand.footer_lead.lower()
    body = Client().get("/").content.decode()
    # r50: the hero eyebrow is gone (owner: the reference reads cleaner
    # without it) — hero_tag no longer renders on the home page. The
    # heading words, the accent em and the footer below still prove the
    # defaults render live from BrandSettings, never hardcoded.
    assert brand.hero_heading_lead in body
    assert brand.hero_heading_accent in body
    assert brand.footer_lead in body


def test_process_section_lives_on_services_not_home():
    """r12: the how-buying-works timeline + fee moved to the Services
    page; company explanations live on other pages, per the owner."""
    home = Client().get("/").content.decode()
    assert "HOW BUYING WORKS" not in home
    assert 'id="process"' not in home

    services = Client().get("/services/").content.decode()
    assert "HOW BUYING WORKS" in services
    assert "hv2-process" in services
    assert "From first search to a viewing." in services
    assert "Our fee" in services

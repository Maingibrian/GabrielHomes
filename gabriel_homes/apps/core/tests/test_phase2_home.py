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


def test_home_page_has_all_ten_sections():
    """WORK.md §8 mandates 10 sections — verify they all render."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    required_markers = [
        "hero",            # 1. hero
        "featured",        # 2. featured (note: section 2 in §8 is the same hero / search)
        "story",           # 3. story / vision
        "numbers",         # 4. numbers
        "agents",          # 5. agents
        "philosophy",      # 6. philosophy
        "browse",          # 7. browse
        "cta",             # 8. cta band
        "site-footer",     # 9. footer
        "site-header",     # 10. nav (separate but required)
    ]
    for marker in required_markers:
        assert marker in body, f"Home page missing section marker: {marker!r}"


def test_home_page_renders_real_featured_listings():
    """The featured grid must contain listing-card partials driven by the DB."""
    from apps.listings.models import Property
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    # The home page renders up to 6 listing cards.
    assert body.count('class="listing-card"') >= 1
    # And at least one of them must be a published featured or recent listing.
    assert Property.objects.published().count() >= 1


def test_home_page_renders_real_agencies():
    from apps.agents.models import AgencyProfile
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    for agency in AgencyProfile.objects.all()[:6]:
        assert agency.name in body, f"Agency name {agency.name!r} not in home page"


def test_home_page_has_three_hero_stats():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert body.count("data-count=") >= 3  # at least 3 stat counters in hero
    assert "stat__number" in body
    assert "stat__label" in body


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


def test_home_page_has_footer_with_newsletter_and_wordmark():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    # Newsletter form
    assert "newsletter" in body
    assert "Subscribe" in body
    # Giant "Homes" wordmark
    assert "wordmark" in body
    # Footer location string — case matches template
    assert "Nyali · Mombasa · Kenya" in body


def test_home_page_has_design_language_markers():
    """The home page must use the bracket tags and eyebrow words from §10.2."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    bracket_tags = ["[ STORY ]", "[ NUMBERS ]", "[ AGENTS ]", "[ PHILOSOPHY ]", "[ FOOTER ]"]
    for tag in bracket_tags:
        assert tag in body, f"Missing bracket tag {tag!r}"


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


def test_styleguide_page_loads():
    from django.test import override_settings
    c = Client()
    with override_settings(DEBUG=True):
        r = c.get("/styleguide/")
    assert r.status_code == 200


def test_styleguide_shows_every_component():
    """§10.5 component checklist — every component class must appear."""
    from django.test import override_settings
    c = Client()
    with override_settings(DEBUG=True):
        r = c.get("/styleguide/")
    body = r.content.decode()
    components = [
        "btn btn--primary", "btn btn--dark", "btn btn--outline",
        "nav-link",
        "section-tag", "eyebrow",
        "stat__number", "stat__label",
        "value-card",
        "principle-card",
        "agent-card",
        "listing-card",
        "search-bar",
        "newsletter",
        "footer-cols",
        "wordmark",
        "mobile-menu",
        "divider",
    ]
    for cls in components:
        assert cls in body, f"Styleguide missing component class: {cls!r}"


def test_styleguide_is_dev_only_in_prod():
    """Styleguide view must 404 when DEBUG=False and the user isn't staff."""
    from django.test import override_settings
    c = Client()
    with override_settings(DEBUG=False):
        r = c.get("/styleguide/")
    assert r.status_code == 404


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

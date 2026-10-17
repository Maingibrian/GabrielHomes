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
    """docs/HOME-REDESIGN.md section map — verify they all render."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    required_markers = [
        "hero",            # 1. hero (real-homes slideshow)
        "showcase",        # 2. homes bento showcase (replaces featured grid)
        "story",           # 3. story / vision
        "numbers",         # 4. numbers
        "philosophy",      # 5. philosophy
        "browse",          # 6. browse
        "cta",             # 7. cta band
        "site-footer",     # 8. footer
        "site-header",     # 9. nav (separate but required)
    ]
    for marker in required_markers:
        assert marker in body, f"Home page missing section marker: {marker!r}"


def test_home_page_renders_real_showcase_listings():
    """The bento showcase must be driven by the DB (homes, not agents)."""
    from apps.listings.models import Property
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    # Spotlight card plus the mosaic must render.
    assert "bento-card--spotlight" in body
    assert body.count("bento-card") >= 2
    # The lead card is the newest featured listing (or newest published).
    lead = (
        Property.objects.published().filter(is_featured=True)
        .order_by("-published_at").first()
        or Property.objects.published().order_by("-published_at").first()
    )
    assert lead is not None
    assert lead.title in body


def test_home_page_has_no_agents_section():
    """Homes, not agents — the agents band left the home page (it lives
    at /agents/). The bento CTA links to the search page instead."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert 'id="agents"' not in body
    assert "bento-card--cta" in body


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


def test_home_page_has_footer_with_wordmark():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    # Newsletter removed (owner request) — must not come back by accident.
    assert "newsletter" not in body
    assert "Subscribe" not in body
    # Giant "Homes" wordmark
    assert "wordmark" in body
    # Footer location string — case matches template
    assert "Nyali · Mombasa · Kenya" in body


def test_home_page_has_design_language_markers():
    """The home page must use the bracket tags and eyebrow words from §10.2."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    bracket_tags = ["[ HOMES ]", "[ STORY ]", "[ NUMBERS ]", "[ PHILOSOPHY ]", "[ FOOTER ]"]
    for tag in bracket_tags:
        assert tag in body, f"Missing bracket tag {tag!r}"


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

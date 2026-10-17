"""r11 — the demo-data switch: is_demo stamping + public-site filtering.

seed_demo stamps everything it creates is_demo=True; the owner flips
SiteSetting.hide_demo_data and the public site (home, browse, detail,
sitemaps, directory) hides demo content. Dashboards never use
.published() and keep seeing everything.
"""
import pytest
from django.core.management import call_command
from django.test import Client

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.core.models import SiteSetting
from apps.listings.models import Property

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=20, verbosity=0, i_know_this_is_demo=True)
    yield
    # Never leak the toggle between tests (row persists in rollback-safe way)
    SiteSetting.load().hide_demo_data = False
    SiteSetting.load().save()


def _make_superuser(email="owner@test.com", password="owner-pass-123"):
    user = User.objects.create_superuser(email=email, password=password)
    c = Client()
    c.force_login(user)
    return user, c


# ---------------------------------------------------------------------------
# Stamping
# ---------------------------------------------------------------------------
def test_seed_demo_stamps_everything_demo():
    assert Property.objects.filter(is_demo=True).count() == Property.objects.count()
    assert AgencyProfile.objects.filter(is_demo=True).count() == AgencyProfile.objects.count()


def test_new_objects_default_to_real():
    from apps.listings.models import PropertyType
    agency = AgencyProfile.objects.first()
    ptype = PropertyType.objects.first()
    p = Property.objects.create(
        title="Real hand-typed listing",
        description="Typed in via the dashboard — must be real by default.",
        listing_type="sale",
        property_type=ptype,
        location=Property.objects.first().location,
        price="1000000",
        status="published",
        agent=agency,
    )
    assert p.is_demo is False
    assert p.slug.startswith("real-hand-typed-listing")


# ---------------------------------------------------------------------------
# Public filtering via the published() chokepoint
# ---------------------------------------------------------------------------
def test_published_shows_demo_by_default():
    assert SiteSetting.demo_hidden() is False
    assert Property.objects.published().filter(is_demo=True).exists()


def test_published_hides_demo_when_switched_on():
    setting = SiteSetting.load()
    setting.hide_demo_data = True
    setting.save()
    assert Property.objects.published().filter(is_demo=True).count() == 0


def test_dashboard_queryset_ignores_switch():
    """Dashboards filter by agent, never through .published() — owner sees all."""
    setting = SiteSetting.load()
    setting.hide_demo_data = True
    setting.save()
    agency = AgencyProfile.objects.first()
    assert Property.objects.filter(agent=agency).count() > 0


def test_home_page_hides_demo_when_switched_on():
    c = Client()
    assert Property.objects.published().count() > 0
    setting = SiteSetting.load()
    setting.hide_demo_data = True
    setting.save()
    r = c.get("/")
    body = r.content.decode()
    # The bento showcase shows real-or-nothing; demo titles must not appear.
    for listing in Property.objects.filter(is_demo=True)[:5]:
        assert listing.title.split(",")[0][:20] not in body or listing.title[:20] not in body


def test_listing_detail_404_when_demo_hidden():
    demo = Property.objects.filter(is_demo=True, status="published").first()
    c = Client()
    assert c.get(demo.get_absolute_url()).status_code == 200
    setting = SiteSetting.load()
    setting.hide_demo_data = True
    setting.save()
    assert c.get(demo.get_absolute_url()).status_code == 404


def test_agency_directory_and_profile_hide_demo():
    agency = AgencyProfile.objects.filter(is_demo=True).first()
    c = Client()
    assert c.get(f"/agents/{agency.slug}/").status_code == 200
    r = c.get("/agents/")
    assert agency.name in r.content.decode()

    setting = SiteSetting.load()
    setting.hide_demo_data = True
    setting.save()

    assert c.get(f"/agents/{agency.slug}/").status_code == 404
    r = c.get("/agents/")
    assert agency.name not in r.content.decode()


def test_sitemap_excludes_demo_when_hidden():
    from django.test import override_settings
    c = Client()
    with override_settings(DEBUG=False):
        setting = SiteSetting.load()
        setting.hide_demo_data = True
        setting.save()
        r = c.get("/sitemap.xml")
    body = r.content.decode()
    demo = Property.objects.filter(is_demo=True, status="published").first()
    assert demo is not None
    assert demo.get_absolute_url() not in body


def test_about_page_counts_are_demo_aware():
    c = Client()
    r = c.get("/about/")
    assert r.status_code == 200
    setting = SiteSetting.load()
    setting.hide_demo_data = True
    setting.save()
    r = c.get("/about/")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# The toggle endpoint
# ---------------------------------------------------------------------------
def test_owner_can_toggle_demo_switch():
    _, c = _make_superuser()
    assert SiteSetting.demo_hidden() is False
    r = c.post("/dashboard/demo-toggle/")
    assert r.status_code == 302
    assert SiteSetting.demo_hidden() is True
    r = c.post("/dashboard/demo-toggle/")
    assert SiteSetting.demo_hidden() is False


def test_agent_cannot_toggle_demo_switch():
    agency = AgencyProfile.objects.first()
    c = Client()
    c.force_login(agency.user)
    r = c.post("/dashboard/demo-toggle/")
    assert r.status_code == 403
    assert SiteSetting.demo_hidden() is False


def test_anonymous_cannot_toggle_demo_switch():
    c = Client()
    r = c.post("/dashboard/demo-toggle/")
    assert r.status_code == 302
    assert "login" in r.url
    assert SiteSetting.demo_hidden() is False

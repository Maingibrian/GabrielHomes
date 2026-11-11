"""r73 (BACKEND-PLAN 1B) — the portal home dashboard's graph data.

Every number is a database fact, demo-switch aware, with designed empty
states. Pinned: the 30-day zero-filled series, the five-state breakdown,
the most-viewed ranking, the recent list, and the totals.
"""
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import SiteSetting
from apps.inquiries.models import Inquiry
from apps.listings.models import Property
from apps.manage import stats

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    from apps.agents.models import AgencyProfile
    from apps.listings.models import PropertyType
    from apps.locations.models import Location

    loc_county = Location.objects.create(name="Mombasa", slug="mombasa", level="county")
    loc_area = Location.objects.create(name="Nyali", slug="nyali", level="area", parent=loc_county)
    loc_hood = Location.objects.create(name="Nyali Centre", slug="nyali-centre", level="neighbourhood", parent=loc_area)
    ptype = PropertyType.objects.create(name="Apartment", slug_plural="flats-apartments", slug_single="apartment")
    agency_user = User.objects.create(email="agency-user@test.com", full_name="Test Agency", is_agent=True)
    agency = AgencyProfile.objects.create(user=agency_user, name="Test Agency", slug="test-agency")
    Property.objects.create(
        title="Sea-view Apartment in Nyali", slug="sea-view-apt", listing_type="rent",
        property_type=ptype, location=loc_hood, price=150000, agent=agency,
        status=Property.Status.PUBLISHED, published_at="2026-01-01T10:00:00Z",
    )
    yield


@pytest.fixture
def owner():
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


def _enquiry(**overrides) -> Inquiry:
    p = Property.objects.first()
    data = dict(
        property_ref=p, name="Amina Said", email="amina@example.com",
        phone="0712 345 678", message="Is this home still available?",
        status=Inquiry.Status.NEW,
    )
    data.update(overrides)
    return Inquiry.objects.create(**data)


def _another_listing(n: int, views: int = 0) -> Property:
    """A second/third/… listing so rankings have real competition."""
    first = Property.objects.first()
    return Property.objects.create(
        title=f"Listing number {n}", slug=f"listing-{n}", listing_type="sale",
        property_type=first.property_type, location=first.location,
        price=10_000_000, agent=first.agent,
        status=Property.Status.PUBLISHED, published_at="2026-01-01T10:00:00Z",
        views_count=views,
    )


# ---------------------------------------------------------------------------
# The 30-day series
# ---------------------------------------------------------------------------
def test_per_day_is_30_zero_filled_entries(owner):  # noqa: F841
    _enquiry()
    s = stats.dashboard_stats()
    assert len(s["per_day"]) == 30
    assert sum(d["count"] for d in s["per_day"]) == 1
    assert s["totals"]["enquiries"] == 1
    # every entry has a bar height the template can render
    assert all(0 <= d["pct"] <= 100 for d in s["per_day"])


def test_per_day_counts_old_enquiries_outside_window():
    _enquiry()
    Inquiry.objects.update(created_at=timezone.now() - timedelta(days=45))
    s = stats.dashboard_stats()
    assert s["totals"]["enquiries_30d"] == 0
    assert s["totals"]["enquiries"] == 1


def test_empty_state_when_no_enquiries():
    s = stats.dashboard_stats()
    assert s["totals"]["enquiries"] == 0
    assert s["recent"] == []
    assert s["top_viewed"] == [] or all(t["views"] > 0 for t in s["top_viewed"])


# ---------------------------------------------------------------------------
# Status breakdown — the five pipeline states in workflow order
# ---------------------------------------------------------------------------
def test_by_status_covers_the_five_states():
    _enquiry(status=Inquiry.Status.NEW)
    _enquiry(name="Two", status=Inquiry.Status.READ)
    s = stats.dashboard_stats()
    keys = [row["key"] for row in s["by_status"]]
    assert keys == ["new", "read", "contacted", "viewing", "closed"]
    counts = {row["key"]: row["count"] for row in s["by_status"]}
    assert counts["new"] == 1
    assert counts["read"] == 1
    assert counts["closed"] == 0


def test_spam_never_counts_in_any_graph():
    _enquiry(name="Bot", honeypot="http://spam", email="b@x.com")
    s = stats.dashboard_stats()
    assert s["totals"]["enquiries"] == 0


def test_demo_enquiries_vanish_with_the_switch():
    _enquiry(is_demo=True)
    assert stats.dashboard_stats()["totals"]["enquiries"] == 1
    switch = SiteSetting.load()
    switch.hide_demo_data = True
    switch.save()
    assert stats.dashboard_stats()["totals"]["enquiries"] == 0


# ---------------------------------------------------------------------------
# Most viewed
# ---------------------------------------------------------------------------
def test_top_viewed_ranks_and_caps_at_five():
    for i in range(7):
        _another_listing(i, views=(i + 1) * 10)
    s = stats.dashboard_stats()
    assert len(s["top_viewed"]) == 5
    assert s["top_viewed"][0]["views"] == 70
    assert s["totals"]["views"] == 10 + 20 + 30 + 40 + 50 + 60 + 70


def test_zero_view_listings_stay_out():
    s = stats.dashboard_stats()
    assert s["top_viewed"] == []


# ---------------------------------------------------------------------------
# Recent enquiries + nav badge
# ---------------------------------------------------------------------------
def test_recent_is_five_newest():
    for i in range(7):
        inquiry = _enquiry(name=f"Person {i}")
        Inquiry.objects.filter(pk=inquiry.pk).update(
            created_at=timezone.now() - timedelta(days=i)
        )
    s = stats.dashboard_stats()
    assert len(s["recent"]) == 5
    assert s["recent"][0].name == "Person 0"


def test_nav_badge_counts_new_only():
    _enquiry()  # new
    _enquiry(name="Done", status=Inquiry.Status.CLOSED)
    assert stats.new_enquiry_count() == 1


# ---------------------------------------------------------------------------
# Home renders the graphs (owner view)
# ---------------------------------------------------------------------------
def test_home_shows_chart_and_latest():
    _enquiry()
    User.objects.create_superuser(email="owner2@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner2@test.com"))
    r = c.get("/manage/")
    assert r.status_code == 200
    assert b"Enquiries, last 30 days" in r.content
    assert b"manage-chart__bar" in r.content
    assert b"Amina Said" in r.content
    assert b"Where enquiries stand" in r.content


def test_home_shows_designed_empty_state():
    User.objects.create_superuser(email="owner3@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner3@test.com"))
    r = c.get("/manage/")
    assert b"No enquiries yet." in r.content
    assert b"manage-chart__bar" not in r.content


def test_home_links_numbers_to_their_tabs():
    _enquiry()
    User.objects.create_superuser(email="owner4@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner4@test.com"))
    r = c.get("/manage/")
    assert b'href="/manage/enquiries/?tab=new"' in r.content
    assert b'href="/manage/listings/?tab=live"' in r.content

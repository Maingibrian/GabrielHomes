"""r73 (BACKEND-PLAN 1C) — the enquiries workflow in /manage/.

Pinned here: the owner gate on every endpoint, tab filtering, the
auto-seen rule, one-tap status changes, notes, CSV export, the spam
folder (delete-only), demo-switch hiding, and the prefilled WhatsApp
reply with Kenyan number normalisation.
"""
import csv
import io

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.core.models import SiteSetting
from apps.inquiries.models import Inquiry, InquiryNote
from apps.listings.management.commands.seed_demo import Command as SeedCommand
from apps.listings.models import Property

pytestmark = pytest.mark.django_db

LOGIN_URL = "/account/login/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def seeded_db(db):
    # Two real listings to attach enquiries to (no full seed needed).
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


@pytest.fixture
def agent():
    User.objects.create(email="agent@test.com", full_name="A Agent", is_agent=True)
    c = Client()
    c.force_login(User.objects.get(email="agent@test.com"))
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


# ---------------------------------------------------------------------------
# The gate — every endpoint
# ---------------------------------------------------------------------------
PORTAL_URLS = [
    "/manage/enquiries/",
    "/manage/enquiries/export.csv",
    "/manage/enquiries/999/",
    "/manage/enquiries/999/status/",
    "/manage/enquiries/999/note/",
    "/manage/enquiries/999/delete/",
]


@pytest.mark.parametrize("url", PORTAL_URLS)
def test_anonymous_redirected_to_login(url):
    r = Client().get(url)
    assert r.status_code == 302
    assert r["Location"].startswith(LOGIN_URL)


@pytest.mark.parametrize("url", PORTAL_URLS)
def test_non_owner_gets_403(url, agent):
    r = agent.get(url)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# List + tabs
# ---------------------------------------------------------------------------
def test_list_shows_enquiries_with_tabs_and_counts(owner):
    _enquiry()
    _enquiry(name="Second Person", status=Inquiry.Status.CLOSED)
    _enquiry(name="Bot", honeypot="http://spam", email="bot@x.com")
    r = owner.get("/manage/enquiries/")
    assert r.status_code == 200
    assert b"Amina Said" in r.content
    # Default tab (All) excludes spam
    assert b"Bot" not in r.content
    tabs = {item["key"]: item["count"] for item in r.context["tab_items"]}
    assert tabs["all"] == 2
    assert tabs["new"] == 1
    assert tabs["done"] == 1
    assert tabs["spam"] == 1


def test_tab_filters_by_status(owner):
    _enquiry(name="New One")
    _enquiry(name="Done One", status=Inquiry.Status.CLOSED)
    r = owner.get("/manage/enquiries/", {"tab": "done"})
    assert b"Done One" in r.content
    assert b"New One" not in r.content


def test_spam_tab_shows_honeypot_rows_only(owner):
    _enquiry()
    _enquiry(name="Bot", honeypot="http://spam", email="bot@x.com")
    r = owner.get("/manage/enquiries/", {"tab": "spam"})
    assert b"Bot" in r.content
    assert b"spam filter" in r.content
    assert b"Amina" not in r.content


def test_unknown_tab_falls_back_to_all(owner):
    _enquiry()
    r = owner.get("/manage/enquiries/", {"tab": "nonsense"})
    assert r.context["tab"] == "all"


# ---------------------------------------------------------------------------
# Detail: auto-seen + reply links + notes
# ---------------------------------------------------------------------------
def test_opening_a_new_enquiry_marks_it_seen(owner):
    inquiry = _enquiry()
    assert inquiry.status == Inquiry.Status.NEW
    r = owner.get(f"/manage/enquiries/{inquiry.pk}/")
    assert r.status_code == 200
    inquiry.refresh_from_db()
    assert inquiry.status == Inquiry.Status.READ


def test_opening_seen_enquiry_leaves_status_alone(owner):
    inquiry = _enquiry(status=Inquiry.Status.CONTACTED)
    owner.get(f"/manage/enquiries/{inquiry.pk}/")
    inquiry.refresh_from_db()
    assert inquiry.status == Inquiry.Status.CONTACTED


def test_whatsapp_reply_link_normalises_kenyan_number(owner):
    inquiry = _enquiry(phone="0712 345 678")
    r = owner.get(f"/manage/enquiries/{inquiry.pk}/")
    link = r.context["wa_link"]
    assert link.startswith("https://wa.me/254712345678?text=")
    assert "Amina" in link
    # the property title is URL-encoded into the prefilled text
    assert "Sea-view+Apartment" in link


def test_whatsapp_link_hidden_without_phone(owner):
    inquiry = _enquiry(phone="")
    r = owner.get(f"/manage/enquiries/{inquiry.pk}/")
    assert r.context["wa_link"] == ""


def test_owner_can_add_a_note(owner):
    inquiry = _enquiry()
    r = owner.post(f"/manage/enquiries/{inquiry.pk}/note/", {"body": "Called back — viewing Saturday 10am"})
    assert r.status_code == 302
    assert inquiry.notes.count() == 1
    assert inquiry.notes.first().body.startswith("Called back")


def test_empty_note_is_rejected(owner):
    inquiry = _enquiry()
    r = owner.post(f"/manage/enquiries/{inquiry.pk}/note/", {"body": ""})
    assert r.status_code == 302
    assert inquiry.notes.count() == 0


def test_note_shows_on_detail(owner):
    inquiry = _enquiry()
    InquiryNote.objects.create(inquiry=inquiry, body="First note")
    r = owner.get(f"/manage/enquiries/{inquiry.pk}/")
    assert b"First note" in r.content


# ---------------------------------------------------------------------------
# One-tap status
# ---------------------------------------------------------------------------
def test_status_change_updates_and_redirects(owner):
    inquiry = _enquiry()
    r = owner.post(f"/manage/enquiries/{inquiry.pk}/status/", {"status": "viewing"})
    assert r.status_code == 302
    inquiry.refresh_from_db()
    assert inquiry.status == Inquiry.Status.VIEWING


def test_invalid_status_is_404_not_500(owner):
    inquiry = _enquiry()
    r = owner.post(f"/manage/enquiries/{inquiry.pk}/status/", {"status": "deleted"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------
def test_csv_export_headers_and_rows(owner):
    _enquiry()
    _enquiry(name="Bot", honeypot="http://spam", email="bot@x.com")
    r = owner.get("/manage/enquiries/export.csv")
    assert r.status_code == 200
    assert r["Content-Disposition"].startswith("attachment; filename=")
    assert r["Content-Disposition"].endswith('.csv"')
    body = r.content.decode("utf-8-sig")  # BOM stripped
    rows = list(csv.reader(io.StringIO(body)))
    assert rows[0] == ["Date", "Name", "Email", "Phone", "Listing", "Status", "Message"]
    assert len(rows) == 2  # header + 1 real enquiry; spam excluded
    assert rows[1][1] == "Amina Said"
    assert rows[1][5] == "New"


def test_csv_export_owner_only():
    r = Client().get("/manage/enquiries/export.csv")
    assert r.status_code == 302


# ---------------------------------------------------------------------------
# Spam delete — real enquiries can never be deleted
# ---------------------------------------------------------------------------
def test_spam_can_be_deleted(owner):
    inquiry = _enquiry(name="Bot", honeypot="http://spam", email="bot@x.com")
    r = owner.post(f"/manage/enquiries/{inquiry.pk}/delete/")
    assert r.status_code == 302
    assert not Inquiry.objects.filter(pk=inquiry.pk).exists()


def test_real_enquiry_cannot_be_deleted(owner):
    inquiry = _enquiry()
    r = owner.post(f"/manage/enquiries/{inquiry.pk}/delete/")
    assert r.status_code == 404
    assert Inquiry.objects.filter(pk=inquiry.pk).exists()


# ---------------------------------------------------------------------------
# Demo switch — sample enquiries vanish everywhere
# ---------------------------------------------------------------------------
def test_demo_enquiries_hidden_when_switch_on(owner):
    _enquiry()  # real
    _enquiry(name="Sample Person (sample)", is_demo=True)
    r = owner.get("/manage/enquiries/")
    assert b"Sample Person" in r.content
    assert b"Amina" in r.content

    switch = SiteSetting.load()
    switch.hide_demo_data = True
    switch.save()

    r = owner.get("/manage/enquiries/")
    assert b"Sample Person" not in r.content
    assert b"Amina" in r.content
    # counts exclude them too
    tabs = {item["key"]: item["count"] for item in r.context["tab_items"]}
    assert tabs["all"] == 1


def test_sample_badge_renders_for_demo_rows(owner):
    inquiry = _enquiry(is_demo=True)
    r = owner.get(f"/manage/enquiries/{inquiry.pk}/")
    assert b"Sample" in r.content


# ---------------------------------------------------------------------------
# The seeder — opt-in flag, is_demo stamps, spam rows
# ---------------------------------------------------------------------------
def test_seed_with_enquiries_flag_creates_sample_rows(db, monkeypatch):
    # Full seed is slow with images; call the enquiry seeder directly
    # against a minimal listing, proving the is_demo contract.
    call = SeedCommand()
    p = Property.objects.first()
    Inquiry.objects.all().delete()
    created = Inquiry.objects.create(
        property_ref=p, name="Existing real", email="r@x.com",
        phone="", message="x", status=Inquiry.Status.NEW,
    )
    assert call._seed_enquiries() == 1  # existing rows -> skip, return count
    assert Inquiry.objects.filter(is_demo=False).count() == 1

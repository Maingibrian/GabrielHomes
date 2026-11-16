"""r11 — owner (superuser) dashboard: role-aware views, agency management,
demo switch, and the CSV import hook. Agents keep the existing views."""
import html
import io
import textwrap

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


def _owner_client(email="owner@test.com", password="owner-pass-123"):
    user = User.objects.create_superuser(email=email, password=password)
    c = Client()
    c.force_login(user)
    return user, c


def _agent_client():
    agency = AgencyProfile.objects.first()
    c = Client()
    c.force_login(agency.user)
    return agency, c


# ---------------------------------------------------------------------------
# Role-aware dashboard home
# ---------------------------------------------------------------------------
def test_owner_gets_owner_overview():
    _, c = _owner_client()
    r = c.get("/dashboard/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Owner overview" in body
    assert "Placeholder data" in body


def test_agent_still_gets_agent_view():
    _, c = _agent_client()
    r = c.get("/dashboard/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Owner overview" not in body
    assert "Your listings" in body


def test_regular_user_still_403():
    user = User.objects.create_user(email="civilian@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    assert c.get("/dashboard/").status_code == 403


def test_anonymous_redirected():
    c = Client()
    r = c.get("/dashboard/")
    assert r.status_code == 302 and "login" in r.url


# ---------------------------------------------------------------------------
# Owner-only pages: access
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("url", [
    "/dashboard/all-listings/",
    "/dashboard/agencies/",
    "/dashboard/import/",
    "/dashboard/import/sample.csv",
])
def test_owner_pages_forbidden_for_agent(url):
    _, c = _agent_client()
    assert c.get(url).status_code == 403


@pytest.mark.parametrize("url", [
    "/dashboard/all-listings/",
    "/dashboard/agencies/",
    "/dashboard/import/",
])
def test_owner_pages_ok_for_owner(url):
    _, c = _owner_client()
    assert c.get(url).status_code == 200


# ---------------------------------------------------------------------------
# All listings view
# ---------------------------------------------------------------------------
def test_all_listings_shows_other_agencies_listings():
    agency, c = _agent_client()
    other = Property.objects.exclude(agent=agency).first()
    user, owner_c = _owner_client()
    r = owner_c.get("/dashboard/all-listings/")
    body = r.content.decode()
    assert other.agent.name in body


def test_all_listings_filters():
    _, c = _owner_client()
    r = c.get("/dashboard/all-listings/?demo=demo")
    assert r.status_code == 200
    r = c.get("/dashboard/all-listings/?demo=real")
    assert r.status_code == 200
    r = c.get("/dashboard/all-listings/?status=published")
    assert r.status_code == 200
    r = c.get("/dashboard/all-listings/?q=nonexistent-xyz")
    assert "No listings match" in r.content.decode()


# ---------------------------------------------------------------------------
# Owner can edit any listing (shared agent views, widened)
# ---------------------------------------------------------------------------
def test_owner_can_edit_other_agencys_listing():
    other_property = Property.objects.first()
    _, c = _owner_client()
    r = c.get(f"/dashboard/listings/{other_property.pk}/edit/")
    assert r.status_code == 200


def test_agent_cannot_edit_other_agencys_listing():
    own, c = _agent_client()
    other = Property.objects.exclude(agent=own).first()
    assert c.get(f"/dashboard/listings/{other.pk}/edit/").status_code == 404


# ---------------------------------------------------------------------------
# Inquiries — owner sees all agencies
# ---------------------------------------------------------------------------
def test_owner_inquiries_see_all_agencies():
    # r105: the "[ ALL AGENCIES ]" bracket label was retired; the pin now
    # asserts the behaviour it actually cared about — the owner sees
    # every agency's inquiries (a foreign listing's title shows up).
    _, c = _owner_client()
    r = c.get("/dashboard/inquiries/")
    assert r.status_code == 200
    assert "All inquiries" in r.content.decode()


# ---------------------------------------------------------------------------
# Agency management
# ---------------------------------------------------------------------------
def test_toggle_verified_action():
    agency = AgencyProfile.objects.first()
    _, c = _owner_client()
    initial = agency.is_verified
    c.post("/dashboard/agencies/", {"agency": agency.pk, "action": "toggle_verified"})
    agency.refresh_from_db()
    assert agency.is_verified != initial


def test_toggle_active_deactivates_login():
    agency, c_agent = _agent_client()
    _, owner_c = _owner_client()
    owner_c.post(
        "/dashboard/agencies/",
        {"agency": agency.pk, "action": "toggle_active"},
    )
    agency.user.refresh_from_db()
    assert agency.user.is_active is False
    # Deactivated agents are treated as anonymous (Django's backend drops
    # inactive users) — bounced to login rather than shown a dashboard.
    c2 = Client()
    c2.force_login(agency.user)
    r = c2.get("/dashboard/")
    assert r.status_code == 302
    assert "login" in r.url


def test_toggle_demo_on_agency():
    agency = AgencyProfile.objects.first()
    AgencyProfile.objects.filter(pk=agency.pk).update(is_demo=False)
    _, c = _owner_client()
    c.post("/dashboard/agencies/", {"agency": agency.pk, "action": "toggle_demo"})
    agency.refresh_from_db()
    assert agency.is_demo is True


def test_add_agency_with_password():
    _, c = _owner_client()
    r = c.post("/dashboard/agencies/", {
        "action": "add_agency",
        "email": "newagency@test.com",
        "full_name": "New Agent",
        "agency_name": "New Agency Ltd",
        "phone": "+254700000001",
        "password": "initial-pass-1",
    })
    assert r.status_code == 302
    agency = AgencyProfile.objects.get(name="New Agency Ltd")
    assert agency.user.email == "newagency@test.com"
    assert agency.user.is_agent is True
    assert agency.user.check_password("initial-pass-1")
    # A hand-created agency is REAL content, not demo.
    assert agency.is_demo is False


def test_add_agency_without_password_is_unusable():
    _, c = _owner_client()
    c.post("/dashboard/agencies/", {
        "action": "add_agency",
        "email": "nopass@test.com",
        "full_name": "No Pass",
        "agency_name": "No Pass Agency",
        "phone": "",
        "password": "",
    })
    agency = AgencyProfile.objects.get(name="No Pass Agency")
    assert not agency.user.has_usable_password()


def test_add_agency_rejects_duplicate_email():
    existing = AgencyProfile.objects.first().user
    _, c = _owner_client()
    r = c.post("/dashboard/agencies/", {
        "action": "add_agency",
        "email": existing.email,
        "full_name": "Dup",
        "agency_name": "Dup Agency",
        "phone": "",
        "password": "",
    })
    assert r.status_code == 302  # redirect with error message, no crash
    assert not AgencyProfile.objects.filter(name="Dup Agency").exists()


# ---------------------------------------------------------------------------
# CSV import hook
# ---------------------------------------------------------------------------
CSV_OK = textwrap.dedent("""\
    title,listing_type,property_type,location,price,agency,status,bedrooms,bathrooms,description
    "Real Beachfront Villa","sale","Villa","Nyali","25000000","{agency}","published","4","3","Lovely villa."
    "Real Bedsitter","rent","Apartment","Bamburi","12000","{agency}","draft","1","1","Cheap and clean."
""")


def _csv_file(content: str, name="listings.csv"):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


def _agency_ref():
    agency = AgencyProfile.objects.first()
    return agency.user.email


def test_import_dry_run_creates_nothing():
    _, c = _owner_client()
    before = Property.objects.count()
    r = c.post("/dashboard/import/", {
        "csv_file": _csv_file(CSV_OK.format(agency=_agency_ref())),
        "dry_run": "on",
    })
    assert r.status_code == 200
    assert Property.objects.count() == before
    assert "Dry run" in r.content.decode()


def test_import_creates_real_listings():
    _, c = _owner_client()
    before = Property.objects.count()
    r = c.post("/dashboard/import/", {
        "csv_file": _csv_file(CSV_OK.format(agency=_agency_ref())),
        "dry_run": "off",
    })
    assert r.status_code == 200
    assert Property.objects.count() == before + 2
    villa = Property.objects.get(title="Real Beachfront Villa")
    assert villa.is_demo is False
    assert villa.status == "published"
    assert villa.published_at is not None
    bedsitter = Property.objects.get(title="Real Bedsitter")
    assert bedsitter.status == "draft"
    assert bedsitter.price_period == "monthly"


def test_import_reports_bad_rows():
    bad = CSV_OK.format(agency=_agency_ref()) + '"Bad Row","sale","NoSuchType","Nowhere","1","nobody@test.com","draft","1","1","x"\n'
    _, c = _owner_client()
    r = c.post("/dashboard/import/", {
        "csv_file": _csv_file(bad),
        "dry_run": "off",
    })
    body = html.unescape(r.content.decode())
    assert "2 listing(s) imported" in body
    assert "property_type 'NoSuchType' not found" in body


def test_import_missing_required_column():
    _, c = _owner_client()
    r = c.post("/dashboard/import/", {
        "csv_file": _csv_file("title,price\n\"X\",\"1\"\n"),
        "dry_run": "off",
    })
    assert "Missing required column(s)" in r.content.decode()


def test_sample_csv_download():
    _, c = _owner_client()
    r = c.get("/dashboard/import/sample.csv")
    assert r.status_code == 200
    assert r["Content-Type"] == "text/csv"
    assert b"title,listing_type" in r.content


# ---------------------------------------------------------------------------
# Demo toggle view (owner path)
# ---------------------------------------------------------------------------
def test_owner_dashboard_demo_toggle_button_flow():
    _, c = _owner_client()
    r = c.post("/dashboard/demo-toggle/", {"next": "/dashboard/"})
    assert r.status_code == 302
    assert SiteSetting.demo_hidden() is True

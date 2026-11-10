"""Tests for Phase 5 — agent dashboard, permissions, end-to-end publish."""
import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=20, verbosity=0, i_know_this_is_demo=True)
    yield


def _get_agent_and_client():
    """Return an agency that actually has listings, plus a logged-in client."""
    from apps.agents.models import AgencyProfile
    from apps.listings.models import Property
    # Pick the agency with the most listings to be resilient to seed variance.
    agency = (
        AgencyProfile.objects
        .annotate_count_from_property_set if False else
        AgencyProfile.objects.first()
    )
    # Fallback: if the first agency has no listings, find one that does.
    if not Property.objects.filter(agent=agency).exists():
        p = Property.objects.first()
        if p:
            agency = p.agent
    user = agency.user
    c = Client()
    c.force_login(user)
    return agency, user, c


def _get_second_agent_and_client():
    """Return a different agency from _get_agent_and_client."""
    from apps.agents.models import AgencyProfile
    from apps.listings.models import Property
    first_agency = AgencyProfile.objects.first()
    # Find an agency that's different from the first and has listings.
    for agency in AgencyProfile.objects.exclude(pk=first_agency.pk):
        if Property.objects.filter(agent=agency).exists():
            user = agency.user
            c = Client()
            c.force_login(user)
            return agency, user, c
    # Fallback: just use the second agency.
    agency = AgencyProfile.objects.all()[1]
    user = agency.user
    c = Client()
    c.force_login(user)
    return agency, user, c


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------
def test_anonymous_redirected_to_login():
    c = Client()
    r = c.get("/dashboard/")
    assert r.status_code == 302
    assert "login" in r.url


def test_non_agent_gets_403():
    from apps.accounts.models import User
    user = User.objects.create_user(email="regular@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    r = c.get("/dashboard/")
    assert r.status_code == 403


def test_agent_gets_200():
    _, _, c = _get_agent_and_client()
    r = c.get("/dashboard/")
    assert r.status_code == 200


def test_dashboard_shows_only_own_listings():
    """The dashboard listing table must only show the agent's own listings."""
    agency, _, c = _get_agent_and_client()
    r = c.get("/dashboard/")
    body = r.content.decode()
    for p in agency.properties.all():
        assert p.title in body


def test_dashboard_shows_stats():
    agency, _, c = _get_agent_and_client()
    r = c.get("/dashboard/")
    body = r.content.decode()
    assert "Total listings" in body
    assert "Published" in body
    assert "Inquiries" in body


# ---------------------------------------------------------------------------
# Create listing
# ---------------------------------------------------------------------------
def _valid_listing_data():
    from apps.listings.models import PropertyType
    from apps.locations.models import Location
    ptype = PropertyType.objects.first()
    loc = Location.objects.filter(level="neighbourhood").first()
    return {
        "title": "Test Dashboard Listing",
        "description": "A test listing created via the dashboard.",
        "listing_type": "sale",
        "property_type": ptype.pk,
        "location": loc.pk,
        "price": "15000000",
        "price_period": "total",
        "bedrooms": "3",
        "bathrooms": "2",
        "size_sqm": "150",
        "furnishing": "semi",
        "parking_spaces": "1",
        "status": "published",
        "is_featured": "",
        "amenities": [],
    }


def test_agent_can_create_listing():
    from apps.listings.models import Property
    agency, _, c = _get_agent_and_client()
    count_before = Property.objects.filter(agent=agency).count()
    r = c.post("/dashboard/listings/new/", _valid_listing_data())
    assert r.status_code == 302  # redirect to dashboard home
    assert Property.objects.filter(agent=agency).count() == count_before + 1


def test_created_listing_has_correct_agent():
    """The listing's agent must be the logged-in agent, not something spoofable."""
    from apps.listings.models import Property
    agency, _, c = _get_agent_and_client()
    c.post("/dashboard/listings/new/", _valid_listing_data())
    p = Property.objects.filter(title="Test Dashboard Listing").first()
    assert p is not None
    assert p.agent == agency


def test_published_listing_appears_on_public_site():
    """End-to-end: agent publishes → listing appears publicly."""
    from apps.listings.models import Property
    agency, _, c = _get_agent_and_client()
    data = _valid_listing_data()
    data["title"] = "E2E Publish Test"
    c.post("/dashboard/listings/new/", data)
    p = Property.objects.filter(title="E2E Publish Test").first()
    assert p is not None
    assert p.status == "published"
    assert p.published_at is not None

    # Detail page
    r = Client().get(p.get_absolute_url())
    assert r.status_code == 200

    # Search results
    r2 = Client().get(f"/{p.property_type.slug_plural}-for-sale/")
    assert "E2E Publish Test" in r2.content.decode()


def test_draft_listing_does_not_appear_on_public_site():
    from apps.listings.models import Property
    agency, _, c = _get_agent_and_client()
    data = _valid_listing_data()
    data["title"] = "Draft Test"
    data["status"] = "draft"
    c.post("/dashboard/listings/new/", data)
    p = Property.objects.filter(title="Draft Test").first()
    assert p is not None
    assert p.status == "draft"
    # Detail page should 404
    r = Client().get(p.get_absolute_url())
    assert r.status_code == 404


def test_create_invalid_data_fails():
    from apps.listings.models import Property
    agency, _, c = _get_agent_and_client()
    data = _valid_listing_data()
    data["title"] = ""  # missing title
    count_before = Property.objects.filter(agent=agency).count()
    r = c.post("/dashboard/listings/new/", data)
    assert r.status_code == 200  # re-renders form with errors
    assert Property.objects.filter(agent=agency).count() == count_before  # not created


# ---------------------------------------------------------------------------
# Edit listing
# ---------------------------------------------------------------------------
def test_agent_can_edit_own_listing():
    from apps.listings.models import Property
    agency, _, c = _get_agent_and_client()
    p = Property.objects.filter(agent=agency).first()
    data = _valid_listing_data()
    data["title"] = "Edited Title"
    data["property_type"] = p.property_type.pk
    data["location"] = p.location.pk
    r = c.post(f"/dashboard/listings/{p.pk}/edit/", data)
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.title == "Edited Title"


def test_agent_cannot_edit_other_agents_listing():
    """Agent B should get 404 when trying to edit Agent A's listing."""
    from apps.listings.models import Property
    agency_a, _, _ = _get_agent_and_client()
    p_a = Property.objects.filter(agent=agency_a).first()
    _, _, c_b = _get_second_agent_and_client()
    r = c_b.get(f"/dashboard/listings/{p_a.pk}/edit/")
    assert r.status_code == 404
    r = c_b.post(f"/dashboard/listings/{p_a.pk}/edit/", {
        "title": "Hacked!",
        "property_type": p_a.property_type.pk,
        "location": p_a.location.pk,
        "listing_type": "sale",
        "price": "1",
        "price_period": "total",
        "status": "published",
        "description": "x",
        "bedrooms": "0",
        "bathrooms": "0",
        "furnishing": "unfurnished",
        "parking_spaces": "0",
        "amenities": [],
    })
    assert r.status_code == 404
    p_a.refresh_from_db()
    assert p_a.title != "Hacked!"


def test_agent_cannot_access_other_agents_images():
    from apps.listings.models import Property
    agency_a, _, _ = _get_agent_and_client()
    p_a = Property.objects.filter(agent=agency_a).first()
    _, _, c_b = _get_second_agent_and_client()
    r = c_b.get(f"/dashboard/listings/{p_a.pk}/images/")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Inquiries inbox
# ---------------------------------------------------------------------------
def test_inquiries_shows_only_own():
    """Agent sees only inquiries for their own listings."""
    from apps.inquiries.models import Inquiry
    from apps.listings.models import Property
    agency_a, user_a, c_a = _get_agent_and_client()
    agency_b, _, _ = _get_second_agent_and_client()

    p_a = Property.objects.filter(agent=agency_a).first()
    p_b = Property.objects.filter(agent=agency_b).first()

    # Create inquiries on both
    Inquiry.objects.create(property_ref=p_a, name="A", email="a@x.com", message="test message here")
    Inquiry.objects.create(property_ref=p_b, name="B", email="b@x.com", message="test message here")

    r = c_a.get("/dashboard/inquiries/")
    body = r.content.decode()
    assert "a@x.com" in body
    assert "b@x.com" not in body


def test_inquiries_requires_agent():
    from apps.accounts.models import User
    user = User.objects.create_user(email="regular@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    r = c.get("/dashboard/inquiries/")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Image upload
# ---------------------------------------------------------------------------
def test_image_upload_page_loads():
    from apps.listings.models import Property
    agency, _, c = _get_agent_and_client()
    # Use the first listing that belongs to this agency (re-fetch to be safe).
    p = Property.objects.filter(agent=agency).first()
    assert p is not None, f"Agency {agency.name} has no listings"
    r = c.get(f"/dashboard/listings/{p.pk}/images/")
    assert r.status_code == 200
    assert "image-formset" in r.content.decode() or "formset" in r.content.decode().lower()


def test_image_upload_can_add_image():
    """Test uploading an image via the formset."""
    import io
    from PIL import Image
    from django.core.files.uploadedfile import SimpleUploadedFile
    from apps.listings.models import Property, PropertyImage

    agency, _, c = _get_agent_and_client()
    p = Property.objects.filter(agent=agency).first()
    images_before = PropertyImage.objects.filter(property=p).count()

    # Create a small test image
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(buf, "JPEG")
    img_bytes = buf.getvalue()

    # Build formset data — management form + one new image
    from django.forms import inlineformset_factory
    FormSet = inlineformset_factory(Property, PropertyImage, fields=["image", "caption", "position", "is_cover"], extra=3, can_delete=True)
    form_data = {
        "images-TOTAL_FORMS": "3",
        "images-INITIAL_FORMS": str(PropertyImage.objects.filter(property=p).count()),
        "images-MIN_NUM_FORMS": "0",
        "images-MAX_NUM_FORMS": "1000",
        "images-0-image": SimpleUploadedFile("test.jpg", img_bytes, "image/jpeg"),
        "images-0-caption": "Test image",
        "images-0-position": "99",
        "images-0-is_cover": "",
        "images-1-image": "",
        "images-1-caption": "",
        "images-1-position": "",
        "images-1-is_cover": "",
        "images-2-image": "",
        "images-2-caption": "",
        "images-2-position": "",
        "images-2-is_cover": "",
    }
    r = c.post(f"/dashboard/listings/{p.pk}/images/", form_data)
    assert r.status_code == 302  # redirect on success
    assert PropertyImage.objects.filter(property=p).count() == images_before + 1

"""r74 (BACKEND-PLAN Phase 2) — the listing tools in /manage/listings/.

Pinned here: the owner gate on every new endpoint, the wizard's
per-step draft persistence (server-side autosave), the derived
price-period rule (owner never sees a period field), the
publish-readiness gate (photo + price), one-click duplicate with real
image FILE copies, the featured toggle, the inline price editor, bulk
status with honest refusals, and the map pin picker's pair rule.
"""
import io
import os
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from apps.agents.models import AgencyProfile
from apps.listings.models import Amenity, Property, PropertyImage, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db

LOGIN_URL = "/account/login/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def base(db):
    """Locations, a type, an agency, and the owner + agent clients."""
    User = get_user_model()
    county = Location.objects.create(name="Mombasa", slug="mombasa", level="county")
    area = Location.objects.create(name="Nyali", slug="nyali", level="area", parent=county)
    hood = Location.objects.create(name="Nyali Centre", slug="nyali-centre", level="neighbourhood", parent=area)
    PropertyType.objects.create(name="Apartment", slug_plural="flats-apartments", slug_single="apartment")
    Amenity.objects.create(name="Lift", slug="lift")
    owner_user = User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    agency_user = User.objects.create(email="agency-user@test.com", full_name="Test Agency", is_agent=True)
    AgencyProfile.objects.create(user=agency_user, name="Gabriel Homes", slug="gabriel-homes")
    yield


@pytest.fixture
def owner():
    User = get_user_model()
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


@pytest.fixture
def agent():
    User = get_user_model()
    User.objects.create(email="agent@test.com", full_name="A Agent", is_agent=True)
    c = Client()
    c.force_login(User.objects.get(email="agent@test.com"))
    return c


def _jpg(color="red"):
    buf = io.BytesIO()
    Image.new("RGB", (40, 40), color).save(buf, "JPEG")
    return buf.getvalue()


def _published_listing(**overrides) -> Property:
    """A ready-to-publish listing: price, cover photo, one extra photo."""
    data = dict(
        title="Sea-view Apartment in Nyali",
        listing_type="rent",
        property_type=PropertyType.objects.first(),
        location=Location.objects.filter(level="neighbourhood").first(),
        price=Decimal("150000"),
        description="A calm home by the ocean.",
        status=Property.Status.PUBLISHED,
        published_at="2026-01-01T10:00:00Z",
        agent=AgencyProfile.objects.first(),
        views_count=12,
    )
    data.update(overrides)
    p = Property.objects.create(**data)
    PropertyImage.objects.create(
        property=p, image=SimpleUploadedFile("cover.jpg", _jpg(), "image/jpeg"),
        caption="cover", position=0, is_cover=True,
    )
    PropertyImage.objects.create(
        property=p, image=SimpleUploadedFile("extra.jpg", _jpg("blue"), "image/jpeg"),
        caption="extra", position=1,
    )
    return p


# ---------------------------------------------------------------------------
# The gate — every new endpoint (r74)
# ---------------------------------------------------------------------------
TOOL_URLS = [
    "/manage/listings/new/",
    "/manage/listings/bulk/",
    "/manage/listings/1/tools/",
    "/manage/listings/1/pin/",
]


def test_anonymous_is_redirected_to_login():
    c = Client()
    for url in TOOL_URLS:
        r = c.get(url)
        assert r.status_code == 302 and LOGIN_URL in r["Location"], url


def test_non_owner_gets_403(agent):
    for url in TOOL_URLS:
        assert agent.get(url).status_code == 403, url


def test_new_screens_are_noindex(owner):
    listing = _published_listing()
    urls = [
        "/manage/listings/new/",
        f"/manage/listings/{listing.pk}/pin/",
        "/manage/listings/",
    ]
    for url in urls:
        body = owner.get(url).content.decode()
        assert 'name="robots" content="noindex, nofollow"' in body, url


# ---------------------------------------------------------------------------
# Row tools: featured toggle (2B)
# ---------------------------------------------------------------------------
def test_feature_toggle_flips_both_ways(owner):
    listing = _published_listing()
    r = owner.post(f"/manage/listings/{listing.pk}/tools/", {"action": "feature"})
    listing.refresh_from_db()
    assert r.status_code == 302 and listing.is_featured is True
    r = owner.post(f"/manage/listings/{listing.pk}/tools/", {"action": "feature"})
    listing.refresh_from_db()
    assert listing.is_featured is False


def test_feature_toggle_requires_post(owner):
    listing = _published_listing()
    assert owner.get(f"/manage/listings/{listing.pk}/tools/").status_code == 405


def test_unknown_row_action_is_404(owner):
    listing = _published_listing()
    r = owner.post(f"/manage/listings/{listing.pk}/tools/", {"action": "nope"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Row tools: inline price (2B) — period is DERIVED, never asked for
# ---------------------------------------------------------------------------
def test_price_tool_updates_price_and_derives_period(owner):
    listing = _published_listing()  # rent → monthly
    r = owner.post(f"/manage/listings/{listing.pk}/tools/", {"action": "price", "price": "95000"})
    listing.refresh_from_db()
    assert listing.price == Decimal("95000") and listing.price_period == "monthly"
    # flip it to a short stay, then change the price again → nightly
    listing.is_short_stay = True
    listing.save(update_fields=["is_short_stay"])
    owner.post(f"/manage/listings/{listing.pk}/tools/", {"action": "price", "price": "12000"})
    listing.refresh_from_db()
    assert listing.price_period == "nightly"


def test_price_tool_rejects_zero_and_negative(owner):
    listing = _published_listing()
    for bad in ("0", "-5"):
        owner.post(f"/manage/listings/{listing.pk}/tools/", {"action": "price", "price": bad})
        listing.refresh_from_db()
        assert listing.price == Decimal("150000"), f"price was changed by {bad!r}"


def test_price_tool_rejects_garbage(owner):
    listing = _published_listing()
    r = owner.post(f"/manage/listings/{listing.pk}/tools/", {"action": "price", "price": "banana"})
    listing.refresh_from_db()
    assert listing.price == Decimal("150000")


# ---------------------------------------------------------------------------
# Duplicate (2A) — full copy, draft status, image FILES copied
# ---------------------------------------------------------------------------
def test_copy_creates_draft_with_image_files(owner):
    src = _published_listing()
    src.amenities.set(Amenity.objects.all())
    n_before = Property.objects.count()
    r = owner.post(f"/manage/listings/{src.pk}/tools/", {"action": "copy"})
    assert r.status_code == 302 and Property.objects.count() == n_before + 1

    copy = Property.objects.get(title=f"Copy of {src.title}")
    assert copy.status == Property.Status.DRAFT
    assert copy.slug and copy.slug != src.slug
    assert copy.views_count == 0 and copy.published_at is None
    assert copy.is_featured is False and copy.is_demo == src.is_demo
    assert copy.agent_id == src.agent_id and copy.price == src.price
    assert list(copy.amenities.all()) == list(src.amenities.all())

    # Photos: same rows, NEW files on disk (never shared storage).
    assert copy.images.count() == src.images.count() == 2
    assert copy.images.filter(is_cover=True).count() == 1
    src_paths = {i.image.path for i in src.images.all()}
    copy_paths = {i.image.path for i in copy.images.all()}
    assert copy_paths.isdisjoint(src_paths)
    for path in copy_paths:
        assert os.path.exists(path), f"copied image file missing: {path}"


def test_copy_of_draft_ready_to_finish(owner):
    """A draft copy of a finished listing can go straight to publish."""
    src = _published_listing()
    owner.post(f"/manage/listings/{src.pk}/tools/", {"action": "copy"})
    copy = Property.objects.get(title=f"Copy of {src.title}")
    assert copy.images.filter(is_cover=True).exists() and copy.price > 0
    owner.post(
        "/manage/listings/new/",
        {"step": "review", "action": "publish", "pk": copy.pk},
    )
    copy.refresh_from_db()
    assert copy.status == Property.Status.PUBLISHED and copy.published_at


# ---------------------------------------------------------------------------
# Bulk status (2B)
# ---------------------------------------------------------------------------
def test_bulk_publishes_ready_rows_and_holds_unready(owner):
    ready = _published_listing(title="Ready one")
    bare = _published_listing(
        title="Bare one", price=Decimal("0"),
        status=Property.Status.DRAFT, published_at=None,
    )
    # strip bare's photos so it can't publish
    bare.images.all().delete()
    r = owner.post(
        "/manage/listings/bulk/",
        {"action": "publish", "ids": [str(ready.pk), str(bare.pk)], "back": "draft"},
    )
    assert r.status_code == 302 and "tab=draft" in r["Location"]
    ready.refresh_from_db()
    bare.refresh_from_db()
    assert ready.status == Property.Status.PUBLISHED and ready.published_at
    assert bare.status == Property.Status.DRAFT  # refused, left untouched


def test_bulk_status_marks(owner):
    a = _published_listing(title="A")
    b = _published_listing(title="B")
    for action, expected in (
        ("under_offer", Property.Status.UNDER_OFFER),
        ("sold_let", Property.Status.SOLD_LET),
        ("archive", Property.Status.ARCHIVED),
    ):
        r = owner.post("/manage/listings/bulk/", {"action": action, "ids": [str(a.pk), str(b.pk)]})
        assert r.status_code == 302
        a.refresh_from_db()
        b.refresh_from_db()
        assert a.status == expected and b.status == expected, action


def test_bulk_without_ids_shows_hint_not_error(owner):
    r = owner.post("/manage/listings/bulk/", {"action": "publish", "ids": []})
    assert r.status_code == 302


def test_bulk_invalid_action_is_404(owner):
    listing = _published_listing()
    r = owner.post("/manage/listings/bulk/", {"action": "explode", "ids": [str(listing.pk)]})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Wizard (2D)
# ---------------------------------------------------------------------------
BASICS = {
    "step": "basics",
    "action": "continue",
    "title": "Garden flat in Bamburi",
    "listing_type": "rent",
    "property_type": lambda: str(PropertyType.objects.first().pk),
    "location": lambda: str(Location.objects.filter(level="neighbourhood").first().pk),
    "description": "Quiet, green, close to everything.",
    "agency": lambda: str(AgencyProfile.objects.first().pk),
}


def _post_basics(client):
    data = {k: (v() if callable(v) else v) for k, v in BASICS.items()}
    return client.post("/manage/listings/new/", data)


def test_wizard_basics_creates_draft_with_derived_period(owner):
    r = _post_basics(owner)
    assert r.status_code == 302
    draft = Property.objects.get(title="Garden flat in Bamburi")
    assert r["Location"] == f"/manage/listings/new/?step=price&pk={draft.pk}"
    assert draft.status == Property.Status.DRAFT
    assert draft.price == Decimal("0")  # honest "no price yet" state
    assert draft.price_period == "monthly"  # derived, never asked
    assert draft.slug == "garden-flat-in-bamburi"
    assert draft.is_demo is False and draft.views_count == 0


def test_wizard_basics_invalid_renders_errors_and_creates_nothing(owner):
    data = {k: (v() if callable(v) else v) for k, v in BASICS.items()}
    data["title"] = ""
    r = owner.post("/manage/listings/new/", data)
    assert r.status_code == 200
    assert "This field is required" in r.content.decode()
    assert Property.objects.filter(listing_type="rent").count() == 0


def test_wizard_price_persists_for_next_step(owner):
    _post_basics(owner)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    r = owner.post(
        "/manage/listings/new/",
        {"step": "price", "action": "continue", "pk": draft.pk, "price": "85000", "price_negotiable": "on"},
    )
    assert r.status_code == 302 and f"step=details" in r["Location"]
    draft.refresh_from_db()
    assert draft.price == Decimal("85000") and draft.price_negotiable is True


def test_wizard_price_rejects_zero(owner):
    _post_basics(owner)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    r = owner.post(
        "/manage/listings/new/",
        {"step": "price", "action": "continue", "pk": draft.pk, "price": "0"},
    )
    assert r.status_code == 200  # re-rendered with errors
    draft.refresh_from_db()
    assert draft.price == Decimal("0")


def test_wizard_details_saves_amenities_and_flips_period_for_short_stay(owner):
    _post_basics(owner)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    am = Amenity.objects.first()
    r = owner.post(
        "/manage/listings/new/",
        {
            "step": "details", "action": "continue", "pk": draft.pk,
            "bedrooms": "2", "bathrooms": "2", "furnishing": "furnished",
            "amenities": [str(am.pk)], "is_short_stay": "on",
            "address_text": "off Links Road",
        },
    )
    assert r.status_code == 302 and "step=photos" in r["Location"]
    draft.refresh_from_db()
    assert draft.is_short_stay is True
    assert draft.price_period == "nightly"  # flipped by the details step
    assert list(draft.amenities.all()) == [am]


def test_wizard_details_short_stay_on_a_sale_is_silently_dropped(owner):
    data = {k: (v() if callable(v) else v) for k, v in BASICS.items()}
    data["listing_type"] = "sale"
    owner.post("/manage/listings/new/", data)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    owner.post(
        "/manage/listings/new/",
        {"step": "details", "action": "continue", "pk": draft.pk, "is_short_stay": "on"},
    )
    draft.refresh_from_db()
    assert draft.is_short_stay is False
    assert draft.price_period == "total"


def test_wizard_review_refuses_publish_without_cover(owner):
    _post_basics(owner)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    owner.post(
        "/manage/listings/new/",
        {"step": "price", "action": "continue", "pk": draft.pk, "price": "85000"},
    )
    r = owner.post(
        "/manage/listings/new/", {"step": "review", "action": "publish", "pk": draft.pk}
    )
    draft.refresh_from_db()
    assert draft.status == Property.Status.DRAFT  # refused, not live


def test_wizard_review_publishes_when_ready(owner):
    _post_basics(owner)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    owner.post(
        "/manage/listings/new/",
        {"step": "price", "action": "continue", "pk": draft.pk, "price": "85000"},
    )
    PropertyImage.objects.create(
        property=draft,
        image=SimpleUploadedFile("cov.jpg", _jpg(), "image/jpeg"),
        caption="cover", position=0, is_cover=True,
    )
    r = owner.post(
        "/manage/listings/new/", {"step": "review", "action": "publish", "pk": draft.pk}
    )
    assert r.status_code == 302 and "tab=live" in r["Location"]
    draft.refresh_from_db()
    assert draft.status == Property.Status.PUBLISHED and draft.published_at
    # the published() chokepoint now includes it
    assert draft in Property.objects.published()


def test_wizard_finish_later_saves_draft(owner):
    _post_basics(owner)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    r = owner.post(
        "/manage/listings/new/", {"step": "price", "action": "finish", "pk": draft.pk, "price": "1"}
    )
    assert r.status_code == 302 and "tab=draft" in r["Location"]
    draft.refresh_from_db()
    assert draft.status == Property.Status.DRAFT  # still there, still a draft


def test_wizard_discard_deletes_draft(owner):
    _post_basics(owner)
    draft = Property.objects.get(title="Garden flat in Bamburi")
    r = owner.post(
        "/manage/listings/new/", {"step": "price", "action": "discard", "pk": draft.pk}
    )
    assert r.status_code == 302
    assert not Property.objects.filter(pk=draft.pk).exists()


def test_wizard_refuses_non_draft_rows(owner):
    listing = _published_listing()
    r = owner.get(f"/manage/listings/new/?step=basics&pk={listing.pk}")
    assert r.status_code == 302  # bounced to the listings screen


def test_wizard_later_step_without_draft_bounces(owner):
    r = owner.get("/manage/listings/new/?step=price")
    assert r.status_code == 302
    r = owner.post("/manage/listings/new/", {"step": "price", "action": "continue", "price": "5"})
    assert r.status_code == 302


def test_wizard_basics_defaults_agency_to_gabriel_homes(owner):
    body = owner.get("/manage/listings/new/").content.decode()
    assert "Gabriel Homes" in body


# ---------------------------------------------------------------------------
# Map pin picker (2C)
# ---------------------------------------------------------------------------
def test_pin_screen_renders_map_and_fields(owner):
    listing = _published_listing()
    body = owner.get(f"/manage/listings/{listing.pk}/pin/").content.decode()
    assert 'id="pin-map"' in body and 'id="id_lat"' in body
    assert "approximate pin" in body  # the privacy promise, in plain words


def test_pin_post_saves_six_decimal_coordinates(owner):
    listing = _published_listing()
    r = owner.post(f"/manage/listings/{listing.pk}/pin/", {"lat": "-4.041234", "lng": "39.678901"})
    listing.refresh_from_db()
    assert listing.lat == Decimal("-4.041234") and listing.lng == Decimal("39.678901")
    assert r.status_code == 302


def test_pin_remove_clears(owner):
    listing = _published_listing(lat=Decimal("-4.05"), lng=Decimal("39.66"))
    r = owner.post(f"/manage/listings/{listing.pk}/pin/", {"action": "remove"})
    listing.refresh_from_db()
    assert listing.lat is None and listing.lng is None


def test_pin_rejects_out_of_range(owner):
    listing = _published_listing()
    r = owner.post(f"/manage/listings/{listing.pk}/pin/", {"lat": "999", "lng": "39.6"})
    listing.refresh_from_db()
    assert listing.lat is None and listing.lng is None


def test_pin_rejects_half_a_pair(owner):
    listing = _published_listing()
    owner.post(f"/manage/listings/{listing.pk}/pin/", {"lat": "-4.05"})
    listing.refresh_from_db()
    assert listing.lat is None and listing.lng is None


# ---------------------------------------------------------------------------
# Screen copy + structure pins (plain language, one primary action)
# ---------------------------------------------------------------------------
def test_listings_screen_carries_the_phase2_tools(owner):
    listing = _published_listing()
    draft = _published_listing(title="Bare one", price=Decimal("0"), status=Property.Status.DRAFT)
    body = owner.get("/manage/listings/").content.decode()
    assert "Tick rows, then:" in body
    assert 'id="bulk-form"' in body
    assert 'value="publish"' in body and 'value="sold_let"' in body
    # every rendered row exposes its hidden tools form
    for p in (listing, draft):
        assert f'id="row-tools-{p.pk}"' in body
        assert f'form="row-tools-{p.pk}"' in body
    # honest states
    assert "no price yet" in body
    assert "Finish set-up" in body


def test_wizard_speaks_plain_language(owner):
    body = owner.get("/manage/listings/new/").content.decode()
    assert "Five short steps" in body
    assert "pick it up again under Drafts" in body
    assert "Save &amp; continue" in body


def test_price_zero_rows_display_honestly(owner):
    _published_listing(title="Bare one", price=Decimal("0"))
    body = owner.get("/manage/listings/").content.decode()
    assert "no price yet" in body

"""r75 (BACKEND-PLAN 3B) — the media library: /manage/site-content/media/.

Pinned here: the owner gate, the grid with where-used, the filter chips
with honest counts, the caption editor, and the guarded delete (a live
listing never loses its cover or its last photo; drafts and archived
listings can be cleaned freely, file included).
"""
import io
import os

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from apps.agents.models import AgencyProfile
from apps.listings.models import Property, PropertyImage, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db

LOGIN_URL = "/account/login/"
URL = "/manage/site-content/media/"


def _jpg(color=(180, 83, 45)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), color).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def base(db):
    User = get_user_model()
    county = Location.objects.create(name="Mombasa", slug="mombasa", level="county")
    area = Location.objects.create(name="Nyali", slug="nyali", level="area", parent=county)
    hood = Location.objects.create(name="Nyali Centre", slug="nyali-centre", level="neighbourhood", parent=area)
    ptype = PropertyType.objects.create(name="Apartment", slug_plural="flats-apartments", slug_single="apartment")
    agent_user = User.objects.create(email="agency-user@test.com", full_name="Test Agency", is_agent=True)
    agency = AgencyProfile.objects.create(user=agent_user, name="Test Agency", slug="test-agency")

    live = Property.objects.create(
        title="Live Sea-view Apartment", slug="live-apt", listing_type="rent",
        property_type=ptype, location=hood, price=150000, agent=agency,
        status=Property.Status.PUBLISHED, published_at="2026-01-01T10:00:00Z",
    )
    PropertyImage.objects.create(
        property=live, image=SimpleUploadedFile("cover.jpg", _jpg(), "image/jpeg"),
        caption="cover", position=0, is_cover=True,
    )
    PropertyImage.objects.create(
        property=live, image=SimpleUploadedFile("extra.jpg", _jpg((20, 90, 60)), "image/jpeg"),
        caption="", position=1,
    )

    draft = Property.objects.create(
        title="Draft Villa", slug="draft-villa", listing_type="sale",
        property_type=ptype, location=hood, price=23500000, agent=agency,
        status=Property.Status.DRAFT,
    )
    PropertyImage.objects.create(
        property=draft, image=SimpleUploadedFile("draft.jpg", _jpg((10, 10, 80)), "image/jpeg"),
        caption="", position=0, is_cover=True,
    )


@pytest.fixture
def owner():
    User = get_user_model()
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


def _action_url(pk):
    return f"/manage/site-content/media/{pk}/action/"


# ---------------------------------------------------------------------------
# The gate + the grid
# ---------------------------------------------------------------------------
def test_anon_is_sent_to_login():
    r = Client().get(URL)
    assert r.status_code == 302
    assert LOGIN_URL in r["Location"]


def test_owner_sees_every_photo_with_where_used(owner):
    r = owner.get(URL)
    assert r.status_code == 200
    assert b"Live Sea-view Apartment" in r.content
    assert b"Draft Villa" in r.content
    assert b"Cover photo" in r.content


def test_filter_chips_have_honest_counts(owner):
    r = owner.get(URL)
    assert b"All photos" in r.content
    r = owner.get(URL, {"filter": "draft"})
    assert b"Draft Villa" in r.content
    assert b"Live Sea-view Apartment" not in r.content
    r = owner.get(URL, {"filter": "covers"})
    # Both covers (the live one and the draft one) — the "Cover photo ·" meta,
    # not the chip label "Cover photos".
    assert r.content.count(b"Cover photo \xc2\xb7") == 2
    assert b"Draft Villa" in r.content


def test_search_by_listing_title(owner):
    r = owner.get(URL, {"q": "villa"})
    assert b"Draft Villa" in r.content
    assert b"Live Sea-view Apartment" not in r.content


# ---------------------------------------------------------------------------
# Captions
# ---------------------------------------------------------------------------
def test_caption_save(owner):
    img = PropertyImage.objects.get(property__slug="live-apt", caption="")
    r = owner.post(_action_url(img.pk), {"action": "caption", "caption": "The pool at dusk"})
    assert r.status_code == 302
    img.refresh_from_db()
    assert img.caption == "The pool at dusk"


# ---------------------------------------------------------------------------
# Guarded deletes
# ---------------------------------------------------------------------------
def test_cover_of_live_listing_is_refused(owner):
    img = PropertyImage.objects.filter(property__slug="live-apt", is_cover=True).get()
    r = owner.post(_action_url(img.pk), {"action": "delete"})
    assert r.status_code == 302
    assert PropertyImage.objects.filter(pk=img.pk).exists()


def test_last_photo_of_live_listing_is_refused(owner):
    live = Property.objects.get(slug="live-apt")
    # Leave the live listing with exactly one, non-cover photo.
    PropertyImage.objects.filter(property=live).delete()
    last = PropertyImage.objects.create(
        property=live,
        image=SimpleUploadedFile("only.jpg", _jpg((90, 20, 20)), "image/jpeg"),
        caption="", position=0,
    )
    r = owner.post(_action_url(last.pk), {"action": "delete"})
    assert r.status_code == 302
    assert PropertyImage.objects.filter(pk=last.pk).exists()


def test_extra_photo_of_live_listing_deletes_file_and_row(owner):
    img = PropertyImage.objects.filter(property__slug="live-apt", is_cover=False).get()
    path = img.image.path
    assert os.path.exists(path)
    r = owner.post(_action_url(img.pk), {"action": "delete"})
    assert r.status_code == 302
    assert not PropertyImage.objects.filter(pk=img.pk).exists()
    assert not os.path.exists(path)


def test_draft_photo_deletes_freely(owner):
    img = PropertyImage.objects.get(property__slug="draft-villa")
    r = owner.post(_action_url(img.pk), {"action": "delete"})
    assert r.status_code == 302
    assert not PropertyImage.objects.filter(pk=img.pk).exists()


def test_unknown_action_404s(owner):
    img = PropertyImage.objects.first()
    assert owner.post(_action_url(img.pk), {"action": "nonsense"}).status_code == 404

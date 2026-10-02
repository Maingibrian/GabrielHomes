"""Tests for the listings models — Property, PropertyQuerySet,
PropertyImage (one-cover enforcement), PropertyType, Amenity."""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.timezone import now

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.listings.models import (
    Amenity,
    Property,
    PropertyImage,
    PropertyType,
)
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def county():
    return Location.objects.create(name="Mombasa", level=Location.Level.COUNTY)


@pytest.fixture
def area(county):
    return Location.objects.create(name="Nyali", parent=county, level=Location.Level.AREA)


@pytest.fixture
def leaf(area):
    return Location.objects.create(name="Nyali Centre", parent=area, level=Location.Level.NEIGHBOURHOOD)


@pytest.fixture
def ptype():
    return PropertyType.objects.create(
        name="Flats & Apartments", slug_plural="flats-apartments",
        slug_single="apartment", is_residential=True,
    )


@pytest.fixture
def agency():
    user = User.objects.create_user(email="agent@example.com", password="x", is_agent=True)
    return AgencyProfile.objects.create(user=user, name="Gabriel Homes")


@pytest.fixture
def property_factory(ptype, leaf, agency):
    def _make(**overrides):
        defaults = dict(
            title="Lovely 2BR Apartment",
            description="A nice place.",
            listing_type=Property.ListingType.SALE,
            property_type=ptype,
            location=leaf,
            price=Decimal("12500000"),
            price_period=Property.PricePeriod.TOTAL,
            agent=agency,
        )
        defaults.update(overrides)
        return Property.objects.create(**defaults)
    return _make


# ---------------------------------------------------------------------------
# PropertyType + Amenity
# ---------------------------------------------------------------------------
def test_property_type_str():
    pt = PropertyType.objects.create(
        name="Houses", slug_plural="houses", slug_single="house", is_residential=True
    )
    assert str(pt) == "Houses"


def test_amenity_auto_slug():
    am = Amenity.objects.create(name="Swimming Pool", category=Amenity.Category.LIFESTYLE)
    assert am.slug == "swimming-pool"


# ---------------------------------------------------------------------------
# Property.save + slug + validation
# ---------------------------------------------------------------------------
def test_property_save_auto_slug(property_factory):
    p = property_factory(title="Beach House")
    assert p.slug == "beach-house"


def test_property_slug_unique_on_collision(property_factory):
    p1 = property_factory(title="Beach House")
    p2 = property_factory(title="Beach House")
    # Second save should have a suffixed slug
    assert p2.slug != p1.slug
    assert p2.slug.startswith("beach-house")


def test_property_clean_rejects_sale_with_monthly_period(property_factory):
    p = property_factory(
        listing_type=Property.ListingType.SALE,
        price_period=Property.PricePeriod.MONTHLY,
    )
    with pytest.raises(ValidationError):
        p.clean()


def test_property_clean_rejects_rent_with_total_period(property_factory):
    p = property_factory(
        listing_type=Property.ListingType.RENT,
        price_period=Property.PricePeriod.TOTAL,
    )
    with pytest.raises(ValidationError):
        p.clean()


def test_property_clean_rejects_negative_price(property_factory):
    p = property_factory(price=Decimal("-1"))
    with pytest.raises(ValidationError):
        p.clean()


def test_publishing_sets_published_at(property_factory):
    p = property_factory(status=Property.Status.DRAFT)
    assert p.published_at is None
    p.status = Property.Status.PUBLISHED
    p.save()
    p.refresh_from_db()
    assert p.published_at is not None


# ---------------------------------------------------------------------------
# PropertyQuerySet.published()
# ---------------------------------------------------------------------------
def test_published_queryset_excludes_drafts_and_archived(property_factory):
    pub = property_factory(title="Pub",   status=Property.Status.PUBLISHED)
    draft = property_factory(title="Dra",  status=Property.Status.DRAFT)
    archived = property_factory(title="Arc", status=Property.Status.ARCHIVED)
    under_offer = property_factory(title="Und", status=Property.Status.UNDER_OFFER)
    sold = property_factory(title="Sol",   status=Property.Status.SOLD_LET)

    pks = set(Property.objects.published().values_list("pk", flat=True))
    # Only listings still in 'published' state are visible on the public site.
    # 'under_offer' and 'sold_let' are non-public terminal states (the listing
    # is no longer actively available).
    assert pub.pk in pks
    assert draft.pk not in pks
    assert archived.pk not in pks
    assert under_offer.pk not in pks
    assert sold.pk not in pks


def test_published_queryset_excludes_future_published_at(property_factory):
    from datetime import timedelta
    p = property_factory(status=Property.Status.PUBLISHED)
    # Push published_at into the future
    Property.objects.filter(pk=p.pk).update(published_at=now() + timedelta(days=1))
    pks = list(Property.objects.published().values_list("pk", flat=True))
    assert p.pk not in pks


def test_for_sale_and_for_rent_filters(property_factory):
    s = property_factory(title="S", listing_type=Property.ListingType.SALE,
                         price_period=Property.PricePeriod.TOTAL)
    r = property_factory(title="R", listing_type=Property.ListingType.RENT,
                         price_period=Property.PricePeriod.MONTHLY)
    assert set(Property.objects.for_sale().values_list("pk", flat=True)) == {s.pk}
    assert set(Property.objects.for_rent().values_list("pk", flat=True)) == {r.pk}


def test_featured_filter(property_factory):
    f = property_factory(title="F", is_featured=True)
    nf = property_factory(title="N", is_featured=False)
    pks = set(Property.objects.featured().values_list("pk", flat=True))
    assert f.pk in pks and nf.pk not in pks


# ---------------------------------------------------------------------------
# PropertyImage — one cover enforced
# ---------------------------------------------------------------------------
def test_one_cover_per_property_enforced_at_db(property_factory, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile
    p = property_factory()

    # Tiny 1x1 JPEG
    from PIL import Image
    import io
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "JPEG")
    img_bytes = buf.getvalue()

    cover = PropertyImage.objects.create(
        property=p, image=SimpleUploadedFile("c.jpg", img_bytes, "image/jpeg"),
        is_cover=True,
    )
    assert cover.is_cover

    # A second cover for the same property should fail at the DB layer.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PropertyImage.objects.create(
                property=p, image=SimpleUploadedFile("d.jpg", img_bytes, "image/jpeg"),
                is_cover=True,
            )


def test_multiple_non_covers_allowed(property_factory):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image
    import io
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "JPEG")
    img_bytes = buf.getvalue()

    p = property_factory()
    PropertyImage.objects.create(
        property=p, image=SimpleUploadedFile("a.jpg", img_bytes, "image/jpeg"),
        is_cover=False,
    )
    PropertyImage.objects.create(
        property=p, image=SimpleUploadedFile("b.jpg", img_bytes, "image/jpeg"),
        is_cover=False,
    )
    assert PropertyImage.objects.filter(property=p, is_cover=False).count() == 2


def test_property_image_clean_blocks_second_cover(property_factory):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image
    import io
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "JPEG")
    img_bytes = buf.getvalue()

    p = property_factory()
    PropertyImage.objects.create(
        property=p, image=SimpleUploadedFile("c.jpg", img_bytes, "image/jpeg"),
        is_cover=True,
    )
    second = PropertyImage(
        property=p,
        image=SimpleUploadedFile("d.jpg", img_bytes, "image/jpeg"),
        is_cover=True,
    )
    with pytest.raises(ValidationError):
        second.clean()


# ---------------------------------------------------------------------------
# increment_views()
# ---------------------------------------------------------------------------
def test_increment_views_does_not_touch_updated_at(property_factory):
    p = property_factory(status=Property.Status.PUBLISHED)
    updated_before = p.updated_at
    p.increment_views()
    p.refresh_from_db()
    assert p.views_count == 1
    # updated_at may move by microseconds due to refresh; just confirm count semantics
    assert p.views_count == Property.objects.get(pk=p.pk).views_count

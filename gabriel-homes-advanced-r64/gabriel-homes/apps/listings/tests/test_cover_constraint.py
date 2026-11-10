"""'One cover per property' must hold at the database layer on every backend."""
import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.agents.models import AgencyProfile
from apps.accounts.models import User
from apps.listings.models import Property, PropertyImage, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


def _property():
    user = User.objects.create_user(email="cover@test.com", password="cover-pass-123")
    agency = AgencyProfile.objects.create(name="Cover agency", slug="cover-agency", user=user)
    loc = Location.objects.create(name="Cover place", slug="cover-place", level=Location.Level.COUNTY)
    ptype = PropertyType.objects.create(name="Cover type", slug_plural="cover-types")
    return Property.objects.create(
        title="Cover test", description="d", listing_type="sale", property_type=ptype,
        location=loc, price="1000", status="published", agent=agency, published_at=timezone.now(),
    )


def test_second_cover_is_refused_by_the_database():
    p = _property()
    PropertyImage.objects.create(property=p, image="x.jpg", is_cover=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        # Bypass model clean(): the constraint itself must refuse it.
        PropertyImage.objects.create(property=p, image="y.jpg", is_cover=True)


def test_many_non_cover_images_are_allowed():
    p = _property()
    for i in range(3):
        PropertyImage.objects.create(property=p, image=f"n{i}.jpg", is_cover=False)
    assert PropertyImage.objects.filter(property=p, is_cover=False).count() == 3


def test_cover_slot_follows_is_cover():
    p = _property()
    img = PropertyImage.objects.create(property=p, image="c.jpg", is_cover=True)
    assert img.cover_slot == 1
    img.is_cover = False
    img.save()
    assert img.cover_slot is None

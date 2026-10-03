"""Tests for the seed_demo management command — idempotency + counts."""
import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.listings.models import Amenity, Property, PropertyImage, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


def _seed(**opts):
    """Run seed_demo with --no-images by default for speed."""
    defaults = {"no_images": True, "target": 80, "verbosity": 0}
    defaults.update(opts)
    call_command("seed_demo", **defaults)


def test_seed_creates_expected_counts():
    _seed()
    # 6 counties, plus areas and neighbourhoods
    assert Location.objects.filter(level=Location.Level.COUNTY).count() == 6
    # 11 property types
    assert PropertyType.objects.count() == 11
    # ~25 amenities
    assert Amenity.objects.count() >= 20
    # 6 agencies, each with a user
    assert AgencyProfile.objects.count() == 6
    assert User.objects.filter(is_agent=True).count() >= 6
    # ~80 listings
    assert Property.objects.count() == 80


def test_seed_is_idempotent():
    """Running seed_demo twice must not duplicate records."""
    _seed()
    counts_before = {
        "locations": Location.objects.count(),
        "types": PropertyType.objects.count(),
        "amenities": Amenity.objects.count(),
        "agencies": AgencyProfile.objects.count(),
        "agents": User.objects.filter(is_agent=True).count(),
        "listings": Property.objects.count(),
        "images": PropertyImage.objects.count(),
    }
    _seed()  # second run
    counts_after = {
        "locations": Location.objects.count(),
        "types": PropertyType.objects.count(),
        "amenities": Amenity.objects.count(),
        "agencies": AgencyProfile.objects.count(),
        "agents": User.objects.filter(is_agent=True).count(),
        "listings": Property.objects.count(),
        "images": PropertyImage.objects.count(),
    }
    assert counts_before == counts_after


def test_seed_clear_wipes_everything():
    _seed()
    assert Property.objects.exists()
    call_command("seed_demo", clear=True, no_images=True, target=10, verbosity=0)
    # After --clear, the seed runs again from scratch with target=10
    assert Property.objects.count() == 10


def test_seed_with_images_creates_at_least_one_cover_per_listing():
    call_command("seed_demo", clear=True, target=10, verbosity=0)
    # Every listing should have at least one image, marked as cover.
    for p in Property.objects.all():
        assert p.images.filter(is_cover=True).count() == 1, (
            f"Property {p.pk} missing a cover image"
        )


def test_seed_listings_are_published_and_have_real_locations():
    _seed()
    assert Property.objects.published().count() == 80
    # All listing locations are at neighbourhood level
    assert all(
        p.location.level == Location.Level.NEIGHBOURHOOD
        for p in Property.objects.all()
    )


def test_seed_listings_have_agent_and_type():
    _seed()
    for p in Property.objects.all():
        assert p.agent_id is not None
        assert p.property_type_id is not None

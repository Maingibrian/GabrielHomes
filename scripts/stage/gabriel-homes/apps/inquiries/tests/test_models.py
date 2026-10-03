"""Tests for the Inquiry model (apps.inquiries)."""
import pytest

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.inquiries.models import Inquiry
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


@pytest.fixture
def property_obj():
    user = User.objects.create_user(email="a@example.com", password="x", is_agent=True)
    agency = AgencyProfile.objects.create(user=user, name="Test Agency")
    county = Location.objects.create(name="Mombasa", level=Location.Level.COUNTY)
    area = Location.objects.create(name="Nyali", parent=county, level=Location.Level.AREA)
    leaf = Location.objects.create(name="Nyali Centre", parent=area, level=Location.Level.NEIGHBOURHOOD)
    ptype = PropertyType.objects.create(
        name="Flats & Apartments", slug_plural="flats-apartments", slug_single="apartment",
        is_residential=True,
    )
    return Property.objects.create(
        title="Test", slug="test",
        description="x", listing_type=Property.ListingType.SALE,
        property_type=ptype, location=leaf, price=10_000_000,
        price_period=Property.PricePeriod.TOTAL, agent=agency,
        status=Property.Status.PUBLISHED,
    )


def test_inquiry_defaults_to_new(property_obj):
    inq = Inquiry.objects.create(
        property_ref=property_obj, name="Jane", email="jane@example.com",
        phone="+254700000000", message="I'm interested.",
    )
    assert inq.status == Inquiry.Status.NEW
    assert inq.is_spam is False


def test_inquiry_honeypot_flags_spam(property_obj):
    inq = Inquiry.objects.create(
        property_ref=property_obj, name="Bot", email="bot@example.com",
        phone="", message="spam", honeypot="filled-by-bot",
    )
    assert inq.is_spam is True


def test_inquiry_user_optional(property_obj):
    inq = Inquiry.objects.create(
        property_ref=property_obj, name="Anon", email="anon@example.com",
        phone="", message="hi",
    )
    assert inq.user is None


def test_inquiry_user_link(property_obj):
    user = User.objects.create_user(email="u@example.com", password="x")
    inq = Inquiry.objects.create(
        property_ref=property_obj, user=user, name="U", email="u@example.com",
        phone="", message="hi",
    )
    assert inq.user_id == user.id

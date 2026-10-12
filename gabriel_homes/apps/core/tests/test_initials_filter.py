"""Tests for the initials template filter (monogram avatars)."""
import pytest

from apps.core.templatetags.core_tags import initials

pytestmark = pytest.mark.django_db


def test_two_words_gives_two_initials():
    assert initials("Ngong Ridge Properties") == "NR"


def test_single_word_gives_one_letter():
    assert initials("Gabriel") == "G"


def test_two_words_exact():
    assert initials("Gabriel Homes") == "GH"


def test_case_is_normalised():
    assert initials("coast homes") == "CH"


def test_empty_and_none_fall_back_to_brand():
    assert initials("") == "GH"
    assert initials(None) == "GH"


def test_extra_whitespace_is_ignored():
    assert initials("  Ridge   Valley  ") == "RV"


def test_filter_registered_in_templates(client):
    """The detail page renders the monogram when the agency has no logo."""
    from apps.accounts.models import User
    from apps.agents.models import AgencyProfile
    from apps.listings.models import Property, PropertyType
    from apps.locations.models import Location

    user = User.objects.create_user(email="mono@x.com", password="x", is_agent=True)
    agency = AgencyProfile.objects.create(user=user, name="Ngong Ridge Properties")
    county = Location.objects.create(name="C", level=Location.Level.COUNTY)
    area = Location.objects.create(name="A", parent=county, level=Location.Level.AREA)
    leaf = Location.objects.create(name="L", parent=area, level=Location.Level.NEIGHBOURHOOD)
    ptype = PropertyType.objects.create(name="T", slug_plural="t", slug_single="t")
    prop = Property.objects.create(
        title="Mono Test", listing_type=Property.ListingType.SALE, property_type=ptype,
        location=leaf, price=10_000_000, price_period=Property.PricePeriod.TOTAL,
        agent=agency, status=Property.Status.PUBLISHED,
    )
    html = client.get(prop.get_absolute_url()).content.decode()
    assert "logo-monogram" in html
    assert ">NR<" in html

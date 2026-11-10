"""r12 — short-stay / BnB listing rules on Property.

A short stay must be a rental priced per night; a long-term rental must
be priced monthly; sales stay total-priced. The short_stays() queryset
powers the BnB quick filter and the short-stay home group.
"""
import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


@pytest.fixture
def leaf():
    county = Location.objects.create(name="Mombasa", level=Location.Level.COUNTY)
    area = Location.objects.create(name="Nyali", parent=county, level=Location.Level.AREA)
    return Location.objects.create(name="Nyali Centre", parent=area, level=Location.Level.NEIGHBOURHOOD)


@pytest.fixture
def ptype():
    return PropertyType.objects.create(name="Villas", slug_plural="villas", slug_single="villa")


@pytest.fixture
def agency():
    user = User.objects.create_user(email="agent@example.com", password="x", is_agent=True)
    return AgencyProfile.objects.create(user=user, name="Gabriel Homes")


def _make(ptype, leaf, agency, **overrides):
    defaults = dict(
        title="Short stay home",
        listing_type=Property.ListingType.RENT,
        price_period=Property.PricePeriod.NIGHTLY,
        property_type=ptype,
        location=leaf,
        price="28000",
        agent=agency,
        is_short_stay=True,
    )
    defaults.update(overrides)
    return Property(**defaults)


def test_valid_short_stay_passes_clean(ptype, leaf, agency):
    p = _make(ptype, leaf, agency)
    p.clean()  # rent + nightly + short_stay flag — no error


def test_short_stay_must_be_a_rental(ptype, leaf, agency):
    p = _make(
        ptype, leaf, agency,
        listing_type=Property.ListingType.SALE,
        price_period=Property.PricePeriod.TOTAL,
    )
    with pytest.raises(ValidationError) as err:
        p.clean()
    assert "is_short_stay" in err.value.message_dict


def test_short_stay_must_use_nightly_pricing(ptype, leaf, agency):
    p = _make(ptype, leaf, agency, price_period=Property.PricePeriod.MONTHLY)
    with pytest.raises(ValidationError) as err:
        p.clean()
    assert "price_period" in err.value.message_dict


def test_long_term_rental_must_stay_monthly(ptype, leaf, agency):
    """Without the short-stay flag, nightly pricing is not a valid rent."""
    p = _make(ptype, leaf, agency, is_short_stay=False)
    with pytest.raises(ValidationError) as err:
        p.clean()
    assert "price_period" in err.value.message_dict


def test_short_stays_queryset_selects_only_flagged_rows(ptype, leaf, agency):
    bnb = _make(ptype, leaf, agency)
    bnb.save()
    monthly = _make(ptype, leaf, agency, is_short_stay=False,
                    price_period=Property.PricePeriod.MONTHLY, price="120000")
    monthly.save()
    sale = _make(ptype, leaf, agency, is_short_stay=False,
                 listing_type=Property.ListingType.SALE,
                 price_period=Property.PricePeriod.TOTAL, price="9000000")
    sale.save()

    short = list(Property.objects.short_stays())
    assert [bnb.pk] == [p.pk for p in short]
    assert monthly.pk not in [p.pk for p in short]

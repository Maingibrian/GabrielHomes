"""S12 — Input limits.

Spec (docs/PLAN.md S12): the enquiry form must cap `message`; `name`,
`email`, `phone` have max lengths and validators; the listing side must
cap `title` and `description`; `size_sqm`, `price`, and `bedrooms` must
reject negatives and absurd values. Caps are documented in the test names.
"""
import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.inquiries.models import Inquiry
from apps.listings.models import Property

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


# ---------------------------------------------------------------------------
# Field cap declarations (self-documenting via field metadata)
# ---------------------------------------------------------------------------
def test_message_cap_is_5000_chars():
    assert Inquiry._meta.get_field("message").max_length == 5000


def test_name_cap_is_160_chars():
    assert Inquiry._meta.get_field("name").max_length == 160


def test_phone_cap_is_32_chars():
    assert Inquiry._meta.get_field("phone").max_length == 32


def test_email_uses_django_email_validation():
    f = Inquiry(name="A", email="not-an-email", message="x", property_ref_id=1)
    with pytest.raises(ValidationError) as exc:
        f.full_clean(exclude=["property_ref", "slug"])
    assert "email" in exc.value.message_dict


def test_listing_title_cap_is_180_chars():
    assert Property._meta.get_field("title").max_length == 180


def test_listing_description_cap_is_20000_chars():
    assert Property._meta.get_field("description").max_length == 20000


# ---------------------------------------------------------------------------
# Value validation — negatives and absurd values
# ---------------------------------------------------------------------------
def _base_property(**overrides):
    from apps.agents.models import AgencyProfile
    from apps.listings.models import PropertyType
    from apps.locations.models import Location
    ptype = PropertyType.objects.first()
    loc = Location.objects.filter(level="neighbourhood").first()
    agent = AgencyProfile.objects.select_related("user").first()
    base = dict(
        title="Valid title", slug="valid-title-s12",
        description="A decent, realistic description.",
        listing_type=Property.ListingType.SALE,
        property_type=ptype, location=loc, agent=agent,
        price="12500000.00",
    )
    base.update(overrides)
    return Property(**base)


def test_price_rejects_negative_value():
    p = _base_property(price="-1.00")
    with pytest.raises(ValidationError) as exc:
        p.full_clean()
    assert "price" in exc.value.message_dict


def test_bedrooms_rejects_absurd_500_bedroom_value():
    p = _base_property(bedrooms=500)
    with pytest.raises(ValidationError) as exc:
        p.full_clean()
    assert "bedrooms" in exc.value.message_dict


def test_bathrooms_rejects_absurd_500_value():
    p = _base_property(bathrooms=500)
    with pytest.raises(ValidationError) as exc:
        p.full_clean()
    assert "bathrooms" in exc.value.message_dict


def test_size_sqm_rejects_absurd_over_100000_sqm():
    p = _base_property(size_sqm=500000)
    with pytest.raises(ValidationError) as exc:
        p.full_clean()
    assert "size_sqm" in exc.value.message_dict


def test_bedrooms_rejects_negative_value():
    with transaction.atomic():
        with pytest.raises((ValidationError, IntegrityError, DataErrorShim)):
            p = _base_property(bedrooms=-3)
            p.full_clean()


class DataErrorShim(Exception):
    """Accept either ValidationError (full_clean) or DB errors."""


def test_realistic_values_pass_full_clean():
    p = _base_property(bedrooms=4, bathrooms=3, size_sqm=220)
    p.full_clean()  # must not raise

"""P1-2 — BrandSettings row + brand contact card (single-owner mode).

The listing-detail sidebar card and mobile bar read the brand settings
row (singleton, empty code defaults), never the retired agency concept.
P3-8 will make the row owner-editable in /manage/; these tests pin the
public-side contract that editor must preserve.
"""
import pytest
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import Client

from apps.core.models import BrandSettings

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (detail page needs a published listing)."""
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


# ---------------------------------------------------------------------------
# Model: singleton, empty defaults, digits helper
# ---------------------------------------------------------------------------
def test_load_creates_singleton_with_empty_defaults():
    brand = BrandSettings.load()
    assert brand.pk == 1
    assert brand.phone == ""
    assert brand.whatsapp == ""
    assert brand.email == ""


def test_save_keeps_single_row():
    BrandSettings.load().save()
    brand = BrandSettings.load()
    brand.phone = "+254 700 000 000"
    brand.save()
    BrandSettings.load().save()  # another save must not fork a second row
    assert BrandSettings.objects.count() == 1
    assert BrandSettings.load().phone == "+254 700 000 000"


def test_whatsapp_digits_strips_formatting():
    brand = BrandSettings.load()
    brand.whatsapp = "+254 (712) 345-678"
    assert brand.whatsapp_digits == "254712345678"
    brand.whatsapp = ""
    assert brand.whatsapp_digits == ""


def test_load_is_defensive_before_migrations(monkeypatch):
    """Pre-migration window: load() returns a transient empty row, no raise."""

    def boom(*args, **kwargs):
        raise OperationalError("no such table: core_brandsettings")

    monkeypatch.setattr(BrandSettings.objects, "get_or_create", boom)
    brand = BrandSettings.load()
    assert brand.pk == 1
    assert brand.phone == ""


# ---------------------------------------------------------------------------
# Context processor: brand is on every public page
# ---------------------------------------------------------------------------
def test_brand_in_context_on_public_pages(client):
    for url in ("/", "/about/"):
        r = client.get(url)
        assert r.status_code == 200
        assert "brand" in r.context


def test_email_button_follows_brand_row(client):
    """Empty brand email = no mailto button; filled = mailto with subject."""
    from apps.listings.models import Property

    p = Property.objects.published().first()
    url = p.get_absolute_url()

    BrandSettings.load().save()
    body = Client().get(url).content.decode()
    assert "mailto:" not in body

    brand = BrandSettings.load()
    brand.email = "hello@gabrielhomes.co.ke"
    brand.save()
    body = Client().get(url).content.decode()
    assert 'href="mailto:hello@gabrielhomes.co.ke?subject=Enquiry' in body


def test_brand_row_escapes_into_markup(client):
    """Owner-entered values must arrive escaped (no raw HTML injection)."""
    from apps.listings.models import Property

    brand = BrandSettings.load()
    brand.phone = '<script>alert(1)</script>'
    brand.save()
    p = Property.objects.published().first()
    body = Client().get(p.get_absolute_url()).content.decode()
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Mobile sticky bar: renders only when a channel exists (no empty strip)
# ---------------------------------------------------------------------------
def test_mobile_bar_hidden_until_channel_exists(client):
    """Empty brand row = no mobile bar markup, no has-contact-bar class."""
    from apps.listings.models import Property

    BrandSettings.load().save()
    p = Property.objects.published().first()
    body = Client().get(p.get_absolute_url()).content.decode()
    assert "mobile-contact-bar" not in body
    assert "has-contact-bar" not in body


def test_mobile_bar_appears_when_phone_set(client):
    from apps.listings.models import Property

    brand = BrandSettings.load()
    brand.phone = "+254 712 000 111"
    brand.save()
    p = Property.objects.published().first()
    body = Client().get(p.get_absolute_url()).content.decode()
    assert "has-contact-bar" in body
    assert "mobile-contact-bar__btn--call" in body

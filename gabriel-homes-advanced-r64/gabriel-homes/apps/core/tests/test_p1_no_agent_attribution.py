"""P1-3 — no agency attribution on listing cards or in seed descriptions.

Single-owner mode: listing cards carry the brand contact only (index tag,
price, location — no agent logo/name), and seeded descriptions direct
enquirers to Gabriel Homes, never to "the listing agent".
"""
import importlib

import pytest
from django.core.management import call_command
from django.test import Client

m8 = importlib.import_module(
    "apps.listings.migrations.0008_fix_seed_agent_phrasing"
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (fresh template → already healed)."""
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


# ---------------------------------------------------------------------------
# Public pages: no "listing agent" phrasing anywhere
# ---------------------------------------------------------------------------
def test_properties_page_has_no_listing_agent_phrase(client):
    body = client.get("/properties/").content.decode()
    assert m8.OLD_SENTENCE not in body
    assert "listing agent" not in body


def test_detail_page_has_no_listing_agent_phrase(client):
    from apps.listings.models import Property

    p = Property.objects.published().first()
    body = Client().get(p.get_absolute_url()).content.decode()
    assert m8.OLD_SENTENCE not in body
    assert "listing agent" not in body


def test_listing_card_shows_no_agency_attribution(client):
    """The card body keeps index/price/location — never an agency identity."""
    from apps.agents.models import AgencyProfile
    from django.conf import settings

    body = client.get("/properties/").content.decode()
    other = (
        AgencyProfile.objects.exclude(name=settings.SITE_NAME)
        .values_list("name", flat=True)
    )
    for name in other:
        assert name not in body


def test_seed_descriptions_are_single_owner():
    """Fresh seeds speak single-owner language (no listing-agent phrasing)."""
    from apps.listings.models import Property

    assert (
        Property.objects.filter(description__contains=m8.OLD_SENTENCE).count() == 0
    )
    assert (
        Property.objects.filter(description__contains=m8.NEW_SENTENCE).count() > 0
    )


def test_heal_description_pure_swap():
    """Pure swap: old phrase rewritten, clean text passes through, idempotent."""
    old = "Checks completed. Contact the listing agent to arrange a viewing."
    healed = m8.heal_description(old)
    assert m8.NEW_SENTENCE in healed
    assert m8.OLD_SENTENCE not in healed
    # Owner-written text without the phrase passes through untouched.
    assert m8.heal_description("A family home in Kilifi.") == "A family home in Kilifi."
    # Idempotent + empty-safe.
    assert m8.heal_description(healed) == healed
    assert m8.heal_description("") == ""
    assert m8.heal_description(None) is None


def test_migration_heals_old_seed_rows_only(db):
    """The 0008 heal function: demo rows rewritten, real rows untouched."""
    from apps.listings.models import Property

    old_desc = (
        "A two-bed apartment in Nyali, Mombasa. Checks completed before "
        "publication. Contact the listing agent to arrange a viewing."
    )
    demo = Property.objects.order_by("pk").first()  # seeded → is_demo=True
    Property.objects.filter(pk=demo.pk).update(description=old_desc, is_demo=True)
    real = Property.objects.order_by("pk").last()
    Property.objects.filter(pk=real.pk).update(description=old_desc, is_demo=False)

    m8.heal_seed_phrasing(None, None)  # (apps, schema_editor) unused by design

    demo.refresh_from_db()
    real.refresh_from_db()
    assert m8.OLD_SENTENCE not in demo.description
    assert m8.NEW_SENTENCE in demo.description
    assert real.description == old_desc  # non-demo row never touched


def test_migration_is_idempotent(db):
    """Running the heal twice changes nothing the second time."""
    from apps.listings.models import Property

    before = list(
        Property.objects.order_by("pk").values_list("pk", "description")
    )
    m8.heal_seed_phrasing(None, None)
    m8.heal_seed_phrasing(None, None)
    after = list(
        Property.objects.order_by("pk").values_list("pk", "description")
    )
    assert before == after

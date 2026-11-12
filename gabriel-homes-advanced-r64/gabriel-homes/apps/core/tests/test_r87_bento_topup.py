"""r87 — the bento tops up thin real inventory with the labelled
Mombasa presentation set.

Owner: "the bento grind in the home page now only has one listing the
real listing...add the others so it has the same layout as before...
dont mess up the animation that was there before."

Root cause: home() chose showcase_source = real_showcase when ANY real
listing existed, and the 6-card top-up only ran inside that source —
with exactly one real listing (post import_real_listing) the bento
rendered 1 card and the shape-shift mosaic collapsed. The fix keeps
real inventory first but tops up from public_listings (the same
disclosed set the sale/rent/nearby rails use).
"""
import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client

from apps.listings.models import Property

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Same isolation pattern as test_phase2_home.py: seed, clear the
    home cache, roll back after."""
    cache.clear()
    call_command("seed_demo", no_images=True, target=20, verbosity=0,
                 i_know_this_is_demo=True)
    yield
    cache.clear()


def _make_real_listing():
    """A published, non-demo listing — stands in for the imported
    'Modern Beachfront Apartment in Nyali'."""
    from apps.accounts.models import User
    from apps.agents.models import AgencyProfile
    from apps.locations.models import Location

    user = User.objects.create_user(email="real-owner@test.com", password="x-12345678")
    agency = AgencyProfile.objects.create(name="Real agency", slug="real-agency", user=user)
    mombasa = Location.objects.filter(level=Location.Level.COUNTY, name="Mombasa").first()
    ptype = Property._meta.get_field("property_type").related_model.objects.first()
    return Property.objects.create(
        title="Real hand-typed listing", description="Real, checked.",
        listing_type="sale", property_type=ptype,
        location=mombasa or Location.objects.filter(level=Location.Level.COUNTY).first(),
        price="1000000", status="published", agent=agency,
    )


def test_thin_real_inventory_still_fills_six_cards():
    """One real listing + demos => real wins the spotlight, demos fill
    the remaining slots — the 6-card grid keeps its shape."""
    real = _make_real_listing()
    body = Client().get("/").content.decode()
    assert "bento-card--spotlight" in body
    assert real.title in body
    # 6 property cards carry prices (the CTA closer card does not)
    assert body.count("bento-card__price") >= 6, \
        "bento must show 6 listings, not collapse to the real one"


def test_real_listings_are_ordered_first():
    """Real inventory leads the bento even when a demo published later."""
    from django.utils import timezone

    real = _make_real_listing()
    demo = Property.objects.published().filter(is_demo=True).first()
    demo.published_at = timezone.now()
    demo.save()
    body = Client().get("/").content.decode()
    assert body.index(real.title) < body.index(demo.title), \
        "real listing must lead the bento"


def test_demo_hidden_switch_still_empties_the_top_up():
    """The top-up source runs through .published(), so the owner's
    hide-demo switch keeps the bento real-or-nothing."""
    from apps.core.models import SiteSetting

    _make_real_listing()
    setting = SiteSetting.load()
    setting.hide_demo_data = True
    setting.save()
    body = Client().get("/").content.decode()
    assert "bento-card--spotlight" in body
    for listing in Property.objects.filter(is_demo=True)[:5]:
        assert listing.title[:20] not in body, "hidden demo leaked into the bento"

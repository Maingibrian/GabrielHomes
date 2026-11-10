"""r12 — market quick filters, the map payload, and the Mombasa scope.

The redesigned /properties/ page carries three button cards under the map
(Selling / Renting / BnB) that act as quick filters via ?market=, an
MapLibre/OpenFreeMap map fed by context["map_listings"], and a row-style
alternating results list. The combined page keeps placeholder inventory
Mombasa-only while genuine owner-entered listings stay visible from
anywhere (demo rows outside Mombasa are never shown).
"""
import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client

from apps.agents.models import AgencyProfile
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    cache.clear()
    call_command("seed_demo", no_images=True, target=12, verbosity=0, i_know_this_is_demo=True)
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# ?market= quick filters
# ---------------------------------------------------------------------------
def test_market_sale_shows_only_sale_listings():
    r = Client().get("/properties/?market=sale")
    assert r.status_code == 200
    rows = list(r.context["page_obj"].object_list)
    assert rows  # seeded Mombasa sale rows exist
    for p in rows:
        assert p.listing_type == Property.ListingType.SALE


def test_market_rent_excludes_short_stays():
    r = Client().get("/properties/?market=rent")
    rows = list(r.context["page_obj"].object_list)
    assert rows
    for p in rows:
        assert p.listing_type == Property.ListingType.RENT
        assert p.is_short_stay is False


def test_market_bnb_shows_only_short_stays():
    r = Client().get("/properties/?market=bnb")
    rows = list(r.context["page_obj"].object_list)
    assert rows  # the seeded BnB presentation rows exist
    for p in rows:
        assert p.is_short_stay is True
        assert p.listing_type == Property.ListingType.RENT


def test_market_filter_cards_render_and_mark_active_state():
    body = Client().get("/properties/?market=rent").content.decode()
    # All three cards render…
    assert 'href="/properties/?market=sale"' in body
    assert 'href="/properties/?market=rent"' in body
    assert 'href="/properties/?market=bnb"' in body
    # …and the active one carries the Selected state.
    assert "market-filter--rent is-active" in body
    assert "market-filter--sale is-active" not in body


def test_market_h1_variants():
    """The map panel headline names the chosen market."""
    assert "Mombasa homes for sale" in Client().get("/properties/?market=sale").content.decode()
    assert "Mombasa homes for long-term rent" in Client().get("/properties/?market=rent").content.decode()
    assert "Mombasa short stays and BnB" in Client().get("/properties/?market=bnb").content.decode()
    assert "Homes across Mombasa" in Client().get("/properties/").content.decode()


# ---------------------------------------------------------------------------
# Map payload (context["map_listings"] → Leaflet price pins)
# ---------------------------------------------------------------------------
def test_map_payload_carries_shape_and_url():
    payload = Client().get("/properties/").context["map_listings"]
    assert payload, "map payload should carry the seeded Mombasa homes"
    for entry in payload:
        for key in ("lat", "lng", "title", "url", "price", "price_short", "market", "location"):
            assert key in entry, f"map payload entry missing {key!r}"
        assert entry["url"].startswith("/listing/")
        assert entry["price"].startswith("KES ")


def test_map_payload_maps_short_stays_to_bnb_market():
    payload = Client().get("/properties/?market=bnb").context["map_listings"]
    assert payload
    assert all(entry["market"] == "bnb" for entry in payload)


def test_map_payload_shortens_prices():
    """Pin labels use KSh xM for millions and KSh xK for thousands —
    the curated sale villa is in the millions, the monthly rentals in
    the thousands."""
    payload = Client().get("/properties/").context["map_listings"]
    assert payload
    for entry in payload:
        assert entry["price_short"].startswith("KSh ")
        assert entry["price_short"].endswith(("M", "K"))
    by_title = {e["title"]: e for e in payload}
    villa = next((t for t in by_title if "Tropical Villa" in t), None)
    assert villa is not None
    assert by_title[villa]["price_short"].endswith("M")      # 48,000,000
    sea = next((t for t in by_title if "Sea-view" in t), None)
    assert sea is not None
    assert by_title[sea]["price_short"].endswith("K")        # 165,000


# ---------------------------------------------------------------------------
# Mombasa scope on the combined /properties/ page
# ---------------------------------------------------------------------------
def test_combined_page_keeps_demo_mombasa_only():
    """Placeholder inventory is Mombasa-only; genuine owner-entered rows
    from anywhere stay visible (the business can expand beyond Mombasa
    without demo rows leaking out of the county)."""
    agency = AgencyProfile.objects.first()
    ptype = PropertyType.objects.first()
    # Kilimani is seeded under Nairobi — outside the Mombasa scope.
    kilimani = Location.objects.get(name="Kilimani", level=Location.Level.NEIGHBOURHOOD)
    Property.objects.create(
        title="Nairobi demo placeholder", listing_type=Property.ListingType.SALE,
        property_type=ptype, location=kilimani, price="9000000",
        status=Property.Status.PUBLISHED, agent=agency, is_demo=True,
    )
    Property.objects.create(
        title="Nairobi real listing", listing_type=Property.ListingType.SALE,
        property_type=ptype, location=kilimani, price="9500000",
        status=Property.Status.PUBLISHED, agent=agency,
    )
    body = Client().get("/properties/").content.decode()
    assert "Nairobi demo placeholder" not in body
    assert "Nairobi real listing" in body


def test_results_rows_alternate_direction():
    """The row list alternates: image left on odd rows, image right
    (listing-row--reverse) on even rows."""
    body = Client().get("/properties/").content.decode()
    assert 'class="listing-row listing-card-row"' in body            # odd rows
    assert 'listing-row--reverse' in body                          # even rows

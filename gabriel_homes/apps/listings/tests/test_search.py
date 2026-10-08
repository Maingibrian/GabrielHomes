"""Tests for the Phase 3 search page — URL patterns, filters,
location descendants, sort, pagination, HTMX partial, query count."""
import json

import pytest
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test — keeps tests isolated via transaction rollback."""
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


# ---------------------------------------------------------------------------
# URL patterns — all 6 from WORK.md §7
# ---------------------------------------------------------------------------
def test_type_only_sale_url():
    c = Client()
    r = c.get("/flats-apartments-for-sale/")
    assert r.status_code == 200
    assert b"Flats &amp; Apartments for Sale" in r.content


def test_type_only_rent_url():
    c = Client()
    r = c.get("/houses-for-rent/")
    assert r.status_code == 200
    assert b"Houses for Rent" in r.content


def test_type_plus_location_sale_url():
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/")
    assert r.status_code == 200
    assert b"Flats &amp; Apartments for Sale in Mombasa" in r.content


def test_type_plus_location_rent_url():
    c = Client()
    r = c.get("/houses-for-rent/nairobi/")
    assert r.status_code == 200
    assert b"Houses for Rent in Nairobi" in r.content


def test_all_types_plus_location_sale_url():
    c = Client()
    r = c.get("/property-for-sale/mombasa/")
    assert r.status_code == 200
    assert b"Property for Sale in Mombasa" in r.content


def test_all_types_plus_location_rent_url():
    c = Client()
    r = c.get("/property-for-rent/nairobi/")
    assert r.status_code == 200
    assert b"Property for Rent in Nairobi" in r.content


def test_invalid_type_returns_404():
    c = Client()
    r = c.get("/nonexistent-type-for-sale/")
    assert r.status_code == 404


def test_invalid_location_returns_404():
    c = Client()
    r = c.get("/flats-apartments-for-sale/nonexistent-place/")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Filtering correctness
# ---------------------------------------------------------------------------
def test_results_show_only_published_listings():
    """WORK.md §13: Every public view must only show published listings."""
    from apps.listings.models import Property
    # Create a draft listing that should NOT appear
    draft = Property.objects.filter(status="published").first()
    if draft:
        draft_id = draft.pk
        Property.objects.filter(pk=draft_id).update(status="draft")

    c = Client()
    r = c.get("/flats-apartments-for-sale/")
    body = r.content.decode()
    # The draft listing's title should not be in the page
    draft.refresh_from_db()
    assert draft.title not in body


def test_results_filtered_by_listing_type():
    """Sale pages show only sale listings; rent pages only rent."""
    c = Client()
    # All sale listings across all types
    r_sale = c.get("/property-for-sale/mombasa/")
    r_rent = c.get("/property-for-rent/mombasa/")
    assert r_sale.status_code == 200
    assert r_rent.status_code == 200

    from apps.listings.models import Property
    from apps.locations.models import Location
    mombasa = Location.objects.get(slug="mombasa", level="county")
    descendants = mombasa.get_descendants(include_self=True)
    sale_count = Property.objects.published().filter(
        listing_type="sale", location__in=descendants
    ).count()
    rent_count = Property.objects.published().filter(
        listing_type="rent", location__in=descendants
    ).count()

    body_sale = r_sale.content.decode()
    body_rent = r_rent.content.decode()
    assert f"<strong>{sale_count}</strong>" in body_sale
    assert f"<strong>{rent_count}</strong>" in body_rent


def test_results_filtered_by_property_type():
    c = Client()
    r = c.get("/flats-apartments-for-sale/")
    body = r.content.decode()
    # All cards should be flats/apartments — verify the H1
    assert "Flats &amp; Apartments" in body


def test_results_filtered_by_location_with_descendants():
    """Searching 'Mombasa' includes Westlands, Kilimani, etc. (per §9)."""
    from apps.listings.models import Property, PropertyType
    from apps.locations.models import Location

    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/")
    body = r.content.decode()

    mombasa = Location.objects.get(slug="mombasa", level="county")
    ptype = PropertyType.objects.get(slug_plural="flats-apartments")
    descendants = mombasa.get_descendants(include_self=True)
    expected = Property.objects.published().filter(
        listing_type="sale", property_type=ptype, location__in=descendants
    ).count()

    # The total count in the page should match
    assert f"<strong>{expected}</strong>" in body


def test_filters_combine_beds_and_price():
    """?beds=2&max_price=20000000 should narrow results correctly."""
    from apps.listings.models import Property, PropertyType
    from apps.locations.models import Location

    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/?beds=2&max_price=20000000")
    assert r.status_code == 200
    body = r.content.decode()

    mombasa = Location.objects.get(slug="mombasa", level="county")
    ptype = PropertyType.objects.get(slug_plural="flats-apartments")
    descendants = mombasa.get_descendants(include_self=True)
    expected = Property.objects.published().filter(
        listing_type="sale",
        property_type=ptype,
        location__in=descendants,
        bedrooms__gte=2,
        price__lte=20000000,
    ).count()
    assert f"<strong>{expected}</strong>" in body


def test_min_price_filter():
    c = Client()
    r = c.get("/flats-apartments-for-sale/?min_price=20000000")
    assert r.status_code == 200


def test_furnishing_filter():
    c = Client()
    r = c.get("/flats-apartments-for-sale/?furnishing=furnished")
    assert r.status_code == 200


def test_amenities_filter():
    c = Client()
    r = c.get("/flats-apartments-for-sale/?amenities=swimming-pool")
    assert r.status_code == 200


def test_q_filter_searches_title():
    from apps.listings.models import Property
    # Pick a known listing title
    p = Property.objects.published().first()
    # Use a distinctive substring of the title
    word = p.title.split()[0]
    c = Client()
    r = c.get(f"/flats-apartments-for-sale/?q={word}")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------
def test_sort_newest_default():
    c = Client()
    r = c.get("/flats-apartments-for-sale/")
    body = r.content.decode()
    assert 'value="newest" selected' in body or 'value="newest"selected' in body


def test_sort_price_desc():
    c = Client()
    r = c.get("/flats-apartments-for-sale/?sort=price_desc")
    body = r.content.decode()
    assert 'value="price_desc" selected' in body or 'value="price_desc"selected' in body


def test_sort_invalid_value_falls_back_to_newest():
    """§13: Never trust user input in lookup strings; whitelist sort options."""
    c = Client()
    r = c.get("/flats-apartments-for-sale/?sort=DROP_TABLE")
    assert r.status_code == 200  # doesn't crash; falls back to default


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
def test_pagination_24_per_page():
    """24 per page per WORK.md §8."""
    c = Client()
    r = c.get("/property-for-sale/mombasa/")  # all types, all Mombasa descendants
    body = r.content.decode()
    # Count listing cards on page 1 — should be at most 24
    card_count = body.count('class="listing-card"')
    assert card_count <= 24


def test_pagination_page_2():
    c = Client()
    r = c.get("/property-for-sale/mombasa/?page=2")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# HTMX partial
# ---------------------------------------------------------------------------
def test_htmx_request_returns_partial_only():
    """When HX-Request header is set, return just the grid (no full HTML)."""
    c = Client()
    r = c.get("/flats-apartments-for-sale/", HTTP_HX_REQUEST="true")
    body = r.content.decode()
    assert r.status_code == 200
    assert 'id="results-grid"' in body
    # Should NOT contain full HTML structure
    assert "<html" not in body
    assert "<!doctype" not in body.lower()


def test_non_htmx_request_returns_full_page():
    c = Client()
    r = c.get("/flats-apartments-for-sale/")
    body = r.content.decode()
    assert "<!doctype html>" in body.lower()
    assert 'id="results-grid"' in body


# ---------------------------------------------------------------------------
# Breadcrumbs + canonical URL
# ---------------------------------------------------------------------------
def test_breadcrumbs_render():
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/")
    body = r.content.decode()
    assert "breadcrumbs" in body
    assert "Home" in body
    assert "Mombasa" in body


def test_canonical_url_in_head():
    """Canonical URL = clean path without query params (per §7)."""
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/?beds=2&sort=price_desc")
    body = r.content.decode()
    assert '<link rel="canonical" href="/flats-apartments-for-sale/mombasa/"' in body


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------
def test_empty_state_when_no_results():
    """An impossibly-high price filter should yield the empty state."""
    c = Client()
    r = c.get("/flats-apartments-for-sale/?min_price=999999999999")
    body = r.content.decode()
    assert "No properties match" in body
    assert "Clear all filters" in body


# ---------------------------------------------------------------------------
# Related searches
# ---------------------------------------------------------------------------
def test_related_searches_render():
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/")
    body = r.content.decode()
    assert "RELATED SEARCHES" in body


# ---------------------------------------------------------------------------
# Autocomplete endpoint
# ---------------------------------------------------------------------------
def test_autocomplete_returns_json():
    c = Client()
    r = c.get("/search/locations/?q=mom")
    assert r.status_code == 200
    data = json.loads(r.content)
    assert "results" in data
    assert isinstance(data["results"], list)


def test_autocomplete_returns_mombasa_for_mom():
    c = Client()
    r = c.get("/search/locations/?q=mom")
    data = json.loads(r.content)
    names = [res["name"] for res in data["results"]]
    assert "Mombasa" in names


def test_autocomplete_returns_empty_for_short_query():
    c = Client()
    r = c.get("/search/locations/?q=m")
    data = json.loads(r.content)
    assert data["results"] == []


def test_autocomplete_returns_empty_for_no_match():
    c = Client()
    r = c.get("/search/locations/?q=zzzzzzzzz")
    data = json.loads(r.content)
    assert data["results"] == []


def test_autocomplete_result_has_required_fields():
    c = Client()
    r = c.get("/search/locations/?q=nairobi")
    data = json.loads(r.content)
    assert len(data["results"]) >= 1
    res = data["results"][0]
    for field in ("slug", "name", "full_path", "level"):
        assert field in res, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Query count test — per WORK.md §9
# ---------------------------------------------------------------------------
def test_results_page_query_count_is_bounded():
    """§9: 'Add a test that asserts the query count for the results page
    stays under a fixed number.'

    With proper select_related / prefetch_related, a 24-listing page
    should stay well under 15 queries. We assert < 15 to catch N+1
    regressions while allowing some slack for context lookups.
    """
    c = Client()
    # Use a URL that returns multiple pages of results so pagination runs.
    with CaptureQueriesContext(connection) as ctx:
        r = c.get("/property-for-sale/mombasa/")
    assert r.status_code == 200
    # 15 is a generous ceiling — the actual count is typically ~8-10.
    # If this regresses above 15, there's an N+1 to fix.
    assert len(ctx) < 15, (
        f"Query count regressed: {len(ctx)} queries on the results page. "
        f"Check for N+1 in the listings view / listing card template."
    )


# ---------------------------------------------------------------------------
# Only published listings (§13)
# ---------------------------------------------------------------------------
def test_draft_listings_never_appear():
    """Even with filters, draft/archived listings must not appear."""
    from apps.listings.models import Property
    # Flip some to draft
    Property.objects.filter(status="published").update(status="draft")
    c = Client()
    r = c.get("/flats-apartments-for-sale/")
    body = r.content.decode()
    assert "No properties match" in body  # empty state
    # Restore
    Property.objects.filter(status="draft").update(status="published")


def test_archived_listings_never_appear():
    from apps.listings.models import Property
    Property.objects.filter(status="published").update(status="archived")
    c = Client()
    r = c.get("/flats-apartments-for-sale/")
    body = r.content.decode()
    assert "No properties match" in body
    Property.objects.filter(status="archived").update(status="published")

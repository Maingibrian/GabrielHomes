"""r75 (BACKEND-PLAN 3A) — the taxonomy editor: /manage/site-content/categories/.

Pinned here: the owner gate, add-by-name for all three kinds (slugs and
levels derived server-side, never typed), rename-in-place (URLs never
break), show/hide with the public-menu chokepoints (home county block,
home type dropdown, search sidebar, related searches, suggestions,
amenities on the detail page), and the no-deletes contract.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.agents.models import AgencyProfile
from apps.listings.models import Amenity, Property, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db

LOGIN_URL = "/account/login/"
URL = "/manage/site-content/categories/"


@pytest.fixture(autouse=True)
def base(db):
    User = get_user_model()
    county = Location.objects.create(name="Mombasa", slug="mombasa", level="county")
    area = Location.objects.create(name="Nyali", slug="nyali", level="area", parent=county)
    Location.objects.create(name="Nyali Centre", slug="nyali-centre", level="neighbourhood", parent=area)
    PropertyType.objects.create(name="Apartment", slug_plural="flats-apartments", slug_single="apartment")
    Amenity.objects.create(name="Lift", slug="lift")
    agent_user = User.objects.create(email="agency-user@test.com", full_name="Test Agency", is_agent=True)
    agency = AgencyProfile.objects.create(user=agent_user, name="Test Agency", slug="test-agency")
    Property.objects.create(
        title="Sea-view Apartment in Nyali", slug="sea-view-apt", listing_type="rent",
        property_type=PropertyType.objects.get(slug_single="apartment"),
        location=Location.objects.get(slug="nyali-centre"), price=150000, agent=agency,
        status=Property.Status.PUBLISHED, published_at="2026-01-01T10:00:00Z",
    )


@pytest.fixture
def owner():
    User = get_user_model()
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


@pytest.fixture
def agent():
    User = get_user_model()
    c = Client()
    c.force_login(User.objects.get(email="agency-user@test.com"))
    return c


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
def test_anon_is_sent_to_login():
    r = Client().get(URL)
    assert r.status_code == 302
    assert LOGIN_URL in r["Location"]


def test_agent_gets_403(agent):
    assert agent.get(URL).status_code == 403


def test_owner_sees_all_three_groups(owner):
    r = owner.get(URL)
    assert r.status_code == 200
    for needle in (b"Places", b"Property types", b"Features (amenities)", b"Mombasa", b"Apartment", b"Lift"):
        assert needle in r.content


# ---------------------------------------------------------------------------
# Add — name only, everything else derived
# ---------------------------------------------------------------------------
def test_add_county_location(owner):
    r = owner.post(URL, {"action": "add", "kind": "location", "name": "Kwale", "parent": ""})
    assert r.status_code == 302
    loc = Location.objects.get(name="Kwale")
    assert loc.level == Location.Level.COUNTY
    assert loc.slug == "kwale"
    assert loc.is_active is True


def test_add_location_under_area_derives_neighbourhood_level(owner):
    area = Location.objects.get(slug="nyali")
    r = owner.post(URL, {"action": "add", "kind": "location", "name": "Mamba Village", "parent": str(area.pk)})
    assert r.status_code == 302
    loc = Location.objects.get(name="Mamba Village")
    assert loc.level == Location.Level.NEIGHBOURHOOD
    assert loc.parent == area


def test_add_property_type_auto_slugs(owner):
    r = owner.post(URL, {"action": "add", "kind": "type", "name": "Villa", "parent": ""})
    assert r.status_code == 302
    pt = PropertyType.objects.get(name="Villa")
    assert pt.slug_single == "villa"
    assert pt.slug_plural == "villas"


def test_add_amenity_auto_slug(owner):
    r = owner.post(URL, {"action": "add", "kind": "amenity", "name": "Borehole", "parent": ""})
    assert r.status_code == 302
    assert Amenity.objects.get(name="Borehole").slug == "borehole"


def test_duplicate_name_is_refused_not_crashed(owner):
    before = PropertyType.objects.count()
    r = owner.post(URL, {"action": "add", "kind": "type", "name": "Apartment", "parent": ""})
    assert r.status_code == 302  # honest error message, back to the screen
    assert PropertyType.objects.count() == before


def test_usage_counts_show_on_screen(owner):
    r = owner.get(URL)
    # One published listing on the Apartment type; the county counts its
    # descendants' listings too.
    assert b"1 listing" in r.content


# ---------------------------------------------------------------------------
# Rename — names change, web addresses never do
# ---------------------------------------------------------------------------
def test_rename_type_keeps_slugs(owner):
    pt = PropertyType.objects.get(slug_single="apartment")
    r = owner.post(URL, {"action": "rename", "kind": "type", "pk": str(pt.pk), "name": "Flat"})
    assert r.status_code == 302
    pt.refresh_from_db()
    assert pt.name == "Flat"
    assert pt.slug_plural == "flats-apartments"
    assert pt.slug_single == "apartment"


# ---------------------------------------------------------------------------
# Hide — the public-menu chokepoints
# ---------------------------------------------------------------------------
def test_hidden_type_leaves_home_menu_and_keeps_browse_url(owner, client):
    pt = PropertyType.objects.get(slug_single="apartment")
    option = b'<option value="flats-apartments">Apartment</option>'
    home = client.get("/")
    assert option in home.content

    owner.post(URL, {"action": "toggle", "kind": "type", "pk": str(pt.pk)})

    home = client.get("/")
    assert option not in home.content
    # The browse URL itself keeps working — hiding is not breaking.
    browse = client.get("/flats-apartments-for-rent/")
    assert browse.status_code == 200


def test_hidden_county_leaves_related_searches_and_suggestions(owner, client):
    county = Location.objects.get(slug="mombasa")
    before = client.get("/property-for-sale/")
    assert b"Property for Sale in Mombasa" in before.content

    owner.post(URL, {"action": "toggle", "kind": "location", "pk": str(county.pk)})

    after = client.get("/property-for-sale/")
    assert b"Property for Sale in Mombasa" not in after.content
    # The county's own browse page still resolves.
    assert client.get("/property-for-sale/mombasa/").status_code == 200


def test_hidden_location_leaves_search_suggestions(owner, client):
    hood = Location.objects.get(slug="nyali-centre")
    before = client.get("/search/locations/", {"q": "nyali"})
    owner.post(URL, {"action": "toggle", "kind": "location", "pk": str(hood.pk)})
    after = client.get("/search/locations/", {"q": "nyali"})
    assert b"Nyali Centre" in before.content
    assert b"Nyali Centre" not in after.content


def test_hidden_amenity_stays_off_the_detail_page(owner, client):
    prop = Property.objects.get(slug="sea-view-apt")
    prop.amenities.add(Amenity.objects.get(slug="lift"))
    detail = client.get(prop.get_absolute_url())
    assert b"Lift" in detail.content

    owner.post(URL, {"action": "toggle", "kind": "amenity", "pk": str(Amenity.objects.get(slug="lift").pk)})

    detail = client.get(prop.get_absolute_url())
    assert b"Lift" not in detail.content
    # The amenity stays attached — hiding is reversible.
    assert prop.amenities.filter(slug="lift").exists()


def test_show_brings_it_back(owner, client):
    pt = PropertyType.objects.get(slug_single="apartment")
    owner.post(URL, {"action": "toggle", "kind": "type", "pk": str(pt.pk)})
    owner.post(URL, {"action": "toggle", "kind": "type", "pk": str(pt.pk)})
    pt.refresh_from_db()
    assert pt.is_active is True
    assert b"Apartment" in client.get("/").content


# ---------------------------------------------------------------------------
# No deletes — the contract
# ---------------------------------------------------------------------------
def test_delete_action_does_not_exist(owner):
    pt = PropertyType.objects.get(slug_single="apartment")
    r = owner.post(URL, {"action": "delete", "kind": "type", "pk": str(pt.pk)})
    assert r.status_code == 404
    assert PropertyType.objects.filter(pk=pt.pk).exists()


def test_unknown_action_404s(owner):
    assert owner.post(URL, {"action": "nonsense"}).status_code == 404

"""P0-4 — the three-state pytest harness (protocol §3).

The public site must look complete and intentional in three states:
  (a) demo data visible — seeded DB, ``SiteSetting.hide_demo_data = False``
  (b) demo data hidden  — seeded DB, ``SiteSetting.hide_demo_data = True``
  (c) zero listings     — empty DB (nothing seeded at all)

Every state renders the four public page shapes — home, /properties/, a
listing detail, and the /agents/ → /about/ redirect target — and asserts
the *designed* screen shows up: a real <main>, the designed empty-state or
fallback section, no leaked template syntax ({% %} / {{ }} / {# #}), and
no phantom sections where content was removed.

QA runs (every 4th run) re-run this module instead of hand-probing pages,
so the three-state duty is automated from run 8 onwards.
"""
import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client

from apps.core.models import SiteSetting
from apps.listings.models import Property

pytestmark = pytest.mark.django_db

SEED_KW = dict(no_images=True, target=12, verbosity=0, i_know_this_is_demo=True)

# Marks that must never survive into rendered HTML (template leaks).
LEAK_MARKS = ("{%", "{{", "{#")


# ---------------------------------------------------------------------------
# Fixtures — one per state
# ---------------------------------------------------------------------------
def _set_demo_hidden(hidden: bool) -> None:
    setting = SiteSetting.load()
    setting.hide_demo_data = hidden
    setting.save()


@pytest.fixture
def state_demo_visible(db):
    """(a) Demo data seeded and visible on the public site."""
    cache.clear()
    call_command("seed_demo", **SEED_KW)
    _set_demo_hidden(False)
    yield
    cache.clear()


@pytest.fixture
def state_demo_hidden(db):
    """(b) Demo data seeded but hidden from the public site."""
    cache.clear()
    call_command("seed_demo", **SEED_KW)
    _set_demo_hidden(True)
    yield
    _set_demo_hidden(False)
    cache.clear()


@pytest.fixture
def state_zero_listings(db):
    """(c) Fresh database — no properties, no agencies, nothing."""
    cache.clear()
    assert Property.objects.count() == 0
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# Shared assertions
# ---------------------------------------------------------------------------
def _assert_designed(html: bytes, *, what: str) -> None:
    """Generic no-blank/no-phantom assertions for a 200 page."""
    assert b"<main" in html, f"{what}: main landmark missing"
    assert b"</main>" in html, f"{what}: main not closed"
    for mark in LEAK_MARKS:
        assert mark.encode() not in html, f"{what}: template leak {mark!r} on page"
    assert b"Gabriel Homes" in html, f"{what}: site chrome (brand) missing"


def _demo_detail_url() -> str:
    prop = Property.objects.filter(is_demo=True, status=Property.Status.PUBLISHED).first()
    assert prop is not None, "seed did not produce a published demo listing"
    return prop.get_absolute_url()


# ---------------------------------------------------------------------------
# State (a) — demo data visible
# ---------------------------------------------------------------------------
class TestDemoVisible:
    def test_home_renders_designed_fallback(self, state_demo_visible):
        """r12 home contract: with no real inventory, the bento and the
        recommended band demonstrate the UI with the clearly-labelled
        Mombasa presentation homes (DEMO chip / Demo listing) — never a
        blank grid, and never unmarked placeholder homes. The 'HOW WE
        CHECK' bento variant belongs to the demo-hidden / zero states."""
        r = Client().get("/")
        assert r.status_code == 200
        html = r.content
        _assert_designed(html, what="home/demo-visible")
        assert b"[ HOMES ]" in html
        # r47: presentation rows are labelled — the on-media bubble now
        # leads with the location and carries the demo flag with it
        assert b"loc-chip" in html
        assert b'loc-chip__flag">demo' in html
        assert b"RECOMMENDED IN MOMBASA" in html
        assert b"Five checks before anything goes live." not in html

    def test_properties_grid_shows_demo_cards(self, state_demo_visible):
        r = Client().get("/properties/")
        assert r.status_code == 200
        html = r.content
        _assert_designed(html, what="properties/demo-visible")
        assert b"listing-card" in html  # the grid is populated

    def test_demo_detail_renders(self, state_demo_visible):
        r = Client().get(_demo_detail_url())
        assert r.status_code == 200
        html = r.content
        _assert_designed(html, what="detail/demo-visible")
        assert b"page-detail" in html

    def test_agents_redirects_and_about_renders(self, state_demo_visible):
        r = Client().get("/agents/")
        assert r.status_code == 301
        assert r["Location"].endswith("/about/")
        r2 = Client().get("/about/")
        assert r2.status_code == 200
        _assert_designed(r2.content, what="about/demo-visible")


# ---------------------------------------------------------------------------
# State (b) — demo data hidden
# ---------------------------------------------------------------------------
class TestDemoHidden:
    def test_home_renders_designed_fallback(self, state_demo_hidden):
        r = Client().get("/")
        assert r.status_code == 200
        _assert_designed(r.content, what="home/demo-hidden")
        assert b"HOW WE CHECK" in r.content

    def test_properties_shows_designed_empty_state(self, state_demo_hidden):
        """Demo hidden + no real rows → the designed empty-state screen,
        not a blank grid and not demo cards leaking through."""
        r = Client().get("/properties/")
        assert r.status_code == 200
        html = r.content
        _assert_designed(html, what="properties/demo-hidden")
        assert b"empty-state" in html
        assert b"No properties match" in html
        assert b"listing-card" not in html  # nothing leaks past the switch

    def test_demo_detail_404s(self, state_demo_hidden):
        """A demo listing hidden by the switch must not serve its detail
        page (published() chokepoint) — 404, not a broken render."""
        r = Client().get(_demo_detail_url())
        assert r.status_code == 404

    def test_agents_redirects_and_about_renders(self, state_demo_hidden):
        r = Client().get("/agents/")
        assert r.status_code == 301
        r2 = Client().get("/about/")
        assert r2.status_code == 200
        _assert_designed(r2.content, what="about/demo-hidden")


# ---------------------------------------------------------------------------
# State (c) — zero listings
# ---------------------------------------------------------------------------
class TestZeroListings:
    def test_home_renders_designed_fallback(self, state_zero_listings):
        r = Client().get("/")
        assert r.status_code == 200
        _assert_designed(r.content, what="home/zero")
        assert b"HOW WE CHECK" in r.content
        assert b"listing-card" not in r.content

    def test_properties_shows_designed_empty_state(self, state_zero_listings):
        r = Client().get("/properties/")
        assert r.status_code == 200
        html = r.content
        _assert_designed(html, what="properties/zero")
        assert b"empty-state" in html
        assert b"listing-card" not in html

    def test_unknown_detail_404s(self, state_zero_listings):
        r = Client().get("/listing/does-not-exist-999999/")
        assert r.status_code == 404

    def test_agents_redirects_and_about_renders(self, state_zero_listings):
        r = Client().get("/agents/")
        assert r.status_code == 301
        r2 = Client().get("/about/")
        assert r2.status_code == 200
        _assert_designed(r2.content, what="about/zero")

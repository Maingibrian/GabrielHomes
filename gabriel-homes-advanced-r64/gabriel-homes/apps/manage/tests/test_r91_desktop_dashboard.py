"""r91 — the owner portal's desktop dashboard shell + board.

Why: the portal capped every screen at max-width:44rem (a 704px column on a
1920px display) and had no sidebar — DESIGN.md §9 has always called for
"agent dashboard (cream background, espresso sidebar)". r91 adds a desktop
shell (>=64rem: espresso sidebar, hidden topbar/chip nav) and restructures
/manage/ into a 12-column board. Mobile (<64rem) must stay as it was.

Pinned here: the shell structure, the board zones, the CSS that swaps the
chrome, and the mobile guarantee. Mirrors the guards used by
test_portal_design_stack (comment-leak etc. stay in their own files).
"""
from pathlib import Path

from django.contrib.auth import get_user_model

import pytest

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / "templates" / "manage" / "base.html"
HOME = REPO / "templates" / "manage" / "home.html"
NAV = REPO / "templates" / "manage" / "_nav.html"
CSS = REPO / "static" / "css" / "manage.css"

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner(client):
    get_user_model().objects.create_superuser(
        email="owner@test.com", password="owner-pass-123"
    )
    client.force_login(get_user_model().objects.get(email="owner@test.com"))
    return client


# ---------- The shell (every portal screen) ----------

def test_sidebar_is_in_the_dom_with_all_five_sections(owner):
    r = owner.get("/manage/")
    assert r.status_code == 200
    body = r.content.decode()
    assert 'class="manage-side"' in body
    for label in ("01</span>Home", "02</span>Enquiries", "03</span>Listings",
                  "04</span>Site content", "05</span>SEO"):
        assert label in body, f"sidebar section missing: {label}"


def test_mobile_chip_nav_still_rendered(owner):
    """The <64rem chip nav stays in the DOM (CSS hides it on desktop)."""
    body = owner.get("/manage/").content.decode()
    assert 'class="manage-nav"' in body
    assert "manage/_nav.html" not in body  # include is resolved, never raw


def test_chip_nav_and_sidebar_come_from_one_partial():
    """One source of truth: both variants include manage/_nav.html."""
    base = BASE.read_text()
    assert '{% include "manage/_nav.html" with variant="sidebar" %}' in base
    assert '{% include "manage/_nav.html" %}' in base


def test_sidebar_badge_uses_the_same_counter(owner):
    """The enquiry badge renders in BOTH nav variants from nav_new_enquiries."""
    from apps.inquiries.models import Inquiry
    from apps.listings.models import Property

    if not Property.objects.exists():
        # one published row so an enquiry can attach to it
        from apps.agents.models import AgencyProfile
        from apps.listings.models import PropertyType
        from apps.locations.models import Location

        u = get_user_model().objects.create(
            email="r91-agency@test.com", full_name="R91 Agency", is_agent=True
        )
        a = AgencyProfile.objects.create(user=u, name="R91 Homes", slug="r91-homes")
        c = Location.objects.create(name="R91 Mombasa", slug="r91-mombasa", level="county")
        ar = Location.objects.create(name="R91 Nyali", slug="r91-nyali", level="area", parent=c)
        h = Location.objects.create(name="R91 Centre", slug="r91-centre", level="neighbourhood", parent=ar)
        t = PropertyType.objects.create(name="R91 Apartment", slug_plural="r91-flats", slug_single="r91-apartment")
        Property.objects.create(
            title="R91 row listing", listing_type="rent", property_type=t,
            location=h, price=150000, description="x", agent=a,
            status=Property.Status.PUBLISHED, published_at="2026-01-01T10:00:00Z",
        )
    Inquiry.objects.create(
        property_ref=Property.objects.first(),
        name="R91 Caller", email="r91@example.com", phone="", message="hi",
        status=Inquiry.Status.NEW,
    )
    body = owner.get("/manage/").content.decode()
    assert body.count('class="manage-nav__badge"') == 2  # chip nav + sidebar


# ---------- The board (/manage/ home) ----------

def test_home_is_a_board_with_all_zones(owner):
    body = owner.get("/manage/").content.decode()
    assert 'class="manage-board"' in body
    for zone in ("manage-board__welcome", "manage-board__chart", "manage-board__pipe",
                 "manage-board__top", "manage-board__recent", "manage-board__check",
                 "manage-board__quick"):
        assert zone in body, f"board zone missing: {zone}"


def test_kpi_strip_has_four_tiles_with_hints(owner):
    body = owner.get("/manage/").content.decode()
    # r92: the first tile is the hero — its class list grew, so count
    # the manage-kpi element itself, not an exact attribute string.
    # (?![-_a-z]) skips manage-kpis / manage-kpi--hero / manage-kpi__*.
    import re
    assert len(re.findall(r"manage-kpi(?![-_a-z])", body)) == 4
    assert "manage-kpi__value" in body and "manage-kpi__hint" in body


def test_all_numbers_still_bound_to_real_context(owner):
    """The board is layout only: every KPI still renders its database number."""
    body = owner.get("/manage/").content.decode()
    for fragment in ("New enquiries", "Live listings", "Drafts", "Listing views"):
        assert fragment in body
    # values render as digits (0 on an empty test DB), not blank bindings
    import re
    assert re.search(r"manage-kpi__value[^>]*>\s*(?:<a[^>]*>)?\d", body)


# ---------- The CSS swap ----------

def test_css_defines_the_desktop_shell():
    css = CSS.read_text()
    assert ".manage-side { display: none; }" in css, "sidebar must be hidden below 64rem"
    assert "@media (min-width: 64rem)" in css
    for rule in ("body.page-manage", ".manage-side", ".manage-board",
                 ".manage-board__chart", ".manage-board__recent"):
        assert rule in css, f"missing r91 rule: {rule}"
    # the mobile chrome is hidden on desktop, not removed from the DOM
    swap = css.split("@media (min-width: 64rem)", 2)[1]
    assert ".manage-topbar," in swap and "display: none" in swap


def test_no_javascript_was_added():
    for path in (BASE, HOME, NAV):
        assert "<script" not in path.read_text(), f"{path.name} must stay script-free"


def test_nav_partial_defines_both_variants():
    src = NAV.read_text()
    assert 'variant == "sidebar"' in src
    assert "manage-side__link" in src and "manage-nav__link" in src

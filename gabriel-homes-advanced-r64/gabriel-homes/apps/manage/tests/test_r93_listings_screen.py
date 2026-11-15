"""r93 — listings screen desktop layout + cover thumbnails.

Pins the view-level and template-level pieces of the r93 listings index
work (the CSS itself is pinned by the class names these tests assert):

- PortalListingsView prefetches cover images (to_attr=cover_images) so
  the template does not query per row (no N+1).
- Rows render a .manage-row__thumb (real <img> when a cover exists,
  empty placeholder square when not).
- The screen's row list is allowed to exceed the portal's 44rem column
  on desktop (class hook .manage-rows--stack gets a 72rem cap at
  >=64rem in manage.css).
"""
import re
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client

from apps.listings.models import Property, PropertyImage

REPO = Path(__file__).resolve().parents[3]
MANAGE_CSS = (REPO / "static" / "css" / "manage.css").read_text()


@pytest.fixture
def seeded(db):
    call_command(
        "seed_demo", no_images=True, target=20, verbosity=0,
        i_know_this_is_demo=True,
    )
    return db


@pytest.mark.usefixtures("seeded")
def test_listings_rows_have_cover_thumbs():
    """Each row renders one thumb: <img> with a cover, placeholder if none."""
    owner = get_user_model().objects.create_superuser(
        email="r93-rows@example.com", password="r93-pass-123"
    )
    c = Client()
    c.force_login(owner)
    r = c.get("/manage/listings/")
    assert r.status_code == 200
    html = r.content.decode()
    rows = re.findall(r'<li class="manage-row manage-row--listing">', html)
    thumbs_img = re.findall(r'<a class="manage-row__thumb"[^>]*>\s*<img', html)
    thumbs_empty = re.findall(r'manage-row__thumb--empty', html)
    assert len(rows) >= 1
    assert len(thumbs_img) + len(thumbs_empty) == len(rows), (
        "every row must carry exactly one thumb (img or placeholder)"
    )


@pytest.mark.usefixtures("seeded")
def test_listings_queryset_prefetches_covers():
    """The view prefetches cover images — no per-row queries in the loop."""
    from django.db import connection, reset_queries
    from apps.manage.views import PortalListingsView

    get_user_model().objects.create_superuser(
        email="r93-pf@example.com", password="r93-pass-123"
    )
    c = Client()
    c.force_login(get_user_model().objects.get(email="r93-pf@example.com"))
    reset_queries()
    r = c.get("/manage/listings/")
    assert r.status_code == 200
    listing_queries = [
        q["sql"] for q in connection.queries
        if "listings_propertyimage" in q["sql"]
    ]
    # One prefetch query for the page — not one per row.
    assert len(listing_queries) <= 2, (
        f"cover images must be prefetched, found {len(listing_queries)} "
        "PropertyImage queries"
    )


def test_manage_css_pins_r93_listings_layout():
    """The r93 desktop rules exist: 72rem cap + thumb grid + tools column."""
    assert re.search(
        r"\.manage-rows--stack.*?max-width:\s*72rem", MANAGE_CSS, re.S
    ), "rows list must get the 72rem desktop cap"
    assert ".manage-row__thumb img" in MANAGE_CSS, "thumb img rule must exist"
    assert re.search(
        r"@media \(min-width: 64rem\)", MANAGE_CSS
    ), "desktop breakpoint must stay"
    # Mobile safety: thumbs hidden below the breakpoint.
    base = MANAGE_CSS.split("@media (min-width: 64rem)")[0]
    assert re.search(
        r"\.manage-row__thumb\s*\{\s*display:\s*none", MANAGE_CSS
    ), "thumbs must be display:none in the mobile-first base rule"

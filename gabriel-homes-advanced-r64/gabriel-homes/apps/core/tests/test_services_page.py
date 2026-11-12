"""Services page (/services/) — the nav's "04 Services" target.

The nav item historically pointed at /agents/ because no services page
existed. These tests pin the real page: content markers, the four service
rows, live counts from _static_ctx, and sitemap inclusion.

r82: the four service photographs are served from the owner's REAL
listing gallery (import_real_listing), not static copies — pinned here
together with the static-fallback contract for when the listing is
absent.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

TINY_JPG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)

CONTENT_MARKERS = [
    "[ SERVICES ]",
    "Find a home to buy.",
    "Find a home to rent.",
    "Talk to a person about a listing.",
    "List a property with us.",
    "[ OUR COMMITMENTS ]",
]


def test_services_url_resolves():
    assert reverse("services") == "/services/"


def test_services_page_returns_200(client):
    resp = client.get("/services/")
    assert resp.status_code == 200


@pytest.mark.parametrize("marker", CONTENT_MARKERS)
def test_services_page_has_content_markers(client, marker):
    html = client.get("/services/").content.decode()
    assert marker in html, f"missing marker: {marker}"


def test_services_page_shows_no_unverified_counts(client):
    """The services copy states only confirmed facts — no live or partner counts."""
    html = client.get("/services/").content.decode()
    assert "live properties" not in html
    assert "partner agencies" not in html


def test_header_nav_points_services_to_services_page(client):
    html = client.get("/").content.decode()
    assert 'href="/services/"' in html
    # the old stub must be gone from the primary nav
    assert 'href="/agents/"><span class="nav-link__index">04</span>' not in html


def test_services_in_sitemap(client):
    xml = client.get("/sitemap.xml").content.decode()
    assert "/services/" in xml


def test_services_page_csp_present(client):
    resp = client.get("/services/")
    assert resp.headers.get("Content-Security-Policy", "").startswith("default-src 'self'")


# ---------------------------------------------------------------------------
# r82 — the service photographs come from the REAL listing's gallery
# ---------------------------------------------------------------------------
def _import_real(tmp: Path):
    """Stage 8 stub photos and run the real import, MEDIA isolated.

    The import copies files into settings.MEDIA_ROOT under fixed names, so
    MEDIA_ROOT is pointed at a throwaway dir (same isolation trick as
    test_real_listing.py — never overwrite the live listing's photos).
    """
    src = tmp / "real-listing-src"
    src.mkdir(parents=True)
    for i in range(1, 9):
        (src / f"real-{i:02d}.jpg").write_bytes(TINY_JPG)
    media = tmp / "media"
    media.mkdir()
    call_command("seed_demo", no_images=True, i_know_this_is_demo=True, verbosity=0)
    with override_settings(MEDIA_ROOT=str(media)):
        call_command("import_real_listing", src=str(src), verbosity=0)


def test_services_page_uses_real_listing_photos():
    """All four rows render the real listing's own gallery URLs."""
    with TemporaryDirectory() as tmp:
        _import_real(Path(tmp))

    html = Client().get("/services/").content.decode()
    # slot 0 = buying, 2 = renting, 7 = enquiries, 6 = listing with us
    assert "/media/property-images/real/nyali-real-01.jpg" in html
    assert "/media/property-images/real/nyali-real-03.jpg" in html
    assert "/media/property-images/real/nyali-real-08.jpg" in html
    assert "/media/property-images/real/nyali-real-07.jpg" in html
    # the honest credit names the listing and links to its detail page
    assert "owner-listed" in html
    assert "Modern Beachfront Apartment in Nyali" in html
    assert 'href="/listing/modern-beachfront-apartment-nyali-' in html


def test_services_page_falls_back_to_static_without_real_listing(client):
    """No real listing -> static images, no media URLs, no credit line."""
    html = client.get("/services/").content.decode()
    assert "real-01-kitchen-island.jpg" in html
    assert "real-03-bedroom-garden.jpg" in html
    assert "real-08-aerial.jpg" in html
    assert "cta-balcony.jpg" in html
    assert "/media/property-images/" not in html
    assert "svc-photo-credit" not in html

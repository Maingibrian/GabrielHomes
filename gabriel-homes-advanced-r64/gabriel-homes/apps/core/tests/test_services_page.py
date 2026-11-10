"""Services page (/services/) — the nav's "04 Services" target.

The nav item historically pointed at /agents/ because no services page
existed. These tests pin the real page: content markers, the four service
rows, live counts from _static_ctx, and sitemap inclusion.
"""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

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

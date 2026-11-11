"""r73 (BACKEND-PLAN 1D/1E) — brand assets editor + SEO & tracking wiring.

Pinned: logo/favicon uploads (validated, small, raster), the public
header/favicon/footer/contact swaps, the GA4 snippet with its CSP nonce,
the Search Console meta, the meta-description override, and the simple
listings section.
"""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from apps.accounts.models import User
from apps.core.models import BrandSettings
from apps.listings.models import Property

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    from apps.agents.models import AgencyProfile
    from apps.listings.models import PropertyType
    from apps.locations.models import Location

    loc_county = Location.objects.create(name="Mombasa", slug="mombasa", level="county")
    loc_area = Location.objects.create(name="Nyali", slug="nyali", level="area", parent=loc_county)
    loc_hood = Location.objects.create(name="Nyali Centre", slug="nyali-centre", level="neighbourhood", parent=loc_area)
    ptype = PropertyType.objects.create(name="Apartment", slug_plural="flats-apartments", slug_single="apartment")
    agency_user = User.objects.create(email="agency-user@test.com", full_name="Test Agency", is_agent=True)
    agency = AgencyProfile.objects.create(user=agency_user, name="Test Agency", slug="test-agency")
    Property.objects.create(
        title="Sea-view Apartment in Nyali", slug="sea-view-apt", listing_type="rent",
        property_type=ptype, location=loc_hood, price=150000, agent=agency,
        status=Property.Status.PUBLISHED, published_at="2026-01-01T10:00:00Z",
    )
    yield


@pytest.fixture
def owner():
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


def _png(name: str = "logo.png", size: int = 8) -> SimpleUploadedFile:
    buf = io.BytesIO()
    Image.new("RGB", (size, size), (180, 83, 45)).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def _content_payload(**overrides) -> dict:
    """A full valid site-content POST (copy fields pre-filled from the row)."""
    brand = BrandSettings.load()
    payload = {
        field: getattr(brand, field)
        for field in (
            "phone", "whatsapp", "email", "hero_tag", "hero_heading_lead",
            "hero_heading_accent", "hero_heading_tail", "hero_subtitle",
            "about_heading", "about_intro", "services_heading", "services_intro",
            "cta_heading", "cta_intro", "footer_lead", "address_line",
            "opening_hours", "instagram_url", "facebook_url", "x_url", "tiktok_url",
        )
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Brand assets — the editor
# ---------------------------------------------------------------------------
def test_owner_can_upload_logo(owner):
    r = owner.post("/manage/site-content/", _content_payload(logo=_png()))
    assert r.status_code == 302
    brand = BrandSettings.load()
    assert brand.logo
    assert brand.logo.name.startswith("brand/")


def test_non_png_logo_rejected(owner):
    bad = SimpleUploadedFile("virus.txt", b"not an image", content_type="text/plain")
    r = owner.post("/manage/site-content/", _content_payload(logo=bad))
    assert r.status_code == 200  # re-render with errors
    # Django's ImageField check or our own validator blocks it — either way
    # the owner sees a validation error, never a saved file.
    assert b"valid image" in r.content or b"supported" in r.content
    assert not BrandSettings.load().logo


def test_huge_logo_rejected(owner):
    big = SimpleUploadedFile("big.png", b"x" * (2 * 1024 * 1024 + 1), content_type="image/png")
    r = owner.post("/manage/site-content/", _content_payload(logo=big))
    assert r.status_code == 200
    assert not BrandSettings.load().logo


def test_editor_has_multipart_enctype(owner):
    r = owner.get("/manage/site-content/")
    assert b'enctype="multipart/form-data"' in r.content
    assert b"Logo, address" in r.content


# ---------------------------------------------------------------------------
# Brand assets — public wiring
# ---------------------------------------------------------------------------
def test_default_header_keeps_the_house_mark():
    r = Client().get("/")
    assert b"brand-mark" in r.content
    assert b"brand-logo" not in r.content


def test_uploaded_logo_replaces_the_house_mark(owner):
    owner.post("/manage/site-content/", _content_payload(logo=_png()))
    r = Client().get("/")
    assert b"brand-logo" in r.content
    assert b"class=\"brand-mark\"" not in r.content


def test_favicon_link_swaps_when_set(owner):
    r = Client().get("/")
    assert b"favicon.svg" in r.content
    owner.post("/manage/site-content/", _content_payload(favicon=_png("icon.png")))
    r = Client().get("/")
    assert b"favicon.svg" not in r.content
    assert BrandSettings.load().favicon.url.encode() in r.content


def test_footer_shows_socials_only_when_filled():
    brand = BrandSettings.load()
    brand.instagram_url = "https://instagram.com/gabrielhomes"
    brand.tiktok_url = "https://tiktok.com/@gabrielhomes"
    brand.save()
    r = Client().get("/")
    assert b"Instagram" in r.content
    assert b"TikTok" in r.content
    assert b"Facebook" not in r.content


def test_contact_page_shows_address_and_hours():
    brand = BrandSettings.load()
    brand.address_line = "Links Road, Nyali, Mombasa"
    brand.opening_hours = "Mon–Sat 8am–6pm"
    brand.save()
    r = Client().get("/contact/")
    assert b"Links Road, Nyali, Mombasa" in r.content
    assert b"Mon" in r.content
    assert b"Where to find us" in r.content


def test_contact_page_hides_address_block_by_default():
    r = Client().get("/contact/")
    assert b"Where to find us" not in r.content


# ---------------------------------------------------------------------------
# SEO & tracking — the editor
# ---------------------------------------------------------------------------
def test_seo_screen_saves_fields(owner):
    r = owner.post(
        "/manage/seo/",
        {
            "meta_description": "Coastal homes, properly checked.",
            "analytics_id": "G-ABC123XYZ9",
            "search_console_token": "verify-token-123",
        },
    )
    assert r.status_code == 302
    brand = BrandSettings.load()
    assert brand.meta_description == "Coastal homes, properly checked."
    assert brand.analytics_id == "G-ABC123XYZ9"
    assert brand.search_console_token == "verify-token-123"


def test_seo_rejects_non_ga4_id(owner):
    r = owner.post("/manage/seo/", {"meta_description": "", "analytics_id": "UA-123", "search_console_token": ""})
    assert r.status_code == 200
    assert not BrandSettings.load().analytics_id


def test_seo_owner_only():
    r = Client().get("/manage/seo/")
    assert r.status_code == 302


# ---------------------------------------------------------------------------
# SEO & tracking — public wiring
# ---------------------------------------------------------------------------
def test_no_analytics_snippet_by_default():
    r = Client().get("/")
    assert b"ga-init.js" not in r.content
    assert b"googletagmanager" not in r.content
    assert b"google-site-verification" not in r.content


def test_analytics_loader_renders_with_id_when_set():
    brand = BrandSettings.load()
    brand.analytics_id = "G-ABC123XYZ9"
    brand.save()
    r = Client().get("/")
    # Local loader file carries the ID — zero inline scripts (CSP pin).
    assert b'src="/static/js/ga-init.js' in r.content
    assert b'data-ga-id="G-ABC123XYZ9"' in r.content
    assert b"<script nonce=" not in r.content


def test_csp_header_carries_nonce_and_ga_origins():
    r = Client().get("/")
    csp = r.headers.get("Content-Security-Policy", "")
    assert "'nonce-" in csp
    assert "https://www.googletagmanager.com" in csp
    assert "unsafe-inline" not in csp.split("script-src")[1].split(";")[0]


def test_search_console_meta_emits_when_set():
    brand = BrandSettings.load()
    brand.search_console_token = "verify-token-123"
    brand.save()
    r = Client().get("/")
    assert b'<meta name="google-site-verification" content="verify-token-123">' in r.content


def test_owner_meta_description_overrides_the_default():
    brand = BrandSettings.load()
    brand.meta_description = "Gabriel Homes — coastal living, carefully checked."
    brand.save()
    r = Client().get("/")
    # The context carries the owner's wording; individual pages may still
    # override the meta block with something more specific (home does).
    assert "coastal living, carefully checked" in r.context["DEFAULT_META_DESCRIPTION"]


# ---------------------------------------------------------------------------
# Simple listings section (1F)
# ---------------------------------------------------------------------------
def test_listings_section_lists_rows_with_tabs(owner):
    r = owner.get("/manage/listings/")
    assert r.status_code == 200
    assert b"Sea-view Apartment" in r.content
    tabs = {item["key"]: item["count"] for item in r.context["tab_items"]}
    assert tabs["all"] == 1
    assert tabs["live"] == 1
    assert b"dashboard/listings/1/edit/" in r.content


def test_listings_tab_filters_by_status(owner):
    p = Property.objects.first()
    p.status = Property.Status.DRAFT
    p.save()
    r = owner.get("/manage/listings/", {"tab": "draft"})
    assert b"Sea-view Apartment" in r.content
    r = owner.get("/manage/listings/", {"tab": "live"})
    assert b"Sea-view Apartment" not in r.content


def test_listings_section_owner_only():
    r = Client().get("/manage/listings/")
    assert r.status_code == 302
    assert r["Location"].startswith("/account/login/")


def test_sample_badge_on_demo_listings(owner):
    p = Property.objects.first()
    p.is_demo = True
    p.save()
    r = owner.get("/manage/listings/")
    assert b"Sample" in r.content


# ---------------------------------------------------------------------------
# The portal nav — five sections, badge only when there are new enquiries
# ---------------------------------------------------------------------------
def test_nav_shows_five_sections(owner):
    r = owner.get("/manage/")
    for label in (b"Home", b"Enquiries", b"Listings", b"Site content", b"SEO"):
        assert label in r.content
    assert b"manage-nav__badge" not in r.content


def test_nav_badge_counts_new_enquiries(owner):
    from apps.inquiries.models import Inquiry

    Inquiry.objects.create(
        property_ref=Property.objects.first(), name="Amina",
        email="a@x.com", phone="", message="hi", status=Inquiry.Status.NEW,
    )
    r = owner.get("/manage/")
    assert b"manage-nav__badge" in r.content

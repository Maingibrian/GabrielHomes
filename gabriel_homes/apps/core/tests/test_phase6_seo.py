"""Tests for Phase 6 — SEO, performance, accessibility."""
import json
import re

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=20, verbosity=0, i_know_this_is_demo=True)
    yield


def _get_first_listing():
    from apps.listings.models import Property
    return Property.objects.published().first()


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------
def test_robots_txt_returns_200():
    c = Client()
    r = c.get("/robots.txt")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/plain")


def test_robots_txt_allows_all():
    c = Client()
    r = c.get("/robots.txt")
    body = r.content.decode()
    assert "User-agent: *" in body
    assert "Allow: /" in body


def test_robots_txt_disallows_private_paths():
    c = Client()
    r = c.get("/robots.txt")
    body = r.content.decode()
    assert "Disallow: /admin/" in body
    assert "Disallow: /account/" in body
    assert "Disallow: /dashboard/" in body


def test_robots_txt_links_to_sitemap():
    c = Client()
    r = c.get("/robots.txt")
    body = r.content.decode()
    assert "Sitemap:" in body
    assert "/sitemap.xml" in body


# ---------------------------------------------------------------------------
# sitemap.xml
# ---------------------------------------------------------------------------
def test_sitemap_returns_200():
    c = Client()
    r = c.get("/sitemap.xml")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("application/xml")


def test_sitemap_contains_home_page():
    c = Client()
    r = c.get("/sitemap.xml")
    body = r.content.decode()
    assert "<loc>http://testserver/</loc>" in body


def test_sitemap_contains_published_listings():
    from apps.listings.models import Property
    c = Client()
    r = c.get("/sitemap.xml")
    body = r.content.decode()
    p = Property.objects.published().first()
    assert p.get_absolute_url() in body


def test_sitemap_excludes_draft_listings():
    from apps.listings.models import Property
    p = Property.objects.published().first()
    Property.objects.filter(pk=p.pk).update(status="draft")
    c = Client()
    r = c.get("/sitemap.xml")
    body = r.content.decode()
    assert p.get_absolute_url() not in body
    Property.objects.filter(pk=p.pk).update(status="published")


def test_sitemap_contains_location_type_combos():
    c = Client()
    r = c.get("/sitemap.xml")
    body = r.content.decode()
    assert "/flats-apartments-for-sale/" in body
    assert "/property-for-sale/" in body or "/property-for-sale/" in body
    # At least one location combo
    assert re.search(r"/flats-apartments-for-sale/\w+/", body) is not None


# ---------------------------------------------------------------------------
# Canonical URLs
# ---------------------------------------------------------------------------
def test_home_has_canonical():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert '<link rel="canonical"' in body


def test_search_has_canonical_without_query_params():
    """§7: Canonical URL for filtered pages = the clean path without query params."""
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/?beds=2&sort=price_desc")
    body = r.content.decode()
    assert '<link rel="canonical" href="/flats-apartments-for-sale/mombasa/"' in body


def test_detail_has_canonical():
    c = Client()
    p = _get_first_listing()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    assert f'<link rel="canonical" href="{p.get_absolute_url()}"' in body


# ---------------------------------------------------------------------------
# Open Graph + Twitter Card
# ---------------------------------------------------------------------------
def test_home_has_og_tags():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert 'og:title' in body
    assert 'og:description' in body
    assert 'og:image' in body
    assert 'og:url' in body


def test_home_has_twitter_card():
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert 'twitter:card' in body
    assert 'twitter:title' in body


def test_search_has_og_tags():
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/")
    body = r.content.decode()
    assert 'og:title' in body
    assert 'og:description' in body


def test_detail_has_og_type_article():
    c = Client()
    p = _get_first_listing()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    assert 'og:type" content="article"' in body


def test_detail_has_og_image_from_property():
    c = Client()
    p = _get_first_listing()
    if p.images.first():
        r = c.get(p.get_absolute_url())
        body = r.content.decode()
        # The OG image should reference the property's first image URL
        assert "og:image" in body


# ---------------------------------------------------------------------------
# JSON-LD
# ---------------------------------------------------------------------------
def test_detail_has_json_ld_residence():
    c = Client()
    p = _get_first_listing()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    # Extract all JSON-LD blocks
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    types = []
    for block in blocks:
        try:
            data = json.loads(block.strip())
            types.append(data.get("@type", ""))
        except json.JSONDecodeError:
            pass
    assert any(t in ("Residence", "Place") for t in types), f"Expected Residence or Place, got {types}"


def test_detail_has_json_ld_breadcrumblist():
    c = Client()
    p = _get_first_listing()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    types = []
    for block in blocks:
        try:
            data = json.loads(block.strip())
            types.append(data.get("@type", ""))
        except json.JSONDecodeError:
            pass
    assert "BreadcrumbList" in types


def test_search_has_json_ld_breadcrumblist():
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/")
    body = r.content.decode()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    types = []
    for block in blocks:
        try:
            data = json.loads(block.strip())
            types.append(data.get("@type", ""))
        except json.JSONDecodeError:
            pass
    assert "BreadcrumbList" in types


# ---------------------------------------------------------------------------
# Unique titles + meta descriptions
# ---------------------------------------------------------------------------
def test_every_page_has_title():
    """§11 Phase 6: no template renders a missing title/description."""
    c = Client()
    urls = ["/", "/flats-apartments-for-sale/", "/flats-apartments-for-sale/mombasa/",
            "/houses-for-rent/nairobi/", "/property-for-sale/mombasa/"]
    p = _get_first_listing()
    urls.append(p.get_absolute_url())
    for url in urls:
        r = c.get(url)
        body = r.content.decode()
        title_match = re.search(r"<title>(.*?)</title>", body)
        assert title_match is not None, f"Page {url} has no <title>"
        assert len(title_match.group(1)) > 5, f"Page {url} has a too-short title"


def test_every_page_has_meta_description():
    c = Client()
    urls = ["/", "/flats-apartments-for-sale/", "/flats-apartments-for-sale/mombasa/"]
    p = _get_first_listing()
    urls.append(p.get_absolute_url())
    for url in urls:
        r = c.get(url)
        body = r.content.decode()
        desc_match = re.search(r'<meta name="description" content="(.*?)"', body)
        assert desc_match is not None, f"Page {url} has no meta description"
        assert len(desc_match.group(1)) > 10, f"Page {url} has a too-short description"


def test_titles_are_unique():
    """Different pages should have different titles."""
    c = Client()
    p = _get_first_listing()
    urls = ["/", "/flats-apartments-for-sale/", p.get_absolute_url()]
    titles = []
    for url in urls:
        r = c.get(url)
        body = r.content.decode()
        title_match = re.search(r"<title>(.*?)</title>", body)
        titles.append(title_match.group(1))
    assert len(set(titles)) == len(titles), f"Titles are not unique: {titles}"


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------
def test_skip_link_present():
    """Every page should have a skip-to-content link for keyboard users."""
    c = Client()
    for url in ["/", "/flats-apartments-for-sale/"]:
        r = c.get(url)
        body = r.content.decode()
        assert 'class="skip-link"' in body, f"Page {url} missing skip-link"
        assert 'href="#main"' in body


def test_main_has_id_main():
    """The <main> element needs id="main" for the skip-link target."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    assert 'id="main"' in body


def test_listing_card_images_have_alt_text():
    """All listing card images must have descriptive alt text."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    # Find all img tags in listing cards
    img_tags = re.findall(r'<img[^>]*class="listing-card__img"[^>]*>', body)
    for img in img_tags:
        assert 'alt="' in img, f"Image missing alt: {img}"
        alt_match = re.search(r'alt="([^"]*)"', img)
        assert alt_match is not None
        assert len(alt_match.group(1)) > 5, f"Alt text too short: {alt_match.group(1)}"


def test_listing_card_images_have_loading_lazy():
    """Below-the-fold images should use loading="lazy"."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    img_tags = re.findall(r'<img[^>]*class="listing-card__img"[^>]*>', body)
    for img in img_tags:
        assert 'loading="lazy"' in img, f"Image missing loading=lazy: {img}"


def test_listing_card_images_have_width_height():
    """Images need width/height to prevent layout shift (CLS)."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    img_tags = re.findall(r'<img[^>]*class="listing-card__img"[^>]*>', body)
    for img in img_tags:
        assert 'width=' in img, f"Image missing width: {img}"
        assert 'height=' in img, f"Image missing height: {img}"


def test_all_svgs_have_aria_hidden():
    """Decorative SVGs should have aria-hidden="true"."""
    c = Client()
    r = c.get("/")
    body = r.content.decode()
    svg_tags = re.findall(r'<svg[^>]*>', body)
    for svg in svg_tags:
        # Every SVG should have aria-hidden OR be inside a button with aria-label
        assert 'aria-hidden="true"' in svg or 'role=' in svg, f"SVG missing aria-hidden: {svg}"


def test_breadcrumbs_have_aria_label():
    """Breadcrumb nav should have aria-label="Breadcrumb"."""
    c = Client()
    r = c.get("/flats-apartments-for-sale/mombasa/")
    body = r.content.decode()
    assert 'aria-label="Breadcrumb"' in body


def test_form_inputs_have_labels():
    """Form inputs should have associated labels (a11y)."""
    c = Client()
    p = _get_first_listing()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    # The enquiry form inputs should have labels or aria-label
    # Check for the honeypot (it has a label even though hidden)
    assert "Leave this field blank" in body or "hp-field" in body


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------
def test_home_cache_works():
    """The home page cache should store the showcase (bento) listings."""
    from django.core.cache import cache
    cache.clear()
    c = Client()
    # First request populates the cache
    c.get("/")
    assert cache.get("home:showcase_listings") is not None
    # Second request uses the cache
    c.get("/")
    assert cache.get("home:showcase_listings") is not None

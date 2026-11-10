"""Sitemaps for static pages — home, how we check, and the
future static pages (about, contact, privacy, terms).

WORK.md §11 Phase 6: sitemap.xml covering listings, locations, and
location + type combos. This file handles the static pages; the
listing/location sitemaps live in apps/listings/sitemaps.py.
"""
from django.contrib import sitemaps
from django.urls import reverse


class StaticSitemap(sitemaps.Sitemap):
    """Static pages with fixed URLs and no lastmod."""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["home"]

    def location(self, item):
        return reverse(item)


class FlatSitemap(sitemaps.Sitemap):
    """Flat pages that don't have URL names yet (about, contact, etc.).

    These return 404 until the pages are built (Phase 7 or later), but
    including them in the sitemap is harmless — search engines will
    retry. Once the pages exist, they'll be picked up automatically.
    """
    changefreq = "monthly"
    priority = 0.3

    def items(self):
        return ["/about/", "/checks/", "/services/", "/contact/", "/privacy/", "/terms/"]

    def location(self, item):
        return item

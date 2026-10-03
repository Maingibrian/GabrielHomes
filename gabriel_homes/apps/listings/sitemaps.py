"""Sitemaps for listings + locations + location+type combos.

Per WORK.md §11 Phase 6: sitemap.xml covering listings, locations, and
location + type combos.
"""
from django.contrib import sitemaps
from django.db.models import QuerySet

from apps.locations.models import Location

from .models import Property, PropertyType


class ListingSitemap(sitemaps.Sitemap):
    """One URL per published listing."""
    changefreq = "weekly"
    priority = 0.9

    def items(self) -> QuerySet[Property]:
        return Property.objects.published().select_related("property_type")

    def lastmod(self, obj: Property):
        return obj.updated_at

    def location(self, obj: Property) -> str:
        return obj.get_absolute_url()


class LocationTypeSitemap(sitemaps.Sitemap):
    """One URL per (property_type × listing_type × location) combo.

    Generates URLs like:
        /flats-apartments-for-sale/mombasa/
        /houses-for-rent/nairobi/
        /property-for-sale/mombasa/

    We include all counties + areas (not neighbourhoods — that would
    generate too many URLs and most have 0 listings). For each location,
    we generate the all-types URL plus one URL per property type that
    actually has listings there.
    """
    changefreq = "weekly"
    priority = 0.7

    def items(self) -> list[str]:
        urls = []
        # Counties + areas (not neighbourhoods — too many, mostly empty)
        locations = Location.objects.filter(
            level__in=[Location.Level.COUNTY, Location.Level.AREA]
        ).order_by("level", "name")

        for loc in locations:
            # Count published listings in this location (with descendants)
            descendant_pks = set(loc.get_descendants(include_self=True).values_list("pk", flat=True))
            listing_count = Property.objects.published().filter(location__in=descendant_pks).count()
            if listing_count == 0:
                continue

            # All-types URLs
            urls.append(f"/property-for-sale/{loc.slug}/")
            urls.append(f"/property-for-rent/{loc.slug}/")

            # Per-type URLs — only for types that have listings here
            for pt in PropertyType.objects.order_by("position", "name"):
                sale_count = Property.objects.published().filter(
                    listing_type="sale", property_type=pt, location__in=descendant_pks
                ).count()
                if sale_count:
                    urls.append(f"/{pt.slug_plural}-for-sale/{loc.slug}/")
                rent_count = Property.objects.published().filter(
                    listing_type="rent", property_type=pt, location__in=descendant_pks
                ).count()
                if rent_count:
                    urls.append(f"/{pt.slug_plural}-for-rent/{loc.slug}/")

        # Also include the type-only URLs (no location)
        for pt in PropertyType.objects.order_by("position", "name"):
            urls.append(f"/{pt.slug_plural}-for-sale/")
            urls.append(f"/{pt.slug_plural}-for-rent/")

        return urls

    def location(self, url: str) -> str:
        return url

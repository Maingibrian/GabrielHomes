"""URL patterns for the listings app — SEO-friendly search URLs.

Per WORK.md §7:
    /<type-plural>-for-sale/                  e.g. /flats-apartments-for-sale/
    /<type-plural>-for-sale/<location-slug>/  e.g. /flats-apartments-for-sale/mombasa/
    /<type-plural>-for-rent/                  e.g. /houses-for-rent/
    /<type-plural>-for-rent/<location-slug>/  e.g. /houses-for-rent/nairobi/
    /property-for-sale/<location-slug>/       all types in a location
    /property-for-rent/<location-slug>/
    /listing/<slug>-<id>/                     property detail

Plus the location autocomplete endpoint:
    /search/locations/?q=mom
"""
from django.urls import path

from . import views

urlpatterns = [
    # Listing detail (per §7 — /listing/<slug>-<id>/)
    path(
        "listing/<slug:slug>-<int:pk>/",
        views.listing_detail,
        name="listing_detail",
    ),

    # Location autocomplete (JSON) — used by the hero search bar
    path("search/locations/", views.location_autocomplete, name="location_autocomplete"),

    # All-types + location (must come before the generic <type>-for-* patterns
    # so "property" doesn't get matched as a type_slug).
    path(
        "property-for-sale/<slug:location_slug>/",
        views.search,
        {"listing_type": "sale", "type_slug": None},
        name="search_all_sale_loc",
    ),
    path(
        "property-for-rent/<slug:location_slug>/",
        views.search,
        {"listing_type": "rent", "type_slug": None},
        name="search_all_rent_loc",
    ),

    # Type-only (no location)
    path(
        "<slug:type_slug>-for-sale/",
        views.search,
        {"listing_type": "sale"},
        name="search_type_sale",
    ),
    path(
        "<slug:type_slug>-for-rent/",
        views.search,
        {"listing_type": "rent"},
        name="search_type_rent",
    ),

    # Type + location
    path(
        "<slug:type_slug>-for-sale/<slug:location_slug>/",
        views.search,
        {"listing_type": "sale"},
        name="search_type_sale_loc",
    ),
    path(
        "<slug:type_slug>-for-rent/<slug:location_slug>/",
        views.search,
        {"listing_type": "rent"},
        name="search_type_rent_loc",
    ),
]

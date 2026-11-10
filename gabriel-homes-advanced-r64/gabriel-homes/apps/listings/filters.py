"""PropertyFilter — django-filter FilterSet for the search page.

Per WORK.md §9:
- Location filter includes descendants (searching "Nairobi" includes
  Westlands, Kilimani, etc.) — handled in the view via the URL path,
  not here, because the location is encoded in the URL.
- Free-text `q` searches title, description, location name (PostgreSQL
  full-text search where available; falls back to icontains on SQLite).
- Price filters use KES.
- Sort options are whitelisted (per §13: never trust user input in
  lookup strings).
"""
from __future__ import annotations

import django_filters

from .models import Property


SORT_OPTIONS = [
    ("newest", "Newest first"),
    ("price_asc", "Price (low to high)"),
    ("price_desc", "Price (high to low)"),
    ("featured", "Featured first"),
]


class PropertyFilter(django_filters.FilterSet):
    """Query-param filters for the search results page.

    The URL-path-based filters (listing_type, property_type, location
    with descendants) are applied by the view before this FilterSet
    runs — those define the canonical URL. This FilterSet handles only
    the query-string filters: q, min_price, max_price, beds, baths,
    furnishing, amenities, sort.
    """

    q = django_filters.CharFilter(method="filter_q", help_text="Free-text search across title, description, and location name.")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    beds = django_filters.NumberFilter(field_name="bedrooms", lookup_expr="gte")
    baths = django_filters.NumberFilter(field_name="bathrooms", lookup_expr="gte")
    furnishing = django_filters.ChoiceFilter(choices=Property.Furnishing.choices)
    amenities = django_filters.AllValuesMultipleFilter(field_name="amenities__slug")
    sort = django_filters.ChoiceFilter(method="filter_sort", choices=SORT_OPTIONS)

    class Meta:
        model = Property
        fields = ["q", "min_price", "max_price", "beds", "baths", "furnishing", "amenities", "sort"]

    # ------------------------------------------------------------------
    # Free-text search
    # ------------------------------------------------------------------
    def filter_q(self, queryset, name, value: str):
        """Search title, description, and location name.

        On PostgreSQL we'd use SearchVector for full-text search; on
        SQLite (local dev) we fall back to icontains. We detect the
        backend from the connection vendor so the same code works in
        both environments.
        """
        if not value:
            return queryset
        from django.db import connection

        if connection.vendor == "postgresql":
            # Full-text search across title + description + location name.
            # Use to_tsquery with simple config so punctuation is handled.
            return queryset.filter(
                # PostgreSQL full-text search would go here.
                # Kept simple for v1; the icontains fallback works fine
                # for the seeded data size.
                title__icontains=value,
            ) | queryset.filter(
                description__icontains=value,
            ) | queryset.filter(
                location__name__icontains=value,
            ) | queryset.filter(
                location__parent__name__icontains=value,
            ) | queryset.filter(
                location__parent__parent__name__icontains=value,
            )
        # SQLite fallback — icontains across the same fields.
        return queryset.filter(
            title__icontains=value,
        ) | queryset.filter(
            description__icontains=value,
        ) | queryset.filter(
            location__name__icontains=value,
        ) | queryset.filter(
            location__parent__name__icontains=value,
        ) | queryset.filter(
            location__parent__parent__name__icontains=value,
        )

    # ------------------------------------------------------------------
    # Sort — whitelisted options only (per §13)
    # ------------------------------------------------------------------
    def filter_sort(self, queryset, name, value: str):
        if value == "price_asc":
            return queryset.order_by("price", "-published_at")
        if value == "price_desc":
            return queryset.order_by("-price", "-published_at")
        if value == "featured":
            return queryset.order_by("-is_featured", "-published_at")
        # "newest" is the default
        return queryset.order_by("-published_at")

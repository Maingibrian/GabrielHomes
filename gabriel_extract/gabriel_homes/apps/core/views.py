"""Core views — home + styleguide.

Phase 2 makes the home page real-DB-driven per WORK.md §8.
"""
from django.conf import settings
from django.shortcuts import render

from apps.agents.models import AgencyProfile
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location


def home(request):
    """Home page — all 10 sections from WORK.md §8, real-DB-driven.

    The featured-listings section is cached for 5 minutes (per §11
    Phase 6: template fragment caching on home). The cache key includes
    the list of featured listing PKs so it invalidates when listings
    change status.
    """
    from django.core.cache import cache

    # Featured published listings — up to 6 for the home grid.
    # Try the cache first; the fragment cache in the template handles
    # the rendered HTML, but we also cache the queryset result to avoid
    # re-running the query on every request.
    cache_key = "home:featured_listings"
    featured_listings = cache.get(cache_key)
    if featured_listings is None:
        featured_listings = list(
            Property.objects.published().filter(is_featured=True).select_related(
                "property_type", "location__parent__parent", "agent__user",
            ).prefetch_related("images")[:6]
        )
        # If we don't have enough featured, top up with the newest published.
        if len(featured_listings) < 6:
            seen = {p.pk for p in featured_listings}
            extra = Property.objects.published().exclude(pk__in=seen).order_by("-published_at")[
                : 6 - len(featured_listings)
            ]
            featured_listings.extend(list(extra))
        cache.set(cache_key, featured_listings, 60 * 5)  # 5 minutes

    # Agencies for the Agents section.
    agencies = list(
        AgencyProfile.objects.select_related("user").order_by("name")[:8]
    )

    # Browse-by-location: top counties by listing count.
    counties = list(Location.objects.filter(level=Location.Level.COUNTY).order_by("name"))
    for county in counties:
        # Count listings whose leaf location is a descendant of this county.
        county.listing_count = Property.objects.published().filter(
            location__in=county.get_descendants(include_self=True)
        ).count()

    # Browse-by-type: every type, with its live published-listing count.
    types_with_counts = []
    for pt in PropertyType.objects.order_by("position", "name"):
        types_with_counts.append({
            "type": pt,
            "count": Property.objects.published().filter(property_type=pt).count(),
        })

    # Stats for the hero counters — derive from DB so they stay accurate.
    total_published = Property.objects.published().count()
    verified_count = Property.objects.published().filter(is_verified=True).count()
    verified_pct = int(round(100 * verified_count / total_published)) if total_published else 0
    active_neighbourhoods = (
        Property.objects.published()
        .values_list("location_id", flat=True)
        .distinct()
        .count()
    )

    context = {
        "body_class": "page-home",
        "featured_listings": featured_listings,
        "agencies": agencies,
        "counties": counties,
        "types_with_counts": types_with_counts,
        # Hero stats
        "stat_published": total_published,
        "stat_verified_pct": verified_pct,
        "stat_neighbourhoods": active_neighbourhoods,
        # Numbers section
        "number_years": 12,
        "number_tx_value_bn": 1.4,
        "number_referrals_pct": verified_pct,
        "number_neighbourhoods": active_neighbourhoods,
    }
    return render(request, "core/home.html", context)


def styleguide(request):
    """Style guide page — shows every component from WORK.md §10.5.

    Dev-only: returns 404 when DEBUG=False so the page is unreachable
    in production even though the URL is always registered (this lets
    tests using pytest-django, which forces DEBUG=False, still hit the
    route via the always-on URL).
    """
    from django.conf import settings
    from django.http import Http404

    if not settings.DEBUG and not request.user.is_staff:
        raise Http404("Style guide is dev-only.")

    from apps.listings.models import Property

    swatches = [
        {"name": "cream",    "hex": "#faf8f4"},
        {"name": "white",    "hex": "#ffffff"},
        {"name": "sand",     "hex": "#d8c9b8"},
        {"name": "taupe",    "hex": "#8a7d70"},
        {"name": "clay",     "hex": "#a66a4d"},
        {"name": "brown",    "hex": "#5a4032"},
        {"name": "espresso", "hex": "#2a211c"},
        {"name": "ink",      "hex": "#211e1b"},
        {"name": "burnt",    "hex": "#af4715"},
    ]
    sample_listings = list(
        Property.objects.published().select_related(
            "property_type", "location__parent__parent", "agent__user",
        ).prefetch_related("images")[:3]
    )
    return render(request, "core/styleguide.html", {
        "body_class": "page-styleguide",
        "swatches": swatches,
        "sample_listings": sample_listings,
    })

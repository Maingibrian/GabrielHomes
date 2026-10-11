"""Core views — home, styleguide, and static pages (about/contact/privacy/terms).

Phase 2 makes the home page real-DB-driven per WORK.md §8.
The static pages close the §7 URL-map gap: /about/ /contact/ /privacy/ /terms/.
"""
from django.conf import settings
from django.shortcuts import render

from apps.agents.models import AgencyProfile
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location


def home(request):
    """Home page — hero slideshow, homes bento showcase, story, numbers,
    philosophy, browse, CTA (docs/HOME-REDESIGN.md).

    The showcase (bento) section is cached for 5 minutes; the cache key
    invalidates naturally when listings change because we cache the
    queryset result, and the fragment renders fresh each request.
    """
    from django.core.cache import cache

    # Homes showcase — up to 6 published listings for the bento mosaic.
    # Spotlight (first card) = strongest featured listing; the rest are
    # the most recently published. Topped up from the newest published
    # when not enough are flagged featured.
    cache_key = "home:showcase_listings"
    showcase_listings = cache.get(cache_key)
    if showcase_listings is None:
        showcase_listings = list(
            Property.objects.published().filter(is_featured=True)
            .select_related(
                "property_type", "location__parent__parent", "agent__user",
            )
            .prefetch_related("images")
            .order_by("-published_at")[:6]
        )
        if len(showcase_listings) < 6:
            seen = {p.pk for p in showcase_listings}
            extra = (
                Property.objects.published()
                .exclude(pk__in=seen)
                .select_related(
                    "property_type", "location__parent__parent", "agent__user",
                )
                .prefetch_related("images")
                .order_by("-published_at")[: 6 - len(showcase_listings)]
            )
            showcase_listings.extend(list(extra))
        cache.set(cache_key, showcase_listings, 60 * 5)  # 5 minutes

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
        "showcase_listings": showcase_listings,
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


# ---------------------------------------------------------------------------
# Static pages — /about/ /contact/ /privacy/ /terms/ (WORK.md §7, §8)
# ---------------------------------------------------------------------------
def _static_ctx(**extra):
    """Shared context for the static pages (agency count, listing count)."""
    ctx = {
        "agency_count": AgencyProfile.objects.count(),
        "listing_count": Property.objects.published().count(),
    }
    ctx.update(extra)
    return ctx


def about(request):
    """About page — the Gabriel Homes story, values, and team intro."""
    agencies = list(
        AgencyProfile.objects.select_related("user").order_by("name")[:8]
    )
    return render(request, "core/about.html", _static_ctx(
        body_class="page-about",
        page_title="About us — Gabriel Homes",
        meta_description=(
            "Gabriel Homes is a Kenyan real estate agency with a human point "
            "of view — curated properties, verified details, and full support "
            "across Mombasa, Nairobi, Kilifi, Diani, Kiambu and Kajiado."
        ),
        canonical_url="/about/",
        agencies=agencies,
    ))


def contact(request):
    """Contact page — all the ways to reach Gabriel Homes."""
    return render(request, "core/contact.html", _static_ctx(
        body_class="page-contact",
        page_title="Contact us — Gabriel Homes",
        meta_description=(
            "Talk to Gabriel Homes — call +254 712 345 678, WhatsApp us, or "
            "visit the office at Nyali Centre, Links Road, Mombasa."
        ),
        canonical_url="/contact/",
    ))


def privacy(request):
    """Privacy policy page."""
    return render(request, "core/privacy.html", _static_ctx(
        body_class="page-privacy",
        page_title="Privacy policy — Gabriel Homes",
        meta_description=(
            "How Gabriel Homes collects, uses, and protects your personal "
            "data, in line with the Kenya Data Protection Act, 2019."
        ),
        canonical_url="/privacy/",
    ))


def terms(request):
    """Terms of service page."""
    return render(request, "core/terms.html", _static_ctx(
        body_class="page-terms",
        page_title="Terms of service — Gabriel Homes",
        meta_description=(
            "The terms that govern your use of the Gabriel Homes property "
            "portal — listings, enquiries, accounts, and acceptable use."
        ),
        canonical_url="/terms/",
    ))


# ---------------------------------------------------------------------------
# Health check (D3)
# ---------------------------------------------------------------------------
from django.db import connection  # noqa: E402
from django.http import JsonResponse  # noqa: E402


def healthz(request):
    """Liveness + DB-reachability probe for uptime checkers and load balancers.

    Runs `SELECT 1`: 200 "ok" when the database answers, 503 "unavailable"
    when it does not. Returns no details (no stack traces, no timings) —
    this endpoint is public by design.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})

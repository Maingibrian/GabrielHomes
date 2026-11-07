"""Core views — home, styleguide, and static pages (about/contact/privacy/terms).

Phase 2 makes the home page real-DB-driven per WORK.md §8.
The static pages close the §7 URL-map gap: /about/ /contact/ /privacy/ /terms/.
"""
from django.conf import settings
from django.db.models import Count, Q
from django.contrib import messages
from django.shortcuts import render

from apps.agents.models import AgencyProfile
from apps.core.models import SiteSetting
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location


def published_property_q() -> Q:
    """Q-filter matching Property.objects.published() for use in annotations.

    published() can't be used inside Count(filter=...) directly, so this
    mirrors it — including the r11 demo switch — for aggregate queries.
    """
    q = Q(properties__status=Property.Status.PUBLISHED)
    if SiteSetting.demo_hidden():
        q &= Q(properties__is_demo=False)
    return q


def _hero_popular_areas(mombasa_ids: list[int]) -> list[dict]:
    """r49: the hero's "Popular" chips — the four Mombasa areas with the
    most published listings right now (live data, never hardcoded names),
    each linking to its sale search page. Listings hang off NEIGHBOURHOOD
    leaves, so each area counts its descendants too (same per-area loop
    pattern as the counties browse block above). Thumbs are decorative
    stock shots (aria-hidden in the template), mapped by slug with a
    fallback so an unexpected area still renders."""
    from django.templatetags.static import static as static_url

    thumbs = {
        "nyali": "img/stock/nyali-apartment.jpg",
        "bamburi": "img/stock/mombasa-villa.webp",
        "town": "img/stock/coastal-living.jpg",
        "mtwapa": "img/stock/pool-villa-day.jpg",
        "shanzu": "img/stock/pool-villa-night.webp",
        "likoni": "img/stock/modern-living.jpg",
    }
    areas = []
    for area in Location.objects.filter(
        level=Location.Level.AREA, pk__in=mombasa_ids,
    ).order_by("name"):
        area_ids = [area.pk, *area.get_descendants().values_list("pk", flat=True)]
        count = Property.objects.published().filter(
            location_id__in=area_ids).count()
        if count:
            areas.append((area, count))
    areas.sort(key=lambda pair: (-pair[1], pair[0].name))
    return [
        {
            "name": area.name,
            "url": f"/property-for-sale/{area.slug}/",
            "count": count,
            "thumb": static_url(thumbs.get(area.slug, "img/stock/modern-living.jpg")),
        }
        for area, count in areas[:4]
    ]


def home(request):
    """Home page — hero slideshow, homes bento showcase, story, numbers,
    philosophy, browse, CTA (docs/HOME-REDESIGN.md).

    The showcase (bento) section is cached for 5 minutes; the cache key
    invalidates naturally when listings change because we cache the
    queryset result, and the fragment renders fresh each request.
    """
    from django.core.cache import cache

    # Keep the presentation centred on Mombasa. Demo listings remain clearly
    # labelled in the templates and disappear automatically when the owner
    # enables the existing "hide demo data" switch.
    mombasa = Location.objects.filter(level=Location.Level.COUNTY, name="Mombasa").first()
    mombasa_ids = (mombasa.get_descendants(include_self=True).values_list("pk", flat=True)
                   if mombasa else [])
    public_listings = Property.objects.published().filter(location_id__in=mombasa_ids)
    public_listings = public_listings.select_related(
        "property_type", "location__parent__parent", "agent__user",
    ).prefetch_related("images", "amenities")

    real_showcase = Property.objects.published().exclude(is_demo=True).select_related(
        "property_type", "location__parent__parent", "agent__user",
    ).prefetch_related("images", "amenities")
    # Real owner-entered inventory always takes priority. Until it exists,
    # the explicitly labelled Mombasa presentation set demonstrates the UI.
    showcase_source = real_showcase if real_showcase.exists() else public_listings
    cache_key = "home:showcase_listings"
    showcase_listings = cache.get(cache_key)
    if showcase_listings is None:
        showcase_listings = list(showcase_source.filter(is_featured=True).order_by("-published_at")[:6])
        if len(showcase_listings) < 6:
            seen = {p.pk for p in showcase_listings}
            extra = showcase_source.exclude(pk__in=seen).order_by("-published_at")[: 6 - len(showcase_listings)]
            showcase_listings.extend(list(extra))
        cache.set(cache_key, showcase_listings, 60 * 5)  # 5 minutes

    # r13: three per market so each home-page section can lay out as a
    # feature + rail / banners / stagger instead of twin cards.
    sale_listings = list(public_listings.filter(
        listing_type=Property.ListingType.SALE,
    ).order_by("-is_featured", "-published_at")[:3])
    rent_listings = list(public_listings.filter(
        listing_type=Property.ListingType.RENT, is_short_stay=False,
    ).order_by("-is_featured", "-published_at")[:3])
    short_stay_listings = list(public_listings.filter(is_short_stay=True).order_by(
        "-is_featured", "-published_at",
    )[:3])
    amenity_listings = list(public_listings.exclude(address_text="").order_by(
        "-is_featured", "-published_at",
    )[:4])

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
    # (r2: removed the old verified_pct computation — no template ever
    # rendered it and the name carried the banned "verified" wording.)
    total_published = public_listings.count()
    active_neighbourhoods = (
        public_listings
        .values_list("location_id", flat=True)
        .distinct()
        .count()
    )

    context = {
        "body_class": "page-home",
        "showcase_listings": showcase_listings,
        # r49: the floating hero card promotes the same featured listing the
        # bento spotlights (first showcase entry; None hides the card).
        "hero_card_listing": showcase_listings[0] if showcase_listings else None,
        "popular_areas": _hero_popular_areas(list(mombasa_ids)),
        "sale_listings": sale_listings,
        "rent_listings": rent_listings,
        "short_stay_listings": short_stay_listings,
        "amenity_listings": amenity_listings,
        "counties": counties,
        "types_with_counts": types_with_counts,
        # Browse lists show only places and types with real published listings
        "live_counties": [c for c in counties if c.listing_count],
        "live_types": [e for e in types_with_counts if e["count"]],
        # Hero stats
        "stat_published": total_published,
        "stat_neighbourhoods": active_neighbourhoods,
        # Numbers section
        "number_neighbourhoods": active_neighbourhoods,
    }
    return render(request, "core/home.html", context)


def _static_ctx(**extra):
    """Shared context for the static pages (agency count, listing count)."""
    ctx = {
        "agency_count": AgencyProfile.objects.public().count(),
        "listing_count": Property.objects.published().count(),
    }
    ctx.update(extra)
    return ctx


def about(request):
    """About page — the Gabriel Homes story, values, and team intro.

    Cards on this page carry live contact links, so each agency ships with
    its office location and a count of active (published) listings —
    annotated in SQL rather than per-card queries.
    """
    agencies = list(
        AgencyProfile.objects.public()
        .select_related("user", "office_location")
        .annotate(
            active_listings=Count(
                "properties",
                filter=published_property_q(),
            )
        )
        .order_by("name")[:8]
    )
    return render(request, "core/about.html", _static_ctx(
        body_class="page-about",
        page_title="About us — Gabriel Homes",
        meta_description=(
            "Gabriel Homes is a new Kenyan real estate company, founded in 2026. "
            "Every listing is checked by hand before it goes live."
        ),
        canonical_url="/about/",
        agencies=agencies,
    ))


def newsletter_subscribe(request):
    """POST-only: take an opt-in and send the confirmation email."""
    from django.http import HttpResponseNotAllowed
    from django.shortcuts import redirect
    from apps.core import newsletter as nl
    from apps.core.forms import NewsletterSignupForm

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    form = NewsletterSignupForm(request.POST)
    if not form.is_valid():
        messages.error(request, form.errors.as_text().replace("* ", "").strip() or "Please check the form.")
        nxt = request.POST.get("next") or ""
        # Only same-site paths: never redirect to an external address.
        safe = nxt.startswith("/") and not nxt.startswith("//") and "\\" not in nxt
        return redirect(nxt if safe else "/#newsletter")
    nl.subscribe(form.cleaned_data["email"])
    return render(request, "core/newsletter_message.html", _static_ctx(
        body_class="page-newsletter",
        page_title="Check your email — Gabriel Homes",
        meta_description="Confirm your Gabriel Homes newsletter sign-up.",
        canonical_url="/newsletter/",
        heading="Check your email",
        message="We have sent a link to confirm your sign-up. The newsletter starts "
                "once you confirm, and you can unsubscribe from any email.",
    ))


def newsletter_confirm(request, token):
    from apps.core import newsletter as nl
    sub = nl.confirm(token)
    ok = sub is not None
    return render(request, "core/newsletter_message.html", _static_ctx(
        body_class="page-newsletter",
        page_title="Newsletter — Gabriel Homes",
        meta_description="Gabriel Homes newsletter.",
        canonical_url="/newsletter/",
        heading="You are subscribed" if ok else "This link is not valid",
        message=("Thank you. You will receive the newsletter when we have published ten new listings."
                 if ok else "The link may have expired or been used already. Sign up again on the home page."),
    ), status=200 if ok else 404)


def newsletter_unsubscribe(request, token):
    from apps.core import newsletter as nl
    sub = nl.unsubscribe(token)
    ok = sub is not None
    return render(request, "core/newsletter_message.html", _static_ctx(
        body_class="page-newsletter",
        page_title="Unsubscribed — Gabriel Homes",
        meta_description="Gabriel Homes newsletter.",
        canonical_url="/newsletter/",
        heading="You have been unsubscribed" if ok else "This link is not valid",
        message=("You will not receive any more newsletters from us." if ok
                 else "The link is not recognised. Contact us through the Contact page and we will remove you."),
    ), status=200 if ok else 404)


def checks(request):
    """How Gabriel Homes checks a listing before it is published."""
    return render(request, "core/checks.html", _static_ctx(
        body_class="page-checks",
        page_title="How we check listings — Gabriel Homes",
        meta_description=(
            "Every Gabriel Homes listing is checked by Gabriel and the team before "
            "it is published: five checks before a listing goes live, and five before it is published."
        ),
        canonical_url="/checks/",
    ))


def services(request):
    """Services page — what Gabriel Homes does: buy, rent & stays, list, support."""
    return render(request, "core/services.html", _static_ctx(
        body_class="page-services",
        page_title="Services — Gabriel Homes",
        meta_description=(
            "What Gabriel Homes does: buying with checked listings, rent and "
            "short stays across the Kenyan coast, listing your property with "
            "honest photography, and support from offer to handover."
        ),
        canonical_url="/services/",
    ))


def contact(request):
    """Contact page — all the ways to reach Gabriel Homes."""
    return render(request, "core/contact.html", _static_ctx(
        body_class="page-contact",
        page_title="Contact us — Gabriel Homes",
        meta_description=(
            "Contact Gabriel Homes about a listing, or about a property you want to list."
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

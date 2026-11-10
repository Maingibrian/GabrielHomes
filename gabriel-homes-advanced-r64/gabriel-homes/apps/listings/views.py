"""Listings views — search results page + location autocomplete.

Per WORK.md §7-§9:
- SEO-friendly URLs: /<type-plural>-for-sale/<location-slug>/
- FilterSet with location descendants (searching "Nairobi" includes
  Westlands, Kilimani, etc.)
- Pagination (24 per page) via HTMX with graceful full-page fallback
- Generated H1, breadcrumbs, canonical URL (clean path, no query params)
- Empty state with suggestions
- All queries use select_related / prefetch_related to avoid N+1
"""
from __future__ import annotations

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.locations.models import Location

from .filters import PropertyFilter, SORT_OPTIONS
from .models import Property, PropertyType

# 24 per page — per WORK.md §8 (Search results).
PAGE_SIZE = 24


def _resolve_location(location_slug: str | None) -> Location | None:
    """Resolve a location slug to a Location, matching at any level."""
    if not location_slug:
        return None
    # Slug is unique per parent, so a bare slug may match multiple
    # locations at different levels (e.g. "nyali" the area vs a
    # neighbourhood that happens to share the slug). Prefer the
    # shallowest match (county > area > neighbourhood).
    qs = Location.objects.filter(slug=location_slug).order_by("level")
    return qs.first()


def _location_filter_q(location: Location) -> Q:
    """Build a Q object matching the location AND all its descendants.

    WORK.md §9: "searching 'Nairobi' includes Westlands, Kilimani, etc."
    We walk 3 levels deep (county > area > neighbourhood) and OR the
    pks together.
    """
    descendant_pks = set(location.get_descendants(include_self=True).values_list("pk", flat=True))
    return Q(location__in=descendant_pks)


def _build_h1(listing_type: str, ptype: PropertyType | None, location: Location | None) -> str:
    """Generate the H1 from the URL context.

    Examples:
        sale, Flats & Apartments, None      -> "Flats & Apartments for Sale"
        rent, Houses, Mombasa               -> "Houses for Rent in Mombasa"
        sale, None, Mombasa                 -> "Property for Sale in Mombasa"
    """
    type_name = ptype.name if ptype else "Property"
    if listing_type is None:
        # Combined browse-all page (/properties/) — no type filter applied.
        if not ptype:
            type_name = "Properties"
        return f"{type_name} for Sale and Rent" + (
            f" in {location.name}" if location else ""
        )
    action = "for Sale" if listing_type == "sale" else "for Rent"
    h1 = f"{type_name} {action}"
    if location:
        # Use the location's own name (not the full path) for the H1.
        h1 += f" in {location.name}"
    return h1


def _build_breadcrumbs(listing_type: str, ptype: PropertyType | None, location: Location | None) -> list[dict]:
    """Build breadcrumb trail: Home > [Type] for [Sale/Rent] > [Location]."""
    crumbs = [{"name": "Home", "url": "/"}]
    if listing_type is None:
        # Combined page: Home > Properties > [Location]
        crumbs.append({"name": "Properties", "url": ""})
        if location:
            crumbs.append({"name": location.name, "url": ""})
        return crumbs
    action = "for Sale" if listing_type == "sale" else "for Rent"
    type_name = ptype.name if ptype else "Property"

    if ptype:
        type_url = f"/{ptype.slug_plural}-{'for-sale' if listing_type == 'sale' else 'for-rent'}/"
    else:
        type_url = f"/property-{'for-sale' if listing_type == 'sale' else 'for-rent'}/"

    crumbs.append({"name": f"{type_name} {action}", "url": type_url})
    if location:
        crumbs.append({"name": location.name, "url": ""})  # current page
    return crumbs


def _build_canonical_url(listing_type: str, ptype: PropertyType | None, location: Location | None) -> str:
    """Canonical URL = the clean path without query params (per §7)."""
    if listing_type is None:
        # Combined browse-all page.
        return "/properties/" + (f"{location.slug}/" if location else "")
    if ptype:
        base = f"/{ptype.slug_plural}-{'for-sale' if listing_type == 'sale' else 'for-rent'}/"
    else:
        base = f"/property-{'for-sale' if listing_type == 'sale' else 'for-rent'}/"
    if location:
        base += f"{location.slug}/"
    return base


def _build_related_searches(listing_type: str, ptype: PropertyType | None, location: Location | None) -> list[dict]:
    """Build a 'Related searches' link block for the bottom of the page."""
    if listing_type is None:
        # Combined page — point people at the two canonical SEO surfaces
        # plus the top counties.
        related = [
            {"name": "Property for Sale", "url": "/property-for-sale/"},
            {"name": "Property for Rent", "url": "/property-for-rent/"},
        ]
        top_counties = Location.objects.filter(
            level=Location.Level.COUNTY
        ).order_by("name")[:6]
        for county in top_counties:
            related.append({
                "name": f"Property for Sale in {county.name}",
                "url": f"/property-for-sale/{county.slug}/",
            })
        return related[:8]
    related = []
    action_suffix = "for-sale" if listing_type == "sale" else "for-rent"
    action_label = "for Sale" if listing_type == "sale" else "for Rent"

    if location:
        # Other types in the same location
        other_types = PropertyType.objects.exclude(pk=ptype.pk if ptype else None).order_by("position")[:5]
        for ot in other_types:
            related.append({
                "name": f"{ot.name} {action_label} in {location.name}",
                "url": f"/{ot.slug_plural}-{action_suffix}/{location.slug}/",
            })
        # Same type (or all-types) in sibling locations
        if location.parent:
            siblings = Location.objects.filter(parent=location.parent).exclude(pk=location.pk)[:4]
            for sib in siblings:
                if ptype:
                    url = f"/{ptype.slug_plural}-{action_suffix}/{sib.slug}/"
                else:
                    url = f"/property-{action_suffix}/{sib.slug}/"
                label_pt = ptype.name if ptype else "Property"
                related.append({
                    "name": f"{label_pt} {action_label} in {sib.name}",
                    "url": url,
                })
    else:
        # No location — show top locations for this type
        top_counties = Location.objects.filter(level=Location.Level.COUNTY).order_by("name")[:5]
        for county in top_counties:
            if ptype:
                url = f"/{ptype.slug_plural}-{action_suffix}/{county.slug}/"
            else:
                url = f"/property-{action_suffix}/{county.slug}/"
            label_pt = ptype.name if ptype else "Property"
            related.append({
                "name": f"{label_pt} {action_label} in {county.name}",
                "url": url,
            })

    return related[:8]


def search(request, type_slug: str | None = None, location_slug: str | None = None, listing_type: str = "sale"):
    """Search results page — the heart of the portal.

    URL patterns (per §7):
        /<type>-for-sale/                       -> type_slug set, no location
        /<type>-for-sale/<location>/            -> both set
        /<type>-for-rent/                       -> type_slug set, no location
        /<type>-for-rent/<location>/            -> both set
        /property-for-sale/<location>/          -> type_slug=None, location set
        /property-for-rent/<location>/          -> type_slug=None, location set
    """
    # ------------------------------------------------------------------
    # Resolve URL context
    # ------------------------------------------------------------------
    # No-JS hero-search fallback: when JavaScript is unavailable the hero
    # form submits GET params (listing_type / type / location_slug) to the
    # bare /property-for-<sale|rent>/ route. Honour those params only when
    # the URL path didn't already provide them, so SEO URLs are unaffected.
    if type_slug is None:
        type_slug = request.GET.get("type") or None
    if location_slug is None:
        location_slug = request.GET.get("location_slug") or None

    ptype = None
    if type_slug:
        ptype = get_object_or_404(PropertyType, slug_plural=type_slug)

    location = _resolve_location(location_slug)
    if location_slug and not location:
        from django.http import Http404
        raise Http404("Location not found.")

    # ------------------------------------------------------------------
    # Base queryset — only published listings, filtered by URL context
    # ------------------------------------------------------------------
    qs = Property.objects.published()
    if listing_type:  # None on the combined /properties/ page — all types
        qs = qs.filter(listing_type=listing_type)
    else:
        # Keep placeholder inventory Mombasa-only while never hiding genuine
        # owner-entered listings should the business expand later.
        mombasa = Location.objects.filter(level=Location.Level.COUNTY, name="Mombasa").first()
        if mombasa:
            qs = qs.filter(
                Q(is_demo=False)
                | Q(location__in=mombasa.get_descendants(include_self=True))
            )
    market = request.GET.get("market", "").lower()
    if market == "sale":
        qs = qs.filter(listing_type=Property.ListingType.SALE)
    elif market == "rent":
        qs = qs.filter(listing_type=Property.ListingType.RENT, is_short_stay=False)
    elif market == "bnb":
        qs = qs.filter(listing_type=Property.ListingType.RENT, is_short_stay=True)

    if ptype:
        qs = qs.filter(property_type=ptype)

    if location:
        qs = qs.filter(_location_filter_q(location))

    # Eager-load everything the listing card needs (avoid N+1).
    qs = qs.select_related(
        "property_type", "location__parent__parent", "agent__user",
    ).prefetch_related("images", "amenities")

    # ------------------------------------------------------------------
    # Apply query-param filters via the FilterSet
    # ------------------------------------------------------------------
    filter_set = PropertyFilter(request.GET, queryset=qs)
    qs = filter_set.qs

    # Keep the map readable: presentation/demo mode pins the curated homes,
    # while every genuine owner-entered listing remains eligible.
    map_source = qs.filter(Q(is_demo=False) | ~Q(address_text=""))
    map_rows = map_source.exclude(lat__isnull=True).exclude(lng__isnull=True).values(
        "lat", "lng", "title", "slug", "pk", "price", "listing_type", "is_short_stay", "location__name",
        "location__parent__name", "location__parent__parent__name",
    )[:18]
    map_listings = []
    for item in map_rows:
        location_bits = [
            item.get("location__parent__parent__name"),
            item.get("location__parent__name"),
            item.get("location__name"),
        ]
        map_listings.append({
            "id": item["pk"],  # L1: pairs each pin with its result row
            "lat": float(item["lat"]), "lng": float(item["lng"]),
            "title": item["title"],
            "url": f"/listing/{item['slug']}-{item['pk']}/",
            "price": f"KES {item['price']:,.0f}",
            "price_short": (
                f"KSh {item['price'] / 1_000_000:.1f}M" if item["price"] >= 1_000_000
                else f"KSh {item['price'] / 1_000:.0f}K"
            ),
            "market": "bnb" if item["is_short_stay"] else item["listing_type"],
            "location": " > ".join(bit for bit in location_bits if bit),
        })

    # ------------------------------------------------------------------
    # Paginate (24 per page)
    # ------------------------------------------------------------------
    paginator = Paginator(qs, PAGE_SIZE)
    page_num = request.GET.get("page", "1")
    try:
        page = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page = paginator.page(1)

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------
    h1 = _build_h1(listing_type, ptype, location)
    if listing_type is None and not location:
        h1 = {
            "sale": "Mombasa homes for sale",
            "rent": "Mombasa homes for long-term rent",
            "bnb": "Mombasa short stays and BnB",
        }.get(market, "Homes across Mombasa")
    breadcrumbs = _build_breadcrumbs(listing_type, ptype, location)
    canonical_url = _build_canonical_url(listing_type, ptype, location)
    related_searches = _build_related_searches(listing_type, ptype, location)

    # Count of total results (before pagination)
    total_count = paginator.count

    # Whether we have any active filters (for the "Clear filters" link)
    active_filters = bool(request.GET.dict())

    context = {
        "body_class": "page-search",
        "page_title": h1,
        "meta_description": f"{h1}. Browse checked listings on Gabriel Homes — real estate with a human point of view.",
        "h1": h1,
        "breadcrumbs": breadcrumbs,
        "canonical_url": canonical_url,
        "listing_type": listing_type,
        "property_type": ptype,
        "location": location,
        "page_obj": page,
        "total_count": total_count,
        "page_size": PAGE_SIZE,
        "filter_form": filter_set.form,
        "filterset": filter_set,
        "sort_options": SORT_OPTIONS,
        "current_sort": request.GET.get("sort", "newest"),
        "active_filters": active_filters,
        "current_market": market,
        "map_listings": map_listings,
        "related_searches": related_searches,
        "is_htmx": request.headers.get("HX-Request") == "true",
        # For the filter sidebar — pass all property types and top locations
        "all_property_types": PropertyType.objects.order_by("position", "name"),
        "all_counties": Location.objects.filter(level=Location.Level.COUNTY).order_by("name"),
    }

    # If HTMX request, return just the results partial
    if context["is_htmx"]:
        return render(request, "listings/_results_grid.html", context)

    return render(request, "listings/search.html", context)


def location_autocomplete(request):
    """JSON endpoint for the hero search bar's location input.

    Returns up to 8 locations whose name starts with (or contains)
    the `q` query param. Each result includes the slug, name, full
    path, and level — enough for the JS to build a URL.

    Usage: /search/locations/?q=mom
    Returns: [{"slug": "mombasa", "name": "Mombasa", "full_path": "Mombasa", "level": "county"}, ...]
    """
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    # Match by name (case-insensitive icontains) — shallowest first.
    qs = Location.objects.filter(name__icontains=q).order_by("level", "name")[:8]
    results = [
        {
            "slug": loc.slug,
            "name": loc.name,
            "full_path": loc.full_path(),
            "level": loc.level,
        }
        for loc in qs
    ]
    return JsonResponse({"results": results})


# ---------------------------------------------------------------------------
# Listing detail
# ---------------------------------------------------------------------------
SIMILAR_LISTINGS_COUNT = 3

# Approximate nearby places for the fictional Mombasa showcase listings.
# Replace these presentation values with verified places/times before launch.
_DEMO_NEARBY_AMENITIES = {
    "Bamburi Mwisho": [
        {"symbol": "▦", "category": "Mall", "name": "City Mall Nyali", "distance": "Sample · about 12 min by car"},
        {"symbol": "≈", "category": "Resort", "name": "Sarova Whitesands Beach Resort", "distance": "Sample · about 8 min by car"},
        {"symbol": "▤", "category": "Conference venue", "name": "PrideInn Paradise Beach Resort", "distance": "Sample · about 12 min by car"},
        {"symbol": "◉", "category": "Nature attraction", "name": "Haller Park", "distance": "Sample · about 7 min by car"},
    ],
    "Nyali Centre": [
        {"symbol": "▦", "category": "Mall", "name": "City Mall Nyali", "distance": "Sample · about 5 min by car"},
        {"symbol": "≈", "category": "Resort", "name": "Voyager Beach Resort", "distance": "Sample · about 6 min by car"},
        {"symbol": "▤", "category": "Conference & events", "name": "EnglishPoint Marina", "distance": "Sample · about 9 min by car"},
        {"symbol": "◎", "category": "Leisure", "name": "Wild Waters", "distance": "Sample · about 8 min by car"},
    ],
    "Mkomani": [
        {"symbol": "▦", "category": "Mall", "name": "City Mall Nyali", "distance": "Sample · about 6 min by car"},
        {"symbol": "≈", "category": "Resort", "name": "Voyager Beach Resort", "distance": "Sample · about 7 min by car"},
        {"symbol": "▤", "category": "Conference & events", "name": "EnglishPoint Marina", "distance": "Sample · about 8 min by car"},
        {"symbol": "◎", "category": "Leisure", "name": "Wild Waters", "distance": "Sample · about 9 min by car"},
    ],
    "Shanzu": [
        {"symbol": "≈", "category": "Beach", "name": "Shanzu Beach", "distance": "About 6 min drive"},
        {"symbol": "▦", "category": "Shopping", "name": "Mtwapa shopping area", "distance": "About 12 min drive"},
        {"symbol": "＋", "category": "Healthcare", "name": "Mtwapa health services", "distance": "About 12 min drive"},
        {"symbol": "◉", "category": "Leisure", "name": "North Coast resorts", "distance": "Close by"},
    ],
    "Mtwapa Town": [
        {"symbol": "▦", "category": "Shopping", "name": "Mtwapa Mall", "distance": "About 4 min drive"},
        {"symbol": "≈", "category": "Leisure", "name": "Mtwapa Creek", "distance": "About 8 min drive"},
        {"symbol": "↗", "category": "Getting around", "name": "Mtwapa Bridge", "distance": "About 5 min drive"},
        {"symbol": "＋", "category": "Everyday", "name": "Mtwapa town centre", "distance": "Close by"},
    ],
    "Likoni Ferry": [
        {"symbol": "↗", "category": "Getting around", "name": "Likoni Ferry", "distance": "About 5 min drive"},
        {"symbol": "▦", "category": "Shopping", "name": "Likoni town centre", "distance": "About 5 min drive"},
        {"symbol": "≈", "category": "Beach", "name": "Shelly Beach", "distance": "About 15 min drive"},
        {"symbol": "＋", "category": "Healthcare", "name": "Likoni health services", "distance": "Nearby"},
    ],
    "CBD": [
        {"symbol": "▦", "category": "Shopping", "name": "Mombasa CBD", "distance": "Close by"},
        {"symbol": "＋", "category": "Healthcare", "name": "Coast General Hospital", "distance": "About 8 min drive"},
        {"symbol": "↗", "category": "Getting around", "name": "Likoni Ferry", "distance": "About 8 min drive"},
        {"symbol": "◉", "category": "Culture", "name": "Fort Jesus", "distance": "About 10 min drive"},
    ],
    "Tudor": [
        {"symbol": "＋", "category": "Healthcare", "name": "Coast General Hospital", "distance": "About 8 min drive"},
        {"symbol": "▦", "category": "Shopping", "name": "Mombasa CBD", "distance": "About 8 min drive"},
        {"symbol": "↗", "category": "Getting around", "name": "Tudor Creek routes", "distance": "Close by"},
        {"symbol": "◎", "category": "Education", "name": "Mombasa town schools", "distance": "Nearby"},
    ],
}


def listing_detail(request, slug: str, pk: int):
    """Property detail page — per WORK.md §8 (Listing detail).

    URL: /listing/<slug>-<pk>/
    - Only published listings are visible (404 otherwise).
    - View counter is debounced per session (one count per session per
      listing — a session flag prevents reloads from inflating the count).
    - Sticky brand contact card (Call / WhatsApp / Email, brand row) and enquiry form.
    - Save and Share buttons.
    - Similar listings: same property_type + same county (via location
      ancestors), ±30% price, exclude self.
    - JSON-LD structured data for SEO.
    - Leaflet map with approximate pin (respects address_text privacy).
    """
    from django.shortcuts import get_object_or_404, render as _render

    property = get_object_or_404(
        Property.objects.published().select_related(
            "property_type",
            "location__parent__parent",
            "agent__user",
        ).prefetch_related("images", "amenities"),
        slug=slug, pk=pk,
    )

    # ------------------------------------------------------------------
    # View counter — debounced per session (one count per session per listing)
    # ------------------------------------------------------------------
    session_key = f"viewed_property_{property.pk}"
    if not request.session.get(session_key):
        property.increment_views()
        request.session[session_key] = True
        # Mark session as modified so it's saved.
        request.session.modified = True

    # ------------------------------------------------------------------
    # Similar listings — same type + same county, ±30% price, exclude self
    # ------------------------------------------------------------------
    from decimal import Decimal
    price_min = property.price * Decimal("0.7")
    price_max = property.price * Decimal("1.3")
    # Get the county ancestor of this listing's location.
    county = None
    if property.location.parent:
        county = property.location.parent
        if county.parent:
            county = county.parent
    else:
        county = property.location  # property is at county level (shouldn't happen but safe)

    similar_qs = Property.objects.published().filter(
        property_type=property.property_type,
        listing_type=property.listing_type,
        price__gte=price_min,
        price__lte=price_max,
    ).exclude(pk=property.pk)

    # Filter to the same county via descendants.
    if county:
        descendant_pks = set(county.get_descendants(include_self=True).values_list("pk", flat=True))
        similar_qs = similar_qs.filter(location__in=descendant_pks)

    similar_listings = list(
        similar_qs.select_related(
            "property_type", "location__parent__parent", "agent__user",
        ).prefetch_related("images")[:SIMILAR_LISTINGS_COUNT]
    )

    # ------------------------------------------------------------------
    # Breadcrumbs
    # ------------------------------------------------------------------
    crumbs = [{"name": "Home", "url": "/"}]
    if property.listing_type == "sale":
        type_url = f"/{property.property_type.slug_plural}-for-sale/"
        type_label = f"{property.property_type.name} for Sale"
    else:
        type_url = f"/{property.property_type.slug_plural}-for-rent/"
        type_label = f"{property.property_type.name} for Rent"
    crumbs.append({"name": type_label, "url": type_url})
    if property.location.parent:
        # location is a neighbourhood; link to the area
        loc_url = f"/{property.property_type.slug_plural}-{'for-sale' if property.listing_type == 'sale' else 'for-rent'}/{property.location.parent.slug}/"
        crumbs.append({"name": property.location.parent.name, "url": loc_url})
    crumbs.append({"name": property.title, "url": ""})

    # ------------------------------------------------------------------
    # JSON-LD structured data
    # ------------------------------------------------------------------
    from django.conf import settings
    from django.urls import reverse

    json_ld = {
        "@context": "https://schema.org",
        "@type": "Residence" if property.property_type.is_residential else "Place",
        "name": property.title,
        "description": property.description[:500] if property.description else "",
        "url": f"{settings.SITE_DOMAIN}{property.get_absolute_url()}",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": property.location.name,
            "addressRegion": county.name if county else "",
            "addressCountry": "KE",
        },
        "offers": {
            "@type": "Offer",
            "price": str(property.price),
            "priceCurrency": "KES",
        },
    }
    if property.lat and property.lng:
        json_ld["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": str(property.lat),
            "longitude": str(property.lng),
        }
    if property.bedrooms:
        json_ld["numberOfRooms"] = property.bedrooms
    if property.bathrooms:
        json_ld["amenityFeature"] = [{
            "@type": "LocationFeatureSpecification",
            "name": "Bathrooms",
            "value": property.bathrooms,
        }]

    # ------------------------------------------------------------------
    # Enquiry form (for the sticky agent card)
    # ------------------------------------------------------------------
    from apps.inquiries.forms import InquiryForm
    enquiry_form = InquiryForm()

    # ------------------------------------------------------------------
    # WhatsApp link with prefilled message (single-owner mode: the brand
    # row, not the retired agency concept — P1-2)
    # ------------------------------------------------------------------
    from apps.core.models import BrandSettings
    wa_number = BrandSettings.load().whatsapp_digits
    wa_message = (
        f"Hello Gabriel Homes, I'm interested in '{property.title}' "
        f"({property.price} KES) listed on Gabriel Homes. "
        f"{settings.SITE_DOMAIN}{property.get_absolute_url()}"
    )
    from urllib.parse import quote
    wa_url = f"https://wa.me/{wa_number}?text={quote(wa_message)}" if wa_number else ""

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------
    # NOTE: body_class here is informational only — the template's
    # {% block body_class %} is the real switch for page-level CSS
    # (see detail.html; has-contact-bar gates the mobile sticky bar).
    context = {
        "body_class": "page-detail",
        "page_title": f"{property.title} — {property.get_listing_type_display()} in {property.location.name}",
        "meta_description": (
            f"{property.title} — {property.get_listing_type_display().lower()} in "
            f"{property.location.full_path()}. "
            f"{property.bedrooms} bed, {property.bathrooms} bath. "
            f"Checked by Gabriel Homes."
        ),
        "property": property,
        "nearby_amenities": _DEMO_NEARBY_AMENITIES.get(property.location.name, []) if property.is_demo else [],
        "similar_listings": similar_listings,
        "breadcrumbs": crumbs,
        "json_ld": json_ld,
        "enquiry_form": enquiry_form,
        "whatsapp_url": wa_url,
        "canonical_url": property.get_absolute_url(),
        "county": county,
    }

    return _render(request, "listings/detail.html", context)

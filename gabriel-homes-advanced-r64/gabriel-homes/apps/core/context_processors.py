"""Core context processors — available on every template."""
from django.conf import settings


def _brand(request):
    """The brand singleton, loaded at most once per request.

    Both site_meta and brand_contact need the row; caching it on the
    request halves the singleton reads on every page (r73).
    """
    if not hasattr(request, "_brand_cache"):
        from apps.core.models import BrandSettings

        request._brand_cache = BrandSettings.load()
    return request._brand_cache


def site_meta(request):
    """Expose site-wide metadata to all templates.

    r73 (BACKEND-PLAN 1E): the owner's SEO description (BrandSettings.
    meta_description, editable in /manage/seo/) wins over the coded
    default when filled. Reads the SAME cached singleton row as
    brand_contact below — one SELECT per request, not two (the search
    page's query-count pin would notice).
    """
    brand = _brand(request)
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
        "DEFAULT_META_DESCRIPTION": brand.meta_description or settings.DEFAULT_META_DESCRIPTION,
        "csp_nonce": getattr(request, "csp_nonce", ""),
    }


def brand_contact(request):
    """Expose the brand contact row (singleton) to all templates.

    Single-owner mode: public contact buttons read the owner's own brand
    details — never the retired agency concept. Fields default to empty,
    and templates hide buttons whose value is missing (honest blank by
    design). r73: the row now also carries logo/favicon/socials/address/
    hours (the brand assets) and the SEO knobs.
    """
    return {"brand": _brand(request)}

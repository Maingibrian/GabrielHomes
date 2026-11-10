"""Core context processors — available on every template."""
from django.conf import settings


def site_meta(request):
    """Expose site-wide metadata to all templates."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
        "DEFAULT_META_DESCRIPTION": settings.DEFAULT_META_DESCRIPTION,
    }


def brand_contact(request):
    """Expose the brand contact row (singleton) to all templates.

    Single-owner mode: public contact buttons read the owner's own brand
    details — never the retired agency concept. Fields default to empty,
    and templates hide buttons whose value is missing (honest blank by
    design). P3-8 makes the row owner-editable in /manage/.
    """
    from apps.core.models import BrandSettings

    return {"brand": BrandSettings.load()}


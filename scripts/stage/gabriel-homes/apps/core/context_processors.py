"""Core context processors — available on every template."""
from django.conf import settings


def site_meta(request):
    """Expose site-wide metadata to all templates."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
        "DEFAULT_META_DESCRIPTION": settings.DEFAULT_META_DESCRIPTION,
    }

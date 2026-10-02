"""Root URL configuration for Gabriel Homes."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.urls import include, path
from django.views.decorators.http import require_GET

from apps.core import views as core_views
from apps.core.sitemaps import FlatSitemap, StaticSitemap
from apps.listings.sitemaps import ListingSitemap, LocationTypeSitemap

SITEMAPS = {
    "static": StaticSitemap,
    "flat": FlatSitemap,
    "listings": ListingSitemap,
    "location-types": LocationTypeSitemap,
}


@require_GET
def robots_txt(request):
    """robots.txt — allow all crawlers, point to sitemap, disallow private paths.

    Per WORK.md §7: /robots.txt is part of the URL map.
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        # Private areas — never index
        "Disallow: /admin/",
        "Disallow: /account/",
        "Disallow: /dashboard/",
        "Disallow: /search/locations/",
        "Disallow: /styleguide/",
        # Sitemap
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    from django.http import HttpResponse
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.home, name="home"),
    path("styleguide/", core_views.styleguide, name="styleguide"),
    # SEO
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_view, {"sitemaps": SITEMAPS}, name="sitemap"),
    # Search results + listing detail + autocomplete (per WORK.md §7)
    path("", include("apps.listings.urls")),
    # Enquiry form submission (per WORK.md §11 Phase 4)
    path("", include("apps.inquiries.urls")),
    # Saved properties + saved list page (per WORK.md §11 Phase 5)
    path("", include("apps.accounts.urls")),
    # Agent dashboard (per WORK.md §11 Phase 5)
    path("", include("apps.agents.urls")),
    # allauth — login / signup / password reset live under /account/
    path("account/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

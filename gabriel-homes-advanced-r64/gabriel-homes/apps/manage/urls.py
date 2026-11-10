"""URL patterns for the owner portal — everything lives under /manage/.

app_name = "manage" so portal links reverse as manage:home, manage:listings, …
"""
from django.urls import path

from apps.manage import views

app_name = "manage"

urlpatterns = [
    path("", views.PortalHomeView.as_view(), name="home"),
    path("site-content/", views.SiteContentView.as_view(), name="site_content"),
    path(
        "checklist/<slug:key>/toggle/",
        views.ChecklistToggleView.as_view(),
        name="checklist_toggle",
    ),
]

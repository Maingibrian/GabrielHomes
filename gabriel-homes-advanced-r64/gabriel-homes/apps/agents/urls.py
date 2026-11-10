"""URL patterns for the agents app — retired public pages + agent dashboard.

Public (RETIRED, loop protocol §4 / P1-1, run 5): the site is single-owner,
so /agents/ and /agents/<slug>/ now send PERMANENT redirects to /about/.
The route names are kept so dashboard-side reversals keep resolving; the
old view classes stay in views.py untouched (unrouted, logged in BRIEF).
Dashboard (per WORK.md §11 Phase 5):
    /dashboard/...           agent-only views (owner uses these until /manage/)
"""
from django.urls import path
from django.views.generic import RedirectView

from . import owner_views, views

app_name = "agents"

urlpatterns = [
    # Retired public agent pages — permanent redirect to /about/ (P1-1).
    # Names kept: owner dashboard + directory template still reverse() them.
    path(
        "agents/",
        RedirectView.as_view(url="/about/", permanent=True),
        name="agent_directory",
    ),
    path(
        "agents/<slug:slug>/",
        RedirectView.as_view(url="/about/", permanent=True),
        name="agent_detail",
    ),

    # Dashboard index — listing table (role-aware: owner gets the overview)
    path("dashboard/", views.DashboardHome.as_view(), name="dashboard_home"),
    # Create / edit listings
    path("dashboard/listings/new/", views.DashboardListingCreate.as_view(), name="dashboard_listing_create"),
    path("dashboard/listings/<int:pk>/edit/", views.DashboardListingEdit.as_view(), name="dashboard_listing_edit"),
    path("dashboard/listings/<int:pk>/images/", views.DashboardListingImages.as_view(), name="dashboard_listing_images"),
    # Inquiries inbox (role-aware: owner sees all agencies')
    path("dashboard/inquiries/", views.DashboardInquiries.as_view(), name="dashboard_inquiries"),
    # Owner-only (r11): cross-agency management, demo switch, import hook
    path("dashboard/all-listings/", owner_views.OwnerListingsView.as_view(), name="owner_listings"),
    path("dashboard/agencies/", owner_views.OwnerAgenciesView.as_view(), name="owner_agencies"),
    path("dashboard/import/", owner_views.OwnerImportView.as_view(), name="owner_import"),
    path("dashboard/import/sample.csv", owner_views.OwnerImportSampleView.as_view(), name="owner_import_sample"),
    path("dashboard/demo-toggle/", owner_views.OwnerDemoToggleView.as_view(), name="owner_demo_toggle"),
]

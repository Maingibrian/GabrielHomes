"""URL patterns for the agents app — public agent pages + agent dashboard.

Public (per WORK.md §7):
    /agents/                 agent directory with search
    /agents/<agency-slug>/   agency profile + their listings
Dashboard (per WORK.md §11 Phase 5):
    /dashboard/...           agent-only views
"""
from django.urls import path

from . import owner_views, views

app_name = "agents"

urlpatterns = [
    # Public agent directory + profile (per §7)
    path("agents/", views.AgentDirectoryView.as_view(), name="agent_directory"),
    path("agents/<slug:slug>/", views.AgentProfileView.as_view(), name="agent_detail"),

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

"""URL patterns for the agents app — public agent pages + agent dashboard.

Public (per WORK.md §7):
    /agents/                 agent directory with search
    /agents/<agency-slug>/   agency profile + their listings
Dashboard (per WORK.md §11 Phase 5):
    /dashboard/...           agent-only views
"""
from django.urls import path

from . import views

app_name = "agents"

urlpatterns = [
    # Public agent directory + profile (per §7)
    path("agents/", views.AgentDirectoryView.as_view(), name="agent_directory"),
    path("agents/<slug:slug>/", views.AgentProfileView.as_view(), name="agent_detail"),

    # Dashboard index — listing table
    path("dashboard/", views.DashboardHome.as_view(), name="dashboard_home"),
    # Create / edit listings
    path("dashboard/listings/new/", views.DashboardListingCreate.as_view(), name="dashboard_listing_create"),
    path("dashboard/listings/<int:pk>/edit/", views.DashboardListingEdit.as_view(), name="dashboard_listing_edit"),
    path("dashboard/listings/<int:pk>/images/", views.DashboardListingImages.as_view(), name="dashboard_listing_images"),
    # Inquiries inbox
    path("dashboard/inquiries/", views.DashboardInquiries.as_view(), name="dashboard_inquiries"),
]

"""URL patterns for the agents app — agent dashboard."""
from django.urls import path

from . import views

app_name = "agents"

urlpatterns = [
    # Dashboard index — listing table
    path("dashboard/", views.DashboardHome.as_view(), name="dashboard_home"),
    # Create / edit listings
    path("dashboard/listings/new/", views.DashboardListingCreate.as_view(), name="dashboard_listing_create"),
    path("dashboard/listings/<int:pk>/edit/", views.DashboardListingEdit.as_view(), name="dashboard_listing_edit"),
    path("dashboard/listings/<int:pk>/images/", views.DashboardListingImages.as_view(), name="dashboard_listing_images"),
    # Inquiries inbox
    path("dashboard/inquiries/", views.DashboardInquiries.as_view(), name="dashboard_inquiries"),
]

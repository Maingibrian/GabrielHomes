"""URL patterns for the owner portal — everything lives under /manage/.

app_name = "manage" so portal links reverse as manage:home,
manage:enquiries, …

r73 (BACKEND-PLAN Phase 1): five sections —
    /manage/                     Home (graphs + checklist)
    /manage/enquiries/…          Enquiries workflow (tabs, detail, notes, CSV, spam)
    /manage/listings/            Listings (read-first; wizard tools land Phase 2)
    /manage/site-content/        Site content (copy + brand assets)
    /manage/seo/                 SEO & tracking
"""
from django.urls import path

from apps.manage import views

app_name = "manage"

urlpatterns = [
    path("", views.PortalHomeView.as_view(), name="home"),
    path("site-content/", views.SiteContentView.as_view(), name="site_content"),
    # r75 (BACKEND-PLAN Phase 3) — Site content's tabs
    path("site-content/categories/", views.CategoriesView.as_view(), name="categories"),
    path("site-content/media/", views.MediaLibraryView.as_view(), name="media"),
    path("site-content/media/<int:pk>/action/", views.MediaImageActionView.as_view(), name="media_action"),
    path("site-content/testimonials/", views.TestimonialsView.as_view(), name="testimonials"),
    path(
        "site-content/testimonials/<int:pk>/action/",
        views.TestimonialActionView.as_view(),
        name="testimonial_action",
    ),
    path("site-content/newsletter/", views.NewsletterComposeView.as_view(), name="newsletter"),
    path("seo/", views.SeoSettingsView.as_view(), name="seo"),
    path(
        "checklist/<slug:key>/toggle/",
        views.ChecklistToggleView.as_view(),
        name="checklist_toggle",
    ),
    # Enquiries (r73)
    path("enquiries/", views.EnquiryListView.as_view(), name="enquiries"),
    path("enquiries/export.csv", views.EnquiryExportView.as_view(), name="enquiries_export"),
    path("enquiries/<int:pk>/", views.EnquiryDetailView.as_view(), name="enquiry_detail"),
    path("enquiries/<int:pk>/status/", views.EnquiryStatusView.as_view(), name="enquiry_status"),
    path("enquiries/<int:pk>/note/", views.EnquiryNoteView.as_view(), name="enquiry_note"),
    path("enquiries/<int:pk>/delete/", views.EnquiryDeleteView.as_view(), name="enquiry_delete"),
    # Listings (r73 read-first + r74 Phase 2 tools)
    path("listings/", views.PortalListingsView.as_view(), name="listings"),
    path("listings/new/", views.ListingWizardView.as_view(), name="listing_wizard"),
    path("listings/bulk/", views.ListingBulkView.as_view(), name="listing_bulk"),
    path("listings/<int:pk>/tools/", views.ListingRowToolsView.as_view(), name="listing_tools"),
    path("listings/<int:pk>/pin/", views.ListingPinView.as_view(), name="listing_pin"),
]

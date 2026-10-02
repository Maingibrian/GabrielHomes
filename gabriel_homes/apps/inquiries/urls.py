"""URL patterns for the inquiries app — enquiry form submission."""
from django.urls import path

from . import views

urlpatterns = [
    # Enquiry form submission (HTMX-friendly POST)
    path(
        "listing/<slug:slug>-<int:pk>/enquire/",
        views.submit_enquiry,
        name="submit_enquiry",
    ),
]

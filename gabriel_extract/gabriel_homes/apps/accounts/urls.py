"""URL patterns for the accounts app — saved properties + rate-limited auth.

Per WORK.md §11 Phase 7: rate limiting on auth endpoints.
We wrap allauth's login + signup views with a 5-per-minute IP-based limiter
by overriding the specific URL patterns before including the rest of allauth.
"""
from django.urls import include, path
from allauth.account import views as allauth_views

from . import views
from .rate_limit import auth_rate_limit


urlpatterns = [
    # Save/unsave toggle (HTMX-friendly POST)
    path("account/save/<int:pk>/", views.toggle_save, name="toggle_save"),
    # Saved properties list page
    path("account/saved/", views.saved_list, name="saved_list"),

    # Rate-limited auth views (override allauth's defaults)
    path("account/login/", auth_rate_limit(max_requests=5, window=60)(allauth_views.login),
         name="account_login"),
    path("account/signup/", auth_rate_limit(max_requests=3, window=60)(allauth_views.signup),
         name="account_signup"),
    path("account/password/reset/", auth_rate_limit(max_requests=3, window=60)(allauth_views.password_reset),
         name="account_reset_password"),

    # allauth — the rest (logout, password change, email verification, etc.)
    path("account/", include("allauth.urls")),
]

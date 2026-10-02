"""Views for the accounts app — saved properties + saved list page.

The save/unsave toggle is HTMX-friendly: returns a small partial that
swaps the heart icon's state. Falls back to a redirect for non-HTMX.
"""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.listings.models import Property

from .models import SavedProperty


@login_required
@require_POST
def toggle_save(request, pk: int):
    """Toggle the saved-state of a property for the logged-in user.

    HTMX: returns _save_button.html partial.
    Non-HTMX: redirects back to the property detail page.
    """
    property = get_object_or_404(Property.objects.published(), pk=pk)
    saved, created = SavedProperty.objects.get_or_create(
        user=request.user, property=property,
    )
    if not created:
        saved.delete()
        is_saved = False
    else:
        is_saved = True

    if request.headers.get("HX-Request") == "true":
        return render(request, "accounts/_save_button.html", {
            "property": property,
            "is_saved": is_saved,
        })
    return redirect(property.get_absolute_url())


@login_required
def saved_list(request):
    """The user's saved-properties page — /account/saved/."""
    saved = (
        SavedProperty.objects
        .filter(user=request.user)
        .select_related("property__property_type", "property__location__parent__parent", "property__agent__user")
        .prefetch_related("property__images")
        .order_by("-created_at")
    )
    return render(request, "accounts/saved_list.html", {
        "body_class": "page-saved",
        "saved_properties": saved,
    })

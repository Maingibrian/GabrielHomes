"""Views for the agents app — agent dashboard.

Per WORK.md §11 Phase 5:
- Agent role and dashboard: create/edit listing, multi-image upload,
  status changes, inquiries inbox.
- Permissions: agents can only edit their own listings (test this).
- Done when: an agent can publish a listing end to end and it appears
  on the public site.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import inlineformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.accounts.models import User
from apps.inquiries.models import Inquiry
from apps.listings.models import Property, PropertyImage, PropertyType
from apps.locations.models import Location

from .models import AgencyProfile


# ---------------------------------------------------------------------------
# Mixin: agent-only access
# ---------------------------------------------------------------------------
class AgentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only allow users with is_agent=True AND an AgencyProfile.

    Redirects unauthenticated users to login; 403s authenticated non-agents.
    """

    def test_func(self) -> bool:
        user = self.request.user
        return bool(
            user.is_authenticated
            and user.is_agent
            and hasattr(user, "agency_profile")
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            # Logged in but not an agent — 403
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You need an agent account to access the dashboard.")
        return super().handle_no_permission()


# ---------------------------------------------------------------------------
# Dashboard index — listing table
# ---------------------------------------------------------------------------
class DashboardHome(AgentRequiredMixin, TemplateView):
    """Dashboard index — the agent's listings table."""
    template_name = "agents/dashboard_home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        agency = self.request.user.agency_profile
        listings = (
            Property.objects.filter(agent=agency)
            .select_related("property_type", "location__parent")
            .order_by("-updated_at")
        )
        ctx["listings"] = listings
        ctx["total_listings"] = listings.count()
        ctx["published_count"] = listings.filter(status=Property.Status.PUBLISHED).count()
        ctx["draft_count"] = listings.filter(status=Property.Status.DRAFT).count()
        ctx["inquiries_count"] = Inquiry.objects.filter(property_ref__agent=agency).count()
        return ctx


# ---------------------------------------------------------------------------
# Listing create / edit
# ---------------------------------------------------------------------------
class PropertyFormMixin:
    """Shared form configuration for create + edit."""
    fields = [
        "title", "listing_type", "property_type", "location",
        "address_text", "lat", "lng",
        "price", "price_period", "price_negotiable",
        "bedrooms", "bathrooms", "size_sqm", "land_size_acres",
        "furnishing", "parking_spaces", "year_built", "service_charge",
        "amenities", "status", "is_featured", "description",
    ]
    template_name = "agents/dashboard_listing_form.html"


class DashboardListingCreate(AgentRequiredMixin, PropertyFormMixin, CreateView):
    """Create a new listing owned by the current agent."""
    model = Property
    success_url = reverse_lazy("agents:dashboard_home")

    def form_valid(self, form):
        # Stamp the agent + auto-slug + published_at (model.save handles the rest).
        form.instance.agent = self.request.user.agency_profile
        response = super().form_valid(form)
        messages.success(self.request, f"Listing '{self.object.title}' created.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_create"] = True
        ctx["property_types"] = PropertyType.objects.order_by("position", "name")
        # Locations: only neighbourhood-level (limit_choices_to is on the model,
        # but we pass the list for the <select> in the template)
        ctx["locations"] = Location.objects.filter(level=Location.Level.NEIGHBOURHOOD).order_by("parent__parent__name", "parent__name", "name")
        return ctx


class DashboardListingEdit(AgentRequiredMixin, PropertyFormMixin, UpdateView):
    """Edit an existing listing — only if owned by the current agent."""
    model = Property
    success_url = reverse_lazy("agents:dashboard_home")

    def get_queryset(self):
        """Agents can only edit their own listings."""
        return Property.objects.filter(agent=self.request.user.agency_profile)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Listing '{self.object.title}' updated.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_create"] = False
        ctx["property_types"] = PropertyType.objects.order_by("position", "name")
        ctx["locations"] = Location.objects.filter(level=Location.Level.NEIGHBOURHOOD).order_by("parent__parent__name", "parent__name", "name")
        return ctx


# ---------------------------------------------------------------------------
# Multi-image upload
# ---------------------------------------------------------------------------
PropertyImageFormSet = inlineformset_factory(
    Property, PropertyImage,
    fields=["image", "caption", "position", "is_cover"],
    extra=3,
    can_delete=True,
    # Make position and image optional in the form so empty extra forms validate.
    # The model's `position` has default=0; image is required only when the
    # form has data (i.e. when the user is actually uploading).
)


class DashboardListingImages(AgentRequiredMixin, UpdateView):
    """Multi-image upload + reorder + cover selection."""
    model = Property
    template_name = "agents/dashboard_images.html"
    fields = []  # no Property fields — just the formset
    success_url = reverse_lazy("agents:dashboard_home")

    def get_queryset(self):
        return Property.objects.filter(agent=self.request.user.agency_profile)

    def get_formset(self, **kwargs):
        """Build the formset with field overrides for empty-form tolerance."""
        fs = PropertyImageFormSet(**kwargs)
        # Make image + position not required so empty extra forms validate.
        for form in fs.forms:
            form.fields["image"].required = False
            form.fields["position"].required = False
        return fs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["formset"] = self.get_formset(
                data=self.request.POST, files=self.request.FILES, instance=self.object
            )
        else:
            ctx["formset"] = self.get_formset(instance=self.object)
        return ctx

    def form_valid(self, form):
        formset = self.get_context_data()["formset"]
        if formset.is_valid():
            # Filter out forms with no image (empty extra forms).
            # The formset.save() handles this via can_delete, but we need
            # to skip forms that have no image file.
            instances = formset.save(commit=False)
            for instance in instances:
                # Only save if there's an actual image file.
                if instance.image:
                    instance.property = self.object
                    instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(self.request, "Images updated.")
            return redirect(self.success_url)
        return self.form_invalid(form)


# ---------------------------------------------------------------------------
# Inquiries inbox
# ---------------------------------------------------------------------------
class DashboardInquiries(AgentRequiredMixin, ListView):
    """Inquiries for the agent's listings."""
    template_name = "agents/dashboard_inquiries.html"
    context_object_name = "inquiries"
    paginate_by = 20

    def get_queryset(self):
        agency = self.request.user.agency_profile
        return (
            Inquiry.objects.filter(property_ref__agent=agency)
            .select_related("property_ref", "property_ref__property_type")
            .order_by("-created_at")
        )

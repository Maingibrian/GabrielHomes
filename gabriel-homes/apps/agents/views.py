"""Views for the agents app — agent dashboard (public pages retired).

Per loop protocol §4 (single-owner mode) + P1-1 (run 5), the public agent
pages are retired: /agents/ and /agents/<slug>/ are permanent redirects to
/about/ (see urls.py). AgentDirectoryView and AgentProfileView below are
kept, unrouted, for reference and possible reuse by the /manage/ portal —
they are NOT reachable from any public URL. Per WORK.md §11 Phase 5
(dashboard):
- Agent role and dashboard: create/edit listing, multi-image upload,
  status changes, inquiries inbox.
- Permissions: agents can only edit their own listings (test this).
- The owner (superuser) reuses these views via the role-aware dashboard.
"""
from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.models import User
from apps.inquiries.models import Inquiry
from apps.listings.models import Property, PropertyImage, PropertyType
from apps.locations.models import Location

from .models import AgencyProfile


# ---------------------------------------------------------------------------
# Public agent pages — /agents/ and /agents/<slug>/ (WORK.md §7, §8)
# ---------------------------------------------------------------------------
class AgentDirectoryView(ListView):
    """Public agent directory — all agencies with a free-text search.

    Search matches agency name, bio, and office location name (§8:
    "directory with search").
    """
    template_name = "agents/agent_directory.html"
    context_object_name = "agencies"
    paginate_by = 12

    def get_queryset(self):
        qs = AgencyProfile.objects.public().select_related("user", "office_location")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(bio__icontains=q)
                | Q(office_location__name__icontains=q)
            )
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-agents"
        ctx["page_title"] = "Agent directory — Gabriel Homes"
        ctx["meta_description"] = (
            "Browse the Kenyan property agencies on Gabriel Homes — "
            "search by name, speciality, or location and connect directly."
        )
        ctx["canonical_url"] = "/agents/"
        ctx["q"] = self.request.GET.get("q", "")
        # Published-listing counts per agency for the cards.
        from django.db.models import Count
        from apps.listings.models import Property
        counts = {
            row["agent"]: row["c"]
            for row in (
                Property.objects.published()
                .values("agent")
                .annotate(c=Count("pk"))
            )
        }
        for agency in ctx["agencies"]:
            agency.active_listings = counts.get(agency.pk, 0)
        return ctx


class AgentProfileView(DetailView):
    """Public agency profile — bio, contact buttons, active listings."""
    model = AgencyProfile
    template_name = "agents/agent_detail.html"
    context_object_name = "agency"
    slug_field = "slug"

    def get_queryset(self):
        return AgencyProfile.objects.public().select_related("user", "office_location")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        agency = self.object
        active = (
            Property.objects.published()
            .filter(agent=agency)
            .select_related(
                "property_type", "location__parent__parent", "agent__user",
            )
            .prefetch_related("images")
            .order_by("-is_featured", "-published_at")
        )
        ctx["body_class"] = "page-agent-profile"
        ctx["page_title"] = f"{agency.name} — Gabriel Homes"
        ctx["meta_description"] = (
            f"{agency.name} on Gabriel Homes — see their active "
            f"listings and get in touch directly."
        )
        ctx["canonical_url"] = f"/agents/{agency.slug}/"
        ctx["active_listings"] = active[:12]
        ctx["active_count"] = active.count()
        # WhatsApp click-to-chat for the profile CTA.
        wa_number = agency.display_whatsapp
        from urllib.parse import quote
        ctx["whatsapp_url"] = (
            f"https://wa.me/{wa_number}?text={quote('Hello ' + agency.name + ', I found you on Gabriel Homes.')}"
            if wa_number else ""
        )
        return ctx


# ---------------------------------------------------------------------------
# Mixin: agent-only access
# ---------------------------------------------------------------------------
class AgentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only allow users with is_agent=True AND an AgencyProfile.

    Superusers (the site owner) also pass — the owner dashboard reuses
    the listing create/edit/image views. Redirects unauthenticated users
    to login; 403s authenticated non-agents.
    """

    def test_func(self) -> bool:
        user = self.request.user
        return bool(
            user.is_authenticated
            and (
                user.is_superuser
                or (user.is_agent and hasattr(user, "agency_profile"))
            )
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
    """Dashboard index — role-aware (r11).

    Superuser (site owner) -> cross-agency owner overview. Agent -> the
    agent's own listings table, unchanged.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            from .owner_views import OwnerDashboardHomeView
            return OwnerDashboardHomeView.as_view()(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

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
        "is_short_stay",
        "bedrooms", "bathrooms", "size_sqm", "land_size_acres",
        "furnishing", "parking_spaces", "year_built", "service_charge",
        "amenities", "status", "is_featured", "description",
    ]
    template_name = "agents/dashboard_listing_form.html"


class DashboardListingCreate(AgentRequiredMixin, PropertyFormMixin, CreateView):
    """Create a new listing owned by the current agent.

    The owner (superuser) picks the owning agency from an extra field.
    Owner-created listings are real content by default (is_demo=False).
    """
    model = Property
    success_url = reverse_lazy("agents:dashboard_home")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.is_superuser:
            form.fields["agent"] = forms.ModelChoiceField(
                queryset=AgencyProfile.objects.order_by("name"),
                label="Agency",
                help_text="The agency this listing belongs to.",
            )
        return form

    def form_valid(self, form):
        # Stamp the agent + auto-slug + published_at (model.save handles the rest).
        if self.request.user.is_superuser:
            form.instance.agent = form.cleaned_data["agent"]
        else:
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
        """Agents can only edit their own listings; the owner edits any."""
        if self.request.user.is_superuser:
            return Property.objects.all()
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
        """Agents manage their own listing's images; the owner manages any."""
        if self.request.user.is_superuser:
            return Property.objects.all()
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
# Inquiries inbox — role-aware (r11): owner sees every agency's
# ---------------------------------------------------------------------------
class DashboardInquiries(AgentRequiredMixin, ListView):
    """Inquiries for the agent's listings — or all of them for the owner."""
    template_name = "agents/dashboard_inquiries.html"
    context_object_name = "inquiries"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = Inquiry.objects.select_related(
            "property_ref", "property_ref__property_type",
        )
        if user.is_superuser:
            return qs.select_related("property_ref__agent").order_by("-created_at")
        agency = user.agency_profile
        return (
            qs.filter(property_ref__agent=agency)
            .order_by("-created_at")
        )

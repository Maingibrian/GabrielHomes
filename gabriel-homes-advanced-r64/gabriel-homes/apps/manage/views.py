"""Owner portal views — /manage/.

The portal is the owner's own workspace, deliberately separate from both
the public site chrome and the retired agent dashboards:

  * The access gate lives HERE (``OwnerRequiredMixin``), not in
    apps.agents — the portal must never depend on the agents app, which
    only survives as a developer-side dashboard until /manage/ absorbs it
    (P3). The agents app keeps its own copy; this one is the portal's.
  * One primary action per screen (protocol §5): the home screen's
    primary action is the checklist's exact next step.
  * Plain language, mobile-first, cream/espresso tokens only.

r73 (BACKEND-PLAN Phase 1): the portal grows its five sections —
Home (graphs) · Enquiries (workflow) · Listings (read-first) ·
Site content (copy + brand assets) · SEO & tracking. Every view mixes
in PortalNavMixin so the section nav always knows the unread count.
"""
from __future__ import annotations

import csv
import re
from datetime import date

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import FormView, ListView, TemplateView, View

from . import checklist, stats
from .forms import InquiryNoteForm, SeoSettingsForm, SiteContentForm
from .models import ChecklistItemState
from apps.core.models import BrandSettings, SiteSetting
from apps.inquiries.models import Inquiry
from apps.listings.models import Property


class OwnerRequiredMixin:
    """Only the site owner (superuser) may pass.

    Unauthenticated visitors are redirected to login (honours
    settings.LOGIN_URL and ?next=). Authenticated non-owners — agents,
    regular users — get 403, never a redirect loop.

    (Deliberately NOT using LoginRequiredMixin as a base any more: the
    P2-2 toggle view is a plain View, so the gate is self-contained
    instead of tied to class-based-view dispatch ordering.)
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())
        if not request.user.is_superuser:
            raise PermissionDenied("This area is for the site owner only.")
        return super().dispatch(request, *args, **kwargs)


class PortalNavMixin:
    """Context every portal screen needs: the nav badge count."""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_new_enquiries"] = stats.new_enquiry_count()
        return ctx


# ---------------------------------------------------------------------------
# Home — greeting, graphs, checklist (P2-2 + r73 BACKEND-PLAN 1B)
# ---------------------------------------------------------------------------
class PortalHomeView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """Portal home: quick numbers + graphs + setup checklist."""

    template_name = "manage/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"
        ctx["counts"] = checklist.counts()
        ctx["checklist"] = checklist.build_checklist()
        ctx["stats"] = stats.dashboard_stats()
        return ctx


class ChecklistToggleView(OwnerRequiredMixin, View):
    """Owner ticks / un-ticks a MANUAL checklist item (POST only).

    Derived items refuse to be toggled — their state is computed from
    the database, and the owner ticking "publish a listing" by hand
    would not make a listing exist.
    """

    def post(self, request, key: str):
        if key not in checklist.MANUAL_KEYS:
            raise Http404("No manual checklist item with that key.")
        spec = next(i for i in checklist.REGISTRY if i.key == key)
        state, _created = ChecklistItemState.objects.get_or_create(key=key)
        state.done = not state.done
        state.done_at = timezone.now() if state.done else None
        state.save(update_fields=["done", "done_at", "updated_at"])
        if state.done:
            messages.success(request, f"Done: {spec.label}. Well paced.")
        else:
            messages.info(request, f"Reopened: {spec.label}.")
        return redirect("manage:home")


# ---------------------------------------------------------------------------
# Site content + SEO editors (P2-5 + r73 BACKEND-PLAN 1D/1E)
# ---------------------------------------------------------------------------
class SiteContentView(OwnerRequiredMixin, PortalNavMixin, FormView):
    """One screen to edit the public site: copy + brand assets."""

    template_name = "manage/site_content.html"
    form_class = SiteContentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = BrandSettings.load()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Site content saved. The public site is updated.")
        return redirect("manage:site_content")


class SeoSettingsView(OwnerRequiredMixin, PortalNavMixin, FormView):
    """Three plain-language fields: meta description, analytics, search console."""

    template_name = "manage/seo.html"
    form_class = SeoSettingsForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = BrandSettings.load()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "SEO & tracking saved.")
        return redirect("manage:seo")


# ---------------------------------------------------------------------------
# Enquiries (r73 BACKEND-PLAN 1C)
# ---------------------------------------------------------------------------
TAB_KEYS = ("all", "new", "seen", "contacted", "viewing", "done", "spam")
TAB_LABELS = {
    "all": "All",
    "new": "New",
    "seen": "Seen",
    "contacted": "Contacted",
    "viewing": "Viewing",
    "done": "Done",
    "spam": "Spam",
}
STATUS_FOR_TAB = {
    "new": Inquiry.Status.NEW,
    "seen": Inquiry.Status.READ,
    "contacted": Inquiry.Status.CONTACTED,
    "viewing": Inquiry.Status.VIEWING,
    "done": Inquiry.Status.CLOSED,
}


def _visible_inquiries():
    """Non-spam enquiries; sample rows vanish with the demo switch."""
    qs = Inquiry.objects.filter(honeypot="")
    if SiteSetting.demo_hidden():
        qs = qs.exclude(is_demo=True)
    return qs


def _tab_counts() -> dict:
    """Count per nav tab — one query per surface, shown as chip badges."""
    qs = _visible_inquiries()
    counts = {"all": qs.count(), "spam": Inquiry.objects.exclude(honeypot="").count()}
    by_status = dict(qs.values_list("status").annotate(c=Count("pk")))
    for tab, status in STATUS_FOR_TAB.items():
        counts[tab] = by_status.get(status, 0)
    return counts


class EnquiryListView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """The enquiries inbox: tab chips with counts + newest first rows."""

    template_name = "manage/enquiries_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "all")
        if tab not in TAB_KEYS:
            tab = "all"
        ctx["tab"] = tab
        counts = _tab_counts()
        ctx["tab_items"] = [
            {"key": key, "label": TAB_LABELS[key], "count": counts[key],
             "is_current": key == tab}
            for key in TAB_KEYS
        ]

        base = Inquiry.objects.select_related("property_ref").order_by("-created_at")
        if tab == "spam":
            qs = base.exclude(honeypot="")
        else:
            qs = _visible_inquiries().select_related("property_ref").order_by("-created_at")
            if tab in STATUS_FOR_TAB:
                qs = qs.filter(status=STATUS_FOR_TAB[tab])
        page = int(self.request.GET.get("page", 1) or 1)
        paginator_range = 20
        total = qs.count()
        # Simple pagination without django.core.paginator's page-object
        # overhead — the portal list is a phone screen, not a data grid.
        pages = max(1, -(-total // paginator_range))
        page = min(max(1, page), pages)
        ctx["page"] = page
        ctx["pages"] = pages
        ctx["enquiries"] = qs[(page - 1) * paginator_range : page * paginator_range]
        return ctx


class EnquiryDetailView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """One enquiry: message, listing, one-tap status, reply links, notes.

    Opening a New enquiry marks it Seen automatically (BACKEND-PLAN 1C)
    — the owner never has to press a button just for reading.
    """

    template_name = "manage/enquiry_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inquiry = get_object_or_404(
            Inquiry.objects.select_related(
                "property_ref", "property_ref__location", "property_ref__property_type"
            ),
            pk=kwargs["pk"],
        )
        if inquiry.status == Inquiry.Status.NEW:
            Inquiry.objects.filter(pk=inquiry.pk).update(
                status=Inquiry.Status.READ, updated_at=timezone.now()
            )
            inquiry.status = Inquiry.Status.READ
        ctx["inquiry"] = inquiry
        ctx["notes"] = inquiry.notes.all()
        ctx["note_form"] = InquiryNoteForm()
        ctx["wa_link"] = _whatsapp_reply_link(inquiry)
        ctx["status_choices"] = Inquiry.Status.choices
        return ctx


def _whatsapp_reply_link(inquiry: Inquiry) -> str:
    """Prefilled wa.me reply (BACKEND-PLAN 1C reply templates).

    Local Kenyan numbers (07…) are normalised to +254 form for wa.me;
    numbers that don't look usable return "" and the button hides.
    """
    phone = (inquiry.phone or "").strip()
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return ""
    if digits.startswith("0") and len(digits) == 10:
        digits = "254" + digits[1:]
    text = (
        f"Hi {inquiry.name.split(' ')[0]}, thanks for your enquiry about "
        f"{inquiry.property_ref.title} on Gabriel Homes."
    )
    from django.utils.http import urlencode

    return f"https://wa.me/{digits}?{urlencode({'text': text})}"


class EnquiryStatusView(OwnerRequiredMixin, View):
    """One-tap status change (POST). Unknown statuses never match."""

    def post(self, request, pk: int):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        new_status = request.POST.get("status", "")
        valid = {value for value, _label in Inquiry.Status.choices}
        if new_status not in valid:
            raise Http404("Unknown status.")
        inquiry.status = new_status
        inquiry.save(update_fields=["status", "updated_at"])
        label = inquiry.get_status_display()
        messages.success(request, f"Marked as {label.lower()}.")
        return redirect("manage:enquiry_detail", pk=inquiry.pk)


class EnquiryNoteView(OwnerRequiredMixin, View):
    """Append a note to the enquiry's private timeline (POST)."""

    def post(self, request, pk: int):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        form = InquiryNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.inquiry = inquiry
            note.save()
            messages.success(request, "Note added.")
        else:
            messages.error(request, "Write the note first — it can't be empty.")
        return redirect("manage:enquiry_detail", pk=inquiry.pk)


class EnquiryDeleteView(OwnerRequiredMixin, View):
    """Delete a SPAM row (POST). Real enquiries can never be deleted here."""

    def post(self, request, pk: int):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        if not inquiry.is_spam:
            raise Http404("Only spam can be deleted from the portal.")
        inquiry.delete()
        messages.success(request, "Spam enquiry deleted.")
        return redirect("manage:enquiries")


class EnquiryExportView(OwnerRequiredMixin, View):
    """CSV export of all non-spam enquiries (Excel-friendly, BOM first)."""

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="gabriel-enquiries-{date.today():%Y-%m-%d}.csv"'
        )
        response.write("\ufeff")  # UTF-8 BOM so Excel opens it correctly
        writer = csv.writer(response)
        writer.writerow(
            ["Date", "Name", "Email", "Phone", "Listing", "Status", "Message"]
        )
        for i in (
            _visible_inquiries()
            .select_related("property_ref")
            .order_by("-created_at")
        ):
            writer.writerow(
                [
                    i.created_at.strftime("%Y-%m-%d %H:%M"),
                    i.name,
                    i.email,
                    i.phone,
                    i.property_ref.title,
                    i.get_status_display(),
                    i.message,
                ]
            )
        return response


# ---------------------------------------------------------------------------
# Listings (r73 BACKEND-PLAN 1F — read-first; heavy tools land Phase 2)
# ---------------------------------------------------------------------------
LISTING_TABS = {
    "all": None,
    "live": Property.Status.PUBLISHED,
    "draft": Property.Status.DRAFT,
    "under_offer": Property.Status.UNDER_OFFER,
    "sold_let": Property.Status.SOLD_LET,
    "archived": Property.Status.ARCHIVED,
}
LISTING_TAB_LABELS = {
    "all": "All",
    "live": "Live",
    "draft": "Draft",
    "under_offer": "Under offer",
    "sold_let": "Sold / Let",
    "archived": "Archived",
}


class PortalListingsView(OwnerRequiredMixin, PortalNavMixin, ListView):
    """Every listing the owner has (samples badged), status chips, edit links."""

    template_name = "manage/listings.html"
    context_object_name = "listings"
    paginate_by = 20

    def get_queryset(self):
        qs = Property.objects.select_related("property_type", "location").order_by(
            "-updated_at"
        )
        status = LISTING_TABS.get(self.request.GET.get("tab", "all"))
        if status is not None:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "all")
        if tab not in LISTING_TABS:
            tab = "all"
        ctx["tab"] = tab
        counts = {"all": Property.objects.count()}
        for key, status in LISTING_TABS.items():
            if status is not None:
                counts[key] = Property.objects.filter(status=status).count()
        ctx["tab_items"] = [
            {"key": key, "label": LISTING_TAB_LABELS[key], "count": counts[key],
             "is_current": key == tab}
            for key in LISTING_TABS
        ]
        return ctx

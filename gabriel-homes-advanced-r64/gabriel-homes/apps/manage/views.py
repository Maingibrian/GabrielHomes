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
from django.template.response import TemplateResponse
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
    """Context every portal screen needs: the nav badge count.

    Tolerates plain Views (the r74 wizard/pin screens): when there is no
    TemplateView-style get_context_data above us in the MRO, start from
    an empty dict instead of crashing.
    """

    def get_context_data(self, **kwargs):
        if hasattr(super(), "get_context_data"):
            ctx = super().get_context_data(**kwargs)
        else:
            ctx = {}
        ctx.setdefault("nav_new_enquiries", stats.new_enquiry_count())
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


# ---------------------------------------------------------------------------
# Listing tools (r74 BACKEND-PLAN Phase 2)
#
# 2A duplicate · 2B bulk status + featured + inline price ·
# 2C map pin picker · 2D wizard with per-step draft saves.
#
# UX rules carried over from Phase 1 (owner's own words): plain language,
# one primary action per screen, zero-JS where possible (the only new
# script is the pin picker, which degrades to number fields), every
# screen gated + noindex, sample rows badged, honest empty states.
# ---------------------------------------------------------------------------
import os
from decimal import Decimal

from django.core.files.base import ContentFile
from django.urls import reverse

from .forms import (
    ListingPinForm,
    ListingPriceForm,
    WizardBasicsForm,
    WizardDetailsForm,
    WizardPriceForm,
)
from apps.listings.models import Property, PropertyImage


def _derive_period(property: Property) -> str:
    """The one true price-period rule (mirrors Property.clean()).

    Sale = total, long-term rent = monthly, short stay = nightly. The
    owner never sees a period field — it is derived, so it can't be wrong.
    """
    if property.is_short_stay:
        return Property.PricePeriod.NIGHTLY
    if property.listing_type == Property.ListingType.RENT:
        return Property.PricePeriod.MONTHLY
    return Property.PricePeriod.TOTAL


def _publish_ready(property: Property) -> bool:
    """The 'live' rule from the checklist: photos + a real price."""
    return (
        property.price is not None
        and property.price > 0
        and property.images.filter(is_cover=True).exists()
    )


def _duplicate_listing(src: Property) -> Property:
    """One-click copy: full content, draft status, cover kept (2A).

    Views reset to 0 and Featured off (curation is a fresh decision),
    published_at cleared, slug regenerated, image FILES copied so the
    copy never shares storage with the original.
    """
    copy = Property.objects.get(pk=src.pk)
    copy.pk = None
    copy._state.adding = True
    copy.title = f"Copy of {src.title}"[:180]
    copy.slug = ""  # save() regenerates a unique slug
    copy.status = Property.Status.DRAFT
    copy.is_featured = False
    copy.is_verified = False
    copy.views_count = 0
    copy.published_at = None
    copy.save()
    copy.amenities.set(src.amenities.all())
    for img in src.images.all():
        if not img.image.name:
            continue
        raw_name = os.path.basename(img.image.name)
        with img.image.open("rb") as fh:
            data = fh.read()
        dup = PropertyImage(
            property=copy,
            caption=img.caption,
            position=img.position,
            is_cover=img.is_cover,
        )
        # storage.get_available_name keeps same-day copies from colliding;
        # save=True runs PropertyImage.save() which mirrors cover_slot.
        dup.image.save(raw_name, ContentFile(data), save=True)
    return copy


class ListingRowToolsView(OwnerRequiredMixin, View):
    """Per-row quick tools, one POST endpoint (2A + 2B parts).

    action=feature → flip Featured; action=copy → duplicate; action=price
    → inline price edit. The row's visible controls submit this view via
    the HTML5 `form` attribute, so the markup stays flat.
    """

    def post(self, request, pk: int):
        listing = get_object_or_404(Property, pk=pk)
        action = request.POST.get("action", "")
        back_tab = request.POST.get("back") or ""
        back = f"{reverse('manage:listings')}?tab={back_tab}" if back_tab else reverse("manage:listings")

        if action == "feature":
            listing.is_featured = not listing.is_featured
            listing.save(update_fields=["is_featured", "updated_at"])
            if listing.is_featured:
                messages.success(request, "Added to Featured — it gets priority on the home page.")
            else:
                messages.info(request, "Removed from Featured.")
        elif action == "copy":
            copy = _duplicate_listing(listing)
            messages.success(
                request,
                f"Draft copy of “{listing.title}” created — find it under Drafts, "
                "add fresh photos and a price, then publish.",
            )
        elif action == "price":
            form = ListingPriceForm(request.POST)
            if form.is_valid() and form.cleaned_data["price"] > 0:
                listing.price = form.cleaned_data["price"]
                listing.price_period = _derive_period(listing)
                listing.save(update_fields=["price", "price_period", "updated_at"])
                messages.success(request, f"Price updated to KES {listing.price:,.0f}.")
            else:
                messages.error(
                    request,
                    "That price didn't look right — nothing was changed. "
                    "Use a whole number above zero.",
                )
        else:
            raise Http404("Unknown row action.")
        return redirect(back)


BULK_STATUSES = {
    "publish": (Property.Status.PUBLISHED, "Published"),
    "under_offer": (Property.Status.UNDER_OFFER, "Under offer"),
    "sold_let": (Property.Status.SOLD_LET, "Sold / Let"),
    "archive": (Property.Status.ARCHIVED, "Archived"),
}


class ListingBulkView(OwnerRequiredMixin, View):
    """Tick rows → one bar (2B). Status changes only — featured, copy and
    price are per-row decisions and live on the rows themselves."""

    def post(self, request):
        action = request.POST.get("action", "")
        ids = [int(i) for i in request.POST.getlist("ids") if i.isdigit()]
        back_tab = request.POST.get("back") or ""
        back = f"{reverse('manage:listings')}?tab={back_tab}" if back_tab else reverse("manage:listings")
        if not ids:
            messages.info(request, "Tick the rows first, then press an action.")
            return redirect(back)
        rows = list(Property.objects.filter(pk__in=ids))

        if action == "publish":
            published, held = [], []
            for row in rows:
                if _publish_ready(row):
                    row.status = Property.Status.PUBLISHED
                    row.save()  # save() stamps published_at on first publish
                    published.append(row)
                else:
                    held.append(row)
            parts = [f"Published {len(published)} listing{'s' if len(published) != 1 else ''}."]
            if held:
                names = ", ".join(h.title for h in held[:3])
                if len(held) > 3:
                    names += f" and {len(held) - 3} more"
                parts.append(
                    f"Needs a photo and a price first, so left untouched: {names}."
                )
            messages.success(request, " ".join(parts))
        elif action in BULK_STATUSES:
            status, label = BULK_STATUSES[action]
            for row in rows:
                row.status = status
                row.save(update_fields=["status", "updated_at"])
            n = len(rows)
            messages.success(request, f"Marked {n} listing{'s' if n != 1 else ''} as {label.lower()}.")
        else:
            raise Http404("Unknown bulk action.")
        return redirect(back)


class ListingPinView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """2C — click-to-set map pin on the self-hosted MapLibre stack.

    No-JS fallback: the same two number fields work by hand. The public
    site only ever shows an approximate pin — that promise is repeated
    on the save message, not just the public page.
    """

    template_name = "manage/listing_pin.html"

    def get_listing(self, pk: int) -> Property:
        return get_object_or_404(
            Property.objects.select_related("location"), pk=pk
        )

    def get(self, request, pk: int):
        listing = self.get_listing(pk)
        ctx = super().get_context_data()
        ctx["listing"] = listing
        ctx["form"] = ListingPinForm(initial={"lat": listing.lat, "lng": listing.lng})
        return self.render_to_response(ctx)

    def post(self, request, pk: int):
        listing = self.get_listing(pk)
        if request.POST.get("action") == "remove":
            listing.lat = None
            listing.lng = None
            listing.save(update_fields=["lat", "lng", "updated_at"])
            messages.info(request, "Pin removed — the listing shows its neighbourhood only.")
            return redirect("manage:listings")
        form = ListingPinForm(request.POST)
        if form.is_valid():
            listing.lat = form.cleaned_data["lat"]
            listing.lng = form.cleaned_data["lng"]
            listing.save(update_fields=["lat", "lng", "updated_at"])
            messages.success(
                request,
                "Pin saved. Visitors see an approximate pin — the exact spot is never shown.",
            )
            return redirect("manage:listings")
        ctx = super().get_context_data()
        ctx["listing"] = listing
        ctx["form"] = form
        return self.render_to_response(ctx)


# ---------------------------------------------------------------------------
# Wizard (2D) — Basics → Price → Details → Photos → Review.
# Every step POST persists to the draft row (server-side autosave), so
# a phone call or a dead battery never loses finished steps.
# ---------------------------------------------------------------------------
WIZARD_STEPS = ("basics", "price", "details", "photos", "review")
WIZARD_LABELS = {
    "basics": "Basics",
    "price": "Price",
    "details": "Details",
    "photos": "Photos",
    "review": "Review",
}
WIZARD_FORMS = {
    "basics": WizardBasicsForm,
    "price": WizardPriceForm,
    "details": WizardDetailsForm,
}


class ListingWizardView(OwnerRequiredMixin, PortalNavMixin, View):
    """All five steps on one URL: /manage/listings/new/.

    GET  ?step=<key>&pk=<draft>  — pk empty on the first visit.
    POST step + pk + action ∈ {continue, finish, discard, publish}.
    """

    def _steps(self, current: str):
        current_i = WIZARD_STEPS.index(current)
        return [
            {
                "key": key,
                "num": i + 1,
                "label": WIZARD_LABELS[key],
                "is_current": key == current,
                "is_done": i < current_i,
            }
            for i, key in enumerate(WIZARD_STEPS)
        ]

    def _wizard_url(self, step: str, pk=None) -> str:
        url = f"{reverse('manage:listing_wizard')}?step={step}"
        return f"{url}&pk={pk}" if pk else url

    def _get_draft(self, pk_text):
        if not pk_text or not pk_text.isdigit():
            return None
        draft = Property.objects.filter(pk=int(pk_text)).first()
        if draft is None:
            return None
        if draft.status != Property.Status.DRAFT:
            messages.info(
                self.request,
                f"“{draft.title}” has already left the wizard — use Edit on the listings screen.",
            )
            return "redirect"
        return draft

    # -- GET ---------------------------------------------------------------
    def get(self, request):
        step = request.GET.get("step", "basics")
        if step not in WIZARD_STEPS:
            step = "basics"
        draft_or_flag = self._get_draft(request.GET.get("pk"))
        if draft_or_flag == "redirect":
            return redirect("manage:listings")
        draft = draft_or_flag
        if draft is None and step != "basics":
            # Nothing to show on later steps without a draft row.
            return redirect("manage:listing_wizard")

        ctx = super().get_context_data()  # PortalNavMixin
        ctx["step"] = step
        ctx["steps"] = self._steps(step)
        ctx["draft"] = draft
        ctx["photos_count"] = draft.images.count() if draft else 0
        ctx["has_cover"] = bool(draft and draft.images.filter(is_cover=True).exists())
        if step in WIZARD_FORMS:
            form_cls = WIZARD_FORMS[step]
            if draft is not None:
                if step == "basics":
                    initial = {
                        "agency": draft.agent_id,
                    }
                    form = form_cls(instance=draft, initial=initial)
                else:
                    form = form_cls(instance=draft)
            else:
                form = form_cls()
            ctx["form"] = form
        return TemplateResponse(
            request, "manage/listing_wizard.html", ctx
        )

    # -- POST --------------------------------------------------------------
    def post(self, request):
        step = request.POST.get("step", "basics")
        if step not in WIZARD_STEPS:
            step = "basics"
        action = request.POST.get("action", "continue")
        draft_or_flag = self._get_draft(request.POST.get("pk"))
        if draft_or_flag == "redirect":
            return redirect("manage:listings")
        draft = draft_or_flag

        # A later step without a draft row can't be posted to — bounce
        # to the start instead of crashing on an unbound form.
        if draft is None and step != "basics":
            return redirect("manage:listing_wizard")

        # Cross-step actions available from any step's footer.
        if action == "discard" and draft is not None:
            title = draft.title
            draft.delete()
            messages.info(request, f"Draft “{title}” discarded.")
            return redirect("manage:listings")
        if action == "finish" and draft is not None:
            messages.success(
                request,
                "Draft saved — pick it up any time under Drafts (“Finish set-up”).",
            )
            return redirect(f"{reverse('manage:listings')}?tab=draft")

        if step == "basics":
            form = WizardBasicsForm(request.POST, instance=draft)
            if form.is_valid():
                saved = form.save(commit=False)
                saved.agent = form.cleaned_data["agency"]
                if draft is None:  # first save — stamp the wizard defaults
                    saved.status = Property.Status.DRAFT
                    saved.slug = ""  # regenerated by save()
                    saved.is_demo = False
                    saved.is_featured = False
                    saved.views_count = 0
                    saved.published_at = None
                    if not saved.price:
                        saved.price = Decimal("0")
                saved.price_period = _derive_period(saved)
                saved.save()
                form.save_m2m()
                messages.success(request, "Basics saved.")
                return redirect(self._wizard_url("price", saved.pk))
        elif step == "price" and draft is not None:
            form = WizardPriceForm(request.POST, instance=draft)
            if form.is_valid():
                saved = form.save(commit=False)
                saved.price_period = _derive_period(saved)
                saved.save()
                messages.success(request, "Price saved.")
                return redirect(self._wizard_url("details", draft.pk))
        elif step == "details" and draft is not None:
            form = WizardDetailsForm(request.POST, instance=draft)
            if form.is_valid():
                saved = form.save(commit=False)
                saved.price_period = _derive_period(saved)  # short-stay may have flipped
                saved.save()
                form.save_m2m()
                messages.success(request, "Details saved.")
                return redirect(self._wizard_url("photos", draft.pk))
        elif step == "photos" and draft is not None:
            return redirect(self._wizard_url("review", draft.pk))
        elif step == "review" and draft is not None:
            if action == "publish":
                if _publish_ready(draft):
                    draft.status = Property.Status.PUBLISHED
                    draft.save()  # stamps published_at
                    messages.success(
                        request, f"“{draft.title}” is live. Well paced."
                    )
                    return redirect(f"{reverse('manage:listings')}?tab=live")
                missing = []
                if not (draft.price and draft.price > 0):
                    missing.append("a price")
                if not draft.images.filter(is_cover=True).exists():
                    missing.append("a cover photo")
                messages.error(
                    request,
                    "Not ready to publish — it still needs "
                    + " and ".join(missing)
                    + ". It stays a draft; add them and press Publish again.",
                )
                return redirect(self._wizard_url("review", draft.pk))
            # anything else on review falls through as save-draft
            messages.success(
                request, "Saved as a draft — finish it any time under Drafts."
            )
            return redirect(f"{reverse('manage:listings')}?tab=draft")

        # Invalid form (or guard failed): re-render the step with errors.
        ctx = super().get_context_data()
        ctx["step"] = step
        ctx["steps"] = self._steps(step)
        ctx["draft"] = draft
        ctx["photos_count"] = draft.images.count() if draft else 0
        ctx["has_cover"] = bool(draft and draft.images.filter(is_cover=True).exists())
        ctx["form"] = form if step in WIZARD_FORMS else None
        return TemplateResponse(
            request, "manage/listing_wizard.html", ctx
        )

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
from django.db.models import Count, Prefetch
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
    """The enquiries inbox: tab chips with counts + newest first rows.

    r90 (backend reassessment): a search box (name, email, phone,
    message, listing title) so the owner can find "the one from
    Amina" without paging; page numbers that never crash (?page=abc
    now falls back to page 1 instead of a 500); a "email didn't send"
    pill on rows whose notification failed, linking to the fix; and a
    bulk bar (mark seen / mark done / delete spam) mirroring the
    listings screen's pattern.
    """

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

        q = (self.request.GET.get("q") or "").strip()
        if q:
            from django.db.models import Q

            qs = qs.filter(
                Q(name__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q)
                | Q(message__icontains=q)
                | Q(property_ref__title__icontains=q)
            )
        ctx["q"] = q

        # r90: a non-numeric ?page= used to raise ValueError (a 500 for
        # a typo'd URL). Coerce honestly: not a number = page 1.
        try:
            page = int(self.request.GET.get("page", 1) or 1)
        except (TypeError, ValueError):
            page = 1
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


class EnquiryBulkView(OwnerRequiredMixin, View):
    """r90: tick enquiry rows → one bar, mirroring the listings screen.

    Actions are deliberately the safe, common ones: mark seen, mark
    done, and delete — with delete refusing anything the spam filter
    didn't catch, exactly like the per-row delete. All-or-nothing per
    row: non-spam rows in a mixed selection are skipped with a count,
    never silently destroyed.
    """

    def post(self, request):
        action = request.POST.get("action", "")
        tab = request.POST.get("back") or "all"
        back = f"{reverse('manage:enquiries')}?tab={tab}"
        q = (request.POST.get("q") or "").strip()
        if q:
            from urllib.parse import urlencode

            back += "&" + urlencode({"q": q})
        ids = [int(i) for i in request.POST.getlist("ids") if i.isdigit()]
        if not ids:
            messages.info(request, "Tick the rows first, then press an action.")
            return redirect(back)
        rows = list(Inquiry.objects.filter(pk__in=ids))

        if action == "seen":
            for row in rows:
                if row.status == Inquiry.Status.NEW:
                    Inquiry.objects.filter(pk=row.pk).update(
                        status=Inquiry.Status.READ, updated_at=timezone.now()
                    )
            messages.success(request, f"Marked {len(rows)} as seen.")
        elif action == "done":
            for row in rows:
                Inquiry.objects.filter(pk=row.pk).update(
                    status=Inquiry.Status.CLOSED, updated_at=timezone.now()
                )
            messages.success(request, f"Marked {len(rows)} as done.")
        elif action == "delete":
            spam, refused = [], []
            for row in rows:
                if row.is_spam:
                    spam.append(row)
                else:
                    refused.append(row)
            for row in spam:
                row.delete()
            parts = [f"Deleted {len(spam)} spam enquiry{'' if len(spam) == 1 else 's'}."]
            if refused:
                parts.append(
                    f"{len(refused)} real enquir{'y was' if len(refused) == 1 else 'ies were'} "
                    "left alone — only spam can be deleted."
                )
            messages.success(request, " ".join(parts))
        else:
            raise Http404("Unknown enquiry bulk action.")
        return redirect(back)


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
    """Every listing the owner has (samples badged), status chips, edit links.

    r90: a search box (title, location, type) — same pattern as the
    enquiries screen, so both big lists are findable on a phone.
    """

    template_name = "manage/listings.html"
    context_object_name = "listings"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Property.objects.select_related("property_type", "location")
            .order_by("-updated_at")
            # r93: rows show their cover photo on desktop — one query for
            # all covers on the page, no N+1 in the loop.
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=PropertyImage.objects.filter(is_cover=True),
                    to_attr="cover_images",
                )
            )
        )
        status = LISTING_TABS.get(self.request.GET.get("tab", "all"))
        if status is not None:
            qs = qs.filter(status=status)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            from django.db.models import Q

            qs = qs.filter(
                Q(title__icontains=q)
                | Q(location__name__icontains=q)
                | Q(property_type__name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "all")
        if tab not in LISTING_TABS:
            tab = "all"
        ctx["tab"] = tab
        ctx["q"] = (self.request.GET.get("q") or "").strip()
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
        elif action == "archive":
            # r90: the row gets its own reversible "put away" — the
            # same status the bulk bar sets, one tap from the row, and
            # un-doable from the Archived tab.
            listing.status = Property.Status.ARCHIVED
            listing.save(update_fields=["status", "updated_at"])
            messages.info(
                request,
                f"“{listing.title}” is archived — nothing is deleted; "
                "find it under the Archived tab to restore.",
            )
        elif action == "restore":
            # Restoring returns the row to Draft, never straight to
            # live: a stale price or removed photos must be reviewed
            # before the public sees it again (the publish gate
            # re-checks anyway).
            listing.status = Property.Status.DRAFT
            listing.save(update_fields=["status", "updated_at"])
            messages.success(
                request,
                f"“{listing.title}” is back as a draft — check it over and "
                "press Publish when it's ready.",
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

        # r90: one transaction for the whole batch — a mid-list failure
        # used to leave half the rows moved, which reads as random
        # behaviour to the owner ("I pressed Archive and three did").
        from django.db import transaction

        if action == "publish":
            published, held = [], []
            for row in rows:
                if _publish_ready(row):
                    published.append(row)
                else:
                    held.append(row)
            with transaction.atomic():
                for row in published:
                    row.status = Property.Status.PUBLISHED
                    row.save()  # save() stamps published_at on first publish
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
            with transaction.atomic():
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


# ---------------------------------------------------------------------------
# r75 (BACKEND-PLAN Phase 3) — categories, media library, testimonials,
# newsletter compose. All live under /manage/site-content/… so the five
# section nav stays five (rule 3); these are the Site content section's
# tabs, exactly like the enquiries tabs.
# ---------------------------------------------------------------------------
from django.core.paginator import Paginator  # noqa: E402
from django.utils.text import slugify as _slugify  # noqa: E402

from .forms import (  # noqa: E402
    MediaCaptionForm,
    NewsletterComposeForm,
    TaxonomyAddForm,
    TaxonomyRenameForm,
    TestimonialForm,
)
from apps.core.models import NewsletterIssue, NewsletterSubscriber, Testimonial  # noqa: E402
from apps.core.newsletter import compose_issue  # noqa: E402
from apps.listings.models import Amenity, PropertyImage, PropertyType  # noqa: E402
from apps.locations.models import Location  # noqa: E402

TAXONOMY_KINDS = {"location": Location, "type": PropertyType, "amenity": Amenity}


def _taxonomy_model(kind: str):
    model = TAXONOMY_KINDS.get(kind)
    if model is None:
        raise Http404("No such category kind.")
    return model


class CategoriesView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """Locations, property types, amenities — add, rename, show/hide.

    No deletes, ever (BACKEND-PLAN 3A): a category with listings on it
    must not be deletable, and hiding is reversible — so the only
    destructive-looking button is "Hide", and it isn't destructive.
    """

    template_name = "manage/categories.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"

        locations = []
        for loc in Location.objects.order_by("level", "name"):
            loc.listing_count = Property.objects.filter(
                location__in=loc.get_descendants(include_self=True)
            ).count()
            locations.append(loc)

        ctx["locations"] = locations
        ctx["property_types"] = PropertyType.objects.annotate(
            listing_count=Count("properties")
        ).order_by("position", "name")
        ctx["amenities"] = Amenity.objects.annotate(
            listing_count=Count("properties")
        ).order_by("category", "name")
        ctx["add_form"] = TaxonomyAddForm()
        return ctx

    def post(self, request):
        action = request.POST.get("action", "")

        if action == "add":
            form = TaxonomyAddForm(request.POST)
            if form.is_valid():
                self._add(request, form)
            else:
                messages.error(request, "That name didn't work — check it and try again.")
            return redirect("manage:categories")

        if action == "rename":
            form = TaxonomyRenameForm(request.POST)
            model = _taxonomy_model(request.POST.get("kind", ""))
            obj = get_object_or_404(model, pk=request.POST.get("pk"))
            if form.is_valid():
                new_name = form.cleaned_data["name"].strip()
                # Pre-check (no IntegrityError games): renaming to a name
                # another row already has is refused, everything else saves.
                if model.objects.exclude(pk=obj.pk).filter(name__iexact=new_name).exists():
                    messages.error(request, f"“{new_name}” already exists.")
                else:
                    obj.name = new_name
                    obj.save(update_fields=["name"])
                    messages.success(request, f"Renamed to “{obj.name}”. Web addresses stay as they were.")
            return redirect("manage:categories")

        if action == "toggle":
            model = _taxonomy_model(request.POST.get("kind", ""))
            obj = get_object_or_404(model, pk=request.POST.get("pk"))
            obj.is_active = not obj.is_active
            obj.save(update_fields=["is_active"])
            if obj.is_active:
                messages.success(request, f"“{obj.name}” is back in the public menus.")
            else:
                messages.info(
                    request,
                    f"“{obj.name}” is hidden from the menus. Existing pages keep working.",
                )
            return redirect("manage:categories")

        raise Http404("Unknown categories action.")

    def _add(self, request, form):
        """Create one category — duplicates refused BEFORE the save.

        No try/except IntegrityError: a constraint error would poison
        the surrounding transaction, so the honest check happens first
        (name or derived web address already in use → refuse).
        """
        kind = form.cleaned_data["kind"]
        name = form.cleaned_data["name"].strip()

        if kind == "location":
            parent = form.cleaned_data.get("parent")
            slug = _slugify(name)
            if Location.objects.filter(parent=parent, name__iexact=name).exists() or (
                parent and Location.objects.filter(parent=parent, slug=slug).exists()
            ):
                messages.error(
                    request,
                    f"“{name}” already exists there"
                    + (f" (under {parent})" if parent else " as a county") + ".",
                )
                return
            Location(name=name, slug=slug, parent=parent).save()
            messages.success(
                request,
                f"Added “{name}” " + (f"under {parent}." if parent else "as a county."),
            )
        elif kind == "type":
            plural = _slugify(name if name.lower().endswith("s") else f"{name}s")
            single = _slugify(name)
            clash = (
                PropertyType.objects.filter(name__iexact=name).exists()
                or PropertyType.objects.filter(slug_plural=plural).exists()
                or PropertyType.objects.filter(slug_single=single).exists()
            )
            if clash:
                messages.error(
                    request,
                    f"“{name}” (or a type with the same web address) already exists.",
                )
                return
            PropertyType(name=name, slug_plural=plural, slug_single=single).save()
            messages.success(request, f"Added the “{name}” type.")
        else:
            slug = _slugify(name)
            if Amenity.objects.filter(name__iexact=name).exists() or Amenity.objects.filter(slug=slug).exists():
                messages.error(request, f"“{name}” already exists.")
                return
            Amenity(name=name).save()
            messages.success(request, f"Added the “{name}” amenity.")


class MediaLibraryView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """Every photo on the site, where it's used, and its caption.

    Cleanup is guarded: a live listing's cover or last photo can never
    be deleted from here — the public site can't be left photo-less.
    """

    template_name = "manage/media.html"
    per_page = 24

    MEDIA_FILTERS = {
        "all": ("All photos", None),
        "covers": ("Cover photos", lambda qs: qs.filter(is_cover=True)),
        "live": ("On live listings", lambda qs: qs.filter(property__status=Property.Status.PUBLISHED)),
        "draft": ("On drafts", lambda qs: qs.filter(property__status=Property.Status.DRAFT)),
        "archived": (
            "On archived & sold",
            lambda qs: qs.filter(
                property__status__in=(Property.Status.ARCHIVED, Property.Status.SOLD_LET)
            ),
        ),
    }

    def _base_qs(self):
        return (
            PropertyImage.objects.select_related("property", "property__location")
            .order_by("-created_at", "-pk")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"

        key = self.request.GET.get("filter", "all")
        if key not in self.MEDIA_FILTERS:
            key = "all"
        qs = self._base_qs()
        narrow = self.MEDIA_FILTERS[key][1]
        if narrow:
            qs = narrow(qs)

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(property__title__icontains=q)

        page = Paginator(qs, self.per_page).get_page(self.request.GET.get("page"))
        ctx.update(
            page_obj=page,
            media=page.object_list,
            current_filter=key,
            q=q,
        )
        # Filter chips with honest counts (computed pre-search so the
        # chips stay stable while typing).
        chips = []
        for k, (label, narrow_fn) in self.MEDIA_FILTERS.items():
            base = self._base_qs()
            chips.append(
                {"key": k, "label": label, "count": narrow_fn(base).count() if narrow_fn else base.count()}
            )
        ctx["tab_items"] = chips
        return ctx


class MediaImageActionView(OwnerRequiredMixin, View):
    """Caption edit + guarded delete for one library photo (POST only)."""

    def post(self, request, pk: int):
        image = get_object_or_404(
            PropertyImage.objects.select_related("property"), pk=pk
        )
        action = request.POST.get("action", "")

        if action == "caption":
            form = MediaCaptionForm(request.POST)
            if form.is_valid():
                image.caption = form.cleaned_data["caption"]
                image.save(update_fields=["caption"])
                messages.success(request, "Caption saved.")
            else:
                messages.error(request, "That caption is too long — keep it under 200 letters.")
            return redirect("manage:media")

        if action == "delete":
            prop = image.property
            if prop.status == Property.Status.PUBLISHED:
                if image.is_cover:
                    messages.error(
                        request,
                        f"“{image.image.name.split('/')[-1]}” is the cover photo of the live listing "
                        f"“{prop.title}” — choose a different cover there first.",
                    )
                    return redirect("manage:media")
                if prop.images.count() <= 1:
                    messages.error(
                        request,
                        f"“{prop.title}” is live and needs at least one photo — "
                        "add a new one before deleting this.",
                    )
                    return redirect("manage:media")
            image.image.delete(save=False)
            image.delete()
            messages.success(request, "Photo deleted.")
            return redirect("manage:media")

        raise Http404("Unknown media action.")


class TestimonialsView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """The owner's client quotes — entered here, shown on the home page.

    The consent box is the whole game: no permission, no publication
    (the screen says so, and the public template enforces it).
    """

    template_name = "manage/testimonials.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"
        rows = list(Testimonial.objects.order_by("position", "-created_at"))
        ctx["testimonials"] = rows
        ctx["add_form"] = TestimonialForm()
        ctx["on_site"] = sum(1 for t in rows if t.publishable and not t.is_demo)
        return ctx

    def post(self, request):
        form = TestimonialForm(request.POST)
        if form.is_valid():
            row = form.save()
            if row.consent_given:
                messages.success(request, f"“{row.name}” is now on the website.")
            else:
                messages.info(
                    request,
                    f"Saved “{row.name}”. It stays hidden until you have their permission.",
                )
        else:
            messages.error(request, "A name and their words are needed — check the form and try again.")
        return redirect("manage:testimonials")


class TestimonialActionView(OwnerRequiredMixin, View):
    """Show/hide, edit, delete one testimonial (POST only)."""

    def post(self, request, pk: int):
        row = get_object_or_404(Testimonial, pk=pk)
        action = request.POST.get("action", "")

        if action == "toggle":
            row.shown = not row.shown
            row.save(update_fields=["shown"])
            if row.shown:
                messages.success(request, f"“{row.name}” is on the website again.")
            else:
                messages.info(request, f"“{row.name}” is hidden — the words stay saved.")
            return redirect("manage:testimonials")

        if action == "delete":
            row.delete()
            messages.success(request, f"Deleted “{row.name}”.")
            return redirect("manage:testimonials")

        if action == "edit":
            form = TestimonialForm(request.POST, instance=row)
            if form.is_valid():
                form.save()
                messages.success(request, f"Updated “{row.name}”.")
            else:
                messages.error(request, "That didn't save — a name and their words are needed.")
            return redirect("manage:testimonials")

        raise Http404("Unknown testimonial action.")


class NewsletterComposeView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """Write a newsletter: pick live listings, preview, send.

    Plain rules: only confirmed subscribers receive it, every email
    carries its own unsubscribe link, and the send is recorded in the
    past-issues list on the same screen.
    """

    template_name = "manage/newsletter_compose.html"

    def _numbers(self) -> dict:
        subs = NewsletterSubscriber.objects.all()
        confirmed = [s for s in subs if s.is_active]
        pending = [s for s in subs if s.confirmed_at is None and s.unsubscribed_at is None]
        gone = [s for s in subs if s.unsubscribed_at is not None]
        biggest = max(len(confirmed), len(pending), len(gone), 1)
        return {
            "confirmed": len(confirmed),
            "pending": len(pending),
            "gone": len(gone),
            # CSS bar widths for the subscriber graph (never zero-width).
            "confirmed_pct": max(round(len(confirmed) * 100 / biggest), 2 if confirmed else 0),
            "pending_pct": max(round(len(pending) * 100 / biggest), 2 if pending else 0),
            "gone_pct": max(round(len(gone) * 100 / biggest), 2 if gone else 0),
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"
        ctx["form"] = NewsletterComposeForm()
        ctx["numbers"] = self._numbers()
        ctx["issues"] = NewsletterIssue.objects.all()[:10]
        return ctx

    def post(self, request):
        action = request.POST.get("action", "")
        form = NewsletterComposeForm(request.POST)
        valid = form.is_valid()
        picks = form.cleaned_data.get("listings", []) if valid else []
        too_many = valid and len(picks) > NewsletterComposeForm.MAX_PICKS

        if action == "preview" and valid and picks and not too_many:
            listings = list(
                Property.objects.published()
                .filter(pk__in=[int(p) for p in picks])
                .order_by("-published_at")
            )
            ctx = self.get_context_data()
            ctx.update(preview_listings=listings, form=form, picks=picks)
            return TemplateResponse(request, self.template_name, ctx)

        if action == "send" and valid and picks and not too_many:
            listings = list(
                Property.objects.published()
                .filter(pk__in=[int(p) for p in picks])
                .order_by("-published_at")
            )
            summary = compose_issue(listings)
            if summary["sent"]:
                messages.success(
                    request,
                    f"Newsletter sent to {summary['recipients']} "
                    f"subscriber{'s' if summary['recipients'] != 1 else ''}.",
                )
            elif not summary["recipients"]:
                messages.error(
                    request,
                    "Nobody to send to yet — subscribers must confirm by email first.",
                )
            else:
                messages.error(request, "Nothing was picked — choose at least one listing.")
            return redirect("manage:newsletter")

        # Anything else lands back on the form with an honest message.
        if too_many:
            messages.error(
                request, f"Up to {NewsletterComposeForm.MAX_PICKS} listings per newsletter."
            )
        elif not picks:
            messages.error(request, "Pick at least one listing first.")
        else:
            messages.error(request, "That didn't work — check the picks and try again.")
        return redirect("manage:newsletter")


# ---------------------------------------------------------------------------
# r90 (backend reassessment) — the "easy to use" round.
#
# Every screen below closes a gap found by the full-backend survey:
#   * SampleDataScreenView  — the portal's own demo-data switch (the
#     checklist used to say "Ask Brian"; the switch lived only in the
#     retired agents dashboard)
#   * confirmation screens  — a plain-language "this cannot be undone"
#     step before every irreversible delete (spam enquiry, photo,
#     testimonial, draft) — zero-JS, GET then POST
#   * OwnerPasswordChangeView — change password WITHOUT going through
#     the Django admin skin; allauth's page exists but is unbranded
#     and unlinked from the portal
# ---------------------------------------------------------------------------
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm  # noqa: E402


class SampleDataScreenView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """Sample data on/off — the portal's own switch (r90).

    The public site ships with seeded sample rows so it never looks
    empty. This screen flips SiteSetting.hide_demo_data exactly like
    the retired agents-dashboard toggle did (same cache invalidation),
    but in the portal's plain language: what the switch does, what
    stays visible where, and an honest count of what's sample data
    right now.
    """

    template_name = "manage/sample_data.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"
        setting = SiteSetting.load()
        ctx["hidden"] = setting.hide_demo_data
        ctx["sample_counts"] = {
            "listings": Property.objects.filter(is_demo=True).count(),
            "live_sample_listings": Property.objects.published()
            .filter(is_demo=True)
            .count(),
            "agencies": 0,  # single-owner mode: agency rows are legacy
        }
        return ctx

    def post(self, request):
        from django.core.cache import cache

        setting = SiteSetting.load()
        setting.hide_demo_data = not setting.hide_demo_data
        setting.save()
        cache.delete("home:showcase_listings")  # same key the agents toggle used
        if setting.hide_demo_data:
            messages.success(
                request,
                "Sample data is hidden — the public site now shows only "
                "your real listings.",
            )
        else:
            messages.info(
                request,
                "Sample data is visible again — useful while the site is "
                "still being filled in.",
            )
        return redirect("manage:sample_data")


class _ConfirmScreenView(OwnerRequiredMixin, PortalNavMixin, TemplateView):
    """Shared base for the delete confirmations: GET shows the stakes,
    POST (action=confirm) does the delete.

    Subclasses set ``what`` (short noun), ``headline``, ``detail`` and
    implement ``load()`` + ``do_delete()``. The URL always carries the
    row's pk so a shared link lands exactly on the decision.
    """

    def load(self, pk: int):
        raise NotImplementedError

    def do_delete(self, request, obj):
        raise NotImplementedError

    def get(self, request, pk: int):
        obj = self.load(pk)  # may raise Http404
        ctx = super().get_context_data()
        ctx["obj"] = obj
        ctx["headline"] = self.headline(obj)
        ctx["detail"] = self.detail(obj)
        return TemplateResponse(request, "manage/confirm_delete.html", ctx)

    def post(self, request, pk: int):
        if request.POST.get("action") != "confirm":
            return redirect(self.back_url(pk))
        obj = self.load(pk)
        done = self.do_delete(request, obj)
        if done is None:
            done = self.done_message(obj)
        messages.success(request, done)
        return redirect(self.after_delete_url())


class EnquiryDeleteConfirmView(_ConfirmScreenView):
    """Spam-enquiry delete, with the message spelled out first."""

    def load(self, pk: int):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        if not inquiry.is_spam:
            raise Http404("Only spam can be deleted from the portal.")
        return inquiry

    def headline(self, inquiry):
        return f"Delete this spam enquiry from {inquiry.name}?"

    def detail(self, inquiry):
        return (
            "The spam filter caught this message, so it was never emailed "
            "to you. Deleting it removes it for good — the name, email and "
            "message will be gone from this portal."
        )

    def back_url(self, pk):
        return reverse("manage:enquiry_detail", kwargs={"pk": pk})

    def do_delete(self, request, inquiry):
        inquiry.delete()

    def done_message(self, inquiry):
        return "Spam enquiry deleted."

    def after_delete_url(self):
        return reverse("manage:enquiries")


class MediaImageDeleteConfirmView(_ConfirmScreenView):
    """Photo delete, with the same guards the one-tap version had."""

    def load(self, pk: int):
        return get_object_or_404(
            PropertyImage.objects.select_related("property"), pk=pk
        )

    def headline(self, image):
        return f"Delete this photo from “{image.property.title}”?"

    def detail(self, image):
        return (
            "The photo file is removed from the site for good. Captions "
            "and the photo itself can't be recovered afterwards."
        )

    def back_url(self, pk):
        return reverse("manage:media")

    def do_delete(self, request, image):
        prop = image.property
        if prop.status == Property.Status.PUBLISHED:
            if image.is_cover:
                messages.error(
                    request,
                    f"This is the cover photo of the live listing "
                    f"“{prop.title}” — choose a different cover there first.",
                )
                return "SKIP"  # signal: do not show the success message
            if prop.images.count() <= 1:
                messages.error(
                    request,
                    f"“{prop.title}” is live and needs at least one photo — "
                    "add a new one before deleting this.",
                )
                return "SKIP"
        image.image.delete(save=False)
        image.delete()

    def done_message(self, image):
        return "Photo deleted."

    def after_delete_url(self):
        return reverse("manage:media")


class TestimonialDeleteConfirmView(_ConfirmScreenView):
    """Testimonial delete, quotes spelled out first."""

    def load(self, pk: int):
        return get_object_or_404(Testimonial, pk=pk)

    def headline(self, row):
        return f"Delete the testimonial from “{row.name}”?"

    def detail(self, row):
        return (
            "Their words, role and rating are removed for good. If you "
            "only want it off the site for now, cancel here and use Hide "
            "instead — hidden quotes stay saved."
        )

    def back_url(self, pk):
        return reverse("manage:testimonials")

    def do_delete(self, request, row):
        row.delete()

    def done_message(self, row):
        return f"Deleted “{row.name}”."

    def after_delete_url(self):
        return reverse("manage:testimonials")


class DraftDiscardConfirmView(_ConfirmScreenView):
    """Wizard draft discard, with what's lost spelled out first."""

    def load(self, pk: int):
        draft = get_object_or_404(Property, pk=pk)
        if draft.status != Property.Status.DRAFT:
            raise Http404("Only wizard drafts can be discarded.")
        return draft

    def headline(self, draft):
        return f"Discard the draft “{draft.title or 'Untitled listing'}”?"

    def detail(self, draft):
        return (
            "The draft and everything in it — description, price, details "
            "and uploaded photos — is deleted for good. Published listings "
            "are never affected."
        )

    def back_url(self, pk):
        return f"{reverse('manage:listing_wizard')}?step=review&pk={pk}"

    def do_delete(self, request, draft):
        draft.delete()

    def done_message(self, draft):
        return f"Draft “{draft.title or 'Untitled listing'}” discarded."

    def after_delete_url(self):
        return f"{reverse('manage:listings')}?tab=draft"


class OwnerPasswordChangeView(OwnerRequiredMixin, PortalNavMixin, FormView):
    """Change the owner password in the portal's own skin (r90).

    allauth's /account/password/change/ works but is unbranded and was
    linked from nowhere — the sanctioned path was "navigate Django
    admin → CHANGE PASSWORD". This screen is the same form, the
    portal's plain language, and it keeps the session signed in after
    the change (update_session_auth_hash) so the owner isn't logged
    out mid-task.
    """

    template_name = "manage/password_change.html"
    form_class = SetPasswordForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)
        messages.success(
            self.request,
            "Password changed. You stay signed in — use the new password "
            "next time you sign in.",
        )
        return redirect("manage:password_change")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"
        return ctx

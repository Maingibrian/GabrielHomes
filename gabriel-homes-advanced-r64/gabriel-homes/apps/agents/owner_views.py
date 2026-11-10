"""Owner (site-operator) dashboard — r11.

The owner is the superuser (admin@gabrielhomes.co.ke). They get a
role-aware, Gabriel-branded dashboard with powers no agent has:

- overview across ALL agencies (listings, inquiries, accounts)
- every listing, editable (reuses the agent edit/image views)
- agency & agent-account management (verify / deactivate / add)
- the demo-data switch (hide/show seeded placeholder content)
- a real-listing import hook (CSV -> Property, is_demo=False)

Deep power pages (types, amenities, locations, migrations) stay in the
branded admin at /admin/ — linked from the owner sidebar as "Advanced".
Agents never see any of this: their dashboard is unchanged.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, TemplateView, View

from apps.agents.models import AgencyProfile
from apps.accounts.models import User
from apps.core.models import SiteSetting
from apps.inquiries.models import Inquiry
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location

IMPORT_ROW_CAP = 500
DEMO_CACHE_KEY = "home:showcase_listings"


# ---------------------------------------------------------------------------
# Access
# ---------------------------------------------------------------------------
class OwnerRequiredMixin(LoginRequiredMixin):
    """Only the site owner (superuser) may pass."""

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin only checks authentication — the owner gate
        # needs its own check for authenticated non-owners (403).
        if request.user.is_authenticated and not request.user.is_superuser:
            raise PermissionDenied("This area is for the site owner only.")
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("This area is for the site owner only.")
        return super().handle_no_permission()


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
class OwnerDashboardHomeView(TemplateView):
    """Cross-agency overview: stats, demo switch, recent listings."""

    template_name = "agents/owner_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        listings = Property.objects.select_related("agent", "property_type", "location__parent")
        ctx["total_listings"] = listings.count()
        ctx["published_count"] = listings.filter(status=Property.Status.PUBLISHED).count()
        ctx["draft_count"] = listings.filter(status=Property.Status.DRAFT).count()
        ctx["demo_listings"] = listings.filter(is_demo=True).count()
        ctx["real_listings"] = ctx["total_listings"] - ctx["demo_listings"]
        ctx["inquiries_count"] = Inquiry.objects.count()
        ctx["new_inquiries"] = Inquiry.objects.filter(status="new").count()
        ctx["agency_count"] = AgencyProfile.objects.count()
        ctx["agent_count"] = User.objects.filter(is_agent=True).count()
        ctx["recent_listings"] = listings.order_by("-updated_at")[:10]
        ctx["top_agencies"] = (
            AgencyProfile.objects.annotate(n_props=Count("properties"))
            .order_by("-n_props")[:6]
        )
        ctx["demo_hidden"] = SiteSetting.demo_hidden()
        return ctx


# ---------------------------------------------------------------------------
# All listings across agencies
# ---------------------------------------------------------------------------
class OwnerListingsView(OwnerRequiredMixin, ListView):
    """Every listing on the platform, filterable by agency/status/demo."""

    template_name = "agents/owner_listings.html"
    context_object_name = "listings"
    paginate_by = 25

    def get_queryset(self):
        qs = Property.objects.select_related(
            "property_type", "location__parent__parent", "agent"
        ).order_by("-updated_at")
        params = self.request.GET
        q = params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(slug__icontains=q))
        agency = params.get("agency", "")
        if agency.isdigit():
            qs = qs.filter(agent_id=int(agency))
        status = params.get("status", "")
        if status in Property.Status.values:
            qs = qs.filter(status=status)
        demo = params.get("demo", "")
        if demo == "demo":
            qs = qs.filter(is_demo=True)
        elif demo == "real":
            qs = qs.filter(is_demo=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["agencies"] = AgencyProfile.objects.order_by("name")
        ctx["statuses"] = Property.Status.choices
        ctx["current"] = {
            "q": self.request.GET.get("q", ""),
            "agency": self.request.GET.get("agency", ""),
            "status": self.request.GET.get("status", ""),
            "demo": self.request.GET.get("demo", ""),
        }
        return ctx


# ---------------------------------------------------------------------------
# Agency & agent-account management
# ---------------------------------------------------------------------------
class AddAgencyForm(forms.Form):
    """Owner creates an agency + its login account in one step."""

    email = forms.EmailField(label="Login email (agent)")
    full_name = forms.CharField(label="Agent full name", max_length=180)
    agency_name = forms.CharField(label="Agency name", max_length=160)
    phone = forms.CharField(label="Phone (optional)", max_length=32, required=False)
    password = forms.CharField(
        label="Initial password (optional)",
        required=False,
        help_text="Leave blank to create the account without a password — set one later via Advanced.",
        widget=forms.TextInput,
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class OwnerAgenciesView(OwnerRequiredMixin, TemplateView):
    """List agencies + their login accounts, with one-click actions."""

    template_name = "agents/owner_agencies.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["agencies"] = (
            AgencyProfile.objects.select_related("user", "office_location")
            .annotate(n_props=Count("properties"))
            .order_by("name")
        )
        ctx["add_form"] = kwargs.get("add_form") or AddAgencyForm()
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "")

        if action == "add_agency":
            return self._add_agency(request)

        agency = get_object_or_404(AgencyProfile, pk=request.POST.get("agency", ""))

        if action == "toggle_verified":
            agency.is_verified = not agency.is_verified
            agency.save(update_fields=["is_verified", "updated_at"])
            # Private owner-dashboard wording — kept in sync with the
            # "Checked" relabel from run 2 (P0-1); the public site never
            # shows this text, but consistency avoids confusion.
            messages.success(
                request,
                f"{agency.name} {'marked checked' if agency.is_verified else 'marked not checked'}.",
            )
        elif action == "toggle_demo":
            agency.is_demo = not agency.is_demo
            agency.save(update_fields=["is_demo", "updated_at"])
            self._invalidate_home_cache()
            messages.success(
                request,
                f"{agency.name} is now marked as "
                f"{'demo (hideable)' if agency.is_demo else 'real content'}.",
            )
        elif action == "toggle_active":
            user = agency.user
            user.is_active = not user.is_active
            user.save(update_fields=["is_active", "updated_at"])
            messages.success(
                request,
                f"Account {user.email} {'deactivated — the agent can no longer sign in' if not user.is_active else 'reactivated'}.",
            )
        else:
            messages.error(request, "Unknown action.")
        return redirect("agents:owner_agencies")

    def _add_agency(self, request):
        form = AddAgencyForm(request.POST)
        if not form.is_valid():
            for errs in form.errors.values():
                for e in errs:
                    messages.error(request, e)
            return redirect("agents:owner_agencies")

        data = form.cleaned_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"] or None,
            full_name=data["full_name"],
            phone=data.get("phone", ""),
            is_agent=True,
        )
        if not data["password"]:
            user.set_unusable_password()
            user.save(update_fields=["password"])
        agency = AgencyProfile.objects.create(
            user=user,
            name=data["agency_name"],
            phone=data.get("phone", ""),
            email=data["email"],
        )
        msg = f"Agency '{agency.name}' created with login {user.email}."
        if not data["password"]:
            msg += " No password yet — set one via Advanced → Users."
        messages.success(request, msg)
        return redirect("agents:owner_agencies")

    @staticmethod
    def _invalidate_home_cache():
        cache.delete(DEMO_CACHE_KEY)


# ---------------------------------------------------------------------------
# Demo-data switch (one click)
# ---------------------------------------------------------------------------
class OwnerDemoToggleView(OwnerRequiredMixin, View):
    """Flip SiteSetting.hide_demo_data for the whole public site."""

    def post(self, request):
        setting = SiteSetting.load()
        setting.hide_demo_data = not setting.hide_demo_data
        setting.save()
        cache.delete(DEMO_CACHE_KEY)
        if setting.hide_demo_data:
            messages.success(
                request,
                "Demo data hidden — the public site now shows only real listings and agencies.",
            )
        else:
            messages.success(request, "Demo data visible again on the public site.")
        return redirect(request.POST.get("next") or reverse("agents:dashboard_home"))


# ---------------------------------------------------------------------------
# Real-listing import hook (CSV)
# ---------------------------------------------------------------------------
class ListingImportForm(forms.Form):
    csv_file = forms.FileField(label="CSV file")
    # TypedChoiceField (not BooleanField): a bare select's "off" string is
    # truthy in Python — coerce explicitly.
    dry_run = forms.TypedChoiceField(
        label="Mode",
        choices=(("on", "Dry run — validate only, save nothing"),
                 ("off", "Import — create the listings")),
        initial="on",
        coerce=lambda v: v == "on",
    )


_COLUMN_DOC = [
    ("title", "required", "Listing title"),
    ("listing_type", "required", "sale / rent"),
    ("property_type", "required", "e.g. Apartment, Townhouse (must exist)"),
    ("location", "required", "Neighbourhood name, e.g. Nyali"),
    ("price", "required", "KES number, no commas"),
    ("agency", "required", "Agency login email or agency name"),
    ("status", "optional", "draft (default) / published"),
    ("description", "optional", "Listing copy"),
    ("bedrooms", "optional", "0–20"),
    ("bathrooms", "optional", "0–20"),
    ("size_sqm", "optional", "Whole square metres"),
    ("address_text", "optional", "Public-safe street description"),
    ("furnishing", "optional", "unfurnished / semi / furnished"),
    ("price_negotiable", "optional", "true / false"),
    ("service_charge", "optional", "KES per month (rentals)"),
]


class OwnerImportView(OwnerRequiredMixin, TemplateView):
    """CSV -> Property import with dry-run validation."""

    template_name = "agents/owner_import.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = kwargs.get("form") or ListingImportForm()
        ctx["columns"] = _COLUMN_DOC
        ctx["row_cap"] = IMPORT_ROW_CAP
        ctx["result"] = kwargs.get("result")
        return ctx

    def post(self, request):
        form = ListingImportForm(request.POST, request.FILES)
        if not form.is_valid():
            for errs in form.errors.values():
                for e in errs:
                    messages.error(request, e)
            return redirect("agents:owner_import")

        result = import_listings_csv(
            fileobj=form.cleaned_data["csv_file"],
            dry_run=form.cleaned_data["dry_run"],
        )
        messages.success(
            request,
            result["summary"],
        )
        for err in result["errors"][:40]:
            messages.warning(request, err)
        if len(result["errors"]) > 40:
            messages.warning(request, f"…and {len(result['errors']) - 40} more issues.")
        return render(
            request,
            self.template_name,
            self.get_context_data(form=form, result=result),
        )


class OwnerImportSampleView(OwnerRequiredMixin, View):
    """Downloadable CSV template for the import hook."""

    def get(self, request):
        header = [c[0] for c in _COLUMN_DOC]
        rows = [
            ["2-Bed Apartment, Nyali Centre", "rent", "Apartment", "Nyali", "85000", "admin-agency@example.com", "published", "Bright 2-bed minutes from Links Road.", "2", "2", "120", "Off Links Road", "furnished", "false", "8000"],
            ["4-Bed Townhouse, Bamburi", "sale", "Townhouse", "Bamburi", "18500000", "admin-agency@example.com", "draft", "", "4", "3", "240", "", "semi", "true", ""],
        ]
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="gabriel-homes-listing-import-template.csv"'
        writer = csv.writer(resp)
        writer.writerow(header)
        writer.writerows(rows)
        return resp


def _to_bool(raw: str) -> bool:
    return raw.strip().lower() in {"true", "yes", "1", "y"}


def import_listings_csv(fileobj, dry_run: bool) -> dict:
    """Parse and (optionally) create listings. Returns a result report.

    Every created listing is stamped is_demo=False — this hook exists to
    bring in REAL inventory. Rows are independent: one bad row never
    blocks the rest.
    """
    created, errors, changed = 0, [], []

    try:
        text = fileobj.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return {"created": 0, "errors": ["File is not UTF-8 text."], "summary": "Import failed — file must be UTF-8 CSV.", "dry_run": dry_run}

    reader = csv.DictReader(text.splitlines())
    if not reader.fieldnames:
        return {"created": 0, "errors": ["No header row found."], "summary": "Import failed — empty file.", "dry_run": dry_run}

    fieldnames = [(f or "").strip().lower() for f in reader.fieldnames]
    required = {"title", "listing_type", "property_type", "location", "price", "agency"}
    missing = required - set(fieldnames)
    if missing:
        return {
            "created": 0,
            "errors": [f"Missing required column(s): {', '.join(sorted(missing))}."],
            "summary": "Import failed — required columns missing.",
            "dry_run": dry_run,
        }

    for lineno, raw_row in enumerate(reader, start=2):
        if lineno > IMPORT_ROW_CAP + 1:
            errors.append(f"Row cap reached ({IMPORT_ROW_CAP} rows) — upload the rest in a second file.")
            break
        row = {
            (k or "").strip().lower(): (v or "").strip()
            for k, v in raw_row.items()
            if k is not None
        }
        n = 0
        try:
            n = _import_one_row(row, dry_run=dry_run)
        except ValueError as exc:
            errors.append(f"Row {lineno}: {exc}")
            continue
        created += 1
        changed.append(n)

    label = "validated (dry run — nothing saved)" if dry_run else "imported"
    if created:
        summary = f"{created} listing(s) {label}." + ("" if not errors else f" {len(errors)} row(s) skipped.")
    elif errors:
        summary = f"Nothing {label} — all rows had issues."
    else:
        summary = "No rows found in the file."
    return {"created": created, "errors": errors, "summary": summary, "dry_run": dry_run}


def _resolve_location(raw: str):
    """Resolve a CSV location to a neighbourhood Location node.

    Accepts, in order: 'Area > Neighbourhood', a neighbourhood name,
    or an area name (resolves to the area's first neighbourhood so
    plain names like 'Nyali' work).
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    if ">" in raw:
        area_name, _, nb_name = raw.partition(">")
        area = Location.objects.filter(
            name__iexact=area_name.strip(), level=Location.Level.AREA
        ).first()
        if area:
            return (
                Location.objects.filter(
                    parent=area, name__iexact=nb_name.strip()
                ).first()
                or area.children.order_by("name").first()
            )
        return None
    nb = Location.objects.filter(
        name__iexact=raw, level=Location.Level.NEIGHBOURHOOD
    ).first()
    if nb:
        return nb
    area = Location.objects.filter(
        name__iexact=raw, level=Location.Level.AREA
    ).first()
    if area:
        return area.children.order_by("name").first()
    return None


def _import_one_row(row: dict, dry_run: bool = False) -> int:
    """Validate one row and (unless dry_run) create the Property.

    Raises ValueError on bad data; in dry-run mode the row is fully
    validated and built but never saved.
    """
    title = row.get("title", "")
    if not title:
        raise ValueError("title is empty")
    if len(title) > 180:
        raise ValueError("title longer than 180 characters")

    raw_type = row.get("listing_type", "").lower()
    listing_type = (
        Property.ListingType.SALE
        if raw_type in {"sale", "for sale", "sell"}
        else Property.ListingType.RENT
        if raw_type in {"rent", "to let", "let", "rental"}
        else None
    )
    if not listing_type:
        raise ValueError(f"listing_type '{raw_type}' not recognised (use sale or rent)")

    ptype = PropertyType.objects.filter(name__iexact=row.get("property_type", "")).first()
    if not ptype:
        # Friendly fallback: real-world CSVs say "Villa"/"Apartment" while
        # the catalogue stores "Villas"/"Flats & Apartments".
        ptype = PropertyType.objects.filter(
            name__icontains=row.get("property_type", "")
        ).first()
    if not ptype:
        raise ValueError(f"property_type '{row.get('property_type')}' not found")

    loc_name = row.get("location", "")
    loc = _resolve_location(loc_name)
    if not loc:
        raise ValueError(
            f"location '{loc_name}' not found (use a neighbourhood such as "
            f"'Nyali Centre', or an area name like 'Nyali')"
        )

    try:
        price = Decimal(row.get("price", ""))
    except (InvalidOperation, ArithmeticError):
        raise ValueError(f"price '{row.get('price')}' is not a number")
    if price < 0:
        raise ValueError("price cannot be negative")

    agency_ref = row.get("agency", "")
    agency = AgencyProfile.objects.filter(user__email__iexact=agency_ref).first() or (
        AgencyProfile.objects.filter(name__iexact=agency_ref).first()
    )
    if not agency:
        raise ValueError(f"agency '{agency_ref}' not found (use the login email or agency name)")

    status = row.get("status", "draft").lower() or "draft"
    if status not in Property.Status.values:
        raise ValueError(f"status '{status}' not recognised")

    def _int(name, lo, hi):
        raw = row.get(name, "")
        if not raw:
            return 0 if name in {"bedrooms", "bathrooms"} else None
        try:
            val = int(float(raw))
        except ValueError:
            raise ValueError(f"{name} '{raw}' is not a number")
        if not lo <= val <= hi:
            raise ValueError(f"{name} must be between {lo} and {hi}")
        return val

    bedrooms = _int("bedrooms", 0, 20)
    bathrooms = _int("bathrooms", 0, 20)
    size_sqm = _int("size_sqm", 0, 100000)

    furnishing_raw = row.get("furnishing", "").lower()
    furnishing = {
        "": Property.Furnishing.UNFURNISHED,
        "unfurnished": Property.Furnishing.UNFURNISHED,
        "semi": Property.Furnishing.SEMI,
        "semi-furnished": Property.Furnishing.SEMI,
        "furnished": Property.Furnishing.FURNISHED,
    }.get(furnishing_raw)
    if furnishing is None:
        raise ValueError(f"furnishing '{furnishing_raw}' not recognised")

    service_charge = None
    if row.get("service_charge"):
        try:
            service_charge = Decimal(row["service_charge"])
        except (InvalidOperation, ArithmeticError):
            raise ValueError("service_charge is not a number")

    description = row.get("description", "") or (
        f"{title} — {bedrooms}-bedroom {ptype.name.lower()} in {loc_name}, Kenya. "
        "Contact the agency for details and viewing arrangements."
    )
    if len(description) > 20000:
        raise ValueError("description longer than 20000 characters")

    prop = Property(
        title=title,
        description=description,
        listing_type=listing_type,
        property_type=ptype,
        location=loc,
        address_text=row.get("address_text", ""),
        price=price,
        price_period=(
            Property.PricePeriod.TOTAL
            if listing_type == Property.ListingType.SALE
            else Property.PricePeriod.MONTHLY
        ),
        price_negotiable=_to_bool(row.get("price_negotiable", "")),
        bedrooms=bedrooms or 0,
        bathrooms=bathrooms or 0,
        size_sqm=size_sqm,
        furnishing=furnishing,
        service_charge=service_charge,
        status=status,
        agent=agency,
        # The import hook exists for REAL inventory — never stamped demo.
        is_demo=False,
    )
    # slug is generated in save(); full_clean would reject the blank
    # slug, so exclude it here (uniqueness is enforced by _make_unique_slug).
    try:
        prop.full_clean(exclude=["lat", "lng", "slug"])
    except ValidationError as exc:
        raise ValueError(str(exc.messages[0]) if exc.messages else str(exc))
    if dry_run:
        return 0
    prop.save()
    return prop.pk

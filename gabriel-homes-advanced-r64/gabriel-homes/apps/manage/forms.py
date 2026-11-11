"""Owner-facing forms for the portal editors (P2-5 + r73 BACKEND-PLAN 1D/1E).

r74 (BACKEND-PLAN Phase 2): + listing wizard step forms, the inline
price editor, and the map-pin form.
"""

from django import forms

from apps.core.models import BrandSettings
from apps.inquiries.models import InquiryNote
from apps.listings.models import Amenity, Property


class InquiryNoteForm(forms.ModelForm):
    """One timeline note on an enquiry (r73 BACKEND-PLAN 1C)."""

    class Meta:
        model = InquiryNote
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "e.g. Called back — viewing Saturday 10am",
                }
            ),
        }


class SiteContentForm(forms.ModelForm):
    """Edit public copy + brand assets without accepting HTML or code.

    r73: extended with the "Logo, address & socials" group so the owner
    edits the whole public identity from ONE screen (rule: one place,
    no hunting). Image fields make the form multipart — the template
    carries enctype="multipart/form-data".
    """

    class Meta:
        model = BrandSettings
        fields = (
            # Contact details
            "phone",
            "whatsapp",
            "email",
            # Homepage hero
            "hero_tag",
            "hero_heading_lead",
            "hero_heading_accent",
            "hero_heading_tail",
            "hero_subtitle",
            # Homepage sections
            "about_heading",
            "about_intro",
            "services_heading",
            "services_intro",
            "cta_heading",
            "cta_intro",
            "footer_lead",
            # Logo, address & socials (r73)
            "logo",
            "favicon",
            "address_line",
            "opening_hours",
            "instagram_url",
            "facebook_url",
            "x_url",
            "tiktok_url",
        )
        widgets = {
            "hero_subtitle": forms.Textarea(attrs={"rows": 3}),
            "about_intro": forms.Textarea(attrs={"rows": 3}),
            "services_intro": forms.Textarea(attrs={"rows": 3}),
            "cta_intro": forms.Textarea(attrs={"rows": 3}),
            "address_line": forms.TextInput(attrs={"placeholder": "Links Road, Nyali, Mombasa"}),
            "opening_hours": forms.TextInput(attrs={"placeholder": "Mon–Sat 8am–6pm"}),
            "instagram_url": forms.URLInput(attrs={"placeholder": "https://instagram.com/yourhandle"}),
            "facebook_url": forms.URLInput(attrs={"placeholder": "https://facebook.com/yourpage"}),
            "x_url": forms.URLInput(attrs={"placeholder": "https://x.com/yourhandle"}),
            "tiktok_url": forms.URLInput(attrs={"placeholder": "https://tiktok.com/@yourhandle"}),
        }


class SeoSettingsForm(forms.ModelForm):
    """SEO & tracking (r73 BACKEND-PLAN 1E) — three fields, plain help."""

    class Meta:
        model = BrandSettings
        fields = ("meta_description", "analytics_id", "search_console_token")
        widgets = {
            "meta_description": forms.Textarea(attrs={"rows": 3}),
            "analytics_id": forms.TextInput(attrs={"placeholder": "G-XXXXXXXXXX"}),
            "search_console_token": forms.TextInput(
                attrs={"placeholder": "google-site-verification code"}
            ),
        }

    def clean_analytics_id(self):
        value = (self.cleaned_data.get("analytics_id") or "").strip()
        if value and not value.startswith("G-"):
            raise forms.ValidationError(
                "A Google Analytics 4 ID starts with 'G-' (e.g. G-ABC123XYZ9). "
                "Leave the field empty if you don't want tracking."
            )
        return value


# ---------------------------------------------------------------------------
# r74 (BACKEND-PLAN Phase 2) — listing tools: wizard steps, row tools, pin.
# ---------------------------------------------------------------------------
from decimal import Decimal  # noqa: E402


def _default_agency():
    """The wizard's default owning agency: Gabriel Homes, else first by name."""
    from apps.agents.models import AgencyProfile

    agency = AgencyProfile.objects.filter(name__iexact="Gabriel Homes").first()
    return agency or AgencyProfile.objects.order_by("name").first()


def _period_for(listing_type, is_short_stay):
    """Derived price period — the one rule, in one place for the forms.

    The model's clean() enforces the same rule at save time; deriving it
    here means the owner never sees a period field AND the ModelForm's
    _post_clean (which runs model.full_clean) never sees an inconsistent
    instance.
    """
    if is_short_stay:
        return Property.PricePeriod.NIGHTLY
    if listing_type == Property.ListingType.RENT:
        return Property.PricePeriod.MONTHLY
    return Property.PricePeriod.TOTAL


class _PeriodDerivingForm(forms.ModelForm):
    """Shared by the three wizard ModelForms: keeps the in-memory
    instance consistent (period derived, short-stay only on rentals)
    before _post_clean runs the model's cross-field clean()."""

    def clean(self):
        cleaned = super().clean()
        lt = cleaned.get("listing_type") or self.instance.listing_type
        ss = cleaned.get("is_short_stay")
        if ss is None:
            ss = self.instance.is_short_stay
        if ss and lt != Property.ListingType.RENT:
            # Short stays are rentals by definition; flipping the listing
            # to For Sale quietly turns the short-stay flag off.
            ss = False
        self.instance.listing_type = lt
        self.instance.is_short_stay = ss
        self.instance.price_period = _period_for(lt, ss)
        return cleaned


class WizardBasicsForm(_PeriodDerivingForm):
    """Wizard step 1 — who it is: names, type, place, and the pitch."""

    agency = forms.ModelChoiceField(
        queryset=None,  # set in __init__ (kept fresh per request)
        label="Managed by",
        help_text="Usually Gabriel Homes — change only if another team manages it.",
    )

    class Meta:
        model = Property
        fields = ("title", "listing_type", "property_type", "location", "description")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. 3BR sea-view apartment in Nyali"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "listing_type": "Listing is for",
            "property_type": "Property type",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.agents.models import AgencyProfile

        self.fields["agency"].queryset = AgencyProfile.objects.order_by("name")
        if not self.initial.get("agency") and self.instance.pk is None:
            self.fields["agency"].initial = _default_agency()
        # Neighbourhood-level locations only (the FK's limit_choices_to is
        # applied by formfield(), but the ordering needs doing here).
        from apps.locations.models import Location

        self.fields["location"].queryset = Location.objects.filter(
            level="neighbourhood"
        ).order_by("parent__parent__name", "parent__name", "name")


class WizardPriceForm(_PeriodDerivingForm):
    """Wizard step 2 — the money question."""

    class Meta:
        model = Property
        fields = ("price", "price_negotiable")
        labels = {
            "price": "Asking price (KES)",
            "price_negotiable": "Price is negotiable",
        }

    def clean_price(self):
        value = self.cleaned_data.get("price")
        if value is not None and value <= 0:
            raise forms.ValidationError(
                "Enter the real asking price — you can add it in a later step "
                "if you don't know it yet, but it can't be zero or negative."
            )
        return value


class WizardDetailsForm(_PeriodDerivingForm):
    """Wizard step 3 — the numbers that matter to buyers."""

    class Meta:
        model = Property
        fields = (
            "bedrooms", "bathrooms", "size_sqm", "land_size_acres",
            "furnishing", "parking_spaces", "year_built",
            "address_text", "is_short_stay", "amenities",
        )
        widgets = {
            "address_text": forms.TextInput(
                attrs={"placeholder": "e.g. off Links Road, Nyali"}
            ),
            "amenities": forms.CheckboxSelectMultiple,
        }
        labels = {
            "size_sqm": "Size (sq m)",
            "land_size_acres": "Land (acres)",
            "address_text": "Street area (optional)",
            "is_short_stay": "Also a short stay (priced per night)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amenities"].queryset = Amenity.objects.order_by("category", "name")
        for name in ("bedrooms", "bathrooms", "parking_spaces", "year_built"):
            self.fields[name].required = False


class ListingPriceForm(forms.Form):
    """The inline price editor on a listings row (one number, save)."""

    price = forms.DecimalField(
        min_value=Decimal("0"),
        max_digits=14,
        decimal_places=2,
        localize=False,
        widget=forms.NumberInput(attrs={"step": "any", "inputmode": "decimal"}),
        help_text="Whole KES. A price of 0 shows as “no price yet”.",
    )


class ListingPinForm(forms.Form):
    """Map pin coordinates — both or neither, sane ranges, 6 decimals."""

    lat = forms.DecimalField(
        min_value=Decimal("-90"), max_value=Decimal("90"),
        max_digits=9, decimal_places=6, required=False,
        widget=forms.NumberInput(attrs={"step": "any", "inputmode": "decimal"}),
    )
    lng = forms.DecimalField(
        min_value=Decimal("-180"), max_value=Decimal("180"),
        max_digits=9, decimal_places=6, required=False,
        widget=forms.NumberInput(attrs={"step": "any", "inputmode": "decimal"}),
    )

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("lat"), cleaned.get("lng")
        if (lat is None) != (lng is None):
            raise forms.ValidationError("Set the pin on the map — it needs both a latitude and a longitude.")
        return cleaned

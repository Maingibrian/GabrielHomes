"""Owner-facing forms for the portal editors (P2-5 + r73 BACKEND-PLAN 1D/1E)."""

from django import forms

from apps.core.models import BrandSettings
from apps.inquiries.models import InquiryNote


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

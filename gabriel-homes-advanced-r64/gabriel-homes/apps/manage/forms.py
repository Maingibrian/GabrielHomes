"""Owner-facing forms for the small site-content editor."""

from django import forms

from apps.core.models import BrandSettings


class SiteContentForm(forms.ModelForm):
    """Edit public copy without accepting HTML or template code."""

    class Meta:
        model = BrandSettings
        fields = (
            "phone",
            "whatsapp",
            "email",
            "hero_tag",
            "hero_heading_lead",
            "hero_heading_accent",
            "hero_heading_tail",
            "hero_subtitle",
            "about_heading",
            "about_intro",
            "services_heading",
            "services_intro",
            "cta_heading",
            "cta_intro",
            "footer_lead",
        )
        widgets = {
            "phone": forms.TextInput(attrs={"autocomplete": "tel"}),
            "whatsapp": forms.TextInput(attrs={"autocomplete": "tel"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "hero_subtitle": forms.Textarea(attrs={"rows": 4}),
            "about_intro": forms.Textarea(attrs={"rows": 4}),
            "services_intro": forms.Textarea(attrs={"rows": 4}),
            "cta_intro": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        for name, value in cleaned.items():
            if isinstance(value, str):
                cleaned[name] = value.strip()
        return cleaned

"""Forms for the inquiries app — enquiry form with honeypot."""
from __future__ import annotations

from django import forms

from .models import Inquiry


class InquiryForm(forms.ModelForm):
    """Enquiry form for a property detail page.

    The `website` field is a honeypot — it's hidden via CSS and labelled
    "Leave this field blank". Bots tend to fill every field; humans don't.
    Any non-empty value flags the submission as spam (the Inquiry is
    still saved, with `honeypot` set, so we can audit; but no email is
    sent and no success message is shown).

    Per-IP rate limiting is handled in the view (not the form) because
    it needs the request object.
    """

    # Honeypot — visually hidden, labelled for screen readers as "do not fill".
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "tabindex": "-1",
            "aria-hidden": "true",
            "class": "hp-field",  # visually hidden via CSS
        }),
        label="Leave this field blank (spam trap)",
    )

    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "message"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form__input",
                "placeholder": "Your name",
                "autocomplete": "name",
                "aria-label": "Your name",  # r12: placeholder-only label
            }),
            "email": forms.EmailInput(attrs={
                "class": "form__input",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "aria-label": "Your email address",  # r12
            }),
            "phone": forms.TextInput(attrs={
                "class": "form__input",
                "placeholder": "+254 7XX XXX XXX",
                "autocomplete": "tel",
                "aria-label": "Your phone number",  # r12
            }),
            "message": forms.Textarea(attrs={
                "class": "form__textarea",
                "placeholder": "I'm interested in this property. When can I view it?",
                "rows": 4,
                "aria-label": "Your message",  # r12
            }),
        }

    def clean_website(self) -> str:
        """If the honeypot is filled, flag as spam but don't raise."""
        value = self.cleaned_data.get("website", "")
        # Don't raise — we want to save the row as spam for audit.
        # The view checks form.cleaned_data['website'] and short-circuits.
        return value

    def clean_message(self) -> str:
        message = self.cleaned_data.get("message", "").strip()
        if len(message) < 10:
            raise forms.ValidationError(
                "Please write a slightly longer message (at least 10 characters)."
            )
        return message

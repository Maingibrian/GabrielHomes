from django import forms


class NewsletterSignupForm(forms.Form):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={
        "placeholder": "you@example.com", "autocomplete": "email", "required": True,
    }))
    consent = forms.BooleanField(
        required=True,
        error_messages={"required": "Please tick the box to agree to receive the newsletter."},
    )

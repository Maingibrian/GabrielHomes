"""Views for the inquiries app — enquiry form submission.

Per WORK.md §11 Phase 4:
- Enquiry form (HTMX submit, honeypot, rate limit), email to agent,
  Inquiry saved.
- Done when: enquiry creates an Inquiry and sends an email (console
  backend in dev).
"""
from __future__ import annotations

from datetime import timedelta

from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.listings.models import Property

from .forms import InquiryForm
from .models import Inquiry

# Per-IP rate limit: max 3 enquiries per minute from the same IP.
RATE_LIMIT_MAX = 3
RATE_LIMIT_WINDOW = timedelta(minutes=1)


def _get_client_ip(request) -> str:
    """Get the client IP, respecting X-Forwarded-For behind a proxy."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _is_rate_limited(request) -> bool:
    """Return True if the client IP has exceeded the enquiry rate limit."""
    ip = _get_client_ip(request)
    if not ip:
        return False
    cutoff = timezone.now() - RATE_LIMIT_WINDOW
    recent = Inquiry.objects.filter(
        submitter_ip=ip, created_at__gte=cutoff
    ).count()
    return recent >= RATE_LIMIT_MAX


@require_POST
def submit_enquiry(request, slug: str, pk: int):
    """Handle an enquiry form submission for a specific property.

    - HTMX-friendly: returns an HTML partial (success or error) that
      swaps into #enquiry-form-container.
    - Honeypot: if the hidden `website` field is filled, save the Inquiry
      as spam (for audit) but return a fake-success response so the bot
      doesn't know it was caught.
    - Rate limit: max RATE_LIMIT_MAX enquiries per minute per IP.
    """
    property = get_object_or_404(
        Property.objects.published().select_related("agent__user", "property_type", "location__parent__parent"),
        slug=slug, pk=pk,
    )

    form = InquiryForm(request.POST)
    if form.is_valid():
        # Honeypot check — save as spam, return fake success.
        honeypot_value = form.cleaned_data.get("website", "")
        if honeypot_value:
            inquiry = form.save(commit=False)
            inquiry.property_ref = property
            inquiry.honeypot = honeypot_value
            inquiry.submitter_ip = _get_client_ip(request)
            if request.user.is_authenticated:
                inquiry.user = request.user
            inquiry.save()
            # Return success-looking response without sending email.
            return render(request, "inquiries/_enquiry_success.html", {
                "property": property,
                "fake_success": True,
            })

        # Rate limit check.
        if _is_rate_limited(request):
            return render(request, "inquiries/_enquiry_error.html", {
                "property": property,
                "error": "You've sent too many enquiries in the last minute. Please wait a moment and try again.",
            }, status=429)

        # Save the genuine inquiry.
        inquiry = form.save(commit=False)
        inquiry.property_ref = property
        inquiry.submitter_ip = _get_client_ip(request)
        if request.user.is_authenticated:
            inquiry.user = request.user
        inquiry.save()

        # Send email to the agent.
        _send_enquiry_email(property, inquiry)

        return render(request, "inquiries/_enquiry_success.html", {
            "property": property,
            "inquiry": inquiry,
        })

    # Form invalid — re-render with errors.
    return render(request, "inquiries/_enquiry_form.html", {
        "property": property,
        "form": form,
    }, status=422)


def _send_enquiry_email(property: Property, inquiry: Inquiry) -> None:
    """Send the enquiry notification email to the listing agent.

    Uses Django's email backend — console in dev (per WORK.md §11
    Phase 4: "console backend in dev"), SMTP in prod.
    """
    agent_email = property.agent.display_email
    if not agent_email:
        return  # nothing we can do without an address

    context = {
        "property": property,
        "inquiry": inquiry,
        "site_name": "Gabriel Homes",
    }
    subject = f"New enquiry for {property.title}"
    body_text = render_to_string("inquiries/email/enquiry.txt", context)
    body_html = render_to_string("inquiries/email/enquiry.html", context)

    send_mail(
        subject=subject,
        message=body_text,
        from_email="enquiries@gabrielhomes.co.ke",
        recipient_list=[agent_email],
        html_message=body_html,
        fail_silently=True,  # don't 500 the form submit if email fails
    )

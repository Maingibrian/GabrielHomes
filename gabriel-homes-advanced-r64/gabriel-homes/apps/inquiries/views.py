"""Views for the inquiries app — enquiry form submission.

Per WORK.md §11 Phase 4:
- Enquiry form (HTMX submit, honeypot, rate limit), email to agent,
  Inquiry saved.
- Done when: enquiry creates an Inquiry and sends an email (console
  backend in dev).
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.clientip import get_client_ip
from apps.listings.models import Property

from .forms import InquiryForm
from .models import Inquiry

logger = logging.getLogger(__name__)

# Per-IP rate limit: max 3 enquiries per minute from the same IP.
RATE_LIMIT_MAX = 3
RATE_LIMIT_WINDOW = timedelta(minutes=1)


def _is_rate_limited(request) -> bool:
    """Return True if the client IP has exceeded the enquiry rate limit."""
    ip = get_client_ip(request)
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
            inquiry.submitter_ip = get_client_ip(request)
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
        inquiry.submitter_ip = get_client_ip(request)
        if request.user.is_authenticated:
            inquiry.user = request.user
        inquiry.save()

        # Notify the owner (single-owner mode) — falls back to the listing
        # agent's address only when OWNER_EMAIL is unset (dev/demo).
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
    """Send the enquiry notification email.

    P1-4 single-owner routing: the recipient is ``settings.OWNER_EMAIL``
    whenever it is set — every enquiry on the platform reaches the owner,
    regardless of which (legacy) agency row owns the listing. When
    OWNER_EMAIL is unset or blank (dev/demo), the email falls back to the
    listing agent's own address so the flow still demonstrates end-to-end.

    Uses Django's email backend — console in dev (per WORK.md §11
    Phase 4: "console backend in dev"), SMTP in prod (A2).

    Delivery tracking (S9): on success the inquiry's email_sent_at is
    stamped; on failure email_error records the exception (truncated to
    300 chars) and the failure is logged — never silently swallowed.
    In both cases the caller proceeds: the enquiry itself was saved, so
    the visitor still gets the success partial.
    """
    # r90 (backend reassessment): recipient priority is now
    # BrandSettings.notification_email (editable in the portal's Site
    # content screen) → settings.OWNER_EMAIL → the listing agent's
    # address. The DB field first means the owner can retarget alerts
    # without a redeploy; the env setting remains the deployment
    # default and the checklist fallback.
    recipient = ""
    try:
        from apps.core.models import BrandSettings

        recipient = (BrandSettings.load().notification_email or "").strip()
    except Exception:
        pass  # a brand-row failure must never block the notification
    if not recipient:
        recipient = (getattr(settings, "OWNER_EMAIL", "") or "").strip()
    if not recipient:
        recipient = property.agent.display_email
    if not recipient:
        return  # nothing we can do without an address — leave tracking untouched

    context = {
        "property": property,
        "inquiry": inquiry,
        "site_name": "Gabriel Homes",
    }
    subject = f"New enquiry for {property.title}"
    body_text = render_to_string("inquiries/email/enquiry.txt", context)
    body_html = render_to_string("inquiries/email/enquiry.html", context)

    try:
        send_mail(
            subject=subject,
            message=body_text,
            from_email="enquiries@gabrielhomes.co.ke",
            recipient_list=[recipient],
            html_message=body_html,
            fail_silently=False,  # failures are caught below and recorded (S9)
        )
    except Exception as exc:
        # Truncate to the column limit — SMTP traces can be enormous.
        inquiry.email_error = f"{type(exc).__name__}: {exc}"[:300]
        inquiry.save(update_fields=["email_error", "updated_at"])
        logger.exception(
            "Enquiry notification email failed for inquiry %s (recipient %s)",
            inquiry.pk, recipient,
        )
        return
    inquiry.email_sent_at = timezone.now()
    inquiry.save(update_fields=["email_sent_at", "updated_at"])

"""Newsletter service: sign-up, confirmation, unsubscribe and the
ten-listings trigger.

Rules (owner decisions, see the content audit):
  * a newsletter is sent only once at least NEWSLETTER_THRESHOLD new REAL
    listings have been published since the last issue;
  * it goes only to people who opted in AND confirmed by email;
  * every email carries a one-click unsubscribe link.
"""
from __future__ import annotations

import secrets

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.core.models import NewsletterIssue, NewsletterSubscriber

NEWSLETTER_THRESHOLD = 10


def _absolute(path: str) -> str:
    return settings.SITE_DOMAIN.rstrip("/") + path


def subscribe(email: str) -> NewsletterSubscriber:
    """Create or refresh a pending subscription and send the confirmation email."""
    email = email.strip().lower()
    sub, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={"consent_at": timezone.now(), "token": secrets.token_hex(24)},
    )
    if not created:
        # Subscribing again re-issues the consent and the link; an unsubscribed
        # person who asks again is treated as a fresh opt-in.
        sub.consent_at = timezone.now()
        sub.unsubscribed_at = None
        sub.confirmed_at = None
        sub.token = secrets.token_hex(24)
        sub.save(update_fields=["consent_at", "unsubscribed_at", "confirmed_at", "token"])
    send_confirmation(sub)
    return sub


def send_confirmation(sub: NewsletterSubscriber) -> None:
    link = _absolute(reverse("newsletter_confirm", args=[sub.token]))
    body = render_to_string("core/email/newsletter_confirm.txt", {"link": link})
    EmailMultiAlternatives(
        subject="Confirm your Gabriel Homes newsletter sign-up",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[sub.email],
    ).send()


def confirm(token: str) -> NewsletterSubscriber | None:
    sub = NewsletterSubscriber.objects.filter(token=token).first()
    if sub is None:
        return None
    if sub.confirmed_at is None:
        sub.confirmed_at = timezone.now()
        sub.unsubscribed_at = None
        sub.save(update_fields=["confirmed_at", "unsubscribed_at"])
    return sub


def unsubscribe(token: str) -> NewsletterSubscriber | None:
    sub = NewsletterSubscriber.objects.filter(token=token).first()
    if sub is None:
        return None
    if sub.unsubscribed_at is None:
        sub.unsubscribed_at = timezone.now()
        sub.save(update_fields=["unsubscribed_at"])
    return sub


def new_listings_since_last_issue():
    """Real, published listings added since the last issue went out."""
    from apps.listings.models import Property

    qs = Property.objects.published().exclude(is_demo=True)
    last = NewsletterIssue.objects.first()
    if last is not None:
        qs = qs.filter(published_at__gt=last.sent_at)
    return qs.order_by("-published_at")


def send_issue_if_due(dry_run: bool = False) -> dict:
    """Send one issue when the threshold is met. Returns a summary dict."""
    listings = list(new_listings_since_last_issue()[:50])
    total_new = new_listings_since_last_issue().count()
    recipients = list(NewsletterSubscriber.objects.filter(
        confirmed_at__isnull=False, unsubscribed_at__isnull=True,
    ).order_by("email"))

    summary = {
        "new_listings": total_new,
        "threshold": NEWSLETTER_THRESHOLD,
        "recipients": len(recipients),
        "sent": False,
        "dry_run": dry_run,
    }
    if total_new < NEWSLETTER_THRESHOLD or not recipients or dry_run:
        return summary

    for sub in recipients:
        unsub = _absolute(reverse("newsletter_unsubscribe", args=[sub.token]))
        ctx = {"listings": listings, "unsubscribe_link": unsub, "total_new": total_new,
               "SITE_DOMAIN": settings.SITE_DOMAIN.rstrip("/")}
        text = render_to_string("core/email/newsletter_issue.txt", ctx)
        html = render_to_string("core/email/newsletter_issue.html", ctx)
        msg = EmailMultiAlternatives(
            subject=f"Gabriel Homes: {total_new} new listings",
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[sub.email],
            headers={
                "List-Unsubscribe": f"<{unsub}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        )
        msg.attach_alternative(html, "text/html")
        msg.send()

    NewsletterIssue.objects.create(listing_count=total_new, recipient_count=len(recipients))
    summary["sent"] = True
    return summary

"""Send the newsletter when at least ten new real listings are published.

Run this on a schedule (for example daily, from cron or the host's scheduler):

    python manage.py send_newsletter

It does nothing until the threshold is met. Use --dry-run to see what would
happen without sending.
"""
from django.core.management.base import BaseCommand

from apps.core.newsletter import send_issue_if_due


class Command(BaseCommand):
    help = "Send a newsletter when at least 10 new real listings have been published."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only; send nothing.")

    def handle(self, *args, **options):
        s = send_issue_if_due(dry_run=options["dry_run"])
        if s["sent"]:
            self.stdout.write(self.style.SUCCESS(
                f"Sent to {s['recipients']} confirmed subscriber(s) for {s['new_listings']} new listings."))
        elif s["dry_run"]:
            self.stdout.write(f"Dry run: {s['new_listings']} new listings, {s['recipients']} recipients.")
        elif s["new_listings"] < s["threshold"]:
            self.stdout.write(f"Not sent: {s['new_listings']} of {s['threshold']} new listings so far.")
        else:
            self.stdout.write("Not sent: no confirmed subscribers yet.")

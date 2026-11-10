"""purge_inquiries — enforce the inquiry data-retention policy (C3).

Privacy / Data Protection Act, 2019 (Kenya) housekeeping: enquiries are
personal data and must not be kept forever. This command deletes inquiries
older than --days (default 365; the owner sets the final period, PLAN O4)
and prints the count.

Run it from cron on the server (line lives in DEPLOY.md, task D4):
    0 3 * * *  cd /srv/gabriel-homes && .venv/bin/python manage.py purge_inquiries

Examples:
    python manage.py purge_inquiries --dry-run
    python manage.py purge_inquiries --days 730
"""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from apps.inquiries.models import Inquiry


class Command(BaseCommand):
    help = (
        "Delete inquiries older than the retention period "
        "(default 365 days). Supports --dry-run."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--days", type=int, default=365,
            help="Retention period in days (default 365).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Report what would be deleted without deleting anything.",
        )

    def handle(self, *args, **opts) -> None:
        days: int = opts["days"]
        dry_run: bool = opts["dry_run"]

        if days < 1:
            raise SystemExit("purge_inquiries: --days must be >= 1.")

        cutoff = timezone.now() - timedelta(days=days)
        to_delete = Inquiry.objects.filter(created_at__lt=cutoff)
        count = to_delete.count()

        if dry_run:
            self.stdout.write(
                f"DRY RUN: would delete {count} inquiry(ies) "
                f"created before {cutoff.isoformat()} "
                f"(retention: {days} days)."
            )
            return

        # cascade removal of related rows happens via FK on_delete.
        deleted, _ = to_delete.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} inquiry(ies) older than {days} days "
                f"(cutoff {cutoff.isoformat()})."
            )
        )

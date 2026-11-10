"""bootstrap_owner — create the site-owner superuser (r11).

    python manage.py bootstrap_owner

Creates admin@gabrielhomes.co.ke as a superuser the first time it runs.
If the account already exists it is NEVER touched (same posture as the
S4 demo-credential guards: a management command never overwrites a
password). A temporary password is printed exactly once — the owner
changes it after first sign-in via Studio → Change password.

Options:
    --password <pw>   set a specific temporary password instead of a
                      generated one (still only applied on CREATE)
    --quiet           don't print the password (for scripted runs)
"""
from __future__ import annotations

import secrets
import string

from django.core.management.base import BaseCommand

from apps.accounts.models import User

OWNER_EMAIL = "admin@gabrielhomes.co.ke"


class Command(BaseCommand):
    help = (
        "Create the site-owner superuser (admin@gabrielhomes.co.ke). "
        "Existing accounts are never modified."
    )

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Temporary password to use on create.")
        parser.add_argument(
            "--quiet", action="store_true", help="Do not print the password."
        )

    def handle(self, *args, **options):
        user = User.objects.filter(email__iexact=OWNER_EMAIL).first()
        if user:
            self.stdout.write(
                self.style.WARNING(
                    f"Owner account {OWNER_EMAIL} already exists — nothing changed."
                )
            )
            return

        password = options.get("password") or self._generate_password()
        User.objects.create_superuser(
            email=OWNER_EMAIL,
            password=password,
            full_name="Gabriel Homes Owner",
        )
        self.stdout.write(self.style.SUCCESS(f"Owner account created: {OWNER_EMAIL}"))
        if options.get("quiet"):
            self.stdout.write("Password was set via --quiet run (not printed).")
        else:
            self.stdout.write(f"TEMP PASSWORD: {password}")
            self.stdout.write(
                "Sign in at /admin/ (Studio) or /account/login/, then change the "
                "password under Studio → CHANGE PASSWORD in the top-right menu."
            )

    @staticmethod
    def _generate_password() -> str:
        """Readable-but-strong temporary password (no ambiguous glyphs)."""
        alphabet = string.ascii_letters + string.digits
        # Groups of 4 separated by dashes — easy to read off a screen.
        groups = [
            "".join(secrets.choice(alphabet) for _ in range(4))
            for _ in range(4)
        ]
        return "GH-" + "-".join(groups)

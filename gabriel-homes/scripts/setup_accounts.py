"""One-time demo account setup — run via `manage.py shell < scripts/setup_accounts.py`.

Ensures, idempotently, in LOCAL DEVELOPMENT ONLY:
  1. A Django admin superuser:  admin@gabrielhomes.co.ke / gabriel2026
  2. A demo agent with a working login:  hello@gabrielhomes.co.ke / gabriel2026

Guards (PLAN task S4, defects D-CRED + D-LAUNCH):
  - Refuses to run when settings.DEBUG is False (production).
  - Sets a password only when it creates an account, or when the account has
    no usable password yet (a freshly seeded agent). It NEVER resets an
    existing password, so a password changed afterwards is never undone.
"""
from django.conf import settings

if not settings.DEBUG:
    raise SystemExit(
        "Refusing to run: scripts/setup_accounts.py creates demo accounts with "
        "well-known passwords and must only run in local development "
        "(settings.DEBUG is False). Use the admin to create production accounts."
    )

from apps.accounts.models import User  # noqa: E402  (after the DEBUG guard)

ADMIN_EMAIL = "admin@gabrielhomes.co.ke"
AGENT_EMAIL = "hello@gabrielhomes.co.ke"
DEMO_PASSWORD = "gabriel2026"

admin, admin_created = User.objects.get_or_create(
    email=ADMIN_EMAIL,
    defaults={
        "full_name": "Site Admin",
        "is_staff": True,
        "is_superuser": True,
    },
)
if admin_created:
    admin.set_password(DEMO_PASSWORD)
    admin.save()
    print(f"  Admin account created:  {ADMIN_EMAIL} / {DEMO_PASSWORD}")
else:
    promoted = False
    if not admin.is_superuser or not admin.is_staff:
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()
        promoted = True
    print(
        f"  Admin account exists ({'promoted to superuser' if promoted else 'password left unchanged'})."
    )

agent = User.objects.filter(is_agent=True).order_by("date_joined").first()
if agent is None:
    agent = User.objects.create(
        email=AGENT_EMAIL,
        full_name="Demo Agent",
        is_staff=True,
        is_agent=True,
    )
    agent.set_password(DEMO_PASSWORD)
    agent.save()
    print(f"  Demo agent login created: {agent.email} / {DEMO_PASSWORD}")
elif not agent.has_usable_password() or not agent.password:
    # Seeded agents start with an unusable password — set the initial demo
    # password. This is an initial set, not a reset of an existing password.
    # NB: an EMPTY password string (older seed versions created users via
    # User.objects.create without touching the password) also counts as
    # "not initialized" — check_password never matches it, and
    # has_usable_password() alone cannot detect it.
    agent.set_password(DEMO_PASSWORD)
    agent.is_staff = True
    agent.is_agent = True
    agent.save(update_fields=["password", "is_staff", "is_agent"])
    print(f"  Demo agent login initialized: {agent.email} / {DEMO_PASSWORD}")
else:
    print(f"  Demo agent login: {agent.email} (existing password left unchanged).")

print("  Account setup OK.")

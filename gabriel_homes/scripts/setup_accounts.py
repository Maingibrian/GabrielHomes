"""One-time demo account setup — run via `manage.py shell < scripts/setup_accounts.py`.

Ensures, idempotently:
  1. A Django admin superuser:  admin@gabrielhomes.co.ke / gabriel2026
  2. The first seeded agent has a known password: hello@gabrielhomes.co.ke / gabriel2026
     (seed_demo creates agents without usable passwords).

Safe to run on every start — it only creates/updates what is missing.
"""
from apps.accounts.models import User

ADMIN_EMAIL = "admin@gabrielhomes.co.ke"
AGENT_EMAIL = "hello@gabrielhomes.co.ke"
DEMO_PASSWORD = "gabriel2026"

admin, created = User.objects.get_or_create(
    email=ADMIN_EMAIL,
    defaults={
        "full_name": "Site Admin",
        "is_staff": True,
        "is_superuser": True,
    },
)
if created:
    admin.set_password(DEMO_PASSWORD)
    admin.save()
    print(f"  Admin account created:  {ADMIN_EMAIL} / {DEMO_PASSWORD}")
elif not admin.is_superuser or not admin.is_staff:
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()

agent = User.objects.filter(is_agent=True).order_by("date_joined").first()
if agent is not None:
    agent.set_password(DEMO_PASSWORD)
    agent.is_staff = True
    agent.is_agent = True
    agent.save(update_fields=["password", "is_staff", "is_agent"])
    print(f"  Demo agent login:       {agent.email} / {DEMO_PASSWORD}")
else:
    print("  (no agent account found yet — run seed_demo first)")

print("  Account setup OK.")

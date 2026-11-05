"""Rewrite seed agency bios that leaked demo wording to the live site.

The demo seeder originally wrote "<name> is a fictional agency seeded for
demo purposes." into every AgencyProfile.bio. That text is visible to
visitors on the About team cards and the agent profile pages — it must
never ship to a real site.

This migration replaces any bio still carrying the demo wording with
real-sounding agency copy (mirroring seed_demo.AGENCY_BIOS). Bios the
owner has customised are left untouched.

Runs automatically via `manage.py migrate` — which UPDATE-WEBSITE.bat
executes on every update — so deployed sites self-heal.
"""
from django.db import migrations

# slug -> bio (kept in sync with seed_demo.AGENCY_BIOS; inlined so the
# migration stays self-contained if the seeder is ever refactored).
REAL_BIOS = {
    "gabriel-homes": (
        "Our flagship Nyali office — curated homes across Mombasa with "
        "verified details, honest photography, and support beyond the keys."
    ),
    "coast-property-co": (
        "Bamburi-based agency covering Mombasa's north coast — apartments, "
        "townhouses, and gated estates from Nyali to Shanzu."
    ),
    "pwani-realty": (
        "Diani team handling beachfront homes, cottages, and short-stay "
        "investments along Kwale's south coast."
    ),
    "highlands-estates": (
        "Ruiru specialists in Nairobi's metropolitan north — gated "
        "communities, townhouses, and family homes across Kiambu."
    ),
    "ngong-ridge-properties": (
        "Ngong Hills specialists — family homes, farms, and gated estates "
        "along Kajiado's rising ridge."
    ),
    "mombasa-bay-realty": (
        "Mtwapa agency covering the creek and north coast — sea-view "
        "apartments, villas, and holiday lets."
    ),
}

DEMO_MARKERS = ("fictional agency", "demo purposes", "seeded for")


def fix_bios(apps, schema_editor):
    AgencyProfile = apps.get_model("agents", "AgencyProfile")
    for agency in AgencyProfile.objects.all():
        bio = agency.bio or ""
        if not any(marker in bio for marker in DEMO_MARKERS):
            continue  # owner-customised bio — leave it alone
        agency.bio = REAL_BIOS.get(
            agency.slug, f"{agency.name} — a Gabriel Homes partner agency."
        )
        agency.save(update_fields=["bio"])


class Migration(migrations.Migration):

    dependencies = [
        ("agents", "0002_alter_agencyprofile_logo"),
    ]

    operations = [
        migrations.RunPython(fix_bios, migrations.RunPython.noop),
    ]

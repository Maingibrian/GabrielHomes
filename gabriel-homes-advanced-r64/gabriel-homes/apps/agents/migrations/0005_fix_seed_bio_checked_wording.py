"""P0-2 follow-up: swap the last "verified" seed wording in agency bios.

Migration 0003 inlined a Gabriel Homes bio containing "verified details".
That migration already shipped, so this one self-heals any database that
ran it (fresh installs included) with a targeted, idempotent text swap.

Non-destructive: only rewrites bios containing the exact seeded phrase;
owner-customised bios are never touched. Reverse is a no-op.
"""
from django.db import migrations

OLD_PHRASE = "verified details"
NEW_PHRASE = "checked details"


def swap_verified_bio(bio: str) -> str:
    """Pure helper so tests can exercise the swap without migrations."""
    if not bio:
        return bio
    return bio.replace(OLD_PHRASE, NEW_PHRASE)


def fix_bios(apps, schema_editor):
    AgencyProfile = apps.get_model("agents", "AgencyProfile")
    for agency in AgencyProfile.objects.filter(bio__icontains=OLD_PHRASE):
        agency.bio = swap_verified_bio(agency.bio)
        agency.save(update_fields=["bio"])


class Migration(migrations.Migration):

    dependencies = [
        ("agents", "0004_agencyprofile_is_demo"),
    ]

    operations = [
        migrations.RunPython(fix_bios, migrations.RunPython.noop),
    ]

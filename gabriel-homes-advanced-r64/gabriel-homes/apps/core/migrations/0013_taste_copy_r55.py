"""r55 (owner request): taste-led copy for the brand rows.

The owner asked for language "about taste and unique special homes and
experiences one can get from the coast" — less about checked and verified
listings. The homepage hero subtitle and the footer lead were the two
most visible check-ledger lines left after the /about/ rewrite
(templates/core/about.html, r55).

Mirrors core.0011: only rows still carrying the r43-era values are
swapped, so deliberately-edited rows (manage portal) are left alone.
Fresh rows pick up the new defaults from models.py.
"""

from django.db import migrations

OLD_SUBTITLE = (
    "Buy, rent or book a short stay anywhere in Mombasa. Gabriel and "
    "the team check every listing before it goes live — and if we "
    "cannot check something, we tell you."
)
NEW_SUBTITLE = (
    "Buy, rent or book a short stay along the Kenyan coast — from "
    "sea-view apartments in Nyali to quiet villas in Shanzu. Every "
    "home here is one we have walked through ourselves."
)

OLD_FOOTER_LEAD = (
    "Homes for sale, rent and short stays across Mombasa, checked "
    "before they are published."
)
NEW_FOOTER_LEAD = (
    "Homes for sale, rent and short stays across Mombasa — chosen "
    "for character, from Nyali sea views to Old Town courtyards."
)

FIELDS = ("hero_subtitle", "footer_lead")
OLD = {"hero_subtitle": OLD_SUBTITLE, "footer_lead": OLD_FOOTER_LEAD}
NEW = {"hero_subtitle": NEW_SUBTITLE, "footer_lead": NEW_FOOTER_LEAD}


def _swap(apps, schema_editor, from_values, to_values):
    BrandSettings = apps.get_model("core", "BrandSettings")
    for brand in BrandSettings.objects.all():
        changed = False
        for field in FIELDS:
            if getattr(brand, field) == from_values[field]:
                setattr(brand, field, to_values[field])
                changed = True
        if changed:
            brand.save(update_fields=FIELDS)


def adopt_taste_copy(apps, schema_editor):
    _swap(apps, schema_editor, OLD, NEW)


def restore_previous_copy(apps, schema_editor):
    _swap(apps, schema_editor, NEW, OLD)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_alter_brandsettings_hero_heading_accent_and_more"),
    ]

    operations = [
        migrations.RunPython(adopt_taste_copy, restore_previous_copy),
    ]

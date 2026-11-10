"""r56 (owner round seven): comfort-led hero subtitle.

The owner: the site is "still talking about homes proven... rather
than comfort and the home feeling". The r55 subtitle closed on the
walked-through promise; r56 closes on the feeling instead — the
walked-through line now lives only on /checks/ and in the footer FAQ.

Mirrors core.0013: only rows still carrying the r55-era subtitle are
swapped, so deliberately-edited rows (manage portal) are left alone.
Fresh rows pick up the new default from models.py.
"""

from django.db import migrations, models

OLD_SUBTITLE = (
    "Buy, rent or book a short stay along the Kenyan coast — from "
    "sea-view apartments in Nyali to quiet villas in Shanzu. Every "
    "home here is one we have walked through ourselves."
)
NEW_SUBTITLE = (
    "Sea-view apartments in Nyali, garden homes in Bamburi, quiet "
    "villas in Shanzu — homes for sale, for rent, and for the weeks "
    "you wish would never end."
)

FIELD = "hero_subtitle"


def adopt_comfort_copy(apps, schema_editor):
    BrandSettings = apps.get_model("core", "BrandSettings")
    for brand in BrandSettings.objects.all():
        if getattr(brand, FIELD) == OLD_SUBTITLE:
            setattr(brand, FIELD, NEW_SUBTITLE)
            brand.save(update_fields=[FIELD])


def restore_previous_copy(apps, schema_editor):
    BrandSettings = apps.get_model("core", "BrandSettings")
    for brand in BrandSettings.objects.all():
        if getattr(brand, FIELD) == NEW_SUBTITLE:
            setattr(brand, FIELD, OLD_SUBTITLE)
            brand.save(update_fields=[FIELD])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_taste_copy_r55"),
    ]

    operations = [
        # Fresh installs pick up the new default from models.py; the
        # footer_lead AlterField clears the r55 default drift too.
        migrations.AlterField(
            model_name="brandsettings",
            name="hero_subtitle",
            field=models.TextField(
                default=(
                    "Sea-view apartments in Nyali, garden homes in Bamburi, "
                    "quiet villas in Shanzu — homes for sale, for rent, and "
                    "for the weeks you wish would never end."
                ),
                max_length=500,
            ),
        ),
        migrations.AlterField(
            model_name="brandsettings",
            name="footer_lead",
            field=models.CharField(
                default=(
                    "Homes for sale, rent and short stays across Mombasa — "
                    "chosen for character, from Nyali sea views to Old Town "
                    "courtyards."
                ),
                max_length=220,
            ),
        ),
        migrations.RunPython(adopt_comfort_copy, restore_previous_copy),
    ]

"""r11 — AgencyProfile.is_demo stamp for seeded placeholder agencies.

Same two-step pattern as listings.0006: backfill existing rows to True
(all pre-r11 agencies are seeded), then flip the default to False for
agencies created from now on.
"""
from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agents", "0003_fix_seed_agency_bios"),
    ]

    operations = [
        migrations.AddField(
            model_name="agencyprofile",
            name="is_demo",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="agencyprofile",
            name="is_demo",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text=(
                    "Seeded placeholder agency. Hidden from the public site "
                    "while the owner's demo switch is off-position (hide "
                    "demo data)."
                ),
            ),
        ),
    ]

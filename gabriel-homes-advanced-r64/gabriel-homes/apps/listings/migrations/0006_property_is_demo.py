"""r11 — Property.is_demo stamp for seeded placeholder content.

Two-step backfill: the field is added with default=True (every pre-r11
row is seed_demo content, so it must be stamped demo), then the default
is altered to False so listings created from now on (dashboard, admin,
CSV import) are real by default. The final AlterField matches the model
definition exactly.
"""
from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0005_set_nyali_listing_coords"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="is_demo",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="property",
            name="is_demo",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text=(
                    "Seeded placeholder content. Hidden from the public site "
                    "while the owner's demo switch is off-position (hide "
                    "demo data)."
                ),
            ),
        ),
    ]

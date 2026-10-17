"""r11 — SiteSetting singleton (owner switches).

The row is created lazily by SiteSetting.load(); this migration only
creates the table.
"""
from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SiteSetting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "hide_demo_data",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Public site: hide all content stamped as demo "
                            "(seeded agencies and listings). Dashboards and "
                            "admin still see everything."
                        ),
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "site setting",
                "verbose_name_plural": "site settings",
            },
        ),
    ]

"""Heal seeded listing descriptions still phrased for the agent era.

P1-3 (single-owner mode): seed_demo's description template used to end
with "Contact the listing agent to arrange a viewing." — the site has no
listing agents any more. This migration rewrites that sentence to the
single-owner phrasing on rows that (a) carry the demo stamp and (b) still
contain the exact old sentence, so it is idempotent and can never touch
owner-authored descriptions on real (non-demo) rows. Reverse is a no-op:
never delete or regress data (protocol §4).
"""
from django.db import migrations

OLD_SENTENCE = "Contact the listing agent to arrange a viewing."
NEW_SENTENCE = "Contact Gabriel Homes directly to arrange a viewing."


def heal_description(description: str) -> str:
    """Pure helper so tests can exercise the swap without migrations."""
    if not description:
        return description
    return description.replace(OLD_SENTENCE, NEW_SENTENCE)


def heal_seed_phrasing(apps, schema_editor):
    if apps is not None:
        Property = apps.get_model("listings", "Property")
    else:
        # Direct call from tests (no historical-apps registry available).
        from apps.listings import models as listings_models

        Property = listings_models.Property
    qs = Property.objects.filter(is_demo=True, description__contains=OLD_SENTENCE)
    for prop in qs.iterator():
        prop.description = heal_description(prop.description)
        prop.save(update_fields=["description"])


def unheal_seed_phrasing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0007_portable_cover_constraint"),
    ]

    operations = [
        migrations.RunPython(heal_seed_phrasing, unheal_seed_phrasing),
    ]

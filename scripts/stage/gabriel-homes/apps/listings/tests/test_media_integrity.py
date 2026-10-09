"""C1 — media integrity: every DB-referenced image must exist on disk.

Complements scripts/list_unused_media.py, which lists the opposite
(files on disk that no row references — those may only be archived
after the owner confirms, PLAN O2).
"""
import pytest
from django.core.management import call_command

from apps.agents.models import AgencyProfile
from apps.listings.models import PropertyImage

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=False, target=10, verbosity=0,
                 i_know_this_is_demo=True)


def test_every_property_image_row_resolves_to_a_file(settings):
    missing = []
    for img in PropertyImage.objects.exclude(image=""):
        if not img.image.storage.exists(img.image.name):
            missing.append(img.image.name)
    assert missing == [], f"DB rows pointing at missing files: {missing}"


def test_every_agency_logo_resolves_to_a_file(settings):
    missing = []
    for profile in AgencyProfile.objects.exclude(logo=""):
        if not profile.logo.storage.exists(profile.logo.name):
            missing.append(profile.logo.name)
    assert missing == [], f"Agency logos pointing at missing files: {missing}"


def test_seed_with_images_actually_created_image_rows():
    # Guard for the fixture itself: if seeding stops creating images this
    # module would silently test nothing.
    assert PropertyImage.objects.count() > 0

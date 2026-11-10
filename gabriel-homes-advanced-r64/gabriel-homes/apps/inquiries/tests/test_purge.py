"""C3 — inquiry data retention: purge_inquiries command tests."""
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.inquiries.models import Inquiry

pytestmark = pytest.mark.django_db


@pytest.fixture
def inquiries_old_and_new(db):
    """One 400-day-old inquiry, one fresh one, on a real seeded listing."""
    from django.core.management import call_command as cc
    cc("seed_demo", no_images=True, target=5, verbosity=0,
       i_know_this_is_demo=True)
    prop = Inquiry._meta.get_field("property_ref").related_model.objects.first()
    old = Inquiry.objects.create(
        property_ref=prop, name="Old Timer", email="old@example.com",
        message="ancient enquiry",
    )
    fresh = Inquiry.objects.create(
        property_ref=prop, name="New Wave", email="new@example.com",
        message="recent enquiry",
    )
    # created_at is auto_now_add — backdate the old row via queryset update.
    Inquiry.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - timedelta(days=400)
    )
    return old, fresh


def test_purge_deletes_only_inquiries_older_than_365_days(inquiries_old_and_new):
    old, fresh = inquiries_old_and_new
    call_command("purge_inquiries", verbosity=0)
    assert not Inquiry.objects.filter(pk=old.pk).exists()
    assert Inquiry.objects.filter(pk=fresh.pk).exists()


def test_purge_respects_custom_days_window(inquiries_old_and_new):
    old, fresh = inquiries_old_and_new
    call_command("purge_inquiries", days=500, verbosity=0)
    # 400 days < 500-day window — nothing is deleted.
    assert Inquiry.objects.filter(pk=old.pk).exists()


def test_purge_dry_run_deletes_nothing(inquiries_old_and_new, capsys):
    old, fresh = inquiries_old_and_new
    call_command("purge_inquiries", dry_run=True, verbosity=0)
    assert Inquiry.objects.filter(pk=old.pk).exists()
    assert Inquiry.objects.filter(pk=fresh.pk).exists()
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "1" in out


def test_purge_refuses_days_below_one():
    with pytest.raises(SystemExit):
        call_command("purge_inquiries", days=0, verbosity=0)


def test_purge_reports_deleted_count(inquiries_old_and_new, capsys):
    call_command("purge_inquiries", verbosity=0)
    out = capsys.readouterr().out
    assert "Deleted 1" in out

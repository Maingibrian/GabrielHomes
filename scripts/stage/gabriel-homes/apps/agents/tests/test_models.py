"""Tests for the AgencyProfile model (apps.agents)."""
import pytest

from apps.accounts.models import User
from apps.agents.models import AgencyProfile

pytestmark = pytest.mark.django_db


def test_agency_slug_auto_generated():
    user = User.objects.create_user(email="a@example.com", password="x", is_agent=True)
    agency = AgencyProfile.objects.create(user=user, name="Gabriel Homes")
    assert agency.slug == "gabriel-homes"


def test_agency_slug_deduplicated():
    user1 = User.objects.create_user(email="a1@example.com", password="x", is_agent=True)
    user2 = User.objects.create_user(email="a2@example.com", password="x", is_agent=True)
    AgencyProfile.objects.create(user=user1, name="Coast Property Co.")
    agency2 = AgencyProfile.objects.create(user=user2, name="Coast Property Co.")
    assert agency2.slug != "coast-property-co"
    assert agency2.slug.startswith("coast-property-co-")


def test_display_whatsapp_strips_non_digits():
    user = User.objects.create_user(email="a@example.com", password="x", is_agent=True)
    agency = AgencyProfile.objects.create(
        user=user, name="Test", whatsapp="+254 (712) 345-678",
    )
    assert agency.display_whatsapp == "254712345678"


def test_display_phone_falls_back_to_user_phone():
    user = User.objects.create_user(
        email="a@example.com", password="x", is_agent=True, phone="+254700000000",
    )
    agency = AgencyProfile.objects.create(user=user, name="Test", phone="")
    assert agency.display_phone == "+254700000000"


def test_display_email_falls_back_to_user_email():
    user = User.objects.create_user(email="agency@example.com", password="x", is_agent=True)
    agency = AgencyProfile.objects.create(user=user, name="Test", email="")
    assert agency.display_email == "agency@example.com"

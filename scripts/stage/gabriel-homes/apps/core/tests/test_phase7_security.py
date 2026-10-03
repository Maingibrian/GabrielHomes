"""Tests for Phase 7 — security hardening: upload validation,
rate limiting, deploy check."""
import io
import os

import pytest
from django.core.management import call_command
from django.test import Client, override_settings

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=20, verbosity=0)
    yield


# ---------------------------------------------------------------------------
# Upload validation
# ---------------------------------------------------------------------------
def _make_image(size_bytes: int = 1024, ext: str = ".jpg", content_type: str = "image/jpeg"):
    """Create a SimpleUploadedFile with a fake image of the given size."""
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "JPEG")
    img_bytes = buf.getvalue()
    # Pad to the requested size
    if size_bytes > len(img_bytes):
        img_bytes = img_bytes + (b"\x00" * (size_bytes - len(img_bytes)))
    return SimpleUploadedFile(f"test{ext}", img_bytes[:size_bytes], content_type=content_type)


def test_image_validator_rejects_oversized_file():
    """Images > 10 MB should be rejected."""
    from apps.listings.models import validate_image_file
    from django.core.exceptions import ValidationError

    big_image = _make_image(size_bytes=11 * 1024 * 1024)  # 11 MB
    with pytest.raises(ValidationError, match="too large"):
        validate_image_file(big_image)


def test_image_validator_accepts_normal_size():
    from apps.listings.models import validate_image_file
    normal_image = _make_image(size_bytes=1024)  # 1 KB
    validate_image_file(normal_image)  # should not raise


def test_image_validator_rejects_wrong_extension():
    from apps.listings.models import validate_image_file
    from django.core.exceptions import ValidationError

    bad_ext = _make_image(ext=".gif", content_type="image/gif")
    with pytest.raises(ValidationError, match="Unsupported file type"):
        validate_image_file(bad_ext)


def test_image_validator_rejects_wrong_content_type():
    from apps.listings.models import validate_image_file
    from django.core.exceptions import ValidationError

    bad_mime = _make_image(ext=".jpg", content_type="application/pdf")
    with pytest.raises(ValidationError, match="Unsupported content type"):
        validate_image_file(bad_mime)


def test_image_validator_accepts_webp():
    from apps.listings.models import validate_image_file
    webp_image = _make_image(ext=".webp", content_type="image/webp")
    validate_image_file(webp_image)  # should not raise


def test_property_image_model_uses_validator():
    """The PropertyImage.image field should have the validator attached."""
    from apps.listings.models import PropertyImage
    validators = PropertyImage._meta.get_field("image").validators
    from apps.listings.models import validate_image_file
    assert any(v == validate_image_file for v in validators)


def test_agency_logo_model_uses_validator():
    from apps.agents.models import AgencyProfile
    from apps.listings.models import validate_image_file
    validators = AgencyProfile._meta.get_field("logo").validators
    assert any(v == validate_image_file for v in validators)


# ---------------------------------------------------------------------------
# Rate limiting on auth
# ---------------------------------------------------------------------------
def test_login_rate_limit_blocks_after_5_attempts():
    """After 5 failed login attempts, the 6th should be rate-limited."""
    from django.core.cache import cache
    cache.clear()
    c = Client()
    for i in range(5):
        r = c.post("/account/login/", {
            "email": f"nonexistent{i}@test.com",
            "password": "wrongpass",
        })
        # 200 = form re-rendered with errors (login failed but not rate-limited)
        assert r.status_code == 200
    # 6th attempt should be rate-limited (allauth raises PermissionDenied → 403)
    r = c.post("/account/login/", {
        "email": "nonexistent@test.com",
        "password": "wrongpass",
    })
    assert r.status_code in (403, 429)


def test_login_get_is_never_rate_limited():
    """GETs (page views) must never count toward the auth rate limit.

    Regression: previously the limiter metered every method, so reloading
    the login form 5+ times in a minute returned a bare 429 and the user
    could not even see the form. Brute force happens on POST only.
    """
    from django.core.cache import cache
    cache.clear()
    c = Client()
    for _ in range(10):
        r = c.get("/account/login/")
        assert r.status_code == 200
    # A POST after many GETs is still metered correctly (GETs added nothing).
    for _ in range(5):
        r = c.post("/account/login/", {
            "email": "nonexistent-x@test.com",
            "password": "wrongpass",
        })
        assert r.status_code == 200
    r = c.post("/account/login/", {
        "email": "nonexistent-x@test.com",
        "password": "wrongpass",
    })
    assert r.status_code in (403, 429)


# ---------------------------------------------------------------------------
# check --deploy
# ---------------------------------------------------------------------------
def test_check_deploy_is_clean_with_prod_settings():
    """check --deploy should report 0 issues with prod settings + proper env."""
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
    env["SECRET_KEY"] = "a-proper-secret-key-with-at-least-50-characters-for-production-use-12345"
    env["ALLOWED_HOSTS"] = "localhost"
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        capture_output=True, text=True, env=env, cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    combined = result.stdout + result.stderr
    assert "no issues" in combined.lower() or "0 issues" in combined, (
        f"check --deploy has warnings:\n{combined}"
    )


def test_check_deploy_warns_on_debug_true():
    """check --deploy should warn when DEBUG=True (dev settings)."""
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        capture_output=True, text=True, env=env, cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    combined = result.stdout + result.stderr
    assert "W018" in combined or "DEBUG" in combined.upper(), (
        f"Expected DEBUG warning in:\n{combined}"
    )


# ---------------------------------------------------------------------------
# CSRF protection
# ---------------------------------------------------------------------------
def test_enquiry_requires_csrf_token():
    """POST without a CSRF token should be rejected (403)."""
    from apps.listings.models import Property
    p = Property.objects.published().first()
    # Use a client that enforces CSRF
    c = Client(enforce_csrf_checks=True)
    r = c.post(f"/listing/{p.slug}-{p.pk}/enquire/", {
        "name": "Test",
        "email": "test@test.com",
        "message": "This is a test message for the enquiry.",
    })
    assert r.status_code == 403


def test_save_requires_csrf_token():
    from apps.listings.models import Property
    from apps.accounts.models import User
    p = Property.objects.published().first()
    user = User.objects.create_user(email="user@test.com", password="pass123!")
    c = Client(enforce_csrf_checks=True)
    c.force_login(user)
    r = c.post(f"/account/save/{p.pk}/")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DEBUG = False in prod settings
# ---------------------------------------------------------------------------
def test_prod_settings_have_debug_false():
    from django.conf import settings
    import importlib
    # Load prod settings module directly
    prod = importlib.import_module("config.settings.prod")
    assert prod.DEBUG is False


def test_prod_settings_have_secure_cookies():
    import importlib
    prod = importlib.import_module("config.settings.prod")
    assert prod.SESSION_COOKIE_SECURE is True
    assert prod.CSRF_COOKIE_SECURE is True


def test_prod_settings_have_hsts():
    import importlib
    prod = importlib.import_module("config.settings.prod")
    assert prod.SECURE_HSTS_SECONDS > 0
    assert prod.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
    assert prod.SECURE_HSTS_PRELOAD is True


# ---------------------------------------------------------------------------
# .env.example has a proper secret key placeholder
# ---------------------------------------------------------------------------
def test_env_example_has_long_secret_key_placeholder():
    """The .env.example should show that SECRET_KEY needs 50+ chars."""
    import pathlib
    # Path: apps/core/tests/test_phase7_security.py -> ../../.env.example
    env_example = pathlib.Path(__file__).resolve().parent.parent.parent.parent / ".env.example"
    content = env_example.read_text()
    assert "SECRET_KEY" in content
    assert "50" in content or "get_random_secret_key" in content, (
        ".env.example should mention 50+ chars or how to generate a key"
    )

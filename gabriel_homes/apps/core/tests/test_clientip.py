"""S2 / defect D-RL: rate limiting must use the real client IP.

The first X-Forwarded-For entry is fully client-controlled — an attacker
rotates it to get a fresh rate-limit bucket per request. Behind production
nginx (D4 adds `proxy_set_header X-Real-IP $remote_addr;`), X-Real-IP is
set by our own proxy from the socket address and is trusted ONLY when the
TRUST_X_REAL_IP setting is on. X-Forwarded-For is never read here.
"""
import pytest
from django.core.management import call_command
from django.test import Client, override_settings

pytestmark = pytest.mark.django_db

ROTATING_XFF = [f"203.0.113.{i}" for i in range(1, 12)]


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


def _get_first_listing():
    from apps.listings.models import Property
    return Property.objects.published().first()


def _enquiry_url(p):
    return f"/listing/{p.slug}-{p.pk}/enquire/"


def _enquiry_data(email):
    return {
        "name": "Jane Doe",
        "email": email,
        "phone": "+254712345678",
        "message": "I am interested in viewing this property next week.",
        "website": "",  # honeypot — empty
    }


# ---------------------------------------------------------------------------
# Unit tests for get_client_ip
# ---------------------------------------------------------------------------
def test_get_client_ip_ignores_xff_when_not_trusted():
    from apps.core.clientip import get_client_ip
    from django.test import RequestFactory
    rf = RequestFactory()
    req = rf.get("/", REMOTE_ADDR="198.51.100.1", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
    assert get_client_ip(req) == "198.51.100.1"


@override_settings(TRUST_X_REAL_IP=True)
def test_get_client_ip_prefers_x_real_ip_when_trusted():
    from apps.core.clientip import get_client_ip
    from django.test import RequestFactory
    rf = RequestFactory()
    req = rf.get(
        "/",
        REMOTE_ADDR="198.51.100.1",
        HTTP_X_REAL_IP="198.51.100.9",
        HTTP_X_FORWARDED_FOR="1.2.3.4",
    )
    assert get_client_ip(req) == "198.51.100.9"


def test_get_client_ip_falls_back_to_remote_addr():
    from apps.core.clientip import get_client_ip
    from django.test import RequestFactory
    rf = RequestFactory()
    req = rf.get("/", REMOTE_ADDR="198.51.100.2")  # no X-Real-IP, not trusted
    assert get_client_ip(req) == "198.51.100.2"


# ---------------------------------------------------------------------------
# Enquiry limiter (DB-backed, 3/min per IP)
# ---------------------------------------------------------------------------
def test_rotating_xff_does_not_reset_enquiry_limit():
    """(a) With TRUST_X_REAL_IP off, rotating X-Forwarded-For must not buy
    a fresh bucket: the 4th enquiry is still blocked."""
    p = _get_first_listing()
    c = Client()
    for i in range(3):
        r = c.post(
            _enquiry_url(p),
            _enquiry_data(f"rl-a{i}@example.com"),
            REMOTE_ADDR="198.51.100.7",
            HTTP_X_FORWARDED_FOR=ROTATING_XFF[i],
        )
        assert r.status_code == 200, f"enquiry {i + 1} should pass"
    r = c.post(
        _enquiry_url(p),
        _enquiry_data("rl-a3@example.com"),
        REMOTE_ADDR="198.51.100.7",
        HTTP_X_FORWARDED_FOR=ROTATING_XFF[10],  # fresh forged IP
    )
    assert r.status_code == 429


@override_settings(TRUST_X_REAL_IP=True)
def test_x_real_ip_determines_enquiry_bucket_when_trusted():
    """(b) When trusted, X-Real-IP defines the bucket: same X-Real-IP from
    two different socket addresses hits the same limit."""
    p = _get_first_listing()
    c = Client()
    for i in range(3):
        r = c.post(
            _enquiry_url(p),
            _enquiry_data(f"rl-b{i}@example.com"),
            REMOTE_ADDR="198.51.100.8",
            HTTP_X_REAL_IP="198.51.100.99",
        )
        assert r.status_code == 200, f"enquiry {i + 1} should pass"
    r = c.post(
        _enquiry_url(p),
        _enquiry_data("rl-b3@example.com"),
        REMOTE_ADDR="198.51.100.9",  # different socket address…
        HTTP_X_REAL_IP="198.51.100.99",  # …same X-Real-IP bucket
    )
    assert r.status_code == 429


# ---------------------------------------------------------------------------
# Auth limiter (cache-backed, 5 POSTs/min per IP+path)
# ---------------------------------------------------------------------------
def test_login_rate_limit_ignores_rotating_xff():
    """(c) Six logins from one socket address with rotating X-Forwarded-For
    values: the 6th must be 429 (fresh forged IPs must not reset the bucket)."""
    from django.core.cache import cache
    cache.clear()
    c = Client()
    for i in range(5):
        r = c.post(
            "/account/login/",
            {"email": f"brute-a{i}@test.com", "password": "wrongpass"},
            REMOTE_ADDR="198.51.100.10",
            HTTP_X_FORWARDED_FOR=ROTATING_XFF[i],
        )
        assert r.status_code == 200, f"attempt {i + 1} should not be limited yet"
    r = c.post(
        "/account/login/",
        {"email": "brute-a9@test.com", "password": "wrongpass"},
        REMOTE_ADDR="198.51.100.10",
        HTTP_X_FORWARDED_FOR=ROTATING_XFF[10],  # fresh forged IP
    )
    assert r.status_code == 429

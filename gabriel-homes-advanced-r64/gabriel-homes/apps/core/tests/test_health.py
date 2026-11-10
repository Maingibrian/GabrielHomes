"""D3 — /healthz/ health check.

Spec (docs/PLAN.md D3):
  * 200 {"status": "ok"} when the DB answers SELECT 1.
  * 503 {"status": "unavailable"} when the DB cursor raises.
  * The response contains no further details.
"""
from unittest import mock

import pytest
from django.core.management import call_command
from django.db import InterfaceError
from django.test import Client

pytestmark = pytest.mark.django_db


def test_healthz_returns_200_when_db_reachable():
    r = Client().get("/healthz/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_healthz_returns_503_when_db_raises():
    with mock.patch("apps.core.views.connection.cursor",
                    side_effect=InterfaceError("connection already closed")):
        r = Client().get("/healthz/")
    assert r.status_code == 503
    assert r.json() == {"status": "unavailable"}


def test_healthz_leaks_no_details_on_failure():
    with mock.patch("apps.core.views.connection.cursor",
                    side_effect=InterfaceError("secret-dsn-detail-leak")):
        body = Client().get("/healthz/").content.decode()
    assert "secret-dsn-detail-leak" not in body
    assert "InterfaceError" not in body


def test_healthz_does_not_csp_break(monkeypatch):
    """Sanity: the health endpoint rides through the full middleware stack."""
    r = Client().get("/healthz/")
    assert "Content-Security-Policy" in r.headers

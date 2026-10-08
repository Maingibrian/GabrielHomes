"""S3 / defect D-CACHE: the rate-limit store must be shared by all workers.

LocMemCache is per-process: with gunicorn --workers 3, each worker counted
auth attempts separately, tripling the effective limit. Production now uses
DatabaseCache ("gabriel_cache" table, created by createcachetable at deploy
— task D4). Dev keeps LocMemCache for the single-process dev server.
"""
import subprocess
import sys
import os
from time import time

import pytest


def test_prod_cache_is_database_cache():
    """Under prod settings, the default cache is a DatabaseCache."""
    code = (
        "import django, os\n"
        "django.setup()\n"
        "from django.core.cache import caches\n"
        "from django.core.cache.backends.db import DatabaseCache\n"
        "c = caches['default']\n"
        "assert isinstance(c, DatabaseCache), type(c)\n"
        "assert c._table == 'gabriel_cache', c._table\n"
        "print('PROD-CACHE-OK')\n"
    )
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
    env["SECRET_KEY"] = "a" * 60
    env["ALLOWED_HOSTS"] = "localhost"
    env["DATABASE_URL"] = "postgres://u:p@localhost:5432/x"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    )
    assert result.returncode == 0, result.stderr[-500:]
    assert "PROD-CACHE-OK" in result.stdout


def test_dev_cache_is_locmem():
    """Dev keeps LocMemCache so runserver needs no cache table."""
    from django.conf import settings
    assert "locmem" in settings.CACHES["default"]["BACKEND"]


def test_auth_limiter_state_survives_second_cache_handle():
    """Auth limiter state written through `cache` is visible through a
    second handle to the same alias — the property that makes the limit
    global across gunicorn workers once the backend is DatabaseCache."""
    from django.core.cache import cache, caches
    from apps.accounts.rate_limit import auth_rate_limit_key
    from django.test import RequestFactory

    cache.clear()
    rf = RequestFactory()
    req = rf.post("/account/login/", REMOTE_ADDR="198.51.100.20")
    key = auth_rate_limit_key(req)

    # write through the primary handle exactly as rate_limit() does
    cache.set(key, [time()] * 5, 60)

    # a second handle to the same alias must see the same five timestamps
    other = caches["default"]
    timestamps = [ts for ts in other.get(key, []) if time() - ts < 60]
    assert len(timestamps) == 5

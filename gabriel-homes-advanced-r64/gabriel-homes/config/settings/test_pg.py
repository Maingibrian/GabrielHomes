"""Test-only settings: run the suite against PostgreSQL (PLAN D2).

dev.py deliberately forces SQLite. This module lets the full test suite run
against a real PostgreSQL without touching dev or prod settings. It is used
ONLY via the environment, never as a project default:

    # Brian's machine (PLAN O11) — one command:
    GABRIEL_TEST_DB_URL=postgres://postgres:postgres@localhost:5432/gabriel_test \
        DJANGO_SETTINGS_MODULE=config.settings.test_pg \
        .venv/bin/python -m pytest -q

The suite must pass identically on SQLite and PostgreSQL before launch
(exit criterion C3). Local fix-its for PG-specific behaviour (case
sensitivity, NULL ordering) belong here or in the models, not dev.py.
"""
from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]

# Never trust proxy headers in tests.
TRUST_X_REAL_IP = False

import os  # noqa: E402
import re  # noqa: E402

from django.core.exceptions import ImproperlyConfigured  # noqa: E402

TEST_DB_URL = os.environ.get("GABRIEL_TEST_DB_URL", "")
if not TEST_DB_URL.startswith("postgres://"):
    raise ImproperlyConfigured(
        "config.settings.test_pg requires GABRIEL_TEST_DB_URL, e.g. "
        "postgres://postgres:postgres@localhost:5432/gabriel_test"
    )

# Parse postgres://user:password@host:port/dbname
_m = re.match(
    r"postgres://(?P<user>[^:]+):(?P<pw>[^@]*)@"
    r"(?P<host>[^:/]+):(?P<port>\d+)/(?P<name>[\w.-]+)",
    TEST_DB_URL,
)
if not _m:
    raise ImproperlyConfigured(f"Unparseable GABRIEL_TEST_DB_URL: {TEST_DB_URL!r}")
_creds = _m.groupdict()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _creds["name"],
        "USER": _creds["user"],
        "PASSWORD": _creds["pw"],
        "HOST": _creds["host"],
        "PORT": _creds["port"],
        # pytest-django creates/destroys test_<NAME>; the DB itself only
        # needs to exist so Django can connect to it for the check.
        "TEST": {"NAME": f"test_{_creds['name']}"},
    }
}

# Prod-style cache backend so rate-limit tests exercise the same code path
# as production (DatabaseCache table is created by pytest-django via
# migrations/runners as needed).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "gabriel_cache",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

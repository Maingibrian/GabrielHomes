"""Test-only settings: run the suite against MariaDB.

Mirrors test_pg.py. Used only via the environment, never as a project default:

    GABRIEL_TEST_DB_URL=mysql://gabriel:password@localhost:3306/gabriel \
        DJANGO_SETTINGS_MODULE=config.settings.test_mariadb \
        python -m pytest -q

The database named in the URL must exist. The suite uses test_<name>, which
pytest-django creates and drops it; the user needs rights on test_<name>.
"""
from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
TRUST_X_REAL_IP = False

import os  # noqa: E402
import re  # noqa: E402

from django.core.exceptions import ImproperlyConfigured  # noqa: E402

TEST_DB_URL = os.environ.get("GABRIEL_TEST_DB_URL", "")
if not TEST_DB_URL.startswith("mysql://"):
    raise ImproperlyConfigured(
        "config.settings.test_mariadb requires GABRIEL_TEST_DB_URL, e.g. "
        "mysql://gabriel:password@localhost:3306/gabriel"
    )

_m = re.match(
    r"mysql://(?P<user>[^:]+):(?P<pw>[^@]*)@"
    r"(?P<host>[^:/]+):(?P<port>\d+)/(?P<name>[\w.-]+)",
    TEST_DB_URL,
)
if not _m:
    raise ImproperlyConfigured(f"Unparseable GABRIEL_TEST_DB_URL: {TEST_DB_URL!r}")
_c = _m.groupdict()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": _c["name"],
        "USER": _c["user"],
        "PASSWORD": _c["pw"],
        "HOST": _c["host"],
        "PORT": _c["port"],
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'",
        },
        "TEST": {
            "NAME": f"test_{_c['name']}",
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

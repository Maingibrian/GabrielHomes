"""S5 / defects D-KEY + D-DB: production refuses unsafe configuration.

Under config.settings.prod, Django must refuse to start when:
  - SECRET_KEY is missing, starts with the dev default, or is < 50 chars
  - ALLOWED_HOSTS is empty
  - DATABASE_URL is empty or not a postgres:// URL (SQLite is dev-only)

Each case runs a subprocess that imports the prod settings with a bad
environment and asserts a non-zero exit and the expected message. One final
subprocess with a good environment must succeed (so `make deploy-check`,
task D6, keeps working with a dummy postgres URL).
"""
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

GOOD_KEY = "x" * 60
GOOD_ENV = {
    "SECRET_KEY": GOOD_KEY,
    "ALLOWED_HOSTS": "example.com",
    "DATABASE_URL": "postgres://u:p@localhost:5432/x",
}

BAD_CASES = [
    ({}, "SECRET_KEY"),
    ({"SECRET_KEY": "dev-insecure-key-change-me"}, "SECRET_KEY"),
    ({"SECRET_KEY": "too-short"}, "SECRET_KEY"),
    ({"SECRET_KEY": GOOD_KEY}, "ALLOWED_HOSTS"),
    ({"SECRET_KEY": GOOD_KEY, "ALLOWED_HOSTS": "example.com"}, "DATABASE_URL"),
    (
        {"SECRET_KEY": GOOD_KEY, "ALLOWED_HOSTS": "example.com",
         "DATABASE_URL": "sqlite:///db.sqlite3"},
        "mysql",
    ),
]


def _run_prod_import(overrides):
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
    env.pop("SECRET_KEY", None)
    env.pop("ALLOWED_HOSTS", None)
    env.pop("DATABASE_URL", None)
    # Hermetic: a developer's repo-root .env must not fill in for the
    # popped vars inside the subprocess under test.
    env["GABRIEL_SKIP_DOTENV"] = "1"
    env.update(overrides)
    return subprocess.run(
        [sys.executable, "-c", "import django; django.setup(); print('IMPORT-OK')"],
        capture_output=True, text=True, env=env, cwd=REPO_ROOT,
    )


@pytest.mark.parametrize("overrides,expected", BAD_CASES, ids=[
    "missing-key", "dev-key", "short-key", "empty-hosts", "empty-db", "non-mysql-db",
])
def test_prod_refuses_bad_configuration(overrides, expected):
    result = _run_prod_import(overrides)
    assert result.returncode != 0
    assert expected in (result.stdout + result.stderr), (result.stdout + result.stderr)[-300:]


def test_prod_starts_with_good_configuration():
    result = _run_prod_import(GOOD_ENV)
    assert result.returncode == 0, result.stderr[-500:]
    assert "IMPORT-OK" in result.stdout

"""S6 / defect D-STATIC: hashed static files must actually be active.

Django 5.1 removed the STATICFILES_STORAGE setting — setting it in base.py
was a silent no-op, so static files were served unhashed while nginx cached
them as immutable for a year. The STORAGES dict is the replacement:
  - prod: whitenoise CompressedManifestStaticFilesStorage (hashed names)
  - dev:  plain StaticFilesStorage so runserver needs no collectstatic
"""
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def test_dev_uses_plain_staticfiles_storage():
    """The test suite (dev settings) must stay on plain storage."""
    from django.conf import settings
    assert (
        settings.STORAGES["staticfiles"]["BACKEND"]
        == "django.contrib.staticfiles.storage.StaticFilesStorage"
    )


def test_prod_uses_manifest_storage_and_hashes_filenames():
    """Under prod settings, staticfiles_storage is whitenoise manifest
    storage, and collectstatic emits hashed filenames into STATIC_ROOT."""
    import tempfile

    tmp_static = tempfile.mkdtemp()
    code = (
        "import django, os\n"
        "django.setup()\n"
        "from django.contrib.staticfiles.storage import staticfiles_storage\n"
        "from whitenoise.storage import CompressedManifestStaticFilesStorage\n"
        "assert isinstance(staticfiles_storage, CompressedManifestStaticFilesStorage), type(staticfiles_storage)\n"
        "from django.core.management import call_command\n"
        "call_command('collectstatic', interactive=False, verbosity=0)\n"
        "import json, os\n"
        "with open(os.path.join(os.environ['STATIC_ROOT'], 'staticfiles.json')) as fh:\n"
        "    paths = json.load(fh)['paths']\n"
        "hashed = {k: v for k, v in paths.items() if v != k}\n"
        "assert hashed, 'no hashed filenames in static manifest'\n"
        "print('HASHED-OK')\n"
    )
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
    env["SECRET_KEY"] = "x" * 60
    env["ALLOWED_HOSTS"] = "example.com"
    env["DATABASE_URL"] = "postgres://u:p@localhost:5432/x"
    env["STATIC_ROOT"] = tmp_static
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr[-600:]
    assert "HASHED-OK" in result.stdout


def test_base_settings_no_longer_set_removed_setting():
    """base.py must not set the removed STATICFILES_STORAGE (no-op in 5.1)."""
    import pathlib
    base = (
        pathlib.Path(REPO_ROOT) / "config" / "settings" / "base.py"
    ).read_text()
    assert "STATICFILES_STORAGE =" not in base

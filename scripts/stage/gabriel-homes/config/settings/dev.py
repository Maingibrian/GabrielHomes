"""Dev settings — local development only."""
from .base import *  # noqa: F401, F403
from .base import BASE_DIR, TEMPLATES

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]

# WORK.md: SQLite allowed in local dev only. Always force SQLite here so a
# stray DATABASE_URL in the surrounding environment does not surprise us.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Use plain StaticFilesStorage in dev so runserver reloads CSS without manifest.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Verbose emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Show template file names in errors for easier debugging
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

# django-debug-toolbar style niceties without the dependency
INTERNAL_IPS = ["127.0.0.1"]

"""Dev settings — local development only."""
from .base import *  # noqa: F401, F403
from .base import BASE_DIR, TEMPLATES, env

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"] + env.list(
    "EXTRA_ALLOWED_HOSTS", default=[]
)
# The workspace live-preview proxy presents its own public origin; without
# this the enquiry form would 403 on CSRF. Empty by default, so plain local
# runs are unaffected.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# D-RL (PLAN S2): dev never trusts X-Real-IP (no trusted proxy locally).
TRUST_X_REAL_IP = False

# WORK.md: SQLite allowed in local dev only. Always force SQLite here so a
# stray DATABASE_URL in the surrounding environment does not surprise us.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# D-STATIC (PLAN S6): plain StaticFilesStorage in dev so runserver reloads
# CSS without collectstatic. (STORAGES is the Django 5.1 replacement for the
# removed STATICFILES_STORAGE setting.)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

# D-CACHE (PLAN S3): LocMem stays fine for the single-process dev server;
# prod uses DatabaseCache so rate limits are shared across workers.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "gabriel-dev",
    }
}

# Verbose emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Show template file names in errors for easier debugging
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

# django-debug-toolbar style niceties without the dependency
INTERNAL_IPS = ["127.0.0.1"]

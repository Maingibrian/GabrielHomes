"""Production settings — hardened."""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

# ---------------------------------------------------------------------------
# Fail-fast guards (PLAN task S5, defects D-KEY + D-DB).
# Production must refuse to start on unsafe configuration rather than
# silently falling back to dev defaults.
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="")
if (
    not SECRET_KEY
    or SECRET_KEY.startswith("dev-insecure")
    or len(SECRET_KEY) < 50
):
    raise ImproperlyConfigured(
        "SECRET_KEY is missing, starts with the dev default, or is shorter "
        "than 50 characters. Generate one with: "
        'python -c "import secrets; print(secrets.token_urlsafe(60))"'
    )

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS is empty in production. Set it in the environment, "
        "e.g. ALLOWED_HOSTS=gabrielhomes.co.ke,www.gabrielhomes.co.ke"
    )

DATABASE_URL = env("DATABASE_URL", default="")
_PROD_DB_SCHEMES = ("postgres://", "postgresql://", "mysql://")
if not DATABASE_URL or not DATABASE_URL.startswith(_PROD_DB_SCHEMES):
    raise ImproperlyConfigured(
        "DATABASE_URL must be set in production to a MariaDB (mysql://) URL. "
        "SQLite is a development-only fallback and is refused here."
    )

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# D-RL (PLAN S2): behind our nginx (which sets X-Real-IP $remote_addr),
# rate limiting keys on the proxy-provided real client IP.
TRUST_X_REAL_IP = env.bool("TRUST_X_REAL_IP", default=True)

# D-STATIC (PLAN S6): hashed static filenames via whitenoise manifest
# storage — the STORAGES replacement for the removed STATICFILES_STORAGE.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Tighten allauth
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# Prod cache — D-CACHE (PLAN S3): LocMemCache is per-process, so auth rate
# limits would be N times looser with N gunicorn workers. DatabaseCache
# shares one store across workers. The "gabriel_cache" table is created by
# `manage.py createcachetable` at deploy time (DEPLOY.md step 6, task D4).
# No Redis — one fewer service to operate.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "gabriel_cache",
    }
}

# Structured-enough logging (D3): everything goes to stdout — journald /
# the container runtime picks it up. App loggers (apps.*) at INFO, root at
# WARNING. `logger.exception` calls (e.g. enquiry email failures, S9) land
# here; view them with:
#   journalctl -u gabriel-homes --since "1 hour ago" -p err
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "plain",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

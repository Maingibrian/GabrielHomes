"""Production settings — hardened."""
from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

# ALLOWED_HOSTS must come from env in prod.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Security
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

# Tighten allauth
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# Prod cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "gabriel-prod",
    }
}

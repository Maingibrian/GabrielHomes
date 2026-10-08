"""Base settings for Gabriel Homes.

Environment-specific overrides live in `dev.py` and `prod.py`.
All values come from environment variables via `django-environ`.
"""
from __future__ import annotations

import os
from pathlib import Path

import environ

# repo root: config/settings/base.py -> ../../
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# .env lives at repo root
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-key-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # `django.contrib.postgres` is added below only when running on Postgres,
    # so local SQLite dev does not require psycopg2.

    # Third-party
    "django_filters",
    "easy_thumbnails",
    "allauth",
    "allauth.account",
    "whitenoise.runserver_nostatic",

    # Local
    "apps.core",
    "apps.accounts",
    "apps.locations",
    "apps.listings",
    "apps.agents",
    "apps.inquiries",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_meta",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database — Postgres in prod, SQLite in dev if DATABASE_URL is unset.
#
# We check the parsed engine rather than the raw env var so a malformed
# DATABASE_URL (e.g. a stray `file:/...` value leaked from a parent
# project's env) does not crash app loading. `dev.py` always forces SQLite.
# ---------------------------------------------------------------------------
_db_url = env("DATABASE_URL", default="")
if _db_url:
    DATABASES = {"default": env.db("DATABASE_URL")}
    if DATABASES["default"].get("ENGINE", "").endswith("postgresql"):
        # Only pull in Postgres-specific helpers when actually on Postgres
        # — they import psycopg at app-load time.
        INSTALLED_APPS.append("django.contrib.postgres")
    elif not DATABASES["default"].get("ENGINE", "").endswith("sqlite3"):
        # Unknown engine — fall back to SQLite for safety.
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Auth — custom user model from day one (WORK.md section 5)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# allauth — email login (WORK.md section 4). Modern allauth config
# (ACCOUNT_LOGIN_METHODS / ACCOUNT_SIGNUP_FIELDS) — no deprecated
# ACCOUNT_AUTHENTICATION_METHOD / ACCOUNT_*_REQUIRED settings.
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"  # tighten to "mandatory" in prod
ACCOUNT_ADAPTER = "apps.accounts.adapters.AccountAdapter"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/account/login/"

# ---------------------------------------------------------------------------
# i18n / tz
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static / media
# ---------------------------------------------------------------------------
STATIC_URL = env.str("STATIC_URL", default="/static/")
STATIC_ROOT = env.str("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
STATICFILES_DIRS = [BASE_DIR / "static"]

# D-STATIC (PLAN S6): Django 5.1 removed STATICFILES_STORAGE — setting it
# here was a silent no-op. STORAGES is the replacement. Base/dev use plain
# storage; prod.py swaps in whitenoise's CompressedManifestStaticFilesStorage
# so files are served under hashed names.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

MEDIA_URL = env.str("MEDIA_URL", default="/media/")
MEDIA_ROOT = env.str("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# ---------------------------------------------------------------------------
# Easy thumbnails
# ---------------------------------------------------------------------------
THUMBNAIL_DEFAULT_ALIAS = "default"
THUMBNAIL_ALIASES = {
    "": {
        "default": {"size": (800, 600), "crop": True},
        "card": {"size": (640, 480), "crop": True},
        "gallery": {"size": (1280, 960), "crop": False},
        "cover": {"size": (1600, 900), "crop": True},
    },
}

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="hello@gabrielhomes.co.ke")

# ---------------------------------------------------------------------------
# Site meta (used by core context processor)
# ---------------------------------------------------------------------------
SITE_NAME = "Gabriel Homes"
SITE_DOMAIN = env.str("SITE_DOMAIN", default="http://localhost:8000")
DEFAULT_META_DESCRIPTION = (
    "Gabriel Homes — real estate with a human point of view. "
    "Buy and rent property in Mombasa, Nairobi, Kilifi, Diani, Kiambu and Kajiado."
)

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security defaults — overridden in prod.py
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# D-RL (PLAN S2): X-Real-IP is only trusted when our own nginx sets it from
# the socket address. Off by default; prod.py turns it on. X-Forwarded-For
# is never used for rate limiting either way.
TRUST_X_REAL_IP = env.bool("TRUST_X_REAL_IP", default=False)

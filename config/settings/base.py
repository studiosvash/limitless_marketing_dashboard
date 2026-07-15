"""
Shared Django settings for the FuseHealth dashboard.

Environment-specific settings live in local.py (development) and production.py (VPS).
Both import everything from this module and override what they need.

Secrets and environment-specific values are read from the environment (.env file in
development, real environment variables in production). Nothing secret is hardcoded here.
"""

import os
from pathlib import Path

# BASE_DIR points at the project root (the `fusehealth/` folder), three levels up
# from this file: config/settings/base.py -> config/settings -> config -> fusehealth/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load variables from a local .env file if one exists. Optional so that
# `manage.py check` never fails just because python-dotenv isn't installed.
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def env(key: str, default: str | None = None) -> str | None:
    """Read an environment variable, returning `default` if it is unset."""
    return os.environ.get(key, default)


# --- Core -------------------------------------------------------------------

# Overridden per-environment. local.py supplies a dev key; production.py requires
# SECRET_KEY to come from the real environment.
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-key-override-in-production")

DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    # FuseHealth apps
    "apps.accounts",
    "apps.dashboard",
    "apps.sync",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Protects every view by default; public views opt out with @login_not_required.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.dashboard.context_processors.navigation",
                "apps.dashboard.context_processors.sites",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --- Databases --------------------------------------------------------------
# Two databases, kept separate on purpose:
#   * default  -> django_internal.db : Django's own tables (auth, sessions, admin,
#                 our UserProfile, sync_log). Managed by the Django ORM + migrations.
#   * analytics: fusehealth.db        : the marketing/SEO data. Managed by SQLAlchemy
#                 in the reused pipeline layer, NOT the Django ORM. Its path is exposed
#                 here so the pipeline reads a single, settings-driven location.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("DJANGO_INTERNAL_DB", str(BASE_DIR / "django_internal.db")),
    }
}

# Path to the SQLAlchemy-managed analytics database. The final schema is decided in
# Phase 3; the pipeline layer reads this value rather than hardcoding a path.
ANALYTICS_DB_PATH = env("ANALYTICS_DB_PATH", str(BASE_DIR / "data" / "fusehealth.db"))


# --- REST API (Limitless Marketing SPA) --------------------------------------
# The frontend (`Limitless marketing dashboard2/`) sends `Authorization: Bearer <token>`
# (see app/api.js), not DRF's default `Token <token>` scheme — hence the custom auth class.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.api.authentication.BearerTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# --- Auth -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Where unauthenticated users get sent, and where login lands them.
LOGIN_URL = "login"
# After login, land on the SPA at the site root. (Was "dashboard:overview" -- the old
# template dashboard, which no longer exists.)
LOGIN_REDIRECT_URL = "spa"
LOGOUT_REDIRECT_URL = "login"


# --- I18N / TZ --------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --- Static files -----------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic target (production)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Logging ----------------------------------------------------------------

import os
LOGS_DIR = BASE_DIR / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "django_errors.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

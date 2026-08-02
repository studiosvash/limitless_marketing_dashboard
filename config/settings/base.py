"""
Shared Django settings for the FuseHealth dashboard.

Environment-specific settings live in local.py (development) and production.py (VPS).
Both import everything from this module and override what they need.

Secrets and environment-specific values are read from the environment (.env file in
development, real environment variables in production). Nothing secret is hardcoded here.
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

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


def _running_tests() -> bool:
    """True when this process is a test run rather than a server/management run.

    DO NOT DELETE THIS — see the RUNNING_TESTS note in the Databases section below.
    Removing it re-arms a live-data-corruption bug the moment POSTGRES_DB is set.

    Signals, in order:
      1. `manage.py test ...` / `django-admin test ...` / `coverage run manage.py test`
         — every one of these leaves "test" as the first argument. (multiprocessing
         spawn, used by `test --parallel`, copies sys.argv into workers, so the
         guard survives there too.)
      2. pytest is already imported. Settings are imported by pytest-django well
         after pytest itself, so this is true before the first test runs. (pytest
         isn't installed today; this costs nothing and covers the day it is.)
      3. DJANGO_TEST_RUN=1 — explicit escape hatch for a runner we can't sniff
         (tox/nox/a bespoke CI script). Set it and the guard engages.
    """
    if sys.argv[1:2] == ["test"]:
        return True
    if "pytest" in sys.modules:
        return True
    return str(env("DJANGO_TEST_RUN", "")).strip().lower() in ("1", "true", "yes")


RUNNING_TESTS = _running_tests()


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
# Two storage layers, kept separate on purpose:
#   * default  -> Django's own tables (auth, sessions, admin, our UserProfile,
#                 sync_log). Managed by the Django ORM + migrations.
#   * analytics-> the marketing/SEO data. Managed by SQLAlchemy in the reused
#                 pipeline layer, NOT the Django ORM. Its location is exposed here
#                 so the pipeline reads a single, settings-driven value.
#
# Two deployment modes, chosen by whether POSTGRES_DB is set:
#
#   POSTGRES_DB unset (default, and the rollback path)
#       default   -> sqlite3 at django_internal.db
#       analytics -> sqlite file at ANALYTICS_DB_PATH (data/fusehealth.db)
#       Behaviour is exactly what it has always been; nothing else has to change.
#
#   POSTGRES_DB set (production)
#       default   -> django.db.backends.postgresql on that database
#       analytics -> the SAME Postgres database, via ANALYTICS_DB_URL
#       One database holds both sets of tables. The names don't collide, so they
#       coexist safely: Django creates its tables with migrations, SQLAlchemy
#       creates the analytics tables with init_db().
#
#   POSTGRES_DB set, but this process is a TEST RUN (RUNNING_TESTS)
#       Postgres is ignored entirely and the SQLite branch is taken. Read the
#       block below before touching that condition — it is load-bearing.
#
# ANALYTICS_DB_PATH stays defined in BOTH branches: the pipeline still falls back
# to it when no URL is configured, and the test suite drives it directly via
# override_settings(ANALYTICS_DB_PATH=...).
#
# ---------------------------------------------------------------------------
# WHY `and not RUNNING_TESTS` IS ON THE BRANCH BELOW — do not "simplify" it away
# ---------------------------------------------------------------------------
# ~40 test files isolate themselves like this:
#
#     db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
#     init_db(get_engine(db_path))
#     override_settings(ANALYTICS_DB_PATH=db_path)
#
# but pipeline/utils/db_connection.py::_get_db_url() resolves
# settings.ANALYTICS_DB_URL *first* and settings.ANALYTICS_DB_PATH only third,
# and override_settings(ANALYTICS_DB_PATH=...) does not clear ANALYTICS_DB_URL.
# So without this guard, the day anyone puts POSTGRES_DB in .env (or CI does),
# every one of those tests silently ignores its temp SQLite file and
# reads/writes the REAL Postgres database — passing or failing against live
# data, and mutating it. The suite would still be green while corrupting prod.
#
# Fixing it in the resolver would weaken the production order; fixing it in the
# tests would mean editing ~40 files and trusting the 41st to remember. So the
# settings layer refuses to hand a Postgres DSN to a test process at all: under
# RUNNING_TESTS we take the SQLite branch wholesale, which leaves
# ANALYTICS_DB_URL = None and lets each test's ANALYTICS_DB_PATH win.
#
# The Django `default` connection is forced to SQLite for the same reason. It is
# the stronger guarantee (the suite cannot open a Postgres connection at all, in
# either layer) and it is what the suite has always run on, so `manage.py test`
# behaves identically whether or not POSTGRES_DB is set.
#
# There is deliberately NO opt-out: if you ever want the suite to run against a
# real Postgres, that has to be a conscious, explicit change here — not something
# a stray .env line turns on behind your back.
#
# With POSTGRES_DB unset (today's default) this guard changes nothing at all:
# the else-branch was already the one being taken.

POSTGRES_DB = env("POSTGRES_DB", "")
POSTGRES_USER = env("POSTGRES_USER", "")
POSTGRES_PASSWORD = env("POSTGRES_PASSWORD", "")
POSTGRES_HOST = env("POSTGRES_HOST", "localhost")
POSTGRES_PORT = env("POSTGRES_PORT", "5432")

# Kept in both branches — see the note above.
ANALYTICS_DB_PATH = env("ANALYTICS_DB_PATH", str(BASE_DIR / "data" / "fusehealth.db"))

# Confines every tempfile.mkdtemp() the suite makes to one directory and deletes it at the
# end of the run. The analytics-DB fixture (.claude/skills.md §8) never removed its temp
# directory, and 58 copies of it across 34 modules quietly accumulated 16.6 GB / 29 216
# directories until the drive hit zero bytes. See config/test_runner.py.
TEST_RUNNER = "config.test_runner.TempCleaningRunner"

if POSTGRES_DB and not RUNNING_TESTS:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": POSTGRES_DB,
            "USER": POSTGRES_USER,
            "PASSWORD": POSTGRES_PASSWORD,
            "HOST": POSTGRES_HOST,
            "PORT": POSTGRES_PORT,
        }
    }

    # SQLAlchemy DSN pointing at the same database Django just configured.
    # The password is percent-encoded so that characters which are meaningful in a
    # URL (@ : / ? #) in a generated password don't corrupt the DSN.
    ANALYTICS_DB_URL = (
        f"postgresql+psycopg://{quote_plus(POSTGRES_USER)}:{quote_plus(POSTGRES_PASSWORD)}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env("DJANGO_INTERNAL_DB", str(BASE_DIR / "django_internal.db")),
        }
    }

    # No Postgres configured (or a test run) -> the pipeline uses the SQLite file at
    # ANALYTICS_DB_PATH. None is required, not merely tidy: _get_db_url() checks this
    # setting for truthiness and only then falls through to ANALYTICS_DB_PATH.
    ANALYTICS_DB_URL = None


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

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
]

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


# --- Error monitoring (Sentry) ----------------------------------------------
# Opt-in: without SENTRY_DSN nothing is initialised and the dependency is never imported,
# so development and the test suite are completely unaffected.
#
# Why this exists: this app integrates ~14 external APIs behind a background sync thread.
# Before this, a connector failing in production surfaced only as a line in a rotating
# log file nobody reads, plus a "system" alert in the UI that names the connector but not
# the cause. A sync that half-fails at 3am was effectively invisible.
#
# Deliberately NOT enabled during tests: RUNNING_TESTS is checked so a CI run can never
# ship noise to the production project.

SENTRY_DSN = env("SENTRY_DSN", "")

if SENTRY_DSN and not RUNNING_TESTS:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                # ERROR and above become Sentry events; INFO stays as breadcrumbs, which is
                # what makes a connector failure readable — you get the run that led to it.
                LoggingIntegration(level=None, event_level="ERROR"),
            ],
            environment=env("SENTRY_ENVIRONMENT", "production"),
            release=env("SENTRY_RELEASE", None),
            # A 2-3 user internal dashboard does not need statistical sampling; catching every
            # trace is cheap here and far more useful when diagnosing a specific failed sync.
            traces_sample_rate=float(env("SENTRY_TRACES_SAMPLE_RATE", "0.0") or 0.0),
            # The app handles API credentials and user emails. Never let Sentry attach PII.
            send_default_pii=False,
        )
    except ImportError:
        # The DSN is set but the package is not installed. Fail loudly in the log rather than
        # silently running unmonitored while the operator believes monitoring is on.
        import logging as _logging
        _logging.getLogger(__name__).error(
            "SENTRY_DSN is set but sentry-sdk is not installed — error monitoring is OFF. "
            "Run: pip install -r requirements.txt"
        )


# --- Email & SMTP -----------------------------------------------------------

EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = str(env("EMAIL_USE_TLS", "True")).lower() in ("true", "1", "yes")
EMAIL_USE_SSL = str(env("EMAIL_USE_SSL", "False")).lower() in ("true", "1", "yes")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Limitless Dashboard <no-reply@fusehealth.com>")
# Base URL used in outbound emails (invitations). Left empty on purpose: with no value,
# apps/api/views.py:build_frontend_link derives the origin from the incoming request, so a
# dev box mails localhost links and the deployed site mails https://<domain> links without
# anyone having to remember this variable. Set it only when the SPA is served from a
# different origin than the API.
FRONTEND_URL = env("FRONTEND_URL", "")

# If running locally with no SMTP user configured, gracefully fall back to console print
# so dev doesn't crash with ConnectionRefused on localhost:25 when testing.
if not EMAIL_HOST_USER and EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"



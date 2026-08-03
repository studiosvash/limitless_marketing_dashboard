"""
Production settings for the VPS (Nginx + Gunicorn + systemd).

Everything secret or host-specific MUST come from the real environment. This module
fails loudly at startup if a required value is missing, which is far safer than
silently booting with an insecure default.
"""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# SECRET_KEY must be provided by the environment in production.
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY is not set. Refusing to start in production without it."
    )

FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
if not FIELD_ENCRYPTION_KEY:
    raise RuntimeError(
        "FIELD_ENCRYPTION_KEY is not set. Refusing to start in production without it -- "
        "saved Ads credentials would be unreadable (or silently orphaned by a freshly "
        "generated key on every boot) without a stable value."
    )

# --- Static files (WhiteNoise) ----------------------------------------------
# whitenoise was already a dependency but was never wired into MIDDLEWARE, so a
# production boot served no CSS or JS at all -- the SPA is ~900 KB of static assets
# and every one of them would have 404'd behind Gunicorn (runserver serves them in
# DEBUG, which is why this never showed up locally).
#
# Position is fixed by WhiteNoise's own docs: immediately AFTER SecurityMiddleware
# and BEFORE everything else, so it can short-circuit a static request before any
# session/auth work happens. Inserted rather than appended for that reason.
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# CompressedManifestStaticFilesStorage fingerprints filenames and gzips them, so the
# assets can be cached hard. Run `manage.py collectstatic` before starting Gunicorn --
# with the manifest backend a missing collectstatic is a hard 500, not a silent miss.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --- Databases ---------------------------------------------------------------
# DATABASES is deliberately NOT overridden here. base.py selects Postgres as soon
# as POSTGRES_DB is present in the real environment (and falls back to SQLite if
# it isn't), so switching the VPS over is an env-var change, not a code change.

# Comma-separated hostnames, e.g. "dashboard.fusehealth.com,1.2.3.4"
_hosts = env("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()]

# --- HTTPS / security hardening --------------------------------------------
# Behind Nginx terminating TLS. These are the standard production defaults;
# revisit only if the reverse-proxy setup differs.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# CSRF trusted origins must include the scheme, e.g. "https://dashboard.fusehealth.com"
_csrf = env("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]

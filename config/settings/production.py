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

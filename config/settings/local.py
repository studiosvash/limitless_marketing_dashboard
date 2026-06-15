"""
Development settings. Active by default (see manage.py).

Safe to run on a laptop: DEBUG on, permissive hosts, a throwaway secret key.
Never use this module on the VPS — production.py is for that.
"""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# A fixed dev key is fine here because DEBUG/dev is never internet-facing.
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-key-not-for-production")

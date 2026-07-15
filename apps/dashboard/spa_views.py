"""Serves the approved Limitless Marketing SPA (static/spa/index.html) at /app/.

Config is race-free and needs NO per-request injection:
  - `apiBaseUrl` is baked into the SPA's `data-props` default (`"/"`), so the app's own
    `boot()` sets `FuseAPI.config.baseUrl` before it fires its first fetch (same function,
    in order -- no race against an injected <script>, which was the original bug).
  - Auth is the Django session cookie: the SPA calls `fetch(..., credentials:"include")`
    and this view is `@login_required`, so a valid session is always present. DRF's
    SessionAuthentication (settings.REST_FRAMEWORK) authenticates those calls -- no token
    to inject.

So this view just serves the static file behind login; the response is intentionally
byte-for-byte the approved design (no template rendering, which would collide with the
file's raw `{{ }}` JS literals).
"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

_SPA_HTML_PATH = Path(settings.BASE_DIR) / "static" / "spa" / "index.html"


@login_required
def spa_index(request):
    html = _SPA_HTML_PATH.read_text(encoding="utf-8")
    return HttpResponse(html, content_type="text/html; charset=utf-8")

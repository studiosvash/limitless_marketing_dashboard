"""Serves the approved Limitless Marketing SPA (static/spa/index.html) at /app/.

Deliberately does NOT run the file through Django's template engine -- the file is
full of raw JS object literals (`{ id: 'x', ... }`) that would collide catastrophically
with Django's `{{ }}` / `{% %}` template syntax. Instead we read the raw bytes and do a
single targeted string replacement to inject a bootstrap <script> that configures
window.FuseAPI before the app's own code runs.

The bootstrap is injected DIRECTLY AFTER app/api.js (which defines window.FuseAPI
synchronously) rather than before </body>: the app component's componentDidMount ->
boot() fires the first `/api/.../overview` fetch, and the dc framework can mount that
component during HTML parse (custom-element connectedCallback). Setting config right
after api.js guarantees baseUrl/authToken are in place before that first fetch, so the
app never falls back to fixtures.

baseUrl is set to '/' (NOT '' ): app/api.js switches to the real backend with
`if (config.baseUrl)` -- an empty string is falsy and would trap the app on fixtures.
'/' is truthy and, after api.js strips the trailing slash, resolves the hardcoded
`/api/...` call paths correctly against the current origin.
"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from rest_framework.authtoken.models import Token

_SPA_HTML_PATH = Path(settings.BASE_DIR) / "static" / "spa" / "index.html"


@login_required
def spa_index(request):
    html = _SPA_HTML_PATH.read_text(encoding="utf-8")
    token, _ = Token.objects.get_or_create(user=request.user)
    api_tag = '<script src="/static/spa/app/api.js"></script>'
    bootstrap = (
        "<script>"
        "(function(){"
        "function boot(){"
        "if(window.FuseAPI&&window.FuseAPI.config){"
        "window.FuseAPI.config.baseUrl = '/';"
        f"window.FuseAPI.config.authToken = '{token.key}';"
        "return true;}return false;}"
        "if(!boot()){var n=0,iv=setInterval(function(){"
        "if(boot()||++n>100)clearInterval(iv);},20);}"
        "})();"
        "</script>"
    )
    if api_tag not in html:
        raise RuntimeError(
            "SPA bootstrap injection point not found -- the api.js <script> tag in "
            "static/spa/index.html changed. Update apps/dashboard/spa_views.py:api_tag."
        )
    # Injected immediately AFTER api.js (which synchronously creates window.FuseAPI), so
    # config is set before the app component mounts and fires its first API fetch.
    html = html.replace(api_tag, api_tag + bootstrap, 1)
    return HttpResponse(html, content_type="text/html; charset=utf-8")

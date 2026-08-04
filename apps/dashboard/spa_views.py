r"""Serves the approved Limitless Marketing SPA (static/spa/index.html) at /app/.

Deliberately does NOT run the file through Django's template engine — the file is
full of raw JS object literals (`{ id: 'x', ... }`) that would collide catastrophically
with Django's `{{ }}` / `{% %}` template syntax. Instead we read the raw bytes and do a
single targeted string insertion (never a blind str.replace — see below) to inject a
bootstrap <script> that configures window.FuseAPI before the app's own code runs.

Three non-obvious footguns discovered by driving the real file in a browser
(Playwright), all load-bearing for correctness:

1. `static/spa/index.html`'s own JS (an Excel-export helper deep inside the
   `<script data-dc-script>` block) contains the literal TEXT "<head>...</head>"
   and "...</table></body></html>" inside a JS string — i.e. the substring
   "<head>" appears TWICE in the file: once as the real structural tag, once
   as inert text inside a JS string (the same is true of "</body>", though we
   don't insert there — see below). A naive `html.replace("<head>", ...)`
   matches BOTH occurrences, splicing our script into the middle of that JS
   string and corrupting the SPA's whole logic script — the browser's HTML
   parser then treats our injected `</script>` as the terminator for that
   (much earlier, unrelated) script element, truncating it and breaking the
   dc-runtime's `evalDcLogic` step ("Unexpected string"). Fix: target the
   structural `<head>` tag by *position* — the FIRST occurrence, via
   `str.index()` — never a blanket `replace()`. (We only ever insert once,
   right after `<head>`, per the interceptor approach in footgun #2 below —
   there is no separate `</body>`-relative insertion in this implementation.)

2. `app/api.js`'s `<script src>` tag actually executes TWICE in a real browser:
   once during the browser's normal top-to-bottom parse of the document, and a
   second time when the SPA's own `<helmet>` processing (in support.js)
   relocates and re-fetches/re-executes it into <head>. Each execution runs
   `window.FuseAPI = (function(){ ... })()`, creating a brand-new object with
   default (null) config — so a simple one-shot
   `window.FuseAPI.config.authToken = '...'` set after the fact gets silently
   wiped out by whichever execution happens last. Fix: install an
   Object.defineProperty interceptor on `window.FuseAPI` itself, at the very
   top of <head> (before anything else can run), so our config is re-applied
   to *every* object api.js ever assigns, regardless of how many times or when
   that happens.

3. `config.baseUrl` must be truthy, NOT ''. app/api.js's public get()/post()/
   put() each gate real-backend mode on a plain JS truthy check —
   `if (config.baseUrl) return http(...)`, else it silently falls through to
   the bundled fixture/demo data forever. An empty string is falsy in
   JavaScript, so baseUrl = '' (the natural-sounding reading of "paths already
   hardcode /api/..., so the base should contribute nothing") never calls the
   real backend at all — verified in a real browser: zero network requests
   ever reached /api/* with baseUrl set to ''. The fix is baseUrl = '/': it is
   truthy (passes the gate), and api.js's own `config.baseUrl.replace(/\/$/,
   '')` strips exactly one trailing slash before prepending it to the path, so
   '/' contributes the same *effective* empty prefix as '' would have, while
   actually enabling the http() branch. Every call site in index.html passes
   an already-/api/-prefixed path (e.g. `window.FuseAPI.get('/api/projects/' +
   pid + '/...')`), so '/' + '/api/projects/...' -> '/api/projects/...',
   exactly as intended.
"""
import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

import re

_SPA_SRC_HTML_PATH = Path(settings.BASE_DIR) / "static" / "spa" / "src" / "index.html"

def resolve_includes(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    
    def replacer(match):
        include_path = match.group(1) or match.group(2)
        target_file = _SPA_SRC_HTML_PATH.parent / include_path
        if target_file.exists():
            return resolve_includes(target_file)
        return f"<!-- INCLUDE ERROR: {include_path} not found -->"
        
    pattern = re.compile(r'<!--\s*#include\s+"([^"]+)"\s*-->|/\*\s*#include\s+"([^"]+)"\s*\*/')
    return pattern.sub(replacer, content)

@login_required
def spa_index(request):
    html = resolve_includes(_SPA_SRC_HTML_PATH)
    token = request.user.auth_token.key
    u = request.user
    role = (getattr(u, "profile", None) and u.profile.role) or "Analyst"
    if u.id == 1 or u.username.lower() in ("founder", "owner"):
        role = "Owner"
    elif role in ("Owner", "Viewer"):
        role = "Admin"
    initials = u.username[:2].upper() if u.username else "U"
    user_info = {
        "id": u.id,
        "username": u.username,
        "email": u.email or "",
        "initials": initials,
        "role": role,
    }
    bootstrap = (
        "<script>"
        "(function(){"
        f"var authToken={json.dumps(token)};"
        f"var userInfo={json.dumps(user_info)};"
        "var real;"
        "Object.defineProperty(window,'FuseAPI',{"
        "configurable:true,"
        "get:function(){return real;},"
        "set:function(v){"
        "if(v&&v.config){v.config.baseUrl='/';v.config.authToken=authToken;v.config.user=userInfo;}"
        "real=v;"
        "}"
        "});"
        "})();"
        "</script>"
    )
    # Insert right after the FIRST "<head>" (the real, structural one — see
    # footgun #1 above for why "first" matters), so the interceptor is in place
    # before app/api.js gets any chance to run (footgun #2).
    insert_at = html.index("<head>") + len("<head>")
    html = html[:insert_at] + bootstrap + html[insert_at:]
    response = HttpResponse(html, content_type="text/html; charset=utf-8")
    # This shell embeds app.js/every page's JS inline, re-read from source and re-assembled on
    # EVERY request (see resolve_includes above) -- there is no server-side cache to bust. But
    # without an explicit header, a browser can still serve a cached copy of the *document itself*
    # (back/forward cache, a plain refresh treated as a revalidation-free hit), so an edit here
    # can look like it did nothing until the user does a hard reload. Explicit no-store removes
    # that guesswork during active iteration.
    response["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response

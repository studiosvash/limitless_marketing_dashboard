import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token


class SpaViewTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_logged_in_gets_html_with_bootstrap_script(self):
        user = get_user_model().objects.create_user("viewer", password="x")
        self.client.force_login(user)
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/html; charset=utf-8")
        token = Token.objects.get(user=user).key
        body = resp.content.decode()

        # The token is embedded as a JSON-encoded JS string literal (safe against
        # quote/backslash characters in the token value).
        self.assertIn(json.dumps(token), body)

        # IMPORTANT: this is '/' , not ''. app/api.js's get()/post()/put() gate
        # real-backend mode on `if (config.baseUrl)` -- a plain JS truthy check.
        # An empty string is falsy, so config.baseUrl = '' (the naive reading of
        # "baseUrl must be empty since paths already hardcode /api/...") would
        # silently leave the SPA in fixture/demo mode forever: verified in a real
        # browser that zero requests ever reach /api/* with baseUrl set to ''.
        # '/' is truthy (passes the gate) AND strips to '' via api.js's own
        # `config.baseUrl.replace(/\/$/, '')` before being prepended to the
        # already-/api/-prefixed path, so the final request URL is unaffected
        # (e.g. '/' + '/api/projects' -> '' + '/api/projects' -> '/api/projects').
        self.assertIn("v.config.baseUrl='/'", body)

        # The bootstrap script installs an Object.defineProperty interceptor on
        # `window.FuseAPI` itself, rather than a one-shot post-hoc assignment.
        # This is necessary because app/api.js's <script> tag actually executes
        # TWICE in a real browser: once during the browser's normal parse of the
        # document, and a second time when the SPA's own <helmet> processing
        # (in support.js) relocates and re-fetches/re-executes it. Each execution
        # reassigns `window.FuseAPI` to a brand-new object with default (null)
        # config, which would silently wipe out a simple
        # `window.FuseAPI.config.authToken = '...'` set after the fact.
        # Intercepting the property *setter* guarantees our config is re-applied
        # to whichever object api.js assigns, no matter how many times that
        # happens. See spa_views.py for the full explanation.
        self.assertIn("Object.defineProperty(window,'FuseAPI'", body)

        # The interceptor must be installed before ANY script that could assign
        # window.FuseAPI runs — so it must appear before the api.js script tag in
        # the raw HTML (opposite of a naive "inject near </body>" approach).
        self.assertLess(body.index("Object.defineProperty(window,'FuseAPI'"), body.index("/static/spa/app/api.js"))

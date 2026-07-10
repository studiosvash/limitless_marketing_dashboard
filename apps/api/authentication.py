"""Authentication for the Limitless Marketing SPA.

The frontend's transport (app/api.js `http()`) sends
`Authorization: Bearer <token>` — DRF's built-in TokenAuthentication expects the
keyword `Token` by default, so we override it. Everything else (token model,
lookup, expiry semantics) is stock DRF TokenAuthentication.
"""

from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    keyword = "Bearer"

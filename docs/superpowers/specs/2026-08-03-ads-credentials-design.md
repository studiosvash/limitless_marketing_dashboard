# Ads platform credentials — design

**Date:** 2026-08-03
**Status:** approved by user, pending written plan

## Problem

Settings → Connections → "Ads platforms" currently renders two large status-card
explainers (`settings.html:302-380`, `settings.js:142-330`) that tell the user *why*
Google Ads / Meta Ads aren't connected, because credentials only ever come from the
server's `.env` file — there is no way to enter them from the UI, and the code says so
explicitly in a comment.

The user wants this replaced with an actual credential-entry form: a few input fields,
a "test connection" button that proves the credentials work (a real API call, not a
format check), and one short instruction line — no long explainer blocks.

Making the fields real (not decorative) requires: somewhere to persist them, a live
test endpoint, and wiring the sync pipeline to actually use what's saved. All three are
in scope (user confirmed "full scope" over a save-only cut).

## Scope

**In scope**
- Per-site encrypted storage for Google Ads + Meta Ads credentials
- `POST` save endpoint (extends existing settings save path)
- Live "test connection" endpoint (real API call per platform)
- `GoogleAdsConnector` / `MetaConnector` read DB-saved creds first, `.env` as fallback
- Frontend: replace the two big cards with a compact field-entry UI

**Out of scope**
- Touching the shared Google OAuth values (`GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN`) —
  these remain global `.env` config, shared across GSC/GA4/Ads, unrelated to this task
- Any other connector (LinkedIn/Reddit/etc. rows stay inert, unchanged)
- Multi-user credential permissions beyond the existing Owner/Admin gate already on
  `ProjectSettingsView` PUT

## Storage

No new table/migration. New key inside the existing `ProjectSettings.data` JSONField
(`apps/dashboard/models.py:122-134`), per site:

```json
"adsCredentials": {
  "google_ads": {"enc": "<fernet-token>", "updated_at": "...", "last_test": {"ok": true, "detail": "...", "at": "..."}},
  "meta_ads":   {"enc": "<fernet-token>", "updated_at": "...", "last_test": {"ok": false, "detail": "...", "at": "..."}}
}
```

`enc` is a single Fernet-encrypted JSON blob of the platform's field dict (e.g.
`{"developer_token": "...", "customer_id": "...", "login_customer_id": "..."}`). Whole-dict
encryption, not per-field, keeps this simple — one key to manage, one thing to decrypt.

New setting `FIELD_ENCRYPTION_KEY`, read via the existing `env(...)` helper
(`config/settings/base.py`), same required-in-production / dev-default pattern as
`DJANGO_SECRET_KEY` (`config/settings/production.py:14-19` raises if missing). Add
`cryptography` to `requirements.txt` explicitly (already present transitively via
`google-auth`, but must be a declared dependency since we now use it directly).

`GET /settings` never returns decrypted secrets. Each saved field returns as a mask
(last 4 chars: `••••1234`) plus whether a value exists. Saving a blank field leaves the
existing stored value untouched — only a non-blank submitted value overwrites.

## Fields

**Google Ads**
- Developer Token (required)
- Customer ID (required, digits only, dashes stripped like the connector already does)
- Manager/Login Customer ID (optional — only needed for MCC accounts)

**Meta Ads**
- Access Token (required)
- Ad Account ID (required, `act_XXXXXXXXXX` format)

## Backend endpoints

Extend `apply_settings_update` (`apps/dashboard/services/settings_service.py:645-754`)
to accept an `adsCredentials` blob key (whitelisted alongside the existing blob keys at
line 739-740), encrypting each platform's dict before storing.

New endpoint, same auth gate as `ProjectSettingsView` (Owner/Admin), e.g.
`POST /api/projects/<slug>/ads-credentials/test`:

```
body: {platform: "google_ads"|"meta_ads", ...fields}   // typed-in values, not yet saved
     | {platform: "google_ads"|"meta_ads", useSaved: true}  // test what's already stored
resp: {ok: bool, detail: string}
```

The `useSaved` form lets the frontend re-test an already-saved credential (shown only as
a mask) without the user retyping the secret — the backend decrypts server-side and
never returns the plaintext back to the client either way.

- `google_ads`: build a `GoogleAdsClient` from the submitted developer token + customer
  id (+ shared OAuth env vars, same as `_build_service()` today) and run a trivial GAQL
  query (`SELECT customer.id FROM customer LIMIT 1`). Any exception → `ok: false` with
  a short human-readable reason (invalid token / no access / bad customer id / etc.)
- `meta_ads`: `GET https://graph.facebook.com/v21.0/<ad_account_id>?fields=name&access_token=<token>`
  via `requests`. 200 → `ok: true`; 4xx → `ok: false` with the Graph API's error message

This lives in `connection_check_service.py` alongside the existing `_check_*` helpers,
since that's the established home for "does this credential actually work" logic — but
as new dedicated functions (`test_google_ads_credential`, `test_meta_ads_credential`),
since the existing `_check_google_ads` deliberately only checks env-var presence and is
used by the unrelated `/api/connection-check` flow.

## Connector wiring

`GoogleAdsConnector.__init__` / `MetaConnector.__init__` gain an optional
`credentials: dict | None` constructor param. When provided (loaded + decrypted by the
sync command from `ProjectSettings` for the site being synced), it's used instead of
`os.getenv(...)`. When `None` (no saved creds for that site), behavior is byte-for-byte
what it is today — `.env` fallback, so sites that never touch this new UI keep working
unchanged. The one-time OAuth values (`GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN`) stay
`.env`-only in both cases, per the out-of-scope note above.

## Frontend

Replace `settings.html:302-380` (and the matching `ADS_PLATFORMS`/`adsCards` logic in
`settings.js:142-330`) with, per platform, a compact two-column card:

- **Left:** status pill (kept — still useful at a glance) + the 2-3 input fields
  (masked existing values, editable) + **Test connection** button (shows inline
  pass/fail + detail message) + **Save** button. Test connection sends the typed values
  if any field was edited, otherwise sends `useSaved: true` to re-check what's stored
- **Right:** one short instruction line + link to where to get the credential (e.g.
  "Get your developer token from the Google Ads API Center →"), replacing the current
  15-line numbered setup + env-var-rows + access-requirements block

The existing "Run Ads sync now" button (Google Ads only, `settings.js:327`) is kept as-is.

## Error handling

- Test-connection call failures (network error, malformed input) surface the same way
  as an API rejection: `ok: false` + message — no silent success, no fabricated "connected".
- Save validates required fields are non-blank server-side before encrypting; a missing
  required field returns a 400 with a field-level message, matching the existing
  `apply_settings_update` validation style.

## Testing

- Backend: unit tests for encrypt/decrypt round-trip, `apply_settings_update` masking
  behavior (blank doesn't overwrite), and the two test-connection functions (mocked HTTP
  / mocked `GoogleAdsClient`)
- Connector: unit test confirming `credentials=None` preserves current env-var behavior,
  and `credentials={...}` overrides it
- Frontend: manual verification (enter creds → test → save → reload → masked value
  shows → re-test still works)

# Ads Platform Credentials — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Settings → Connections "Ads platforms" status-card explainers with a
real credential-entry form (Google Ads + Meta Ads), backed by encrypted per-site storage, a
live "Test connection" call, and connector wiring so a saved credential is what an actual
sync uses (falling back to `.env` when a site has none saved).

**Architecture:** Credentials are stored encrypted (Fernet) inside the existing
`ProjectSettings.data["adsCredentials"]` JSON blob — no new table/migration. A live probe
function lives next to each connector (`pipeline/connectors/google_ads.py::probe_credential`,
`pipeline/connectors/meta.py::probe_credential`), mirroring the existing
`ga4.py::probe_property` pattern. `sync_engine._get_connector` decrypts a site's saved
credential and passes it into the connector's constructor; the connector falls back to
`os.getenv(...)` exactly as it does today when nothing is passed.

**Tech Stack:** Django 6 + DRF, SQLAlchemy analytics DB (unaffected here — this plan only
touches Django ORM state), `cryptography` (Fernet), vanilla-JS SPA (`static/spa/src/`, no
build step, custom `sc-for`/`sc-if`/`{{ }}` template syntax).

**Spec:** `docs/superpowers/specs/2026-08-03-ads-credentials-design.md`

## Global Constraints

- Every API view needs `@method_decorator(login_not_required, name="dispatch")` —
  `LoginRequiredMiddleware` runs before DRF and would otherwise 302 token requests.
- Never fabricate data to fill a shape — return empty, `null`, or an explicit state.
- Analytics writes go through `pipeline/db/writer.py`; this plan touches only Django ORM
  state (`ProjectSettings`) plus two connector constructors — no analytics DB schema change.
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN` stay `.env`-only —
  shared OAuth identity used by GSC/GA4/Ads alike, explicitly out of scope (see spec).
- Secrets are never stored in plaintext and never echoed back in a GET — only a last-4-chars
  mask, per field `SECRET_FIELD` names in `apps/dashboard/services/ads_credentials.py`.
- The SPA is served from `static/spa/src/` with includes resolved per request — no build
  step, edit `src/` directly.
- Update the relevant `.claude/` reference in the same change as the behaviour it describes.
- Run tests with `python manage.py test <label>`.
- Commit after every task.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `requirements.txt` | Dependencies | declare `cryptography` |
| `config/settings/{base,local,production}.py` | `FIELD_ENCRYPTION_KEY` | new setting, same pattern as `SECRET_KEY` |
| `apps/dashboard/services/ads_credentials.py` | Encrypt/decrypt/mask, storage read/write | **new file** |
| `apps/dashboard/services/settings_service.py` | Settings GET/PUT | masked read in `build_settings_response`; save-with-merge in `apply_settings_update` |
| `pipeline/connectors/google_ads.py` | Google Ads connector | `__init__(credentials=None)`; new `probe_credential()` |
| `pipeline/connectors/meta.py` | Meta connector | `__init__(credentials=None)`; new `probe_credential()` |
| `apps/dashboard/services/connection_check_service.py` | Live-probe wrappers | `test_google_ads_credential()`, `test_meta_ads_credential()` |
| `apps/api/views.py` / `urls.py` | HTTP surface | `POST /api/projects/<slug>/ads-credentials/test` |
| `pipeline/services/sync_engine.py` | Connector factory | `_get_connector(name, site_id=None)` loads saved creds |
| `static/spa/src/pages/settings.html` | Ads platforms card markup | replace status-card block with form |
| `static/spa/src/js/pages/settings.js` | Ads platforms render data | replace `ADS_PLATFORMS`/`adsCards` |
| `static/spa/src/js/app.js` | SPA controller | `saveAdsCredential`, `testAdsCredential`, seed/state |
| `.claude/api-reference.md` / `.claude/features.md` | Docs | document the new endpoint + card |

**Test files:**
- `apps/dashboard/services/tests/test_ads_credentials.py` (new)
- `apps/dashboard/services/tests/test_settings_service.py` (existing — add a class)
- `pipeline/connectors/tests/test_google_ads_credential_probe.py` (new)
- `pipeline/connectors/tests/test_meta_credential_probe.py` (new)
- `pipeline/connectors/tests/test_ads_connector_credentials.py` (new)
- `apps/dashboard/services/tests/test_connection_check_service.py` (new)
- `apps/api/tests/test_ads_credentials.py` (new)
- `apps/api/tests/test_sync_engine.py` (existing — add a class, fix `_stub_connectors`)

---

## Task 1: Encryption key + credential storage/masking module

**Files:**
- Modify: `requirements.txt`
- Modify: `config/settings/base.py:66` (right after `SECRET_KEY`), `config/settings/local.py:16`, `config/settings/production.py:14-19`
- Create: `apps/dashboard/services/ads_credentials.py`
- Test: `apps/dashboard/services/tests/test_ads_credentials.py` (new)

**Interfaces:**
- Consumes: `django.conf.settings.FIELD_ENCRYPTION_KEY`
- Produces: `PLATFORM_FIELDS: dict[str, tuple[str,...]]`, `PLATFORM_REQUIRED_FIELDS: dict[str, tuple[str,...]]`, `SECRET_FIELD: dict[str,str]`, `encrypt_fields(fields: dict) -> str`, `decrypt_fields(token: str) -> dict`, `mask(value: str) -> str`, `get_decrypted_credential(site_id: str, platform: str) -> dict | None`, `record_test_result(site_id: str, platform: str, ok: bool, detail: str) -> None`

- [ ] **Step 1: Write the failing test**

Create `apps/dashboard/services/tests/test_ads_credentials.py`:

```python
"""Round-trip encryption + masking for Ads platform credentials. ProjectSettings
persistence (get_decrypted_credential/record_test_result against a real row) is covered
in test_settings_service.py alongside the rest of the settings save/read path."""
from django.test import TestCase

from apps.dashboard.services.ads_credentials import encrypt_fields, decrypt_fields, mask


class EncryptDecryptTests(TestCase):
    def test_round_trips_a_field_dict(self):
        original = {"developer_token": "abc123", "customer_id": "1234567890"}
        token = encrypt_fields(original)
        self.assertNotIn("abc123", token)  # never stored in the clear
        self.assertEqual(decrypt_fields(token), original)


class MaskTests(TestCase):
    def test_masks_all_but_last_four_characters(self):
        self.assertEqual(mask("abcdefgh1234"), "••••1234")

    def test_short_value_masks_completely(self):
        self.assertEqual(mask("abc"), "•••")

    def test_blank_value_masks_to_empty(self):
        self.assertEqual(mask(""), "")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_ads_credentials -v 1`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.dashboard.services.ads_credentials'`

- [ ] **Step 3: Declare the dependency**

In `requirements.txt`, add under the "Google APIs" section (it is already installed
transitively via `google-auth`, but is now used directly and must be a declared
dependency):

```
google-ads>=24.0.0          # used once Google Ads credentials are provisioned
cryptography>=42.0.0        # encrypts Ads platform credentials at rest (ProjectSettings.data)
```

- [ ] **Step 4: Add the setting, same pattern as `SECRET_KEY`**

In `config/settings/base.py`, immediately after line 66 (`SECRET_KEY = env(...)`):

```python
# Symmetric key for encrypting Ads platform credentials at rest (Fernet — 32 url-safe
# base64 bytes). Overridden per-environment exactly like SECRET_KEY above: local.py
# supplies a fixed dev key, production.py requires the real environment to provide one.
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
```

In `config/settings/local.py`, immediately after line 16 (`SECRET_KEY = env(...)`):

```python
# A fixed dev key is fine here because DEBUG/dev is never internet-facing — same
# reasoning as SECRET_KEY above. Generated once with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", "caSjoFGnSMRG4iLBbtcPGWprrK3Yl45D3FEABiBO1OQ=")
```

In `config/settings/production.py`, immediately after line 19 (the `SECRET_KEY` `RuntimeError`
block):

```python
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
if not FIELD_ENCRYPTION_KEY:
    raise RuntimeError(
        "FIELD_ENCRYPTION_KEY is not set. Refusing to start in production without it -- "
        "saved Ads credentials would be unreadable (or silently orphaned by a freshly "
        "generated key on every boot) without a stable value."
    )
```

- [ ] **Step 5: Write the module**

Create `apps/dashboard/services/ads_credentials.py`:

```python
"""apps/dashboard/services/ads_credentials.py — encrypted per-site Ads platform credentials.

Google Ads / Meta Ads secrets are stored inside ProjectSettings.data["adsCredentials"]
[platform] as a single Fernet-encrypted blob of that platform's field dict, keyed by site
(ProjectSettings.site_url). See docs/superpowers/specs/2026-08-03-ads-credentials-design.md
for why: before this, the ONLY place these credentials could live was the server's .env
file, shared by the whole app rather than per-site, with no live way to prove they worked
short of running a real sync.

Encryption, not the plain JSONField the rest of ProjectSettings.data uses: unlike
gsc_property/ga4_property_id (identifiers, not secrets), a Google Ads developer token or
Meta access token grants real API access, so it must not sit in the database in plaintext.
"""
import json
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

PLATFORM_FIELDS = {
    "google_ads": ("developer_token", "customer_id", "login_customer_id"),
    "meta_ads": ("access_token", "ad_account_id"),
}
# The subset of PLATFORM_FIELDS that must be non-blank before a save is accepted.
# login_customer_id is the only optional field (manager/MCC accounts only).
PLATFORM_REQUIRED_FIELDS = {
    "google_ads": ("developer_token", "customer_id"),
    "meta_ads": ("access_token", "ad_account_id"),
}
# Which field is shown masked on GET -- the one value that is actually a secret. The other
# fields (customer_id, ad_account_id) are account identifiers, not secrets, but are never
# echoed back either -- there is no legitimate reason for them to round-trip to the browser.
SECRET_FIELD = {"google_ads": "developer_token", "meta_ads": "access_token"}


def _fernet() -> Fernet:
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "FIELD_ENCRYPTION_KEY is not configured -- cannot encrypt or decrypt Ads "
            "credentials. See config/settings/{local,production}.py."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_fields(fields: dict) -> str:
    """Encrypt one platform's field dict to a single string for storage."""
    return _fernet().encrypt(json.dumps(fields).encode()).decode()


def decrypt_fields(token: str) -> dict:
    """Decrypt a stored blob back to its field dict.

    Raises cryptography.fernet.InvalidToken if the key has rotated or the value is
    corrupt -- callers treat that identically to "nothing saved" (see
    get_decrypted_credential) rather than crashing a page read.
    """
    return json.loads(_fernet().decrypt(token.encode()).decode())


def mask(value: str) -> str:
    """Last 4 characters only -- enough to recognise a saved value, never enough to use
    it. Values of 4 characters or fewer mask completely rather than echo the whole thing."""
    value = value or ""
    if len(value) <= 4:
        return "•" * len(value)
    return "••••" + value[-4:]


def get_decrypted_credential(site_id: str, platform: str) -> dict | None:
    """The live, decrypted field dict for one platform on one site, or None if nothing is
    saved (or the stored value can no longer be decrypted). Used only by the sync engine's
    connector wiring and the "test saved credential" path -- never by a GET response."""
    from apps.dashboard.models import ProjectSettings

    try:
        blob = ProjectSettings.objects.get(site_url=site_id).data
    except ProjectSettings.DoesNotExist:
        return None
    entry = (blob.get("adsCredentials") or {}).get(platform) or {}
    token = entry.get("enc")
    if not token:
        return None
    try:
        return decrypt_fields(token)
    except InvalidToken:
        return None


def record_test_result(site_id: str, platform: str, ok: bool, detail: str) -> None:
    """Persist the outcome of the last "Test connection" press, shown next to the saved
    credential on the next GET. Recorded even when nothing is saved yet (testing a typed-
    but-not-yet-saved value), so re-opening Settings still shows the last result."""
    from apps.dashboard.models import ProjectSettings

    obj, _ = ProjectSettings.objects.get_or_create(site_url=site_id, defaults={"data": {}})
    data = dict(obj.data)
    data.setdefault("adsCredentials", {})
    entry = dict(data["adsCredentials"].get(platform, {}))
    entry["last_test"] = {
        "ok": ok, "detail": detail, "at": datetime.now(timezone.utc).isoformat(),
    }
    data["adsCredentials"][platform] = entry
    obj.data = data
    obj.save(update_fields=["data", "updated_at"])
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python manage.py test apps.dashboard.services.tests.test_ads_credentials -v 1`
Expected: PASS (4 tests)

- [ ] **Step 7: Commit**

```bash
git add requirements.txt config/settings/base.py config/settings/local.py config/settings/production.py apps/dashboard/services/ads_credentials.py apps/dashboard/services/tests/test_ads_credentials.py
git commit -m "feat(settings): encrypted per-site Ads credential storage module"
```

---

## Task 2: Wire storage into Settings GET/PUT

**Files:**
- Modify: `apps/dashboard/services/settings_service.py` (imports; `build_settings_response`
  around line 628-641; `apply_settings_update` around line 731-752)
- Test: `apps/dashboard/services/tests/test_settings_service.py` (add a class)

**Interfaces:**
- Consumes: `apps.dashboard.services.ads_credentials.{PLATFORM_FIELDS, PLATFORM_REQUIRED_FIELDS, SECRET_FIELD, encrypt_fields, decrypt_fields, mask}` (Task 1)
- Produces: `GET /settings` response gains `adsCredentials: {google_ads: {...}, meta_ads: {...}}`; `PUT /settings` accepts an `adsCredentials` body key

- [ ] **Step 1: Write the failing test**

In `apps/dashboard/services/tests/test_settings_service.py`, add:

```python
class AdsCredentialsSettingsTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)

    def test_save_then_get_returns_masked_value_not_plaintext(self):
        from apps.dashboard.services.settings_service import apply_settings_update, build_settings_response
        result = apply_settings_update(SITE_ID, {"adsCredentials": {"google_ads": {
            "developer_token": "supersecrettoken1234", "customer_id": "123-456-7890",
        }}})
        self.assertEqual(result, {"ok": True})

        response = build_settings_response(SITE_ID)
        google = response["adsCredentials"]["google_ads"]
        self.assertTrue(google["configured"])
        self.assertEqual(google["masked"], "••••1234")
        self.assertNotIn("supersecrettoken1234", str(response))

    def test_missing_required_field_is_refused(self):
        from apps.dashboard.services.settings_service import apply_settings_update
        result = apply_settings_update(SITE_ID, {"adsCredentials": {"meta_ads": {
            "access_token": "tok123",
        }}})  # ad_account_id missing
        self.assertIn("error", result)

    def test_blank_field_on_resave_does_not_erase_existing_value(self):
        from apps.dashboard.services.settings_service import apply_settings_update, build_settings_response
        apply_settings_update(SITE_ID, {"adsCredentials": {"meta_ads": {
            "access_token": "tok123", "ad_account_id": "act_999",
        }}})
        # Re-save with access_token blank -- must keep the previously stored token.
        result = apply_settings_update(SITE_ID, {"adsCredentials": {"meta_ads": {
            "access_token": "", "ad_account_id": "act_999",
        }}})
        self.assertEqual(result, {"ok": True})
        response = build_settings_response(SITE_ID)
        self.assertTrue(response["adsCredentials"]["meta_ads"]["configured"])
        self.assertEqual(response["adsCredentials"]["meta_ads"]["masked"], "••••k123")

    def test_unconfigured_platform_is_honest_not_a_crash(self):
        from apps.dashboard.services.settings_service import build_settings_response
        response = build_settings_response(SITE_ID)
        self.assertEqual(response["adsCredentials"]["google_ads"],
                         {"configured": False, "masked": None, "updated_at": None, "last_test": None})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_settings_service.AdsCredentialsSettingsTests -v 1`
Expected: FAIL — `KeyError: 'adsCredentials'`

- [ ] **Step 3: Add the read path**

In `apps/dashboard/services/settings_service.py`, add to the imports near the top (after
the existing `from pipeline.services.competitor_service import ...` line):

```python
from apps.dashboard.services.ads_credentials import (
    SECRET_FIELD, PLATFORM_FIELDS, PLATFORM_REQUIRED_FIELDS, decrypt_fields, encrypt_fields, mask,
)
```

In `build_settings_response`, immediately after the existing `blob["security"] = {...}`
block (right before the final `return {...}` statement, around line 628-632), add:

```python
    # Masked, GET-only view of the encrypted adsCredentials sub-blob -- overwritten here,
    # same pattern as blob["security"] above, so the raw `enc` token never reaches the
    # returned dict via the **blob spread below.
    ads_credentials = {}
    stored_ads = blob.get("adsCredentials", {})
    for platform, secret_field in SECRET_FIELD.items():
        entry = stored_ads.get(platform) or {}
        token = entry.get("enc")
        masked_value = None
        if token:
            try:
                masked_value = mask(decrypt_fields(token).get(secret_field, ""))
            except Exception:
                masked_value = None
        ads_credentials[platform] = {
            "configured": bool(token and masked_value is not None),
            "masked": masked_value,
            "updated_at": entry.get("updated_at"),
            "last_test": entry.get("last_test"),
        }
    blob["adsCredentials"] = ads_credentials
```

- [ ] **Step 4: Add the write path**

In `apply_settings_update`, immediately before the final `blob_obj.data = data` /
`blob_obj.save(...)` lines (around line 731), add:

```python
    if "adsCredentials" in body and isinstance(body["adsCredentials"], dict):
        # NOTE: validated here, near the end of the function -- an error return at this
        # point does NOT roll back team/credentials/project changes already applied above
        # in this same call. That matches this function's existing behaviour (only the
        # `security` block aborts the whole update up front); it is not a new gap.
        stored_ads = data.get("adsCredentials", {})
        updated_ads = dict(stored_ads)
        save_errors = []
        for platform, incoming in body["adsCredentials"].items():
            if platform not in PLATFORM_FIELDS or not isinstance(incoming, dict):
                continue
            existing_token = stored_ads.get(platform, {}).get("enc")
            try:
                merged = decrypt_fields(existing_token) if existing_token else {}
            except Exception:
                merged = {}
            for field in PLATFORM_FIELDS[platform]:
                if field in incoming:
                    value = (incoming.get(field) or "").strip()
                    # Blank means "leave the stored value alone" -- the SPA never sends a
                    # value it didn't get from the user typing into that field.
                    if value:
                        merged[field] = value
            missing = [f for f in PLATFORM_REQUIRED_FIELDS[platform] if not merged.get(f)]
            if missing:
                save_errors.append(f"{platform}: {', '.join(missing)} required")
                continue
            updated_ads[platform] = {
                **stored_ads.get(platform, {}),
                "enc": encrypt_fields(merged),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        if save_errors:
            return {"error": "Could not save Ads credentials — " + "; ".join(save_errors)}
        data["adsCredentials"] = updated_ads
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test apps.dashboard.services.tests.test_settings_service.AdsCredentialsSettingsTests -v 1`
Expected: PASS (4 tests)

- [ ] **Step 6: Run the full settings_service suite to check for regressions**

Run: `python manage.py test apps.dashboard.services.tests.test_settings_service -v 1`
Expected: PASS (all tests, including the ones that predate this change)

- [ ] **Step 7: Commit**

```bash
git add apps/dashboard/services/settings_service.py apps/dashboard/services/tests/test_settings_service.py
git commit -m "feat(settings): read/write encrypted Ads credentials through GET/PUT /settings"
```

---

## Task 3: Live-probe functions + connection_check_service wrappers

**Files:**
- Modify: `pipeline/connectors/google_ads.py` (add `probe_credential`, after `_build_service`)
- Modify: `pipeline/connectors/meta.py` (add `probe_credential`, after `GRAPH_API_BASE`)
- Modify: `apps/dashboard/services/connection_check_service.py` (add two wrapper functions)
- Test: `pipeline/connectors/tests/test_google_ads_credential_probe.py` (new),
  `pipeline/connectors/tests/test_meta_credential_probe.py` (new),
  `apps/dashboard/services/tests/test_connection_check_service.py` (new)

**Interfaces:**
- Consumes: nothing new
- Produces: `pipeline.connectors.google_ads.probe_credential(developer_token, customer_id, login_customer_id=None) -> tuple[bool, str]`, `pipeline.connectors.meta.probe_credential(access_token, ad_account_id) -> tuple[bool, str]`, `apps.dashboard.services.connection_check_service.test_google_ads_credential(fields: dict) -> dict`, `.test_meta_ads_credential(fields: dict) -> dict`

- [ ] **Step 1: Write the failing tests**

Create `pipeline/connectors/tests/test_google_ads_credential_probe.py`:

```python
"""probe_credential -- the live-probe function backing the Settings 'Test connection'
button for Google Ads. Network is always mocked here; see test_ads_connector_credentials.py
for the constructor override/fallback behaviour."""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from pipeline.connectors.google_ads import probe_credential


class ProbeCredentialTests(TestCase):
    @patch("google.ads.googleads.client.GoogleAdsClient")
    def test_ok_when_search_succeeds(self, mock_client_cls):
        mock_service = MagicMock()
        mock_service.search.return_value = iter([MagicMock()])
        mock_client_cls.load_from_dict.return_value.get_service.return_value = mock_service

        ok, detail = probe_credential("dev-token", "1234567890")
        self.assertTrue(ok)
        self.assertIn("1234567890", detail)

    @patch("google.ads.googleads.client.GoogleAdsClient")
    def test_fail_when_sdk_raises(self, mock_client_cls):
        mock_client_cls.load_from_dict.side_effect = Exception("401 Unauthenticated")

        ok, detail = probe_credential("bad-token", "1234567890")
        self.assertFalse(ok)
        self.assertIn("401 Unauthenticated", detail)
```

Create `pipeline/connectors/tests/test_meta_credential_probe.py`:

```python
"""probe_credential -- the live-probe function backing the Settings 'Test connection'
button for Meta Ads. Network is always mocked here."""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from pipeline.connectors.meta import probe_credential


class ProbeCredentialTests(TestCase):
    @patch("pipeline.connectors.meta.requests.get")
    def test_ok_when_graph_api_returns_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"name": "Acme Ads"})
        ok, detail = probe_credential("tok123", "act_999")
        self.assertTrue(ok)
        self.assertIn("Acme Ads", detail)

    @patch("pipeline.connectors.meta.requests.get")
    def test_fail_when_graph_api_rejects(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=400, json=lambda: {"error": {"message": "Invalid OAuth access token"}},
        )
        ok, detail = probe_credential("bad-tok", "act_999")
        self.assertFalse(ok)
        self.assertIn("Invalid OAuth access token", detail)

    @patch("pipeline.connectors.meta.requests.get", side_effect=Exception("timed out"))
    def test_fail_when_network_error(self, mock_get):
        ok, detail = probe_credential("tok123", "act_999")
        self.assertFalse(ok)
        self.assertIn("timed out", detail)
```

Create `apps/dashboard/services/tests/test_connection_check_service.py`:

```python
"""The wrapper functions backing POST /api/projects/<slug>/ads-credentials/test. The
underlying live probes (pipeline.connectors.{google_ads,meta}.probe_credential) are mocked
here -- their own network behaviour is covered in pipeline/connectors/tests/."""
from unittest.mock import patch

from django.test import TestCase

from apps.dashboard.services.connection_check_service import (
    test_google_ads_credential, test_meta_ads_credential,
)


class TestGoogleAdsCredentialTests(TestCase):
    def test_missing_required_fields_short_circuits_without_a_network_call(self):
        result = test_google_ads_credential({"developer_token": ""})
        self.assertFalse(result["ok"])
        self.assertIn("required", result["detail"])

    @patch("pipeline.connectors.google_ads.probe_credential", return_value=(True, "Verified"))
    def test_delegates_to_the_live_probe(self, mock_probe):
        result = test_google_ads_credential({
            "developer_token": "tok", "customer_id": "123-456-7890",
        })
        self.assertEqual(result, {"ok": True, "detail": "Verified"})
        mock_probe.assert_called_once_with("tok", "1234567890", None)


class TestMetaAdsCredentialTests(TestCase):
    def test_missing_required_fields_short_circuits_without_a_network_call(self):
        result = test_meta_ads_credential({"access_token": "tok"})
        self.assertFalse(result["ok"])
        self.assertIn("required", result["detail"])

    @patch("pipeline.connectors.meta.probe_credential", return_value=(True, "Verified"))
    def test_delegates_to_the_live_probe(self, mock_probe):
        result = test_meta_ads_credential({
            "access_token": "tok", "ad_account_id": "act_999",
        })
        self.assertEqual(result, {"ok": True, "detail": "Verified"})
        mock_probe.assert_called_once_with("tok", "act_999")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
python manage.py test pipeline.connectors.tests.test_google_ads_credential_probe pipeline.connectors.tests.test_meta_credential_probe apps.dashboard.services.tests.test_connection_check_service -v 1
```
Expected: FAIL — `ImportError: cannot import name 'probe_credential'` (x2) and `ImportError:
cannot import name 'test_google_ads_credential'`

- [ ] **Step 3: Implement `probe_credential` in `google_ads.py`**

In `pipeline/connectors/google_ads.py`, add after `_build_service` (which stays unchanged —
it is still used by `fetch()`):

```python
def probe_credential(developer_token: str, customer_id: str,
                     login_customer_id: str | None = None) -> tuple[bool, str]:
    """Can these Google Ads credentials actually reach the API? Never raises -- backs a
    "Test connection" button, same contract as ga4.probe_property.

    Uses the shared Google OAuth env vars (GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN) -- those
    are unrelated to per-site Ads credentials (see the design spec) and are assumed already
    configured, exactly as _build_service() above assumes for a real sync.
    """
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError:
        return False, "google-ads SDK is not installed on the server."

    credentials = {
        "developer_token": developer_token,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
        "use_proto_plus": True,
    }
    if login_customer_id:
        credentials["login_customer_id"] = login_customer_id

    try:
        client = GoogleAdsClient.load_from_dict(credentials)
        service = client.get_service("GoogleAdsService")
        response = service.search(customer_id=customer_id,
                                  query="SELECT customer.id FROM customer LIMIT 1")
        next(iter(response), None)
    except Exception as exc:
        return False, f"Google Ads rejected these credentials: {exc}"
    return True, f"Verified — customer {customer_id} is reachable."
```

- [ ] **Step 4: Implement `probe_credential` in `meta.py`**

In `pipeline/connectors/meta.py`, add after `GRAPH_API_BASE = ...`:

```python
def probe_credential(access_token: str, ad_account_id: str) -> tuple[bool, str]:
    """Can this Meta System User token actually read this ad account? Never raises."""
    try:
        resp = requests.get(f"{GRAPH_API_BASE}/{ad_account_id}",
                            params={"fields": "name", "access_token": access_token}, timeout=15)
    except Exception as exc:
        return False, f"Could not reach the Meta Graph API: {exc}"
    if resp.status_code == 200:
        name = resp.json().get("name", ad_account_id)
        return True, f'Verified — reached ad account "{name}".'
    try:
        message = resp.json().get("error", {}).get("message", resp.text)
    except Exception:
        message = resp.text
    return False, f"Meta rejected these credentials (HTTP {resp.status_code}): {message}"
```

- [ ] **Step 5: Implement the wrapper functions in `connection_check_service.py`**

In `apps/dashboard/services/connection_check_service.py`, add after `_check_google_ads()`:

```python
def test_google_ads_credential(fields: dict) -> dict:
    """Live-probe a typed-in (not necessarily saved) Google Ads credential.
    fields: {developer_token, customer_id, login_customer_id?}
    """
    from pipeline.connectors.google_ads import probe_credential
    developer_token = (fields.get("developer_token") or "").strip()
    customer_id = (fields.get("customer_id") or "").replace("-", "").strip()
    login_customer_id = (fields.get("login_customer_id") or "").replace("-", "").strip() or None
    if not developer_token or not customer_id:
        return {"ok": False, "detail": "Developer Token and Customer ID are both required."}
    ok, detail = probe_credential(developer_token, customer_id, login_customer_id)
    return {"ok": ok, "detail": detail}


def test_meta_ads_credential(fields: dict) -> dict:
    """Live-probe a typed-in (not necessarily saved) Meta Ads credential.
    fields: {access_token, ad_account_id}
    """
    from pipeline.connectors.meta import probe_credential
    access_token = (fields.get("access_token") or "").strip()
    ad_account_id = (fields.get("ad_account_id") or "").strip()
    if not access_token or not ad_account_id:
        return {"ok": False, "detail": "Access Token and Ad Account ID are both required."}
    ok, detail = probe_credential(access_token, ad_account_id)
    return {"ok": ok, "detail": detail}
```

- [ ] **Step 6: Run tests to verify they pass**

Run:
```bash
python manage.py test pipeline.connectors.tests.test_google_ads_credential_probe pipeline.connectors.tests.test_meta_credential_probe apps.dashboard.services.tests.test_connection_check_service -v 1
```
Expected: PASS (7 tests)

- [ ] **Step 7: Commit**

```bash
git add pipeline/connectors/google_ads.py pipeline/connectors/meta.py apps/dashboard/services/connection_check_service.py pipeline/connectors/tests/test_google_ads_credential_probe.py pipeline/connectors/tests/test_meta_credential_probe.py apps/dashboard/services/tests/test_connection_check_service.py
git commit -m "feat(ads): live credential-test probes for Google Ads and Meta Ads"
```

---

## Task 4: `POST /api/projects/<slug>/ads-credentials/test`

**Files:**
- Modify: `apps/api/views.py` (new `AdsCredentialTestView`, after `ProjectSettingsView`)
- Modify: `apps/api/urls.py:23` (add route directly after the settings route)
- Test: `apps/api/tests/test_ads_credentials.py` (new)

**Interfaces:**
- Consumes: `apps.dashboard.services.ads_credentials.{get_decrypted_credential, record_test_result}` (Task 1), `apps.dashboard.services.connection_check_service.{test_google_ads_credential, test_meta_ads_credential}` (Task 3), `resolve_project_or_404`, `check_owner_admin` (existing, `apps/api/views.py`)
- Produces: `POST /api/projects/<slug>/ads-credentials/test` → `{ok: bool, detail: str}`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_ads_credentials.py`:

```python
"""apps/api/tests/test_ads_credentials.py -- POST /api/projects/<slug>/ads-credentials/test."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_URL = "sc-domain:fusehealth.com"


def _bootstrap(test_case):
    """Same recipe as test_settings.py's _bootstrap_settings_test_env -- kept as its own
    copy per this project's test-file convention (see that file's docstring)."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)

    with get_session() as session:
        session.add(Site(site_url=SITE_URL, site_name="FuseHealth",
                          slug="fusehealth", is_active=1))

    user = get_user_model().objects.create_user("founder1", password="x")
    token = Token.objects.get(user=user)
    client_auth = APIClient()
    client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client_auth


class AdsCredentialTestEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)

    @patch("apps.dashboard.services.connection_check_service.test_meta_ads_credential",
          return_value={"ok": True, "detail": "Verified"})
    def test_tests_typed_in_fields_without_saving(self, mock_test):
        resp = self.client_auth.post("/api/projects/fusehealth/ads-credentials/test", {
            "platform": "meta_ads", "access_token": "tok", "ad_account_id": "act_999",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "detail": "Verified"})
        mock_test.assert_called_once()

    def test_use_saved_with_nothing_saved_reports_ok_false(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ads-credentials/test", {
            "platform": "google_ads", "useSaved": True,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["ok"])

    def test_invalid_platform_is_a_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ads-credentials/test", {
            "platform": "tiktok_ads",
        })
        self.assertEqual(resp.status_code, 400)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.api.tests.test_ads_credentials -v 1`
Expected: FAIL — `404` (no such route yet)

- [ ] **Step 3: Add the view**

In `apps/api/views.py`, add directly after the `ProjectSettingsView` class (after line 735):

```python
@method_decorator(login_not_required, name="dispatch")
class AdsCredentialTestView(APIView):
    """POST /api/projects/<slug>/ads-credentials/test -- live-probes a Google Ads / Meta
    Ads credential, either freshly typed (not yet saved) or the one already stored for
    this site. Same Owner/Admin gate as ProjectSettingsView.PUT: this spends a real API
    call against the platform's quota, exactly like saving spends a database write.

    body: {platform: "google_ads"|"meta_ads", ...fields}
        | {platform: "google_ads"|"meta_ads", useSaved: true}
    -> {ok: bool, detail: str}
    """
    def post(self, request, slug):
        if not check_owner_admin(request.user):
            return Response({"detail": "Testing Ads credentials requires Owner or Admin access."},
                            status=403)

        from apps.dashboard.services.ads_credentials import get_decrypted_credential, record_test_result
        from apps.dashboard.services.connection_check_service import (
            test_google_ads_credential, test_meta_ads_credential,
        )

        platform = request.data.get("platform")
        if platform not in ("google_ads", "meta_ads"):
            return Response({"detail": "platform must be 'google_ads' or 'meta_ads'."}, status=400)

        site_id = resolve_project_or_404(slug).site_url
        if request.data.get("useSaved"):
            fields = get_decrypted_credential(site_id, platform)
            if fields is None:
                return Response({"ok": False, "detail": "No saved credential to test."})
        else:
            fields = request.data

        tester = test_google_ads_credential if platform == "google_ads" else test_meta_ads_credential
        result = tester(fields)
        record_test_result(site_id, platform, result["ok"], result["detail"])
        return Response(result)
```

- [ ] **Step 4: Add the route**

In `apps/api/urls.py`, immediately after line 23 (`project-settings`):

```python
    path("projects/<slug:slug>/ads-credentials/test", views.AdsCredentialTestView.as_view(), name="ads-credentials-test"),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test apps.api.tests.test_ads_credentials -v 1`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add apps/api/views.py apps/api/urls.py apps/api/tests/test_ads_credentials.py
git commit -m "feat(api): POST /ads-credentials/test endpoint for live credential checks"
```

---

## Task 5: Connector constructor overrides + sync engine wiring

**Files:**
- Modify: `pipeline/connectors/google_ads.py:37-47` (`__init__`)
- Modify: `pipeline/connectors/meta.py:34-43` (`__init__`)
- Modify: `pipeline/services/sync_engine.py:119-170` (`_get_connector`), lines ~334 and ~483 (call sites)
- Modify: `apps/api/tests/test_sync_engine.py` (`_stub_connectors`'s `factory`; add a new test class)
- Test: `pipeline/connectors/tests/test_ads_connector_credentials.py` (new)

**Interfaces:**
- Consumes: `apps.dashboard.services.ads_credentials.get_decrypted_credential` (Task 1)
- Produces: `GoogleAdsConnector(credentials: dict | None = None)`, `MetaConnector(credentials: dict | None = None)`, `sync_engine._get_connector(name: str, site_id: str | None = None)`

- [ ] **Step 1: Write the failing tests**

Create `pipeline/connectors/tests/test_ads_connector_credentials.py`:

```python
"""DB-saved credentials override .env, and .env is still the fallback when nothing is
saved for a site. See docs/superpowers/specs/2026-08-03-ads-credentials-design.md."""
import os
from unittest.mock import patch

from django.test import TestCase

from pipeline.connectors.google_ads import GoogleAdsConnector
from pipeline.connectors.meta import MetaConnector


class GoogleAdsCredentialOverrideTests(TestCase):
    @patch.dict(os.environ, {
        "GOOGLE_ADS_CUSTOMER_ID": "1112223333", "GOOGLE_ADS_DEVELOPER_TOKEN": "env-token",
    })
    def test_falls_back_to_env_when_no_override_given(self):
        conn = GoogleAdsConnector()
        self.assertEqual(conn.developer_token, "env-token")
        self.assertEqual(conn.customer_id, "1112223333")

    @patch.dict(os.environ, {
        "GOOGLE_ADS_CUSTOMER_ID": "1112223333", "GOOGLE_ADS_DEVELOPER_TOKEN": "env-token",
    })
    def test_db_credentials_override_env(self):
        conn = GoogleAdsConnector(credentials={
            "developer_token": "db-token", "customer_id": "999-888-7777",
        })
        self.assertEqual(conn.developer_token, "db-token")
        self.assertEqual(conn.customer_id, "9998887777")  # dashes stripped, same as env path

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_when_neither_db_nor_env_has_credentials(self):
        with self.assertRaises(ValueError):
            GoogleAdsConnector()


class MetaCredentialOverrideTests(TestCase):
    @patch.dict(os.environ, {"META_ACCESS_TOKEN": "env-tok", "META_AD_ACCOUNT_ID": "act_env"})
    def test_falls_back_to_env_when_no_override_given(self):
        conn = MetaConnector()
        self.assertEqual(conn.access_token, "env-tok")

    @patch.dict(os.environ, {"META_ACCESS_TOKEN": "env-tok", "META_AD_ACCOUNT_ID": "act_env"})
    def test_db_credentials_override_env(self):
        conn = MetaConnector(credentials={"access_token": "db-tok", "ad_account_id": "act_db"})
        self.assertEqual(conn.access_token, "db-tok")
        self.assertEqual(conn.ad_account_id, "act_db")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test pipeline.connectors.tests.test_ads_connector_credentials -v 1`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'credentials'`

- [ ] **Step 3: Update `GoogleAdsConnector.__init__`**

In `pipeline/connectors/google_ads.py`, replace `__init__` (lines 37-47):

```python
    def __init__(self, credentials: dict | None = None):
        super().__init__()
        credentials = credentials or {}
        self.customer_id = (credentials.get("customer_id")
                           or os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")).replace("-", "")
        self.developer_token = credentials.get("developer_token") or os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.login_customer_id = (credentials.get("login_customer_id")
                                 or os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")).replace("-", "")

        if not self.customer_id or not self.developer_token:
            raise ValueError(
                "[google_ads] Missing GOOGLE_ADS_CUSTOMER_ID or GOOGLE_ADS_DEVELOPER_TOKEN. "
                "Set them in .env, or save a credential in Settings → Connections. "
                "Also ensure Standard Access has been approved."
            )
```

`GoogleAdsSearchTermsConnector` (`pipeline/connectors/google_ads_search_terms.py`) subclasses
this without overriding `__init__`, so it inherits the new signature unchanged — no edit
needed there.

- [ ] **Step 4: Update `MetaConnector.__init__`**

In `pipeline/connectors/meta.py`, replace `__init__` (lines 34-43):

```python
    def __init__(self, credentials: dict | None = None):
        super().__init__()
        credentials = credentials or {}
        self.access_token = credentials.get("access_token") or os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = credentials.get("ad_account_id") or os.getenv("META_AD_ACCOUNT_ID")

        if not self.access_token or not self.ad_account_id:
            raise ValueError(
                "[meta] Missing META_ACCESS_TOKEN or META_AD_ACCOUNT_ID. Set them in .env, "
                "or save a credential in Settings → Connections. Must use a System User "
                "token — not a personal token."
            )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test pipeline.connectors.tests.test_ads_connector_credentials -v 1`
Expected: PASS (5 tests)

- [ ] **Step 6: Wire the sync engine's connector factory**

In `pipeline/services/sync_engine.py`, replace the `_get_connector` signature and body
(the `connector_map` dict itself is unchanged — only the wrapper around it):

```python
def _get_connector(name: str, site_id: str | None = None):
    """
    Import and instantiate a connector by name.
    Returns None if the module cannot be imported or credentials are missing.
    Lazy imports avoid circular import issues at module load time.

    `site_id`, when given, is used to look up this site's saved Ads credentials
    (google_ads / google_ads_search_terms / meta) so a per-site DB-saved credential wins
    over the process-wide .env fallback those connectors' own __init__ still falls back
    to. Every other connector ignores it -- passing site_id costs nothing for them.
    """
    connector_map: dict[str, tuple[str, str]] = {
        "gsc":          ("pipeline.connectors.gsc",                   "GSCConnector"),
        "ga4":          ("pipeline.connectors.ga4",                   "GA4Connector"),
        "gsc_keywords": ("pipeline.connectors.gsc_keywords",          "GSCKeywordsConnector"),
        "gsc_pages":    ("pipeline.connectors.gsc_pages",             "GSCPagesConnector"),
        "url_inspection":("pipeline.connectors.url_inspection",       "URLInspectionConnector"),
        "pagespeed":    ("pipeline.connectors.pagespeed",             "PageSpeedConnector"),
        "sitemap":      ("pipeline.connectors.sitemap",               "SitemapConnector"),
        # Needs no credentials — it probes the customer's own domain over plain HTTPS.
        "domain_checks":("pipeline.connectors.domain_checks",         "DomainChecksConnector"),
        # DataForSEO — included in map so they can be enabled later; not in
        # PAGE_CONNECTORS or ALL_CONNECTORS until balance is positive.
        "dataforseo_keywords":         ("pipeline.connectors.dataforseo_keywords",         "DataForSEOKeywordsConnector"),
        "dataforseo_serp":             ("pipeline.connectors.dataforseo_serp",             "DataForSEOSerpConnector"),
        "dataforseo_backlinks":        ("pipeline.connectors.dataforseo_backlinks",        "DataForSEOBacklinksConnector"),
        "dataforseo_labs_competitors": ("pipeline.connectors.dataforseo_labs_competitors", "DataForSEOLabsCompetitorsConnector"),
        "dataforseo_onpage":           ("pipeline.connectors.dataforseo_onpage",           "DataForSEOOnPageConnector"),
        "dataforseo_opportunities":    ("pipeline.connectors.dataforseo_opportunities",    "DataForSEOOpportunitiesConnector"),
        # Additive 2026-06-15: per-keyword competitor rank capture + AI search keyword data.
        "dataforseo_serp_competitors": ("pipeline.connectors.dataforseo_serp_competitors", "DataForSEOSerpCompetitorsConnector"),
        "dataforseo_ai_keywords":      ("pipeline.connectors.dataforseo_ai_keywords",      "DataForSEOAIKeywordsConnector"),
        "dataforseo_llm_mentions":     ("pipeline.connectors.dataforseo_llm_mentions",     "DataForSEOLLMMentionsConnector"),
        # Credentials-missing connectors — in map for future use.
        "google_ads":  ("pipeline.connectors.google_ads",  "GoogleAdsConnector"),
        # Separate from google_ads on purpose: search_term_view is a different GAQL resource
        # with its own grain and its own reporting restrictions, so it can 403 independently.
        # One connector = one table = one SyncLog row = you can tell which half broke.
        "google_ads_search_terms": ("pipeline.connectors.google_ads_search_terms", "GoogleAdsSearchTermsConnector"),
        "meta":        ("pipeline.connectors.meta",        "MetaConnector"),
        "linkedin":    ("pipeline.connectors.linkedin",    "LinkedInConnector"),
        "webflow":     ("pipeline.connectors.webflow",     "WebflowConnector"),
        "wordpress":   ("pipeline.connectors.wordpress",   "WordPressConnector"),
    }

    if name not in connector_map:
        logger.warning(f"[sync_engine] Unknown connector: {name!r}")
        return None

    module_path, class_name = connector_map[name]
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        kwargs = {}
        if site_id and name in ("google_ads", "google_ads_search_terms", "meta"):
            from apps.dashboard.services.ads_credentials import get_decrypted_credential
            platform = "meta_ads" if name == "meta" else "google_ads"
            saved = get_decrypted_credential(site_id, platform)
            if saved:
                kwargs["credentials"] = saved
        return cls(**kwargs)
    except (ValueError, ImportError, Exception) as exc:
        logger.warning(f"[sync_engine] Could not load connector {name!r}: {exc}")
        return None
```

(Leave the `connector_map` dict body exactly as it is today — only the code above and
below it changes.)

At the two call sites, change `connector = _get_connector(name)` to
`connector = _get_connector(name, site_id=site_url)` — once in `sync_all` (currently
around line 334) and once in `sync_page` (currently around line 483). Both functions
already have `site_url` in scope at that point.

- [ ] **Step 7: Fix the existing engine test's stub factory**

In `apps/api/tests/test_sync_engine.py`, `_stub_connectors`'s inner `factory` currently
takes only `name`. Since `_get_connector` is now called with a `site_id` keyword at both
call sites, update it:

```python
        def factory(name, site_id=None):
            if name in overrides and overrides[name] is None:
                return None  # simulates missing credentials
            conn = overrides.get(name) or FakeConnector(name)
            self.built[name] = conn
            return conn
```

- [ ] **Step 8: Add a test for the real `_get_connector` credential wiring**

In the same file, add (this exercises the real `_get_connector`, unlike every other test
in this file which patches it away):

```python
class GetConnectorCredentialWiringTests(TestCase):
    """_get_connector itself (not stubbed) -- does it load and pass per-site Ads
    credentials? See docs/superpowers/specs/2026-08-03-ads-credentials-design.md."""

    @patch("apps.dashboard.services.ads_credentials.get_decrypted_credential",
          return_value={"access_token": "db-tok", "ad_account_id": "act_db"})
    def test_meta_connector_receives_saved_credentials(self, mock_get_creds):
        conn = sync_engine._get_connector("meta", site_id=SITE_URL)
        self.assertIsNotNone(conn)
        self.assertEqual(conn.access_token, "db-tok")
        mock_get_creds.assert_called_once_with(SITE_URL, "meta_ads")

    @patch("apps.dashboard.services.ads_credentials.get_decrypted_credential", return_value=None)
    def test_meta_connector_falls_back_to_env_when_nothing_saved(self, mock_get_creds):
        with patch.dict("os.environ", {"META_ACCESS_TOKEN": "env-tok", "META_AD_ACCOUNT_ID": "act_env"}):
            conn = sync_engine._get_connector("meta", site_id=SITE_URL)
        self.assertIsNotNone(conn)
        self.assertEqual(conn.access_token, "env-tok")

    def test_no_site_id_skips_the_credential_lookup_entirely(self):
        # domain_checks needs no credentials at all -- confirms the site_id=None default
        # (every other existing caller) still works unchanged.
        conn = sync_engine._get_connector("domain_checks")
        self.assertIsNotNone(conn)
```

- [ ] **Step 9: Run the full sync engine test file**

Run: `python manage.py test apps.api.tests.test_sync_engine -v 1`
Expected: PASS (every existing test in the file, plus the 3 new ones)

- [ ] **Step 10: Commit**

```bash
git add pipeline/connectors/google_ads.py pipeline/connectors/meta.py pipeline/services/sync_engine.py apps/api/tests/test_sync_engine.py pipeline/connectors/tests/test_ads_connector_credentials.py
git commit -m "feat(sync): connectors use saved per-site Ads credentials, .env as fallback"
```

---

## Task 6: Frontend — credential form replacing the status-card explainers

**Files:**
- Modify: `static/spa/src/pages/settings.html:302-380`
- Modify: `static/spa/src/js/pages/settings.js:142-330` and `~494-495` (`adsCards`/`adsIntro` assignment)
- Modify: `static/spa/src/js/app.js` (state init `~62-63`, seed block `~288-299`, two new methods near `saveCreds`/`testConnections`)

**Interfaces:**
- Consumes: `data.adsCredentials` (Task 2's GET shape), `PUT /settings {adsCredentials: {...}}` (Task 2), `POST /ads-credentials/test` (Task 4)
- Produces: rendered Ads platforms card with editable fields, Test/Save buttons

- [ ] **Step 1: Replace the settings.html markup**

In `static/spa/src/pages/settings.html`, replace lines 302-380 (the whole
`<!-- Ads platforms ... -->` comment through its closing `</div>`) with:

```html
          <!-- Ads platforms: credential entry + live test-connection. See
               docs/superpowers/specs/2026-08-03-ads-credentials-design.md. -->
          <div style="border-radius: 12px; background: white; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); overflow: hidden;">
            <div style="padding: 16px 24px; border-bottom: 1px solid #f1f5f9;">
              <h2 style="font-size: 15px; font-weight: 600; margin: 0;">Ads platforms</h2>
              <p style="font-size: 12px; color: #94a3b8; margin: 4px 0 0;">{{ st.adsIntro }}</p>
            </div>
            <sc-for list="{{ st.adsCards }}" as="ad" hint-placeholder-count="2">
              <div style="padding: 20px 24px; border-top: 1px solid #f1f5f9; display: flex; gap: 28px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 280px;">
                  <div style="display: flex; align-items: center; gap: 9px; flex-wrap: wrap;">
                    <span style="{{ ad.dotStyle }}"></span>
                    <span style="font-size: 14px; font-weight: 600; color: #0f172a;">{{ ad.name }}</span>
                    <span style="{{ ad.statusStyle }}">{{ ad.statusLabel }}</span>
                  </div>

                  <sc-for list="{{ ad.fields }}" as="f" hint-placeholder-count="3">
                    <div style="margin-top: 12px;">
                      <label style="font-size: 12px; font-weight: 600; color: #334155; display: block; margin-bottom: 4px;">{{ f.label }}</label>
                      <input value="{{ f.value }}" onInput="{{ f.onInput }}" placeholder="{{ f.placeholder }}" style="width: 100%; box-sizing: border-box; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-family: monospace; font-size: 13px; color: #334155; outline: none;">
                    </div>
                  </sc-for>

                  <div style="display: flex; align-items: center; gap: 10px; margin-top: 14px; flex-wrap: wrap;">
                    <span onClick="{{ ad.onTest }}" role="button" style="{{ ad.testBtnStyle }}">{{ ad.testLabel }}</span>
                    <span onClick="{{ ad.onSave }}" role="button" style="{{ ad.saveBtnStyle }}">{{ ad.saveLabel }}</span>
                  </div>

                  <sc-if value="{{ ad.hasTestResult }}" hint-placeholder-val="{{ false }}">
                    <div style="{{ ad.testResultStyle }}">{{ ad.testResultText }}</div>
                  </sc-if>
                </div>

                <div style="flex: 1; min-width: 220px; font-size: 12px; color: #64748b; line-height: 1.55;">
                  {{ ad.instruction }}
                </div>
              </div>
            </sc-for>
          </div>
```

- [ ] **Step 2: Replace the settings.js data layer**

In `static/spa/src/js/pages/settings.js`, replace lines 142-330 (the whole
`/* ---- connections: Ads platforms ... */` block through the closing `});` of `adsCards`)
with:

```javascript
      /* ---- connections: Ads platforms (Google Ads / Meta Ads) -------------------------
         A real credential-entry form: fields are typed here, saved via
         PUT /settings {adsCredentials: {...}} (settings_service.apply_settings_update),
         and tested via this.testAdsCredential -> POST .../ads-credentials/test, either
         against the typed-in draft or (if nothing was edited) the already-saved value.
         See docs/superpowers/specs/2026-08-03-ads-credentials-design.md. */
      const adsSaved = data.adsCredentials || {};
      const adsDraft = s.adsCreds || { google_ads: {}, meta_ads: {} };
      const adsTesting = s.adsTesting || {};
      const adsSaving = s.adsSaving || {};
      const adsTestResult = s.adsTestResult || {};
      const SECRET_FIELD_BY_PLATFORM = { google_ads: 'developer_token', meta_ads: 'access_token' };
      const adsPill = tone => ({ fontSize: '11px', fontWeight: 600, padding: '2px 9px', borderRadius: '9999px', background: tone.pillBg, color: tone.pillFg });
      const adsBtn = (busy, bg) => ({ display: 'inline-flex', padding: '8px 16px', background: bg, color: 'white', fontSize: '13px', fontWeight: 600, borderRadius: '8px', cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1 });
      const adsResultBox = ok => ({ marginTop: '10px', fontSize: '12px', lineHeight: 1.5, padding: '8px 10px', borderRadius: '6px', color: ok ? '#15803d' : '#b91c1c', background: ok ? '#f0fdf4' : '#fff1f2', border: '1px solid ' + (ok ? '#bbf7d0' : '#fecaca') });

      const ADS_PLATFORMS = [
        {
          key: 'google_ads',
          name: 'Google Ads',
          fields: [
            { name: 'developer_token', label: 'Developer Token', placeholder: 'Issued in Google Ads → Tools → API Center' },
            { name: 'customer_id', label: 'Customer ID', placeholder: 'e.g. 1234567890' },
            { name: 'login_customer_id', label: 'Manager (MCC) Customer ID — optional', placeholder: 'Only if the account sits under a manager account' },
          ],
          instruction: 'Get your developer token from Google Ads → Tools → API Center. Customer ID is the 10-digit account number shown top-right in Google Ads.',
        },
        {
          key: 'meta_ads',
          name: 'Meta Ads',
          fields: [
            { name: 'access_token', label: 'Access Token', placeholder: 'System User token (Business Manager)' },
            { name: 'ad_account_id', label: 'Ad Account ID', placeholder: 'act_XXXXXXXXXX' },
          ],
          instruction: 'Create a System User token in Business Manager → System Users — a personal token will expire. Ad Account ID is in Business Manager → Ad Accounts, in the act_XXXXXXXXXX form.',
        },
      ];

      const adsCards = ADS_PLATFORMS.map(p => {
        const saved = adsSaved[p.key] || { configured: false, masked: null };
        const draft = adsDraft[p.key] || {};
        const testing = !!adsTesting[p.key];
        const saving = !!adsSaving[p.key];
        const result = adsTestResult[p.key];
        const tone = saved.configured
          ? { label: 'Credential saved', dot: '#22c55e', pillBg: '#ecfdf5', pillFg: '#059669' }
          : { label: 'Not connected', dot: '#cbd5e1', pillBg: '#f1f5f9', pillFg: '#94a3b8' };

        return {
          name: p.name,
          statusLabel: tone.label,
          statusStyle: adsPill(tone),
          dotStyle: { width: '9px', height: '9px', borderRadius: '9999px', background: tone.dot, flexShrink: 0 },
          fields: p.fields.map(f => {
            const isSecret = f.name === SECRET_FIELD_BY_PLATFORM[p.key];
            const placeholder = (isSecret && saved.configured)
              ? ('Saved: ' + saved.masked + ' — leave blank to keep it')
              : f.placeholder;
            return {
              label: f.label,
              value: draft[f.name] || '',
              placeholder: placeholder,
              onInput: e => this.setState(prev => ({
                adsCreds: Object.assign({}, prev.adsCreds, {
                  [p.key]: Object.assign({}, (prev.adsCreds || {})[p.key], { [f.name]: e.target.value }),
                }),
              })),
            };
          }),
          testLabel: testing ? 'Testing…' : 'Test connection',
          testBtnStyle: adsBtn(testing, '#4f46e5'),
          onTest: () => { if (!testing) this.testAdsCredential(p.key); },
          saveLabel: saving ? 'Saving…' : 'Save',
          saveBtnStyle: adsBtn(saving, '#10b981'),
          onSave: () => { if (!saving) this.saveAdsCredential(p.key); },
          hasTestResult: !!result,
          testResultText: result ? result.detail : '',
          testResultStyle: result ? adsResultBox(result.ok) : {},
          instruction: p.instruction,
        };
      });
```

Then, near line 494-495 where `adsCards`/`adsIntro` are assigned onto `vals.st`, change
the intro copy to match the shorter instruction the user asked for:

```javascript
      adsCards: adsCards,
      adsIntro: 'Enter your Ads platform credentials, then test the connection.',
```

- [ ] **Step 3: Add state, seeding, and the two methods to app.js**

In `static/spa/src/js/app.js`, near the existing `creds`/`credsTesting` state
initialisation (around line 62-63), add:

```javascript
    adsCreds: { google_ads: {}, meta_ads: {} }, adsCredsFor: null,
    adsSaving: {}, adsTesting: {}, adsTestResult: {},
```

Near the existing `credsFor` seeding block inside the settings-tab fetch handler (around
line 288-299), add a sibling block:

```javascript
          if (tab === 'settings' && s.adsCredsFor !== pid) {
            // Fields always start blank -- the real value never comes back from the
            // server (see build_settings_response's masking), so there is nothing to
            // pre-fill. Typing something means "replace"; leaving it blank means "keep
            // what's already saved" (see apply_settings_update's merge).
            next.adsCreds = { google_ads: {}, meta_ads: {} };
            next.adsCredsFor = pid;
            next.adsTestResult = {};
          }
```

Near the existing `saveCreds`/`testConnections` methods (around line 1459-1504), add:

```javascript
  saveAdsCredential(platform) {
    const pid = this.state.projectId;
    const fields = this.state.adsCreds[platform] || {};
    this.setState(s => ({ adsSaving: Object.assign({}, s.adsSaving, { [platform]: true }) }));
    window.FuseAPI.put('/api/projects/' + pid + '/settings', {
      adsCredentials: { [platform]: fields },
    }).then(() => {
      if (!this._alive) return;
      this.setState(s => ({
        adsSaving: Object.assign({}, s.adsSaving, { [platform]: false }),
        adsCredsFor: null, // re-seed blank drafts + the fresh masked value from the server
      }));
      this.notify('Saved');
    }).catch(err => {
      if (!this._alive) return;
      this.setState(s => ({ adsSaving: Object.assign({}, s.adsSaving, { [platform]: false }) }));
      this.notify(this.errText(err, 'Could not save these credentials'));
    });
  }

  /* Tests whatever is in the form right now: the typed draft if anything was edited,
     otherwise the already-saved credential (useSaved) -- so re-testing a saved value
     never requires retyping a secret the UI never shows in the clear. */
  testAdsCredential(platform) {
    const pid = this.state.projectId;
    const draft = this.state.adsCreds[platform] || {};
    const edited = Object.values(draft).some(v => (v || '').trim());
    const body = edited
      ? Object.assign({ platform: platform }, draft)
      : { platform: platform, useSaved: true };
    this.setState(s => ({
      adsTesting: Object.assign({}, s.adsTesting, { [platform]: true }),
      adsTestResult: Object.assign({}, s.adsTestResult, { [platform]: null }),
    }));
    window.FuseAPI.post('/api/projects/' + pid + '/ads-credentials/test', body).then(result => {
      if (!this._alive) return;
      this.setState(s => ({
        adsTesting: Object.assign({}, s.adsTesting, { [platform]: false }),
        adsTestResult: Object.assign({}, s.adsTestResult, { [platform]: result }),
      }));
    }).catch(err => {
      if (!this._alive) return;
      this.setState(s => ({ adsTesting: Object.assign({}, s.adsTesting, { [platform]: false }) }));
      this.notify(this.errText(err, 'Could not run the connection test'));
    });
  }
```

- [ ] **Step 4: Manual verification (no JS test runner in this project)**

Per this project's rule that UI changes must be exercised in a real browser before being
called done:

1. Run: `python manage.py runserver`
2. Open `http://localhost:8000/#settings`, go to the Connections sub-tab.
3. Confirm the Ads platforms card now shows input fields (Developer Token / Customer ID /
   Manager Customer ID for Google Ads; Access Token / Ad Account ID for Meta Ads) with a
   short instruction line to the right of each — not the old multi-paragraph explainer.
4. Type an obviously-invalid value into Meta's fields, click **Test connection** — expect
   a red failure detail from the real Graph API call (not a crash, not a false "connected").
5. Click **Save**, reload the page — expect the fields to be blank again but the status
   pill to read "Credential saved", and clicking **Test connection** with nothing typed
   to re-test the saved value (`useSaved`).
6. Repeat steps 3-5 for Google Ads if a developer token is available; otherwise confirm
   the failure path at minimum (e.g. a blank Developer Token still lets Save/Test render
   without a JS console error).

- [ ] **Step 5: Commit**

```bash
git add static/spa/src/pages/settings.html static/spa/src/js/pages/settings.js static/spa/src/js/app.js
git commit -m "feat(settings): replace Ads status-card explainers with a credential-entry form"
```

---

## Task 7: Update `.claude/` documentation

**Files:**
- Modify: `.claude/api-reference.md` (after the `POST /api/connection-check` section, ~line
  235; and the `PUT /api/projects/<slug>/settings` table, ~line 826)
- Modify: `.claude/features.md` (`### Connections` section, ~line 949-955)

**Interfaces:** none (docs only)

- [ ] **Step 1: Document the new endpoint in api-reference.md**

In `.claude/api-reference.md`, immediately after the `POST /api/connection-check` section
(after the line ending "...because the entire point of this endpoint is to survive the
failures it describes."), add:

```markdown
### `POST /api/projects/<slug>/ads-credentials/test`

Live-probes a Google Ads / Meta Ads credential — either freshly typed into the Settings
form (not yet saved) or the credential already stored for this site (`useSaved: true`).
**Permission:** `check_owner_admin` → **403** for an `Analyst` (same gate as the settings
PUT, since this spends a real API call against the platform's quota).

**Request**

```json
{ "platform": "google_ads", "developer_token": "...", "customer_id": "1234567890" }
```
or
```json
{ "platform": "meta_ads", "useSaved": true }
```

**Response:** `{ "ok": true, "detail": "Verified — customer 1234567890 is reachable." }`

Backed by `apps/dashboard/services/connection_check_service.py::test_google_ads_credential`
/ `test_meta_ads_credential`, which delegate to `pipeline/connectors/{google_ads,meta}.py`'s
`probe_credential()`. Every result (pass or fail) is recorded as `last_test` on the site's
stored `adsCredentials` entry via `ads_credentials.record_test_result`, so it survives a
page reload.
```

In the `PUT /api/projects/<slug>/settings` table (the one starting "| Key | Effect |"),
add a row:

```markdown
| `adsCredentials` | Per-platform (`google_ads`/`meta_ads`) fields, encrypted and merged into `ProjectSettings.data` — see `apps/dashboard/services/ads_credentials.py`. A blank submitted field leaves the stored value alone. |
```

- [ ] **Step 2: Update features.md's Connections section**

In `.claude/features.md`, in the `### Connections` section, immediately after the line
ending "...what is missing is on-platform impressions & CTR." (before the "These were
Connect/Disconnect buttons..." paragraph, which is about a different row), add:

```markdown
**Ads platforms** (Google Ads / Meta Ads) is a real credential-entry form as of
2026-08-03 — not a display: each platform has its own fields (Google Ads: Developer
Token, Customer ID, optional Manager/MCC Customer ID; Meta Ads: Access Token, Ad Account
ID), a **Test connection** button that makes one real, cheap API call against whatever is
currently in the form (or the already-saved value if nothing was edited), and a **Save**
button. Credentials are encrypted at rest in `ProjectSettings.data["adsCredentials"]`
(never round-tripped back to the browser — only a last-4-characters mask) and are what
`GoogleAdsConnector`/`MetaConnector` actually use during a sync, falling back to the
server's `.env` values for any site with nothing saved. See
`docs/superpowers/specs/2026-08-03-ads-credentials-design.md`.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/api-reference.md .claude/features.md
git commit -m "docs: document the Ads credentials endpoint and form"
```

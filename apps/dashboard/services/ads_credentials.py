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

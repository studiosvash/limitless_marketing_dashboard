"""pipeline/connectors/dataforseo_probe.py — free credential + balance check for DataForSEO.

There was no DataForSEO validity check anywhere in the codebase. The only signal was each
connector's `__init__` raising when login/password were unset -- and `sync_engine._get_connector`
swallows that, returns None, and `sync_page` logs "unavailable — skipping" while still marking
the run SUCCESS. So a project with wrong (or simply out-of-credit) DataForSEO credentials
reported a clean sync and silently produced no keyword, competitor, backlink or on-page data.

`/v3/appendix/user_data` is the right endpoint for this: it is FREE (it is the account-info
call, not a data call), it authenticates with the same basic auth every other connector uses,
and it returns the remaining balance -- which is the other thing that silently breaks a sync,
because a zero balance fails per-request rather than at login.

Deliberately not a BaseConnector: it writes nothing, has no table, and must never appear as a
SyncLog row. It is a probe, not a data source.
"""

import os

import requests
from dotenv import load_dotenv

from pipeline.utils.logger import get_logger

load_dotenv()

logger = get_logger("connectors.dataforseo_probe")

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
REQUEST_TIMEOUT = 20


def credentials_present() -> bool:
    """Cheap, no-network check — are the env vars set at all?"""
    return bool(os.getenv("DATAFORSEO_LOGIN") and os.getenv("DATAFORSEO_PASSWORD"))


def probe_credentials() -> tuple[bool, str]:
    """Are the DataForSEO credentials valid, and is there credit left?

    Returns (ok, human-readable detail). Never raises: this backs a "Test connection" button
    and a CLI check.

    A valid login with a zero balance returns ok=False, because for every practical purpose
    the integration is broken -- every metered call will fail. The message says which of the
    two problems it is, since the fixes are completely different.
    """
    login = os.getenv("DATAFORSEO_LOGIN")
    password = os.getenv("DATAFORSEO_PASSWORD")
    if not login or not password:
        return False, "DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD are not set in the environment."

    try:
        resp = requests.get(
            f"{DATAFORSEO_BASE}/appendix/user_data",
            auth=(login, password),
            timeout=REQUEST_TIMEOUT,
        )
    except Exception as exc:
        return False, f"Could not reach DataForSEO: {exc}"

    if resp.status_code in (401, 403):
        return False, "DataForSEO rejected the credentials (401/403). Check login and password."
    if resp.status_code != 200:
        return False, f"DataForSEO returned HTTP {resp.status_code}."

    try:
        data = resp.json()
    except Exception:
        return False, "DataForSEO returned a response that was not JSON."

    # DataForSEO nests everything under tasks[0].result[0]; status_code 20000 means OK.
    if data.get("status_code") != 20000:
        return False, f"DataForSEO error {data.get('status_code')}: {data.get('status_message')}"

    try:
        info = data["tasks"][0]["result"][0]
    except (KeyError, IndexError, TypeError):
        return True, "Credentials valid (account details unavailable)."

    balance = (info.get("money") or {}).get("balance")
    if balance is None:
        return True, "Credentials valid (balance not reported)."
    if balance <= 0:
        return False, (
            f"Credentials valid but the account balance is ${balance:.2f}. "
            "Every metered call will fail until the account is topped up."
        )
    return True, f"Credentials valid — balance ${balance:.2f}."

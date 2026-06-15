"""
Environment / API credential audit.

Reads the project .env and reports, for each external API, whether credentials are
present and (for the ones that are) whether they actually authenticate with a light,
read-only call. It NEVER prints secret values — only PASS/FAIL and non-sensitive
account info.

Run:  python scripts/audit_env.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TIMEOUT = 15


def has(*keys: str) -> bool:
    """True only if every named env var is present and non-empty."""
    return all((os.environ.get(k) or "").strip() for k in keys)


def line(api: str, present: bool, status: str, note: str = "") -> None:
    mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "SKIP": "[ -- ]", "MISS": "[MISS]"}[status]
    pres = "yes" if present else "no "
    print(f"  {api:<22} creds:{pres}  {mark:<8} {note}")


def check_google_oauth() -> None:
    """Exchange the refresh token for an access token (validates GSC + GA4 auth)."""
    if not has("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"):
        line("Google OAuth", False, "MISS", "GSC/GA4 cannot authenticate without these")
        return
    try:
        r = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
                "grant_type": "refresh_token",
            },
            timeout=TIMEOUT,
        )
        if r.status_code == 200 and "access_token" in r.json():
            line("Google OAuth", True, "PASS", "refresh token valid (GSC + GA4 ready)")
        else:
            err = r.json().get("error", r.status_code)
            line("Google OAuth", True, "FAIL", f"token refresh rejected: {err}")
    except Exception as exc:  # noqa: BLE001
        line("Google OAuth", True, "FAIL", f"network/error: {exc}")


def check_dataforseo() -> None:
    if not has("DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"):
        line("DataForSEO", False, "MISS", "SERP/Keywords/Backlinks/OnPage unavailable")
        return
    try:
        r = requests.get(
            "https://api.dataforseo.com/v3/appendix/user_data",
            auth=(os.environ["DATAFORSEO_LOGIN"], os.environ["DATAFORSEO_PASSWORD"]),
            timeout=TIMEOUT,
        )
        body = r.json()
        if r.status_code == 200 and body.get("status_code") == 20000:
            bal = body["tasks"][0]["result"][0].get("money", {}).get("balance")
            note = "authenticated" + (f", balance=${bal}" if bal is not None else "")
            line("DataForSEO", True, "PASS", note)
        else:
            line("DataForSEO", True, "FAIL", f"status: {body.get('status_message', r.status_code)}")
    except Exception as exc:  # noqa: BLE001
        line("DataForSEO", True, "FAIL", f"network/error: {exc}")


def check_openai() -> None:
    if not has("OPENAI_API_KEY"):
        line("OpenAI", False, "MISS", "AI summaries unavailable")
        return
    try:
        r = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            n = len(r.json().get("data", []))
            line("OpenAI", True, "PASS", f"key valid ({n} models visible)")
        else:
            line("OpenAI", True, "FAIL", f"HTTP {r.status_code}")
    except Exception as exc:  # noqa: BLE001
        line("OpenAI", True, "FAIL", f"network/error: {exc}")


def check_simple_presence() -> None:
    """APIs we only presence-check here (full live test happens in their connector)."""
    groups = {
        "Google API key": ["GOOGLE_API_KEY"],
        "Google Ads": ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID"],
        "Meta Ads": ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"],
        "LinkedIn Ads": ["LINKEDIN_ACCESS_TOKEN", "LINKEDIN_ACCOUNT_ID"],
        "Webflow": ["WEBFLOW_API_KEY", "WEBFLOW_SITE_ID"],
        "WordPress": ["WP_SITE_URL", "WP_APP_PASSWORD"],
        "Framer sitemap": ["FRAMER_SITEMAP_URL"],
    }
    for name, keys in groups.items():
        present = has(*keys)
        line(name, present, "SKIP" if present else "MISS",
             "present (connector will live-test)" if present else "no credentials")


def main() -> int:
    print("\nFuseHealth — Environment / API audit")
    print("=" * 60)
    print("Live auth checks:")
    check_google_oauth()
    check_dataforseo()
    check_openai()
    print("\nPresence-only (credentials checked, not live-tested here):")
    check_simple_presence()
    print("=" * 60)
    print("No secret values are printed by this script.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

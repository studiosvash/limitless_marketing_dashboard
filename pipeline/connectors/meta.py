"""
pipeline/connectors/meta.py — Meta Marketing API connector.

Fetches: daily campaign spend, clicks, impressions, conversions (purchases).
Writes to: ad_metrics_daily table (platform='meta').

REQUIRES Standard tier (100K pts/hr). Dev tier (300 pts/hr) is unusable.
Apply: Business Manager → App Review → Ads Management Standard Access.

Auth: System User token (never expires, unlike personal tokens).
Token: META_ACCESS_TOKEN in .env — set up via Business Manager → System Users.
"""

import os
from datetime import date, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import days_ago, iso
from pipeline.db.writer import upsert_ad_metrics

load_dotenv()

GRAPH_API_BASE = "https://graph.facebook.com/v18.0"


def probe_credential(access_token: str, ad_account_id: str) -> tuple[bool, str]:
    """Can this Meta System User token actually read this ad account? Never raises."""
    try:
        resp = requests.get(
            f"{GRAPH_API_BASE}/{ad_account_id}",
            params={"fields": "name"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
    except Exception as exc:
        # Never interpolate the raw exception: requests/urllib3 embed the failing URL
        # (and, for the query-param auth style we deliberately moved away from, the
        # token itself) in some exception messages/reprs. Only the exception type is
        # safe to surface -- this string is both returned to the browser AND persisted
        # unencrypted in ProjectSettings.data via record_test_result.
        return False, f"Could not reach the Meta Graph API ({type(exc).__name__})."
    if resp.status_code == 200:
        name = resp.json().get("name", ad_account_id)
        return True, f'Verified — reached ad account "{name}".'
    try:
        message = resp.json().get("error", {}).get("message", resp.text)
    except Exception:
        message = resp.text
    return False, f"Meta rejected these credentials (HTTP {resp.status_code}): {message}"


class MetaConnector(BaseConnector):
    name = "meta"

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

    @with_retry(max_retries=3, base_delay=5.0)
    def _get_insights(self, since: str, until: str) -> list[dict]:
        """
        Fetch campaign-level insights from Meta Graph API.
        Uses time_increment=1 for daily breakdown.
        """
        url = f"{GRAPH_API_BASE}/{self.ad_account_id}/insights"
        params = {
            "access_token": self.access_token,
            "fields": "campaign_name,campaign_id,spend,clicks,impressions,actions,action_values",
            "level": "campaign",
            "time_increment": 1,  # Daily breakdown
            "time_range": f'{{"since":"{since}","until":"{until}"}}',
            "limit": 500,
        }

        all_data = []
        while url:
            resp = requests.get(url, params=params, timeout=30)

            if resp.status_code == 429:
                raise requests.HTTPError(
                    f"[meta] Rate limit hit (429). Current tier may be Dev tier. "
                    "Apply for Standard Access in Meta App Review."
                )
            resp.raise_for_status()

            data = resp.json()
            all_data.extend(data.get("data", []))

            # Handle pagination
            paging = data.get("paging", {})
            next_url = paging.get("next")
            url = next_url
            params = {}  # Next URL already includes all params

        return all_data

    def _extract_conversions(self, actions: list[dict]) -> int:
        """
        Extract purchase conversions from Meta actions array.
        Meta returns a flat list of action objects with action_type.
        """
        if not actions:
            return 0

        purchase_types = {"purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"}
        for action in actions:
            if action.get("action_type") in purchase_types:
                return int(float(action.get("value", 0)))
        return 0

    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch Meta campaign performance for the past N days.

        Returns:
            List of dicts for ad_metrics_daily table.
        """
        since = iso(days_ago(days))
        until = iso(days_ago(1))

        self.logger.info(f"[meta] Fetching insights: {since} → {until}")
        raw_data = self._get_insights(since, until)

        records = []
        for row in raw_data:
            # Meta date_start is the day for time_increment=1
            row_date = date.fromisoformat(row["date_start"])
            spend = float(row.get("spend", 0))
            clicks = int(row.get("clicks", 0))
            impressions = int(row.get("impressions", 0))
            conversions = self._extract_conversions(row.get("actions", []))

            records.append({
                "date": row_date,
                "platform": "meta",
                "campaign": row.get("campaign_name", "Unknown"),
                "campaign_id": row.get("campaign_id", ""),
                "spend": round(spend, 4),
                "clicks": clicks,
                "impressions": impressions,
                "conversions": conversions,
                "roas": None,  # Unknown without revenue values (don't store fake 0)
            })

        self.logger.info(f"[meta] Fetched {len(records)} campaign-day records")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_ad_metrics(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = MetaConnector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} Meta records")
    if records:
        print(f"Sample: {records[0]}")

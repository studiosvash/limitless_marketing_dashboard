"""
pipeline/connectors/linkedin.py — LinkedIn Ads API connector.

Fetches: daily campaign spend, clicks, impressions, conversions.
Writes to: ad_metrics_daily table (platform='linkedin').

Rate limits are NOT published by LinkedIn. All 429s must be handled gracefully.
Strategy: Exponential backoff on every call (max 5 retries, starting at 2s).
Schedule: 00:05 UTC — LinkedIn resets at midnight UTC.

Auth: OAuth2 with 60-day refresh token. Auto-refresh implemented.
"""

import os
import time
from datetime import date, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import days_ago, iso
from pipeline.utils.logger import get_logger
from pipeline.db.writer import upsert_ad_metrics

load_dotenv()

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInConnector(BaseConnector):
    name = "linkedin"

    def __init__(self):
        super().__init__()
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.refresh_token = os.getenv("LINKEDIN_REFRESH_TOKEN")
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.account_id = os.getenv("LINKEDIN_ACCOUNT_ID")

        if not self.access_token or not self.account_id:
            raise ValueError(
                "[linkedin] Missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_ACCOUNT_ID in .env."
            )
        if self.refresh_token and (not self.client_id or not self.client_secret):
            self.logger.warning(
                "[linkedin] LINKEDIN_REFRESH_TOKEN is set but LINKEDIN_CLIENT_ID or "
                "LINKEDIN_CLIENT_SECRET is missing — auto token refresh will fail."
            )

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def _refresh_access_token(self) -> str:
        """
        Use refresh token to get a new access token.
        LinkedIn tokens expire every 60 days.
        """
        if not self.refresh_token:
            raise ValueError("[linkedin] No refresh token available. Re-authenticate manually.")

        resp = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=15,
        )
        resp.raise_for_status()
        new_token = resp.json()["access_token"]
        self.access_token = new_token
        self.logger.warning(
            "[linkedin] Access token refreshed in memory. "
            "IMPORTANT: Update LINKEDIN_ACCESS_TOKEN in your .env file with this new token "
            "to prevent re-authentication after process restart."
        )
        self.logger.info("[linkedin] Access token refreshed successfully")
        return new_token

    @with_retry(max_retries=5, base_delay=2.0, exceptions=(requests.HTTPError, requests.Timeout))
    def _api_get(self, endpoint: str, params: dict = None) -> dict:
        """
        Make a GET request to LinkedIn API with retry + auto token refresh.
        LinkedIn 429s are expected — the retry decorator handles them.
        """
        resp = requests.get(
            f"{LINKEDIN_API_BASE}/{endpoint}",
            headers=self._get_headers(),
            params=params or {},
            timeout=20,
        )

        if resp.status_code == 401:
            # Token expired — refresh and retry once
            self.logger.warning("[linkedin] 401 received — refreshing token")
            self._refresh_access_token()
            resp = requests.get(
                f"{LINKEDIN_API_BASE}/{endpoint}",
                headers=self._get_headers(),
                params=params or {},
                timeout=20,
            )

        resp.raise_for_status()
        return resp.json()

    def _get_campaigns(self) -> list[dict]:
        """Fetch all active campaigns for the account. Paginates through all results."""
        all_campaigns = []
        start = 0
        count = 100

        while True:
            data = self._api_get(
                "adCampaignsV2",
                params={
                    "q": "search",
                    "search.account.values[0]": f"urn:li:sponsoredAccount:{self.account_id}",
                    "search.status.values[0]": "ACTIVE",
                    "count": count,
                    "start": start,
                },
            )
            elements = data.get("elements", [])
            all_campaigns.extend(elements)

            # LinkedIn paging object: {"count": 100, "start": 0, "total": 250}
            paging = data.get("paging", {})
            total = paging.get("total", 0)
            start += count

            if start >= total or not elements:
                break

        self.logger.info(f"[linkedin] Found {len(all_campaigns)} total active campaigns")
        return all_campaigns

    def _get_campaign_analytics(self, campaign_id: str, start_date: date, end_date: date) -> list[dict]:
        """Fetch daily analytics for a single campaign."""
        # LinkedIn date format: {year, month, day} objects in the query
        params = {
            "q": "analytics",
            "pivot": "CAMPAIGN",
            "dateRange.start.year": start_date.year,
            "dateRange.start.month": start_date.month,
            "dateRange.start.day": start_date.day,
            "dateRange.end.year": end_date.year,
            "dateRange.end.month": end_date.month,
            "dateRange.end.day": end_date.day,
            "timeGranularity": "DAILY",
            "campaigns[0]": f"urn:li:sponsoredCampaign:{campaign_id}",
            "fields": "costInLocalCurrency,clicks,impressions,externalWebsiteConversions,dateRange",
        }

        # Small sleep before each call — LinkedIn unpublished rate limits
        time.sleep(0.5)
        data = self._api_get("adAnalyticsV2", params=params)
        return data.get("elements", [])

    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch LinkedIn campaign analytics for past N days.
        Iterates through each active campaign — LinkedIn requires per-campaign calls.

        Returns:
            List of dicts for ad_metrics_daily table.
        """
        start = days_ago(days)
        end = days_ago(1)

        self.logger.info(f"[linkedin] Fetching analytics: {iso(start)} → {iso(end)}")
        campaigns = self._get_campaigns()
        self.logger.info(f"[linkedin] Found {len(campaigns)} active campaigns")

        records = []
        for campaign in campaigns:
            campaign_id = str(campaign["id"])
            campaign_name = campaign.get("name", "Unknown")

            try:
                analytics = self._get_campaign_analytics(campaign_id, start, end)
                for row in analytics:
                    # LinkedIn dateRange has nested start object
                    dr = row.get("dateRange", {}).get("start", {})
                    row_date = date(dr.get("year", 2000), dr.get("month", 1), dr.get("day", 1))

                    spend = float(row.get("costInLocalCurrency", 0))

                    records.append({
                        "date": row_date,
                        "platform": "linkedin",
                        "campaign": campaign_name,
                        "campaign_id": campaign_id,
                        "spend": round(spend, 4),
                        "clicks": int(row.get("clicks", 0)),
                        "impressions": int(row.get("impressions", 0)),
                        "conversions": int(row.get("externalWebsiteConversions", 0)),
                        "roas": None,  # Unknown without revenue values (don't store fake 0)
                    })
            except Exception as exc:
                self.logger.warning(
                    f"[linkedin] Failed to fetch campaign {campaign_id} ({campaign_name}): {exc}"
                )
                continue

        self.logger.info(f"[linkedin] Fetched {len(records)} campaign-day records")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_ad_metrics(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = LinkedInConnector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} LinkedIn records")

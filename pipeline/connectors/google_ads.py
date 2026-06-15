"""
pipeline/connectors/google_ads.py — Google Ads connector.

Fetches: daily campaign spend, clicks, impressions, conversions per campaign.
Writes to: ad_metrics_daily table (platform='google').

REQUIRES Standard Access (apply at https://developers.google.com/google-ads/api/docs/access-levels)
Basic Access: 15,000 operations/day. Standard: unlimited for most use cases.
Rate limit: 2 QPS — enforced by the SDK automatically.

Auth: OAuth2 via pipeline/utils/auth.py + developer token from .env.
"""

import os
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import days_ago, iso
from pipeline.db.writer import upsert_ad_metrics

load_dotenv()


class GoogleAdsConnector(BaseConnector):
    name = "google_ads"

    def __init__(self):
        super().__init__()
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
        self.developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")

        if not self.customer_id or not self.developer_token:
            raise ValueError(
                "[google_ads] Missing GOOGLE_ADS_CUSTOMER_ID or GOOGLE_ADS_DEVELOPER_TOKEN in .env. "
                "Also ensure Standard Access has been approved."
            )

    @with_retry(max_retries=3, base_delay=5.0)
    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch campaign metrics for the past N days.

        Uses GAQL (Google Ads Query Language) to retrieve:
        campaign name, date, spend, clicks, impressions, conversions.

        Returns:
            List of dicts for ad_metrics_daily table.
        """
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            raise ImportError(
                "[google_ads] Missing google-ads SDK. Run: pip install google-ads"
            )

        # Build credentials dict for the SDK
        credentials = {
            "developer_token": self.developer_token,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
            "use_proto_plus": True,
        }
        if self.login_customer_id:
            credentials["login_customer_id"] = self.login_customer_id

        client = GoogleAdsClient.load_from_dict(credentials)
        service = client.get_service("GoogleAdsService")

        start_date = iso(days_ago(days))
        end_date = iso(days_ago(1))

        # GAQL query — fetches campaign-level daily metrics
        # cost_micros = actual spend × 1,000,000 (divide to get USD)
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.conversions,
                segments.date
            FROM campaign
            WHERE
                segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
            ORDER BY segments.date DESC, metrics.cost_micros DESC
        """

        self.logger.info(f"[google_ads] Querying {start_date} → {end_date}")
        response = service.search(customer_id=self.customer_id, query=query)

        records = []
        for row in response:
            spend_usd = row.metrics.cost_micros / 1_000_000
            conversions = int(row.metrics.conversions)
            clicks = int(row.metrics.clicks)

            records.append({
                "date": date.fromisoformat(row.segments.date),
                "platform": "google",
                "campaign": row.campaign.name,
                "campaign_id": str(row.campaign.id),
                "spend": round(spend_usd, 4),
                "clicks": clicks,
                "impressions": int(row.metrics.impressions),
                "conversions": conversions,
                "roas": None,  # Unknown until conversion_value tracking is added (don't store fake 0)
            })

        self.logger.info(f"[google_ads] Fetched {len(records)} campaign-day records")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_ad_metrics(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = GoogleAdsConnector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} Google Ads records")
    if records:
        print(f"Sample: {records[0]}")

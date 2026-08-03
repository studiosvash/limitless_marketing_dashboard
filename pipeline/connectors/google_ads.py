"""
pipeline/connectors/google_ads.py — Google Ads connector.

Fetches: daily campaign spend, clicks, impressions, conversions per campaign.
Writes to: ad_metrics_daily table (platform='google').

Auth lives here and ONLY here for every Google Ads resource: `_build_service()` is the
single place that assembles the SDK credentials dict and returns a GoogleAdsService.
Sibling connectors (see google_ads_search_terms.py) subclass this class so they inherit
the same credential validation in `__init__` and the same client construction — there is
deliberately no second auth path to keep in sync.

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

    def _build_service(self):
        """Construct the GoogleAdsService client. The ONLY place credentials are assembled.

        Subclasses (search-term connector) call this rather than rebuilding the dict, so a
        change to the auth model — e.g. a switch to a service-account or a different token
        source — lands in exactly one place.
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
        return client.get_service("GoogleAdsService")

    @with_retry(max_retries=3, base_delay=5.0)
    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch campaign metrics for the past N days.

        Uses GAQL (Google Ads Query Language) to retrieve:
        campaign name, date, spend, clicks, impressions, conversions, conversion value.

        Returns:
            List of dicts for ad_metrics_daily table.
        """
        service = self._build_service()

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
                metrics.conversions_value,
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
            conv_value = float(getattr(row.metrics, "conversions_value", 0.0) or 0.0)

            # roas is the ONLY place ad_metrics_daily can carry conversion value, and it is
            # nullable precisely so "we don't know" stays distinguishable from "the return
            # was zero". An account with no conversion-value tracking reports
            # conversions_value == 0 for every row: that is *unknown*, not a 0x return, so
            # it stays None. The Attribution table reconstructs ads_value as spend * roas
            # and therefore also stays honestly None for those accounts.
            roas = (conv_value / spend_usd) if (spend_usd > 0 and conv_value > 0) else None

            records.append({
                "date": date.fromisoformat(row.segments.date),
                "platform": "google",
                "campaign": row.campaign.name,
                "campaign_id": str(row.campaign.id),
                "spend": round(spend_usd, 4),
                "clicks": clicks,
                "impressions": int(row.metrics.impressions),
                "conversions": conversions,
                "roas": round(roas, 6) if roas is not None else None,
            })

        self.logger.info(f"[google_ads] Fetched {len(records)} campaign-day records")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_ad_metrics(session, records, site_id=site_id)


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


if __name__ == "__main__":
    connector = GoogleAdsConnector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} Google Ads records")
    if records:
        print(f"Sample: {records[0]}")

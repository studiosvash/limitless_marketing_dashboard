"""
pipeline/connectors/ga4.py — Google Analytics 4 connector.

Fetches: daily sessions, pageviews, conversions, bounce_rate.
Writes to: seo_daily table (merges with GSC data via date + site_id).

Rate limit: 14,000 tokens/hour. Strategy: ONE batched call per day — all
metrics in a single request.

Auth: Same OAuth2 credentials as GSC (reuses pipeline/utils/auth.py).
"""

import os
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest
)

from pipeline.connectors.base import BaseConnector
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import ga4_safe_range
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_seo_daily

load_dotenv()


class GA4Connector(BaseConnector):
    name = "ga4"

    def __init__(self):
        super().__init__()
        # Defaults from .env — used as fallback when no Site row exists.
        self._default_property_id = os.getenv("GA4_PROPERTY_ID")
        self._default_site_url = os.getenv("GSC_SITE_URL", "")

    def _resolve_site(self, site_id: Optional[str]) -> tuple[str, str]:
        """Return (site_url, ga4_property_id) for site_id, falling back to .env."""
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return (
                    site.site_url,
                    site.ga4_property_id or self._default_property_id or "",
                )
        return (self._default_site_url, self._default_property_id or "")

    @with_retry(max_retries=3, base_delay=10.0)
    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch GA4 data — all metrics in ONE batched API call to conserve quota.

        Args:
            site_id: Site.site_url to fetch for. None falls back to first active site.
            days: Number of days to fetch (default: 90).

        Returns:
            List of dicts for seo_daily table (sessions, pageviews, conversions,
            bounce_rate, users, new_users, engagement_rate).
        """
        site_url, property_id = self._resolve_site(site_id)
        if not property_id:
            raise ValueError(
                "[ga4] No GA4 property configured for this site. "
                "Set ga4_property_id in Settings → Manage Sites or GA4_PROPERTY_ID in .env."
            )

        start_str, end_str = ga4_safe_range(days)
        self.logger.info(
            f"[ga4] Fetching {days} days ({start_str} → {end_str}) "
            f"for property={property_id} site={site_url}"
        )

        creds = get_google_credentials()
        client = BetaAnalyticsDataClient(credentials=creds)

        # ONE batched request — GA4 quota is precious (14K tokens/hour).
        # Added Phase 5: totalUsers, newUsers, engagementRate for user-retention reporting.
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="country"),
                Dimension(name="deviceCategory"),
                Dimension(name="pagePath"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
                Metric(name="conversions"),
                Metric(name="bounceRate"),
                Metric(name="totalUsers"),
                Metric(name="newUsers"),
                Metric(name="engagementRate"),
            ],
            date_ranges=[DateRange(start_date=start_str, end_date=end_str)],
            limit=100000,
        )

        response = client.run_report(request)
        records = self._normalize(response, site_url)
        self.logger.info(f"[ga4] Fetched {len(records)} dimension breakdown rows for {site_url}")
        return records

    def _normalize(self, response, site_url: str) -> list[dict]:
        """Convert GA4 RunReportResponse rows to seo_daily format."""
        records = []
        for row in response.rows:
            raw_date = row.dimension_values[0].value
            row_date = date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:]))

            country = row.dimension_values[1].value
            device = row.dimension_values[2].value.lower()
            page_path = row.dimension_values[3].value

            # Reconstruct full absolute URL to align with GSC's landing_page values
            landing_page = site_url.rstrip("/") + page_path

            sessions = int(row.metric_values[0].value)
            pageviews = int(row.metric_values[1].value)
            conversions = int(row.metric_values[2].value)
            bounce_rate = float(row.metric_values[3].value)
            users = int(row.metric_values[4].value)
            new_users = int(row.metric_values[5].value)
            engagement_rate = float(row.metric_values[6].value)

            records.append({
                "date": row_date,
                "site_id": site_url,
                "country": country,
                "device": device,
                "landing_page": landing_page,
                "sessions": sessions,
                "pageviews": pageviews,
                "conversions": conversions,
                "bounce_rate": round(bounce_rate, 4),
                "users": users,
                "new_users": new_users,
                "engagement_rate": round(engagement_rate, 4),

                # GSC fields — left as 0 here; GSC connector fills them in
                "clicks": 0,
                "impressions": 0,
                "ctr": 0.0,
                "avg_position": 0.0,
            })

        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """
        Upsert GA4 metrics into seo_daily in batches.
        Only updates the GA4-specific columns, preserving GSC data.
        Batched to avoid SQLite 'too many SQL variables' limit.
        """
        if not records:
            return 0

        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from pipeline.db.schema import SEODaily

        BATCH_SIZE = 60  # ~14 cols * 60 = 840, safely under SQLite's ~999 limit
        total = 0
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            stmt = sqlite_insert(SEODaily).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["date", "site_id", "country", "device", "landing_page"],
                set_={
                    "sessions": stmt.excluded.sessions,
                    "pageviews": stmt.excluded.pageviews,
                    "conversions": stmt.excluded.conversions,
                    "bounce_rate": stmt.excluded.bounce_rate,
                    "users": stmt.excluded.users,
                    "new_users": stmt.excluded.new_users,
                    "engagement_rate": stmt.excluded.engagement_rate,
                },
            )
            session.execute(stmt)
            total += len(batch)
        return total


if __name__ == "__main__":
    connector = GA4Connector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} days of GA4 data")
    if records:
        print(f"Sample: {records[0]}")

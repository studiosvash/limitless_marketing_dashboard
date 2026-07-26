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
        """Return (site_url, ga4_property_id) for site_id. The .env GA4_PROPERTY_ID is a
        fallback ONLY when no Site row exists (legacy single-site mode). When a Site row
        exists without its own ga4_property_id, return "" so fetch() fails loudly — the
        .env property belongs to the PRIMARY site, and falling back to it here used to
        write the primary site's GA4 rows under the new site's id (real bug: 6,654
        fusehealth rows stored as eventstaff.com on 2026-07-15)."""
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return (site.site_url, site.ga4_property_id or "")
        return (self._default_site_url, self._default_property_id or "")

    @with_retry(max_retries=3, base_delay=10.0)
    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch GA4 data — all metrics in ONE batched API call to conserve quota.

        Args:
            site_id: Site.site_url to fetch for. None falls back to first active site.
            days: Number of days to fetch (default: 90).

        Returns:
            Dict containing two lists of records:
            {"seo_daily": [...], "offsite_daily": [...]}
        """
        site_url, property_id = self._resolve_site(site_id)
        if not property_id:
            raise ValueError(
                f"No GA4 property configured for {site_url or site_id or 'this site'}. "
                "Add its GA4 property ID in Settings → Connections, then Refresh again."
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

        response1 = client.run_report(request)
        seo_records = self._normalize(response1, site_url)
        self.logger.info(f"[ga4] Fetched {len(seo_records)} dimension breakdown rows for {site_url}")

        # SECOND batched request - for Traffic Sources (Off-site SEO)
        request2 = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="sessionDefaultChannelGroup"),
                Dimension(name="sessionSource"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="engagementRate"),
            ],
            date_ranges=[DateRange(start_date=start_str, end_date=end_str)],
            limit=100000,
        )
        response2 = client.run_report(request2)
        offsite_records = self._normalize_offsite(response2, site_url)
        self.logger.info(f"[ga4] Fetched {len(offsite_records)} traffic source rows for {site_url}")

        return {"seo_daily": seo_records, "offsite_daily": offsite_records}

    def _normalize_offsite(self, response, site_url: str) -> list[dict]:
        """Convert GA4 RunReportResponse rows to ga4_traffic_source_daily format."""
        records = []
        for row in response.rows:
            raw_date = row.dimension_values[0].value
            row_date = date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:]))
            channel = row.dimension_values[1].value
            source = row.dimension_values[2].value.lower()
            
            sessions = int(row.metric_values[0].value)
            conversions = int(row.metric_values[1].value)
            engagement_rate = float(row.metric_values[2].value)

            records.append({
                "date": row_date,
                "site_id": site_url,
                "channel": channel,
                "source": source,
                "sessions": sessions,
                "engaged_sessions": round(sessions * engagement_rate),
                "conversions": conversions,
                "revenue": round(conversions * 45.0, 2),
            })
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

    def _write_records(self, session, payload: dict, site_id: Optional[str] = None) -> int:
        """
        Upsert GA4 metrics into seo_daily and ga4_traffic_source_daily in batches.
        Only updates the GA4-specific columns, preserving GSC data.
        Batched to avoid SQLite 'too many SQL variables' limit.
        """
        if not payload:
            return 0
            
        seo_records = payload.get("seo_daily", [])
        offsite_records = payload.get("offsite_daily", [])

        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from pipeline.db.schema import SEODaily, GA4TrafficSourceDaily

        BATCH_SIZE = 60  # ~14 cols * 60 = 840, safely under SQLite's ~999 limit
        total = 0
        for i in range(0, len(seo_records), BATCH_SIZE):
            batch = seo_records[i:i + BATCH_SIZE]
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
            
        for i in range(0, len(offsite_records), BATCH_SIZE):
            batch = offsite_records[i:i + BATCH_SIZE]
            stmt = sqlite_insert(GA4TrafficSourceDaily).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["date", "site_id", "channel", "source"],
                set_={
                    "sessions": stmt.excluded.sessions,
                    "engaged_sessions": stmt.excluded.engaged_sessions,
                    "conversions": stmt.excluded.conversions,
                    "revenue": stmt.excluded.revenue,
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

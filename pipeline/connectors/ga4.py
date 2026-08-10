"""
pipeline/connectors/ga4.py — Google Analytics 4 connector.

Fetches: daily sessions, pageviews, conversions, bounce_rate, traffic sources, per-campaign
key events and revenue.
Writes to: seo_daily (merges with GSC data via date + site_id), ga4_traffic_source_daily,
ga4_campaign_daily.

Rate limit: 14,000 tokens/hour. Strategy: as few batched reports as possible — extra
metrics and dimensions ride on an existing request wherever adding them cannot distort the
report they join. Each of the three reports here is justified at its call site.

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
from pipeline.db.writer import upsert_seo_daily, upsert_ga4_campaign_daily

load_dotenv()


def normalise_property_id(raw: str | None) -> str:
    """Reduce whatever the user pasted to the bare numeric GA4 property id.

    GA4's admin UI displays the property as `properties/123456789`, and that is what people
    copy. Every request builder here does `property=f"properties/{property_id}"`, so storing
    the prefixed form produces `properties/properties/123456789` and an INVALID_ARGUMENT from
    the API -- hours later, inside a sync, long after Settings said "Saved ✓". Strip it once,
    at the edge, so no write path can store the broken form.

    Returns "" for anything that is not a bare number after stripping (e.g. a `G-XXXXXXX`
    Measurement ID, which is a different identifier people confuse for this one). Callers
    decide whether "" is a validation error or simply "not configured".
    """
    s = (raw or "").strip()
    if not s:
        return ""
    if s.lower().startswith("properties/"):
        s = s.split("/", 1)[1].strip()
    return s if s.isdigit() else ""


def probe_property(property_id: str) -> tuple[bool, str]:
    """Can the connected Google identity actually read this GA4 property?

    Returns (ok, human-readable detail). Never raises — this backs a "Test connection" button
    and a CLI check, both of which must report a failure rather than become one.

    Why this exists: there was NO access check for GA4 anywhere. The only gate was a presence
    check (`if not prop_id`), so a wrong-but-real-looking property id passed validation, saved
    cleanly, and then failed 20 minutes into a sync. One deliberately cheap report — one day,
    one metric, one row — is enough to prove read access without spending meaningful quota
    (GA4 allows 14,000 tokens/hour).
    """
    pid = normalise_property_id(property_id)
    if not pid:
        return False, (
            "Not a valid GA4 property ID. Use the numeric ID from GA4 → Admin → Property "
            "details (e.g. 123456789), not a G- Measurement ID."
        )
    try:
        client = BetaAnalyticsDataClient(credentials=get_google_credentials())
        resp = client.run_report(RunReportRequest(
            property=f"properties/{pid}",
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
            limit=1,
        ))
    except Exception as exc:
        return False, f"GA4 rejected property {pid}: {exc}"

    sessions = "0"
    if resp.rows:
        sessions = resp.rows[0].metric_values[0].value
    return True, f"Property {pid} readable — {sessions} sessions in the last 7 days."


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
            Dict containing three lists of records:
            {"seo_daily": [...], "offsite_daily": [...], "campaign_daily": [...]}
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
                # Real money, straight from GA4 — replaces the old
                # `conversions * 45.0` estimate that invented revenue the
                # property never reported. Added to THIS request rather than a
                # third one: GA4 quota is 14K tokens/hour and an extra metric on
                # an existing report is far cheaper than another round-trip.
                Metric(name="totalRevenue"),
            ],
            date_ranges=[DateRange(start_date=start_str, end_date=end_str)],
            limit=100000,
        )
        response2 = client.run_report(request2)
        offsite_records = self._normalize_offsite(response2, site_url)
        self.logger.info(f"[ga4] Fetched {len(offsite_records)} traffic source rows for {site_url}")

        # THIRD batched request — GA4's half of the Ads → Attribution comparison.
        #
        # This one genuinely needs its own round-trip rather than an extra dimension on
        # request2, which is the cheaper move and the one preferred everywhere else in this
        # file. Request2 is already date × sessionDefaultChannelGroup × sessionSource over 90
        # days and runs against `limit=100000`; adding sessionCampaignName multiplies its
        # cardinality by the campaign count. That does two bad things at once: it can push
        # the response past the row limit (silently TRUNCATING the offsite numbers that
        # already ship) and past GA4's own cardinality ceiling, where the tail collapses into
        # an "(other)" bucket that would be double-counted as a traffic source. Corrupting a
        # working report to save a request is not a trade worth making.
        #
        # Quota: this is the smallest of the three reports — 2 dimensions / 3 metrics, and
        # ~days × campaigns rows (typically a few thousand, vs. six figures for the other
        # two). GA4's 14K tokens/hour budget is charged by report complexity, so it is the
        # cheapest report the connector issues, and it runs once per sync alongside the
        # other two rather than per page load.
        request3 = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="sessionCampaignName"),
            ],
            metrics=[
                Metric(name="sessions"),
                # `conversions` (not `keyEvents`) to match the two requests above — the whole
                # connector speaks one metric vocabulary, and this property is already known
                # to answer it. It lands in GA4CampaignDaily.key_events, GA4's current name
                # for the same number.
                Metric(name="conversions"),
                Metric(name="totalRevenue"),
            ],
            date_ranges=[DateRange(start_date=start_str, end_date=end_str)],
            limit=100000,
        )
        response3 = client.run_report(request3)
        campaign_records = self._normalize_campaigns(response3, site_url)
        self.logger.info(f"[ga4] Fetched {len(campaign_records)} campaign rows for {site_url}")

        # FOURTH request — session-scoped truth, for ga4_daily_totals. Request1's grain
        # includes pagePath, and sessions are NOT additive across pages: one visit that viewed
        # three pages is three rows, so summing request1 overstated sessions at 158% of the
        # GA4 UI (21,077 vs 13,333, 2026-06-01..07-27). date × country carries no such
        # inflation — a session has exactly one of each — and matches the UI within GA4's own
        # "(other)"-bucket noise. Headline session/user figures must come from THIS table;
        # request1's rows stay for page-level drill-down only. Same split, same reason, as
        # seo_daily_totals vs seo_daily on the Search Console side.
        #
        # Window is days × 2: every Overview KPI is shown against the preceding period of the
        # same length, and fetching only the visible window is exactly the missing-baseline
        # mistake the GSC totals made (see gsc.py) — the comparison fell through to the
        # inflated breakdown and the dashboard announced +2361% growth.
        #
        # Non-fatal: the three reports above are the expensive part of the sync; losing them
        # because the cheapest report failed would be the worse outcome. The totals keep
        # their last good values and the next run's full re-read repairs them.
        totals_records: list[dict] = []
        try:
            totals_start, _ = ga4_safe_range(days * 2)
            request4 = RunReportRequest(
                property=f"properties/{property_id}",
                dimensions=[Dimension(name="date"), Dimension(name="country")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="screenPageViews"),
                    Metric(name="conversions"),
                    # Real for its own (date, country) cell and stored as such. Never sum it
                    # across dates or countries — unique users are not additive; see
                    # GA4DailyTotal's docstring.
                    Metric(name="totalUsers"),
                ],
                date_ranges=[DateRange(start_date=totals_start, end_date=end_str)],
                limit=100000,
            )
            totals_records = self._normalize_totals(client.run_report(request4), site_url)
            self.logger.info(f"[ga4] Fetched {len(totals_records)} daily-total rows for {site_url}")
        except Exception:
            self.logger.warning(
                f"[ga4] daily-totals fetch failed for {site_url}; keeping previously stored "
                f"totals and continuing with the breakdown reports", exc_info=True
            )

        return {
            "seo_daily": seo_records,
            "offsite_daily": offsite_records,
            "campaign_daily": campaign_records,
            "daily_totals": totals_records,
        }

    def _normalize_totals(self, response, site_url: str) -> list[dict]:
        """Convert the date × country report to ga4_daily_totals rows."""
        records = []
        for row in response.rows:
            raw_date = row.dimension_values[0].value
            records.append({
                "date": date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:])),
                "site_id": site_url,
                "country": row.dimension_values[1].value or "(not set)",
                "sessions": int(row.metric_values[0].value or 0),
                "pageviews": int(row.metric_values[1].value or 0),
                "conversions": int(float(row.metric_values[2].value or 0)),
                "users": int(row.metric_values[3].value or 0),
            })
        return records

    # GA4 returns these placeholders in sessionCampaignName for traffic that has no campaign
    # at all. They are not campaigns and must never reach the Attribution table, where they
    # would sit next to real Google Ads campaigns and never match one.
    _NON_CAMPAIGN_VALUES = {"", "(not set)", "(direct)", "(organic)", "(referral)", "(none)"}

    def _normalize_campaigns(self, response, site_url: str) -> list[dict]:
        """Convert GA4 RunReportResponse rows to ga4_campaign_daily format."""
        records = []
        for row in response.rows:
            campaign = (row.dimension_values[1].value or "").strip()
            if campaign.lower() in self._NON_CAMPAIGN_VALUES:
                continue

            raw_date = row.dimension_values[0].value
            row_date = date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:]))

            records.append({
                "date": row_date,
                "site_id": site_url,
                "campaign": campaign,
                "sessions": int(row.metric_values[0].value or 0),
                "key_events": int(float(row.metric_values[1].value or 0)),
                # Same rule as _normalize_offsite: a property with no revenue events reports
                # a real 0 here. Store it; never substitute a per-conversion estimate.
                "revenue": round(float(row.metric_values[2].value or 0.0), 2),
            })
        return records

    def _normalize_offsite(self, response, site_url: str) -> list[dict]:
        """Convert GA4 RunReportResponse rows to ga4_traffic_source_daily format."""
        records = []
        for row in response.rows:
            raw_date = row.dimension_values[0].value
            row_date = date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:]))
            channel = row.dimension_values[1].value
            source = row.dimension_values[2].value.lower()
            
            sessions = int(row.metric_values[0].value or 0)
            # int(float(...)), like _normalize_campaigns and _normalize_totals already do.
            # `conversions` is a FLOATING-POINT metric in the GA4 Data API -- partial conversion
            # credit is real -- so the same property that answers "3" one day answers "3.0" the
            # next, and int("3.0") raises ValueError. Nothing here catches it: the exception
            # escapes _normalize_offsite into fetch(), past the retry decorator, and kills the
            # ENTIRE GA4 sync -- including the seo_daily and campaign reports that were already
            # fetched and paid for in the same run.
            conversions = int(float(row.metric_values[1].value or 0))
            engagement_rate = float(row.metric_values[2].value or 0.0)
            # GA4 `totalRevenue` = purchase + subscription + ad revenue the
            # property actually recorded. A property with no ecommerce or
            # revenue events configured returns 0 for every row: that is a
            # LEGITIMATE ZERO, not a failure, and must be stored as 0. Never
            # back-fill it with a per-conversion estimate — an invented number
            # that looks real is worse than a visible zero.
            revenue = float(row.metric_values[3].value or 0.0)

            records.append({
                "date": row_date,
                "site_id": site_url,
                "channel": channel,
                "source": source,
                "sessions": sessions,
                "engaged_sessions": round(sessions * engagement_rate),
                "conversions": conversions,
                "revenue": round(revenue, 2),
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

            sessions = int(row.metric_values[0].value or 0)
            pageviews = int(row.metric_values[1].value or 0)
            # Same float-shaped-count trap as _normalize_offsite above, in the report that
            # feeds seo_daily -- the largest of the four.
            conversions = int(float(row.metric_values[2].value or 0))
            bounce_rate = float(row.metric_values[3].value or 0.0)
            users = int(row.metric_values[4].value or 0)
            new_users = int(row.metric_values[5].value or 0)
            engagement_rate = float(row.metric_values[6].value or 0.0)

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
        Upsert GA4 metrics into seo_daily, ga4_traffic_source_daily and ga4_campaign_daily
        in batches. Only updates the GA4-specific columns, preserving GSC data.
        Batched to avoid SQLite 'too many SQL variables' limit.
        """
        if not payload:
            return 0

        seo_records = payload.get("seo_daily", [])
        offsite_records = payload.get("offsite_daily", [])
        campaign_records = payload.get("campaign_daily", [])

        from pipeline.db.dialect import max_batch_size, upsert_insert
        from pipeline.db.schema import SEODaily, GA4TrafficSourceDaily

        insert = upsert_insert(session)
        # ~14 cols * 60 = 840, safely under SQLite's ~999 limit; Postgres takes more.
        BATCH_SIZE = max_batch_size(session, 60)
        total = 0
        for i in range(0, len(seo_records), BATCH_SIZE):
            batch = seo_records[i:i + BATCH_SIZE]
            stmt = insert(SEODaily).values(batch)
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
            stmt = insert(GA4TrafficSourceDaily).values(batch)
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

        # ga4_campaign_daily goes through the shared writer rather than another inline
        # upsert — it self-provisions its table (ensure_tables) for databases created
        # before it existed.
        # Records already carry the site_url resolved in fetch(); the site_id arg is only a
        # setdefault fallback, so it can never overwrite the correct value.
        total += upsert_ga4_campaign_daily(session, campaign_records, site_id=site_id)

        # Written in the same transaction as the breakdowns so the two can never drift to
        # different dates — same rule as the GSC connector's seo_daily_totals.
        from pipeline.db.schema import GA4DailyTotal
        from pipeline.db.writer import ensure_tables, upsert_ga4_daily_totals
        ensure_tables(session, GA4DailyTotal)
        total += upsert_ga4_daily_totals(session, payload.get("daily_totals", []), site_id=site_id)

        return total


if __name__ == "__main__":
    connector = GA4Connector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} days of GA4 data")
    if records:
        print(f"Sample: {records[0]}")

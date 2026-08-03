"""
pipeline/connectors/gsc.py — Google Search Console connector.

Fetches: daily clicks, impressions, CTR, avg_position per site.
Writes to: seo_daily table.

Rate limit: 50,000 page-keyword pairs/day.
Strategy: Fetch only data for dates NOT already in SQLite (append-only).
Auth: OAuth2 via pipeline/utils/auth.py — auto-refreshes every hour.

GSC has a 3-day data delay. We always fetch D-3 to avoid empty responses.
"""

import os
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build

from pipeline.connectors.base import BaseConnector
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import gsc_safe_range, iso
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_seo_daily, upsert_seo_daily_totals
from pipeline.db.schema import SEODaily
from sqlalchemy import select, func

load_dotenv()

# The daily totals cover this many periods: the one on screen, plus the one every KPI is
# compared against. Two, because the Overview shows a single period-over-period delta.
COMPARISON_PERIODS = 2


class GSCConnector(BaseConnector):
    name = "gsc"

    def __init__(self):
        super().__init__()
        # site_url is now resolved per-call from the Site row (Phase 2).
        # We still keep the .env value as a last-resort fallback so this
        # class can be instantiated even when no Site row exists yet.
        self.site_url = os.getenv("GSC_SITE_URL")

    def _resolve_site(self, site_id: Optional[str]) -> str:
        """Return the GSC site URL to query — prefers Site.gsc_property, falls back to .env.
        The stored value is auto-matched against the account's real property list (and the
        Site row repaired) because add_site defaults it to a bare domain, which the GSC API
        reads as the http:// URL-prefix property and 403s — see gsc_property.py."""
        from pipeline.connectors.gsc_property import resolve_gsc_property
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            stored = (site.gsc_property or site.site_url) if site else None
            key = site.site_url if site else None
        if stored:
            return resolve_gsc_property(key, stored)
        return self.site_url or ""

    def _get_last_synced_date(self, site_url: str) -> Optional[date]:
        """Most recent date **this connector** has written search data for, or None.

        `impressions > 0` is what makes the row GSC's own, and the filter is load-bearing:
        `seo_daily` is a shared table where `ga4` writes the analytics columns and leaves
        clicks/impressions/ctr/avg_position at 0 (see ga4._normalize). Asking for the newest
        row of ANY kind therefore read GA4's cursor, not GSC's — and because GA4's window ends
        *yesterday* while gsc_safe_range ends *today − 3*, fetch() computed
        `new_start > new_end` and returned [] on every run once GA4 had synced even once.
        The connector logged `success, 0 records` each time, so nothing looked broken while
        every GSC figure on the Overview page sat at 0 permanently
        (production, premierstaff.com, 2026-07-30).

        The predicate is exact rather than a heuristic: the Search Analytics API only returns
        a row because that page was served, so a GSC row always has impressions >= 1. A row
        both connectors wrote (same date/country/device/landing_page) also has impressions >= 1
        and counts, correctly, as synced.
        """
        with get_session() as session:
            try:
                result = session.execute(
                    select(func.max(SEODaily.date)).where(
                        SEODaily.site_id == site_url,
                        SEODaily.impressions > 0,
                    )
                ).scalar()
            except Exception:
                result = None
        return result

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_date_range(self, site_url: str, start_str: str, end_str: str) -> list[dict]:
        """
        Fetch GSC data for a specific date range from a specific site.
        Makes paginated requests (25,000 rows per call, max 2 pages for most sites).
        """
        creds = get_google_credentials()
        service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

        all_rows = []
        start_row = 0
        row_limit = 25000

        while True:
            body = {
                "startDate": start_str,
                "endDate": end_str,
                "dimensions": ["date", "country", "device", "page"],
                "rowLimit": row_limit,
                "startRow": start_row,
            }

            self.logger.debug(
                f"[gsc] Fetching rows {start_row}–{start_row + row_limit} "
                f"for {start_str} → {end_str} on {site_url}"
            )

            response = (
                service.searchanalytics()
                .query(siteUrl=site_url, body=body)
                .execute()
            )

            rows = response.get("rows", [])
            all_rows.extend(rows)

            # Stop if fewer rows returned than requested (last page)
            if len(rows) < row_limit:
                break

            start_row += row_limit

        return all_rows

    def _normalize(self, raw_rows: list[dict], site_url: str) -> list[dict]:
        """
        Convert GSC API response rows to seo_daily table format.
        """
        records = []
        for row in raw_rows:
            keys = row.get("keys", [])
            if len(keys) < 4:
                continue

            row_date_str = keys[0]
            country_iso = keys[1].upper()  # ISO 3166-1 alpha-3 code (e.g. USA)
            device = keys[2].lower()
            landing_page = keys[3]

            if not row_date_str:
                continue

            records.append({
                "date":         date.fromisoformat(row_date_str),
                "site_id":      site_url,
                "country":      country_iso,
                "device":       device,
                "landing_page": landing_page,
                "clicks":       int(row.get("clicks", 0)),
                "impressions":  int(row.get("impressions", 0)),
                "ctr":          float(row.get("ctr", 0.0)),
                "avg_position": float(row.get("position", 0.0)),

                # GA4 fields - defaulted so SQLAlchemy compile operates clean
                "sessions":     0,
                "pageviews":    0,
                "bounce_rate":  0.0,
                "conversions":  0,
            })

        return records

    def _fetch_totals(self, site_url: str, canonical: str, start_str: str, end_str: str) -> list[dict]:
        """The unfiltered per-day figures, for `seo_daily_totals`.

        One extra call, grouped by date alone. It exists because the 4-dimension breakdown
        this connector's main query fetches cannot be summed back into Search Console's
        reported total — Google drops sub-threshold rows from a grouped response but still
        counts them in the total, and the loss grows with every added dimension. Grouping by
        date alone showed no loss at all when checked against the no-dimension summary
        (`manage.py gsc_reconcile`), so these are the figures every headline KPI reads.

        Cheap by construction: one row per day, so a 90-day backfill is a single page.
        """
        creds = get_google_credentials()
        service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        response = (
            service.searchanalytics()
            .query(siteUrl=site_url, body={
                "startDate": start_str,
                "endDate": end_str,
                "dimensions": ["date"],
                "rowLimit": 25000,
            })
            .execute()
        )

        records = []
        for row in response.get("rows", []):
            keys = row.get("keys", [])
            if not keys or not keys[0]:
                continue
            records.append({
                "date":         date.fromisoformat(keys[0]),
                "site_id":      canonical,
                "clicks":       int(row.get("clicks", 0)),
                "impressions":  int(row.get("impressions", 0)),
                # Stored as Google reported them for that single day. Across a multi-day
                # window these must be re-derived, not averaged — see SEODailyTotal.
                "ctr":          float(row.get("ctr", 0.0)),
                "avg_position": float(row.get("position", 0.0)),
            })
        return records

    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch GSC data. Skips dates already stored in SQLite (append-only strategy).

        Args:
            site_id: The Site.site_url to fetch for. None falls back to first active site.
            days: Max number of days to fetch on first run. Default: 90.

        Returns:
            List of normalized dicts for seo_daily table.
        """
        site_url = self._resolve_site(site_id)
        if not site_url:
            raise ValueError(
                "[gsc] No site configured. Add a Site row in Settings → Manage Sites "
                "or set GSC_SITE_URL in .env."
            )
        # `site_url` is the GSC property to QUERY; records are stored under the canonical
        # Site.site_url key the app reads by. They differ whenever gsc_property is the
        # sc-domain: form of a plain-domain site — stamping the property here once filed
        # 47k eventstaff rows under a key no page ever read.
        canonical = site_id or site_url

        start_str, end_str = gsc_safe_range(days)

        # Optimize: only fetch new dates if we already have data
        last_date = self._get_last_synced_date(canonical)
        if last_date:
            new_start = last_date + timedelta(days=1)
            new_end = date.fromisoformat(end_str)

            if new_start > new_end:
                self.logger.info(f"[gsc] No new dates to fetch for {site_url}. Last synced: {last_date}")
                return []

            start_str = iso(new_start)
            self.logger.info(f"[gsc] Incremental fetch [{site_url}]: {start_str} → {end_str}")
        else:
            self.logger.info(f"[gsc] Full historical fetch [{site_url}]: {start_str} → {end_str}")

        raw_rows = self._fetch_date_range(site_url, start_str, end_str)
        records = self._normalize(raw_rows, canonical)

        # Totals ignore the incremental cursor entirely and re-read the whole window every
        # run. Two reasons, and both matter more than the saving:
        #   * Google keeps revising a day's figures for days after first publishing them, so
        #     anything recent that was stored once is provisional.
        #   * A partially-filled totals table is worse than an empty one. `query_gsc_totals`
        #     cannot tell "28 days, 3 of them synced" from "28 quiet days" — it would report
        #     the 3-day figure as the 28-day one. Covering the full window makes that
        #     unrepresentable rather than merely unlikely, which is what an upgrade on a site
        #     that already has months of `seo_daily` needs.
        # The window is days x COMPARISON_PERIODS, not days: every Overview KPI is shown
        # against the preceding period of the same length, so a 90-day view needs 180 days of
        # totals to have a baseline. Fetching only `days` left the comparison window empty,
        # the previous period fell through to the undercounted breakdown, and the Decision
        # Signals panel announced "Organic traffic up 2361.6%" on a site that had not grown.
        #
        # The cost is one request returning at most days x 2 rows, against the tens of
        # thousands the breakdown above already paged through.
        totals_start, totals_end = (date.fromisoformat(d)
                                    for d in gsc_safe_range(days * COMPARISON_PERIODS))
        self._totals = []
        if totals_start <= totals_end:
            try:
                self._totals = self._fetch_totals(site_url, canonical, iso(totals_start), iso(totals_end))
                self.logger.info(
                    f"[gsc] Fetched {len(self._totals)} daily totals for {site_url} "
                    f"({iso(totals_start)} → {iso(totals_end)})"
                )
            except Exception:
                # Non-fatal on purpose. The breakdown rows above are the expensive part of a
                # sync that can run for half an hour; losing all of them because a one-row-
                # per-day follow-up call failed would be the worse outcome. The totals simply
                # stay at their last good values, and because every run re-reads the whole
                # window rather than only new dates, the next one repairs them.
                self.logger.warning(
                    f"[gsc] daily-totals fetch failed for {site_url}; keeping the previously "
                    f"stored totals and continuing with the breakdown", exc_info=True
                )

        self.logger.info(f"[gsc] Fetched {len(records)} rows for {site_url}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        written = upsert_seo_daily(session, records, site_id=site_id)
        # Written here rather than from a connector of their own so the two can never drift
        # to different dates: one fetch, one transaction, both tables.
        upsert_seo_daily_totals(session, getattr(self, "_totals", []), site_id=site_id)
        return written


if __name__ == "__main__":
    """
    Quick test: python pipeline/connectors/gsc.py
    Prints how many records were fetched without writing to DB.
    """
    import json
    connector = GSCConnector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} records from GSC")
    if records:
        print("Sample record:")
        print(json.dumps(str(records[0]), indent=2))

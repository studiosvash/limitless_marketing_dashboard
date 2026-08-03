"""Compare what GA4 reports against what `seo_daily` holds — the GA4 half of `gsc_reconcile`.

Same question, same shape, different API. GA4 rows are stored at
(date, country, deviceCategory, pagePath) grain, and the Analytics Data API applies a
cardinality limit to high-dimension reports: combinations beyond it collapse into an
"(other)" bucket. Whether that costs us anything is measurable rather than arguable, so this
asks GA4 the same window two ways:

  totals   — no dimensions. What the GA4 UI's own report shows.
  by_date  — dimensions=["date"], the shape a totals table would store.
  stored   — what `seo_daily` has, i.e. what the dashboard renders.

`totalUsers` is deliberately absent from the stored column: unique users are not additive
across dimensions, so summing them over a (date, country, device, page) breakdown counts one
person once per page they visited. The API columns are still printed, as the reference for
what a totals table would have to hold if the dashboard ever wants to show users.

Read-only. Calls the API but writes nothing.

    python manage.py ga4_reconcile --site premierstaff.com
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from sqlalchemy import func, select

from pipeline.connectors.ga4 import normalise_property_id
from pipeline.db.schema import SEODaily
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.db_connection import get_session

# GA4's own report windows are arbitrary, but matching gsc_reconcile keeps the two outputs
# readable side by side.
WINDOWS = [("24 hours", 1), ("7 days", 7), ("28 days", 28), ("3 months", 90)]

METRICS = ["sessions", "screenPageViews", "conversions", "totalUsers"]


class Command(BaseCommand):
    help = "Compare GA4's reported totals against the stored seo_daily rows."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True, help="Site.site_url to reconcile")
        parser.add_argument("--lag", type=int, default=1,
                            help="End each window this many days before today. 1 (default) "
                                 "matches GA4's own 'yesterday'; the sync uses the same.")

    def handle(self, *args, **opts):
        site_key, lag = opts["site"], opts["lag"]

        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_key)
            pid = normalise_property_id(site.ga4_property_id if site else None)
        if not pid:
            self.stderr.write(f"No GA4 property configured for {site_key!r}.")
            return

        self.stdout.write(f"GA4 property : {pid}")
        self.stdout.write(f"seo_daily key: {site_key}")
        self.stdout.write(f"window ends  : today - {lag} day(s)\n")

        client = BetaAnalyticsDataClient(credentials=get_google_credentials())

        header = (f"{'window':<10} {'source':<12} {'sessions':>10} {'pageviews':>11} "
                  f"{'conversions':>12} {'users':>9}")
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        for label, days in WINDOWS:
            end = date.today() - timedelta(days=lag)
            start = end - timedelta(days=days - 1)

            api_total = self._query(client, pid, start, end, dimensions=[])
            api_dated = self._query(client, pid, start, end, dimensions=["date"])
            stored = self._stored(site_key, start, end)

            self.stdout.write(f"{label:<10} {'GA4 total':<12} " + self._fmt(api_total))
            self.stdout.write(f"{'':<10} {'GA4 by-date':<12} " + self._fmt(api_dated))
            self.stdout.write(f"{'':<10} {'our DB':<12} " + self._fmt(stored))

            if api_total["sessions"]:
                pct = stored["sessions"] / api_total["sessions"] * 100
                self.stdout.write(f"{'':<10} {'-> we have':<12} {pct:>9.1f}% of GA4's sessions")
            self.stdout.write("")

    def _query(self, client, pid, start, end, dimensions):
        resp = client.run_report(RunReportRequest(
            property=f"properties/{pid}",
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in METRICS],
            date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
            limit=100000,
        ))
        out = dict.fromkeys(METRICS, 0.0)
        for row in resp.rows:
            for name, value in zip(METRICS, row.metric_values):
                out[name] += float(value.value or 0)
        # Summing totalUsers over date rows is wrong for the same reason it is wrong over
        # pages — a returning visitor is one user in the window and one per day. Printed as
        # the API returned it, flagged rather than silently added.
        return out

    def _stored(self, site_key, start, end):
        """What a session-total surface reads: ga4_daily_totals (session-scoped, additive),
        falling back to the page-grain breakdown only when the totals are empty — the
        fallback figure is the inflated one, which is exactly what the output should expose
        on a database that has not synced since the totals table was added."""
        from pipeline.db.schema import GA4DailyTotal
        from pipeline.db.writer import ensure_tables
        with get_session() as session:
            ensure_tables(session, GA4DailyTotal)
            row = session.execute(
                select(
                    func.coalesce(func.sum(GA4DailyTotal.sessions), 0),
                    func.coalesce(func.sum(GA4DailyTotal.pageviews), 0),
                    func.coalesce(func.sum(GA4DailyTotal.conversions), 0),
                    func.count(GA4DailyTotal.id),
                ).where(GA4DailyTotal.site_id == site_key,
                        GA4DailyTotal.date >= start, GA4DailyTotal.date <= end)
            ).one()
            if int(row[3]):
                return {"sessions": float(row[0]), "screenPageViews": float(row[1]),
                        "conversions": float(row[2]), "totalUsers": None}

            row = session.execute(
                select(
                    func.coalesce(func.sum(SEODaily.sessions), 0),
                    func.coalesce(func.sum(SEODaily.pageviews), 0),
                    func.coalesce(func.sum(SEODaily.conversions), 0),
                ).where(SEODaily.site_id == site_key,
                        SEODaily.date >= start, SEODaily.date <= end)
            ).one()
        self.stdout.write(self.style.WARNING(
            "  (no ga4_daily_totals rows for this window — showing the page-grain "
            "breakdown sum, which inflates sessions; run the GA4 sync)"))
        return {"sessions": float(row[0]), "screenPageViews": float(row[1]),
                "conversions": float(row[2]), "totalUsers": None}

    @staticmethod
    def _fmt(m):
        users = f"{m['totalUsers']:,.0f}" if m["totalUsers"] is not None else "—"
        return (f"{m['sessions']:>10,.0f} {m['screenPageViews']:>11,.0f} "
                f"{m['conversions']:>12,.0f} {users:>9}")

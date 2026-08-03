"""Delete `ga4_traffic_source_daily` rows that GA4 itself does not report.

Why this table can hold fiction at all: the design prototype's fixtures
(`Design_features/app/fixtures.js`) were loaded into the analytics database at some point —
forbes.com, reddit.com, yelp.com and friends, each present on suspiciously exactly 91 days.
No seeder in the current code regenerates them, but no sync removes them either: the GA4
upsert only touches keys the API actually returns, so a key it never returns survives every
re-sync forever. Measured 2026-08-03: 22,454 of 48,437 stored sessions (46%) were fabricated.

The judge is the API, not a hardcoded blocklist: for every stored date this command asks GA4
for that day's real (channel, source) rows and deletes only what GA4 does not corroborate.
A blocklist would rot the day a real forbes.com referral shows up; asking GA4 cannot.

Deleting is irreversible, so the default is a report. Deletion happens only under --apply.

    python manage.py prune_fabricated_ga4_sources --site premierstaff.com
    python manage.py prune_fabricated_ga4_sources --site premierstaff.com --apply
"""
from collections import defaultdict
from datetime import date as date_cls

from django.core.management.base import BaseCommand
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from sqlalchemy import select, text

from pipeline.connectors.ga4 import normalise_property_id
from pipeline.db.schema import GA4TrafficSourceDaily
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.db_connection import get_session


class Command(BaseCommand):
    help = "Delete ga4_traffic_source_daily rows that GA4's own report does not contain."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True, help="Site.site_url to clean")
        parser.add_argument("--apply", action="store_true",
                            help="Actually delete. Without it, report only.")

    def handle(self, *args, **opts):
        site_key, apply = opts["site"], opts["apply"]

        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_key)
            pid = normalise_property_id(site.ga4_property_id if site else None)
            stored = session.execute(
                select(GA4TrafficSourceDaily.date, GA4TrafficSourceDaily.channel,
                       GA4TrafficSourceDaily.source, GA4TrafficSourceDaily.sessions)
                .where(GA4TrafficSourceDaily.site_id == site_key)
            ).all()
        if not pid:
            self.stderr.write(f"No GA4 property configured for {site_key!r}.")
            return
        if not stored:
            self.stdout.write("Nothing stored for this site.")
            return

        dates = sorted({r[0] for r in stored})
        self.stdout.write(f"GA4 property {pid} · {len(stored):,} stored rows over "
                          f"{len(dates)} dates ({dates[0]} → {dates[-1]})\n")

        # One API call for the whole span, grouped by date+channel+source. GA4 date values
        # come back as YYYYMMDD strings.
        client = BetaAnalyticsDataClient(credentials=get_google_credentials())
        real: set[tuple] = set()
        resp = client.run_report(RunReportRequest(
            property=f"properties/{pid}",
            dimensions=[Dimension(name="date"),
                        Dimension(name="sessionDefaultChannelGroup"),
                        Dimension(name="sessionSource")],
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date=dates[0].isoformat(),
                                   end_date=dates[-1].isoformat())],
            limit=100000,
        ))
        for row in resp.rows:
            raw_d = row.dimension_values[0].value
            d = date_cls(int(raw_d[:4]), int(raw_d[4:6]), int(raw_d[6:8]))
            real.add((d, row.dimension_values[1].value, row.dimension_values[2].value))
        self.stdout.write(f"GA4 reports {len(real):,} real (date, channel, source) rows "
                          f"in that span.\n")

        doomed = [(d, ch, src, ses) for d, ch, src, ses in stored if (d, ch, src) not in real]
        if not doomed:
            self.stdout.write(self.style.SUCCESS("Every stored row is corroborated by GA4."))
            return

        by_source = defaultdict(lambda: [0, 0])
        for _, ch, src, ses in doomed:
            by_source[(src, ch)][0] += 1
            by_source[(src, ch)][1] += int(ses or 0)

        self.stdout.write(f"{'source':<28} {'channel':<18} {'rows':>6} {'sessions':>9}")
        self.stdout.write("-" * 63)
        for (src, ch), (n, ses) in sorted(by_source.items(), key=lambda kv: -kv[1][1]):
            self.stdout.write(f"{src:<28} {ch:<18} {n:>6,} {ses:>9,}")
        total_rows = len(doomed)
        total_sessions = sum(x[3] or 0 for x in doomed)
        self.stdout.write(f"\n{total_rows:,} rows / {total_sessions:,} sessions have no "
                          f"corresponding GA4 row.")

        if not apply:
            self.stdout.write("\nReport only. Re-run with --apply to delete.")
            return

        with get_session() as session:
            for d, ch, src, _ in doomed:
                session.execute(
                    text("DELETE FROM ga4_traffic_source_daily WHERE site_id = :sid "
                         "AND date = :d AND channel = :ch AND source = :src"),
                    {"sid": site_key, "d": d, "ch": ch, "src": src},
                )
            session.commit()
        self.stdout.write(self.style.SUCCESS(f"Deleted {total_rows:,} fabricated rows."))

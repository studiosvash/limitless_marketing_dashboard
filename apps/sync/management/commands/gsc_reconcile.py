"""Compare what Search Console reports against what `seo_daily` actually holds.

Why this exists: the Overview KPIs are summed over `seo_daily` rows, which are stored at
(date, country, device, page) grain. Search Console's own Performance report shows the
*unfiltered* total, and Google does not guarantee that a dimension-grouped table adds up to
it — rows below its privacy threshold are dropped from the breakdown but still counted in
the total. So a gap is expected; the question this command answers is *how big*, and whether
it is a Google artefact or our own sync losing data.

It asks the API the same window three ways, so the two effects can be told apart:

  totals   — no dimensions at all. This is the number the Search Console UI shows.
  by_date  — dimensions=["date"]. Should equal `totals`; if it doesn't, Google is
             thresholding even at date grain.
  stored   — what `seo_daily` has for that window, i.e. what the dashboard renders.

Read-only. Calls the API but writes nothing.

    python manage.py gsc_reconcile --site premierstaff.com
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from googleapiclient.discovery import build
from sqlalchemy import func, select

from pipeline.db.schema import SEODaily
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.db_connection import get_session

# (label, days) — mirrors the ranges Search Console's own UI offers, so the operator can put
# this output next to a browser tab and compare like for like.
WINDOWS = [("24 hours", 1), ("7 days", 7), ("28 days", 28), ("3 months", 90)]


class Command(BaseCommand):
    help = "Compare Search Console's reported totals against the stored seo_daily rows."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True,
                            help="Site.site_url to reconcile, e.g. premierstaff.com")
        parser.add_argument("--lag", type=int, default=0,
                            help="End each window this many days before today. 0 (default) "
                                 "matches what the Search Console UI shows; the sync's own "
                                 "gsc_safe_range uses 3.")

    def handle(self, *args, **opts):
        site_key = opts["site"]
        lag = opts["lag"]

        from pipeline.connectors.gsc_property import resolve_gsc_property
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_key)
            stored_prop = (site.gsc_property or site.site_url) if site else None
        if not stored_prop:
            self.stderr.write(f"No Site row for {site_key!r}.")
            return
        prop = resolve_gsc_property(site_key, stored_prop)
        self.stdout.write(f"GSC property : {prop}")
        self.stdout.write(f"seo_daily key: {site_key}")
        self.stdout.write(f"window ends  : today - {lag} day(s)\n")

        service = build("searchconsole", "v1",
                        credentials=get_google_credentials(), cache_discovery=False)

        header = f"{'window':<10} {'source':<10} {'clicks':>9} {'impressions':>13} {'CTR':>7} {'pos':>6}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        for label, days in WINDOWS:
            end = date.today() - timedelta(days=lag)
            start = end - timedelta(days=days - 1)

            api_total = self._query(service, prop, start, end, dimensions=[])
            api_dated = self._query(service, prop, start, end, dimensions=["date"])
            stored = self._stored(site_key, start, end)

            self.stdout.write(f"{label:<10} {'GSC total':<10} " + self._fmt(api_total))
            self.stdout.write(f"{'':<10} {'GSC by-date':<10} " + self._fmt(api_dated))
            self.stdout.write(f"{'':<10} {'our DB':<10} " + self._fmt(stored))

            if api_total["clicks"]:
                pct = stored["clicks"] / api_total["clicks"] * 100
                self.stdout.write(f"{'':<10} {'-> we have':<10} {pct:>8.1f}% of GSC's clicks")
            self.stdout.write("")

    def _query(self, service, prop, start, end, dimensions):
        """One Search Analytics call, paginated. `dimensions=[]` returns a single summary row —
        the unfiltered figure the UI shows."""
        rows, start_row = [], 0
        while True:
            body = {
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "dimensions": dimensions,
                "rowLimit": 25000,
                "startRow": start_row,
            }
            page = service.searchanalytics().query(siteUrl=prop, body=body).execute()
            got = page.get("rows", [])
            rows.extend(got)
            if len(got) < 25000:
                break
            start_row += 25000

        clicks = sum(int(r.get("clicks", 0)) for r in rows)
        impressions = sum(int(r.get("impressions", 0)) for r in rows)
        # Position is impression-weighted, exactly as Search Console computes it. A plain mean
        # over rows would let a single-impression row at position 90 outweigh a page with
        # 50,000 impressions at position 3.
        weighted = sum(float(r.get("position", 0.0)) * int(r.get("impressions", 0)) for r in rows)
        return self._metrics(clicks, impressions, weighted)

    def _stored(self, site_key, start, end):
        with get_session() as session:
            row = session.execute(
                select(
                    func.coalesce(func.sum(SEODaily.clicks), 0),
                    func.coalesce(func.sum(SEODaily.impressions), 0),
                    func.coalesce(func.sum(SEODaily.avg_position * SEODaily.impressions), 0.0),
                ).where(
                    SEODaily.site_id == site_key,
                    SEODaily.date >= start,
                    SEODaily.date <= end,
                    SEODaily.impressions > 0,   # GSC's own rows; GA4 leaves these columns at 0
                )
            ).one()
        return self._metrics(int(row[0]), int(row[1]), float(row[2]))

    @staticmethod
    def _metrics(clicks, impressions, weighted_position):
        return {
            "clicks": clicks,
            "impressions": impressions,
            # Both derived the way Search Console derives them: CTR is total clicks over total
            # impressions, never a mean of per-row CTRs.
            "ctr": (clicks / impressions) if impressions else None,
            "position": (weighted_position / impressions) if impressions else None,
        }

    @staticmethod
    def _fmt(m):
        ctr = f"{m['ctr'] * 100:.2f}%" if m["ctr"] is not None else "—"
        pos = f"{m['position']:.1f}" if m["position"] is not None else "—"
        return f"{m['clicks']:>9,} {m['impressions']:>13,} {ctr:>7} {pos:>6}"

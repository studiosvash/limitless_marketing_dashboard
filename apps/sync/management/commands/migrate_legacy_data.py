"""
One-time migration of real data from the Streamlit MVP DB (data/cache.db) into the
new production databases:
  * analytics rows -> fusehealth.db        (SQLAlchemy schema; this task)
  * insights       -> dashboard.Insight    (Django ORM; Task 8)

Intended as a ONE-TIME migration against an empty fusehealth.db. Re-running ignores
rows whose unique key fully matches an existing row. Caveat: SQLite treats NULLs as
DISTINCT in a unique index, so rows with all-NULL dimension columns (e.g. an aggregate
seo_daily row with no country/device/landing_page) are NOT dedupe-safe on a second run.
Prints before/after row counts — no success is claimed without the counts.
"""
import sqlite3
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from pipeline.db.engine import get_engine
from pipeline.db.schema import (
    init_db,
    Site,
    SEODaily,
    KeywordRanking,
    Page,
    AdMetricDaily,
    Backlink,
    CompetitorVisibility,
    CompetitorDomain,
    TechnicalIssue,
    PageSpeed,
    IndexingStatus,
    SEOAggregate,
    AISummary,
    Anomaly,
    ComparativeMetrics,
)

# (old_table_name, new_model, inject_site_id_when_missing)
TABLE_MAP = [
    ("sites", Site, False),
    ("seo_daily", SEODaily, False),
    ("keyword_rankings", KeywordRanking, False),
    ("pages", Page, False),
    ("ad_metrics_daily", AdMetricDaily, False),
    ("backlinks", Backlink, False),
    ("competitor_visibility", CompetitorVisibility, False),
    ("competitor_domains", CompetitorDomain, False),
    ("technical_issues", TechnicalIssue, False),
    ("page_speed", PageSpeed, False),
    ("indexing_status", IndexingStatus, False),
    ("seo_aggregates", SEOAggregate, False),
    ("ai_summaries", AISummary, False),
    ("anomalies", Anomaly, True),
    ("comparative_metrics", ComparativeMetrics, True),
]


class Command(BaseCommand):
    help = "Migrate real data from the Streamlit MVP cache.db into the new databases."

    def add_arguments(self, parser):
        default_source = str(Path(settings.BASE_DIR).parent / "data" / "cache.db")
        parser.add_argument(
            "--source",
            default=default_source,
            help="Path to the old MVP SQLite DB (default: ../data/cache.db).",
        )

    def handle(self, *args, **opts):
        source = Path(opts["source"])
        if not source.exists():
            raise CommandError(f"Source DB not found: {source}")

        init_db(get_engine(settings.ANALYTICS_DB_PATH))
        active = self._active_site(source)
        self.stdout.write(f"Active site for backfill: {active!r}")

        conn = sqlite3.connect(settings.ANALYTICS_DB_PATH)
        conn.execute("ATTACH DATABASE ? AS old", (str(source),))
        self.stdout.write("\n=== Analytics (cache.db -> fusehealth.db) ===")
        for old_table, model, inject in TABLE_MAP:
            self._copy(conn, old_table, model, inject, active)
        conn.commit()
        conn.close()

        self._migrate_insights(source, active)
        self.stdout.write(self.style.SUCCESS("\nMigration complete."))

    # --- helpers ---------------------------------------------------------

    def _active_site(self, source: Path) -> str:
        c = sqlite3.connect(str(source))
        c.row_factory = sqlite3.Row
        try:
            row = c.execute(
                "SELECT site_url FROM sites WHERE is_active = 1 ORDER BY id LIMIT 1"
            ).fetchone()
            return row["site_url"] if row else ""
        except sqlite3.OperationalError:
            return ""
        finally:
            c.close()

    def _old_cols(self, conn, table: str) -> list:
        return [r[1] for r in conn.execute(f"PRAGMA old.table_info({table})").fetchall()]

    def _copy(self, conn, table: str, model, inject: bool, active: str) -> None:
        old_cols = self._old_cols(conn, table)
        if not old_cols:
            self.stdout.write(f"  {table}: (absent in source, skipped)")
            return

        new_cols = [c for c in model.__table__.columns.keys() if c != "id"]
        shared = [c for c in new_cols if c in old_cols]
        target = list(shared)
        select = list(shared)
        params = ()
        if inject and "site_id" in new_cols and "site_id" not in old_cols:
            target = ["site_id"] + target
            select = ["?"] + select
            params = (active,)

        where = " WHERE data_source = 'real'" if "data_source" in old_cols else ""
        sql = (
            f"INSERT OR IGNORE INTO {table} ({', '.join(target)}) "
            f"SELECT {', '.join(select)} FROM old.{table}{where}"
        )
        before = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.execute(sql, params)
        after = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        self.stdout.write(f"  {table}: {before} -> {after}  (+{after - before})")

    @staticmethod
    def _as_date(value):
        """Coerce a stored ISO date string to a date; pass through real dates/None."""
        if value is None or isinstance(value, date):
            return value
        return date.fromisoformat(str(value)[:10])

    def _migrate_insights(self, source: Path, active: str) -> None:
        from django.contrib.auth import get_user_model
        from apps.dashboard.models import Insight

        self.stdout.write("\n=== Insights (cache.db -> Django dashboard.Insight) ===")
        User = get_user_model()

        c = sqlite3.connect(str(source))
        c.row_factory = sqlite3.Row
        try:
            rows = c.execute("SELECT * FROM insights").fetchall()
        except sqlite3.OperationalError:
            self.stdout.write("  insights: (absent in source, skipped)")
            c.close()
            return

        created = 0
        for r in rows:
            keys = r.keys()
            username = r["created_by"] if "created_by" in keys else None
            user = User.objects.filter(username=username).first() if username else None
            _, was_created = Insight.objects.get_or_create(
                site_url=active,
                date=self._as_date(r["date"]),
                title=r["title"],
                defaults=dict(
                    team=(r["team"] if "team" in keys else "marketing"),
                    description=(r["description"] if "description" in keys else ""),
                    affected_metric=(r["affected_metric"] if "affected_metric" in keys else None),
                    dimension=(r["dimension"] if "dimension" in keys else None),
                    impact=(r["impact"] if "impact" in keys else "neutral"),
                    hypothesis=(r["hypothesis"] if "hypothesis" in keys else None),
                    action_taken=(r["action_taken"] if "action_taken" in keys else None),
                    created_by=user,
                    is_verified=bool(r["is_verified"]) if "is_verified" in keys else False,
                ),
            )
            created += int(was_created)
        c.close()
        self.stdout.write(
            f"  insights: read {len(rows)} rows -> {Insight.objects.count()} in Django "
            f"({created} new this run)"
        )

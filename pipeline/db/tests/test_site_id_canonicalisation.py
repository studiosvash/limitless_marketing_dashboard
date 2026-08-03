"""The writer must file every record under the canonical `Site.site_url`, whatever spelling
the connector stamped.

This is the guard against the duplicated-history incident of 2026-08-03: a connector wrote
premierstaff.com's entire GSC history a second time under `https://premierstaff.com/`,
123,396 rows no page read and any two-spelling query double-counted. The cleanup removed the
rows; this makes the mistake unrepresentable at the write layer, which is where it belongs —
one writer, many connectors.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, Site
from pipeline.db.writer import upsert_seo_daily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class CanonicalSiteIdTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url="example.com", site_name="Example",
                             gsc_property="sc-domain:example.com"))
            session.commit()

    def _row(self, site_id, day=date(2026, 5, 1)):
        return {"date": day, "site_id": site_id, "country": "USA", "device": "mobile",
                "landing_page": "https://example.com/", "clicks": 1, "impressions": 10,
                "ctr": 0.1, "avg_position": 5.0}

    def _stored_site_ids(self):
        with get_session() as session:
            return {r[0] for r in session.execute(
                __import__("sqlalchemy").select(SEODaily.site_id).distinct()).all()}

    def test_all_spellings_collapse_to_the_canonical_key(self):
        with get_session() as session:
            upsert_seo_daily(session, [
                self._row("example.com", date(2026, 5, 1)),
                self._row("sc-domain:example.com", date(2026, 5, 2)),
                self._row("https://example.com/", date(2026, 5, 3)),
            ])
            session.commit()

        self.assertEqual(self._stored_site_ids(), {"example.com"})

    def test_same_day_two_spellings_is_one_row_not_two(self):
        """The exact incident shape: the same day written under two spellings must upsert
        into ONE row, not create a parallel copy."""
        with get_session() as session:
            upsert_seo_daily(session, [self._row("example.com")])
            upsert_seo_daily(session, [self._row("https://example.com/")])
            session.commit()

        with get_session() as session:
            from sqlalchemy import func, select
            n = session.execute(select(func.count(SEODaily.id))).scalar()
        self.assertEqual(n, 1)

    def test_unknown_site_passes_through_unchanged(self):
        """A spelling that matches no Site row is written as-is — refusing would turn a
        missing Site row into silent data loss."""
        with get_session() as session:
            upsert_seo_daily(session, [self._row("stranger.example")])
            session.commit()

        self.assertEqual(self._stored_site_ids(), {"stranger.example"})

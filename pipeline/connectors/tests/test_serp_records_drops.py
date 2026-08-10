"""The SERP connector must actually USE the overwrite capability (P6, wiring half).

`upsert_keyword_rankings` grew an `overwrite_columns` argument so a connector that inspected the
SERP can record a measured ABSENCE. That capability is inert until the caller opts in — and a
writer feature nobody passes is indistinguishable, in production, from never having been built.

This test goes through `DataForSEOSERPConnector._write_records`, not the writer directly, so it
fails if the connector stops passing `SERP_MEASUREMENT_COLUMNS`. The writer's own behaviour is
covered by `pipeline/db/tests/test_ranking_overwrite.py`; this is the wire.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings
from sqlalchemy import select

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import KeywordRanking, init_db
from pipeline.utils.db_connection import get_session

DAY = date(2026, 8, 1)
LOC = "United States"
SITE = "example.com"


class SerpConnectorRecordsMeasuredDropTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        db_connection._SessionFactory = None

    def _write(self, records):
        """Drive the connector's own write path, without constructing the connector (its
        __init__ demands DataForSEO credentials this test has no business needing)."""
        from pipeline.connectors.dataforseo_serp import DataForSEOSERPConnector

        with get_session() as session:
            n = DataForSEOSERPConnector._write_records(
                DataForSEOSERPConnector.__new__(DataForSEOSERPConnector),
                session, records, site_id=SITE,
            )
            session.commit()
        return n

    def _stored(self):
        with get_session() as session:
            return session.execute(
                select(KeywordRanking.position, KeywordRanking.rank_checked_at)
                .where(KeywordRanking.site_id == SITE, KeywordRanking.keyword == "event staffing")
            ).first()

    def test_a_drop_out_of_the_captured_depth_overwrites_a_recorded_position(self):
        self._write([{
            "date": DAY, "site_id": SITE, "keyword": "event staffing", "location": LOC,
            "position": 4, "url": "https://example.com/staffing",
            "rank_checked_at": date(2026, 8, 1),
        }])
        self.assertEqual(self._stored()[0], 4)

        # Re-measured later: the domain is no longer inside the captured depth.
        self._write([{
            "date": DAY, "site_id": SITE, "keyword": "event staffing", "location": LOC,
            "position": None, "url": None,
            "rank_checked_at": date(2026, 8, 2),
        }])

        position, checked_at = self._stored()
        self.assertIsNone(position, "a measured absence must replace the stale #4, not be discarded")
        # The freshness stamp advances with it -- the old behaviour advanced this stamp while
        # keeping the stale rank, which is what made the wrong number look verified.
        self.assertEqual(checked_at, date(2026, 8, 2))

    def test_a_price_only_write_still_cannot_blank_a_position(self):
        """The COALESCE default has to survive for every column this connector does not own —
        otherwise the fix for one connector breaks the other two that share this row."""
        from pipeline.db.writer import upsert_keyword_rankings

        self._write([{
            "date": DAY, "site_id": SITE, "keyword": "event staffing", "location": LOC,
            "position": 4, "url": "https://example.com/staffing",
        }])

        # dataforseo_keywords writes volume and knows nothing about ranks.
        with get_session() as session:
            upsert_keyword_rankings(session, [{
                "date": DAY, "site_id": SITE, "keyword": "event staffing", "location": LOC,
                "search_volume": 480,
            }], site_id=SITE)
            session.commit()

        self.assertEqual(self._stored()[0], 4)

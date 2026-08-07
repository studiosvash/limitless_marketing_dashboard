"""Scoping gap probe (pre-deploy audit, 2026-08-07).

One test, deliberately narrow: the existing location-scoping suite proves
`_get_ranking_distribution` filters measurements by `location`, but the rankings table the
Positioning and Keywords pages actually render comes from
`keywords_service.get_keyword_intelligence_raw`, whose `get_kw_df` query filters only on
`site_id` + date + keyword text. If that query ignores its `location` argument, a New York
project's row for a keyword that a Las Vegas sibling also tracks reads the AVERAGE of both
cities' positions — the exact cross-location blend the location column was added to remove.

This test seeds one domain, one keyword, one day, two cities (NY position 3, LV position 27,
same fixture values as test_location_scoping) and asserts the NY-scoped read reports 3.
If it fails with position 15.0, the measurement query is location-blind.
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import TestCase, override_settings

from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
from pipeline.db.schema import KeywordRanking, SavedKeyword, init_db
from pipeline.db.writer import ensure_tables, upsert_keyword_rankings
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session

SITE = "premierstaff.com"
NY = "United States - New York, NY"
LV = "United States - Las Vegas, NV"
KW = "event staffing"
DAY = date(2026, 8, 6)


def _new_analytics_db(test_case):
    """Fresh temp analytics DB per test — same pattern as test_location_scoping.py."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)


class KeywordIntelligenceMeasurementsAreLocationScopedTests(TestCase):
    """A NY project's keyword table must not average in a LV sibling's SERP rows."""

    def setUp(self):
        _new_analytics_db(self)
        with get_session() as session:
            ensure_tables(session, KeywordRanking, SavedKeyword)
            # Both city projects track the same keyword text — the normal shared-domain case.
            session.add(SavedKeyword(site_id=SITE, keyword=KW, location=NY))
            session.add(SavedKeyword(site_id=SITE, keyword=KW, location=LV))
            session.commit()
        with get_session() as session:
            upsert_keyword_rankings(session, [
                {"date": DAY, "site_id": SITE, "keyword": KW, "location": NY,
                 "position": 3, "url": "https://premierstaff.com/nyc/"},
                {"date": DAY, "site_id": SITE, "keyword": KW, "location": LV,
                 "position": 27, "url": "https://premierstaff.com/"},
            ], site_id=SITE)

    def test_ny_scoped_read_reports_only_new_yorks_position(self):
        intel = get_keyword_intelligence_raw(
            SITE,
            DAY - timedelta(days=1), DAY,          # current window catches both rows' date
            DAY - timedelta(days=30), DAY - timedelta(days=2),
            tracked_only=True, location=NY,
        )
        rows = [r for r in intel["full_keywords"] if r["keyword"] == KW]
        self.assertEqual(len(rows), 1)
        # NY's captured position is 3. If this reads 15.0, the LV row leaked into the
        # average: get_kw_df filtered the tracked LIST by location but not the MEASUREMENTS.
        self.assertEqual(rows[0]["position"], 3)

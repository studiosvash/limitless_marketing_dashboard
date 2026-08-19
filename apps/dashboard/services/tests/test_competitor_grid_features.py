"""SERP features on the competitor grid: AI Overview citation slots and local-pack /
featured-snippet presence attached to the `you` and competitor cells.

The stored rows carry the domain exactly as the SERP reported it; matching to the grid's
columns is a read-time contains-match (the connector's organic rule). A cell whose domain
has no feature row keeps aio=None / feat=None — an absent feature is never invented.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import (init_db, KeywordRanking, CompetitorKeywordRanking,
                                SavedKeyword, SerpFeatureRanking, TrackedCompetitor)
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE = "sc-domain:fusehealth.com"
LOC = "United States"
DAY = date(2026, 8, 17)


class CompetitorGridFeatureTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add_all([
                SavedKeyword(site_id=SITE, keyword="iv therapy", location=LOC),
                SavedKeyword(site_id=SITE, keyword="mobile iv drip", location=LOC),
                KeywordRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                               position=2, url="/iv-therapy", location=LOC),
                KeywordRanking(date=DAY, site_id=SITE, keyword="mobile iv drip",
                               position=6, url="/mobile", location=LOC),
                TrackedCompetitor(site_id=SITE, competitor_domain="driphydration.com"),
                CompetitorKeywordRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                                         competitor_domain="driphydration.com",
                                         position=8, location=LOC),
                # ── SERP features for "iv therapy" @ LOC ────────────────────────────────
                # Yours: cited 2nd in the AI Overview, local pack slot 2. Note the stored
                # domain is the bare form while SITE is the sc-domain: spelling — the
                # contains-match must bridge that.
                SerpFeatureRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                                   location=LOC, domain="fusehealth.com",
                                   feature_type="ai_overview", slot=2,
                                   url="https://fusehealth.com/iv", title="IV"),
                SerpFeatureRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                                   location=LOC, domain="fusehealth.com",
                                   feature_type="local_pack", slot=2),
                # The competitor: citation 1 and the featured snippet.
                SerpFeatureRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                                   location=LOC, domain="driphydration.com",
                                   feature_type="ai_overview", slot=1),
                SerpFeatureRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                                   location=LOC, domain="driphydration.com",
                                   feature_type="featured_snippet", slot=1),
                # An unrelated cited domain — stored (the table keeps the full citation
                # list) but matching NO grid column.
                SerpFeatureRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                                   location=LOC, domain="wikipedia.org",
                                   feature_type="ai_overview", slot=3),
                # Same keyword, ANOTHER location: a better citation slot that must stay
                # invisible to this project's grid.
                SerpFeatureRanking(date=DAY, site_id=SITE, keyword="iv therapy",
                                   location="United States - New York, NY",
                                   domain="fusehealth.com",
                                   feature_type="ai_overview", slot=1),
                # "mobile iv drip" @ NY only — feature rows exist for the keyword, but in
                # a location this grid is not scoped to.
                SerpFeatureRanking(date=DAY, site_id=SITE, keyword="mobile iv drip",
                                   location="United States - New York, NY",
                                   domain="fusehealth.com",
                                   feature_type="featured_snippet", slot=1),
            ])

    def _grid(self):
        from apps.dashboard.services.shared_queries import _get_competitor_grid
        return _get_competitor_grid(SITE, location=LOC)

    def _row(self, grid, kw):
        return next(r for r in grid["rows"] if r["kw"] == kw)

    def test_you_cell_carries_aio_and_feat(self):
        grid = self._grid()
        self.assertEqual(grid["status"], "ok")
        you = self._row(grid, "iv therapy")["you"]
        self.assertEqual(you["aio"], 2)
        self.assertEqual(you["feat"], {"type": "local_pack", "slot": 2})
        # Existing cell keys are untouched.
        for key in ("pos", "prev", "diff", "direction", "url"):
            self.assertIn(key, you)
        self.assertEqual(you["pos"], 2)

    def test_competitor_cell_carries_aio_and_feat(self):
        row = self._row(self._grid(), "iv therapy")
        drip = next(c for c in row["comps"] if c["domain"] == "driphydration.com")
        self.assertEqual(drip["aio"], 1)
        self.assertEqual(drip["feat"], {"type": "featured_snippet", "slot": 1})
        self.assertEqual(drip["pos"], 8)

    def test_unrelated_domain_attaches_to_nothing(self):
        # wikipedia.org holds citation slot 3 — no cell may claim it.
        grid = self._grid()
        for row in grid["rows"]:
            self.assertNotEqual(row["you"]["aio"], 3)
            for c in row["comps"]:
                self.assertNotEqual(c["aio"], 3)

    def test_rows_in_another_location_are_invisible(self):
        grid = self._grid()
        # The NY slot-1 citation for "iv therapy" must not beat the LOC slot 2...
        self.assertEqual(self._row(grid, "iv therapy")["you"]["aio"], 2)
        # ...and "mobile iv drip", whose only feature rows are NY, stays empty-handed.
        you = self._row(grid, "mobile iv drip")["you"]
        self.assertIsNone(you["aio"])
        self.assertIsNone(you["feat"])

    def test_features_captured_is_the_latest_feature_date(self):
        self.assertEqual(self._grid()["features_captured"], str(DAY))

    def test_no_feature_rows_means_none_not_zero(self):
        # A fresh project with competitor ranks but no advanced capture yet: every cell
        # reads None and features_captured is None — never an invented 0/slot.
        with get_session() as session:
            session.query(SerpFeatureRanking).delete()
        grid = self._grid()
        self.assertIsNone(grid["features_captured"])
        you = self._row(grid, "iv therapy")["you"]
        self.assertIsNone(you["aio"])
        self.assertIsNone(you["feat"])

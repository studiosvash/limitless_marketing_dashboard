"""Reads must be scoped to ONE project's tracking location.

The write-side fix (a `location` column in the ranking tables' unique key) only separates two
city projects if the read side filters on it too. Without that, `Premierstaff NY` and
`Premierstaff Las Vegas` — distinct `sites` rows that share one `site_url`, because Position
Tracking registers a domain once per city — still render the union of both cities' rankings,
which is what made six projects report an identical visibility %, keyword count and up/down
count in the project list.
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import TestCase, override_settings

from apps.dashboard.services.shared_queries import (
    _get_ranking_distribution, _location_clause,
)
from pipeline.db.schema import KeywordRanking, SavedKeyword, init_db
from pipeline.db.writer import ensure_tables, upsert_keyword_rankings
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session


def _new_analytics_db(test_case):
    """A fresh temp analytics DB per test — the established pattern in test_ai_service.py.

    Required here rather than merely tidy: the analytics DB is process-global, so without it
    each test in a class would inherit the previous one's rows and the saved-keyword inserts
    below would collide on their unique key.
    """
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)


SITE = "premierstaff.com"
NY = "United States - New York, NY"
LV = "United States - Las Vegas, NV"
KW = "event staffing"
DAY = date(2026, 8, 6)


def _seed(rows):
    with get_session() as session:
        ensure_tables(session, KeywordRanking, SavedKeyword)
        upsert_keyword_rankings(session, rows, site_id=SITE)


def _track(keyword=KW, locations=(NY, LV)):
    """Track `keyword` for each project named by `locations`.

    One row per (project, keyword) — the tracked list is per-project, and `location` is what
    identifies the project when several share a domain. Seeding a single "United States" row
    would leave both city projects tracking nothing, which is now (correctly) an empty read.
    """
    with get_session() as session:
        ensure_tables(session, SavedKeyword)
        for loc in locations:
            session.add(SavedKeyword(site_id=SITE, keyword=keyword, location=loc))
        session.commit()


class LocationClauseTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)

    def test_none_means_no_filter(self):
        # A domain-level caller genuinely wants every city's rows.
        self.assertEqual(_location_clause(KeywordRanking, None), [])
        self.assertEqual(_location_clause(KeywordRanking, ""), [])

    def test_a_location_produces_one_equality_term(self):
        self.assertEqual(len(_location_clause(KeywordRanking, NY)), 1)


class RankingRowsAreSeparatedByLocationTests(TestCase):
    """The core regression: one domain, one keyword, one day, two cities."""

    def setUp(self):
        _new_analytics_db(self)
        # Miami tracks the keyword too but was never synced — so the "no rows" test below
        # proves an empty CAPTURE reads empty, not merely an empty tracked list.
        _track(locations=(NY, LV, "United States - Miami, FL"))
        _seed([
            {"date": DAY, "site_id": SITE, "keyword": KW, "location": NY,
             "position": 3, "url": "https://premierstaff.com/event-staffing-agency-nyc/"},
            {"date": DAY, "site_id": SITE, "keyword": KW, "location": LV,
             "position": 27, "url": "https://premierstaff.com/"},
        ])

    def test_both_rows_survive_the_upsert(self):
        # Under the old (date, site_id, keyword) key the second write OVERWROTE the first.
        with get_session() as session:
            rows = session.query(KeywordRanking).filter(
                KeywordRanking.site_id == SITE, KeywordRanking.keyword == KW).all()
        self.assertEqual(sorted(r.location for r in rows), sorted([LV, NY]))
        self.assertEqual({r.location: r.position for r in rows}, {NY: 3, LV: 27})

    def test_re_syncing_one_city_updates_only_that_city(self):
        _seed([{"date": DAY, "site_id": SITE, "keyword": KW, "location": NY, "position": 1,
                "url": "https://premierstaff.com/event-staffing-agency-nyc/"}])
        with get_session() as session:
            rows = session.query(KeywordRanking).filter(
                KeywordRanking.site_id == SITE, KeywordRanking.keyword == KW).all()
        self.assertEqual({r.location: r.position for r in rows}, {NY: 1, LV: 27})

    def test_each_city_reads_back_only_its_own_position(self):
        ny = _get_ranking_distribution(SITE, DAY - timedelta(days=1), DAY, location=NY)
        lv = _get_ranking_distribution(SITE, DAY - timedelta(days=1), DAY, location=LV)
        self.assertEqual(ny["avg_position"], 3)
        self.assertEqual(lv["avg_position"], 27)
        # The whole point: two projects on one domain no longer report the same number.
        self.assertNotEqual(ny["avg_position"], lv["avg_position"])
        self.assertEqual(ny["top3"], 1)
        self.assertEqual(lv["top3"], 0)

    def test_unscoped_read_still_spans_the_domain(self):
        # Domain-level callers (Overview) are unchanged: both cities average to 15.
        both = _get_ranking_distribution(SITE, DAY - timedelta(days=1), DAY)
        self.assertEqual(both["avg_position"], 15)

    def test_a_city_with_no_captured_rows_reads_empty_not_another_citys_data(self):
        miami = _get_ranking_distribution(SITE, DAY - timedelta(days=1), DAY,
                                          location="United States - Miami, FL")
        # Honest empty. Falling back to the domain's other rows would put New York's ranks
        # under Miami's name, which is the bug this whole change removes.
        self.assertEqual(miami["avg_position"], 0)
        self.assertEqual(miami["top3"], 0)


class TrackedKeywordListIsPerProjectTests(TestCase):
    """A newly created project must start EMPTY, even on a domain another project already
    tracks.

    Reported from the running app: a second project was created for premierstaff.com in a new
    market and opened with the first project's keywords already in its grid and rows in its
    Rankings Overview. The rows were stamped correctly all along — `saved_keyword_service`
    writes the project's location and the unique key is (site_id, keyword, location) — but
    `load_tracked_keywords(site_id)` ignored the column and returned the whole domain's list.
    """

    def setUp(self):
        _new_analytics_db(self)
        # The established project tracks three keywords in New York.
        with get_session() as session:
            ensure_tables(session, SavedKeyword)
            for kw in ("event staffing", "brand ambassador agency", "trade show staffing"):
                session.add(SavedKeyword(site_id=SITE, keyword=kw, location=NY))
            session.commit()

    def test_a_brand_new_project_on_the_same_domain_tracks_nothing(self):
        from pipeline.utils.keywords import load_tracked_keywords
        fresh = load_tracked_keywords(SITE, location="United States - New Jersey")
        self.assertEqual(fresh, [])

    def test_the_established_project_still_sees_its_own_list(self):
        from pipeline.utils.keywords import load_tracked_keywords
        self.assertEqual(len(load_tracked_keywords(SITE, location=NY)), 3)

    def test_tracking_one_keyword_gives_the_new_project_only_that_keyword(self):
        from pipeline.utils.keywords import load_tracked_keywords
        with get_session() as session:
            session.add(SavedKeyword(site_id=SITE, keyword="event staffing nj",
                                     location="United States - New Jersey"))
            session.commit()
        self.assertEqual(load_tracked_keywords(SITE, location="United States - New Jersey"),
                         ["event staffing nj"])
        # ...and the established project is untouched by that.
        self.assertEqual(len(load_tracked_keywords(SITE, location=NY)), 3)

    def test_the_same_keyword_can_be_tracked_by_two_projects_independently(self):
        """Sharing a keyword's TEXT is normal — two projects measuring "event staffing" in two
        markets are two rows, not one shared row."""
        from pipeline.utils.keywords import load_tracked_keywords
        with get_session() as session:
            session.add(SavedKeyword(site_id=SITE, keyword="event staffing",
                                     location="United States - New Jersey"))
            session.commit()
        self.assertEqual(load_tracked_keywords(SITE, location="United States - New Jersey"),
                         ["event staffing"])
        self.assertIn("event staffing", load_tracked_keywords(SITE, location=NY))

    def test_an_unscoped_load_still_sees_the_whole_domain(self):
        # Domain-level callers are unchanged; only per-project callers pass a location.
        from pipeline.utils.keywords import load_tracked_keywords
        self.assertEqual(len(load_tracked_keywords(SITE)), 3)

    def test_a_scoped_load_never_falls_back_to_the_legacy_keywords_file(self):
        """The file fallback is domain-agnostic; handing it to a new project would refill the
        empty state this scoping exists to produce."""
        from pipeline.utils.keywords import load_tracked_keywords
        self.assertEqual(
            load_tracked_keywords(SITE, location="United States - Nowhere"), []
        )


class WriterDefaultsLocationTests(TestCase):
    """`location` is part of a NOT NULL unique key: a writer that omits it must land on the
    documented default rather than a NULL that would bypass ON CONFLICT and duplicate."""

    def setUp(self):
        _new_analytics_db(self)

    def test_missing_location_becomes_the_default(self):
        _seed([{"date": DAY, "site_id": SITE, "keyword": "no location given", "position": 5}])
        with get_session() as session:
            row = session.query(KeywordRanking).filter(
                KeywordRanking.keyword == "no location given").one()
        self.assertEqual(row.location, "United States")

    def test_repeat_write_without_location_updates_rather_than_duplicates(self):
        _seed([{"date": DAY, "site_id": SITE, "keyword": "repeat", "position": 5}])
        _seed([{"date": DAY, "site_id": SITE, "keyword": "repeat", "position": 9}])
        with get_session() as session:
            rows = session.query(KeywordRanking).filter(
                KeywordRanking.keyword == "repeat").all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].position, 9)


class KeywordIntelligenceIsLocationScopedTests(TestCase):
    """The Keywords page / Positions rankings measurement query must be location-scoped.

    `get_keyword_intelligence_raw` scoped only its TRACKED LIST by project; the
    `KeywordRanking` measurement query filtered on site + date alone. Two city projects
    sharing a keyword text therefore averaged each other's positions (NY pos 3 + LV pos 27
    → both pages showed 15) and summed each other's clicks — while the Positioning KPI
    block above the same table (which goes through `_get_ranking_distribution`) was
    correctly scoped, so one page contradicted itself.
    """

    def setUp(self):
        _new_analytics_db(self)
        _track(locations=(NY, LV))
        _seed([
            {"date": DAY, "site_id": SITE, "keyword": KW, "location": NY,
             "position": 3, "clicks": 100, "impressions": 1000},
            {"date": DAY, "site_id": SITE, "keyword": KW, "location": LV,
             "position": 27, "clicks": 5, "impressions": 400},
        ])

    def _intel(self, location):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        return get_keyword_intelligence_raw(
            SITE, DAY - timedelta(days=1), DAY,
            DAY - timedelta(days=60), DAY - timedelta(days=31),
            tracked_only=True, location=location,
        )

    def test_each_city_measures_only_its_own_rows(self):
        ny = self._intel(NY)
        lv = self._intel(LV)
        self.assertEqual([k["position"] for k in ny["full_keywords"]], [3])
        self.assertEqual([k["position"] for k in lv["full_keywords"]], [27])

    def test_clicks_are_not_summed_across_sibling_cities(self):
        ny = self._intel(NY)
        self.assertEqual(ny["total_clicks"], 100)

    def test_avg_position_matches_the_citys_own_capture(self):
        self.assertEqual(self._intel(NY)["avg_position"], 3)
        self.assertEqual(self._intel(LV)["avg_position"], 27)

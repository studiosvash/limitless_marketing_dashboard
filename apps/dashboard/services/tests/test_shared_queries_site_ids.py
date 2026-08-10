"""Positioning reads must match every spelling of a site_id (report bug P1).

The join key between the two databases is a string, and four spellings of one site legitimately
exist (skills.md 3): `example.com`, `sc-domain:example.com`, `https://example.com/` and
`https://example.com`. `views.latest_ranking_anchor` -- which decides WHICH DATE WINDOW the
Positioning page renders -- already matches all of them through `resolve_site_ids`, but every
read in `shared_queries` matched `site_id ==` exactly.

So rows written by a connector under an alternate spelling moved the anchor forward while
staying invisible to the queries that fill the page: the Positioning page rendered empty
*because* data existed. These tests pin both halves to the same matcher.
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, KeywordRanking, SavedKeyword, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class SharedQueriesSiteIdSpellingTests(TestCase):
    """The project is registered as `example.com`; the connector wrote rankings under
    `https://example.com/`. Both are the same site."""

    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        db_connection._SessionFactory = None

        self.measured = date.today() - timedelta(days=2)
        with get_session() as session:
            site = Site(site_url="example.com", site_name="Example", slug="example",
                        location="United States", is_active=1)
            session.add(site)
            session.commit()
            self.site_pk = site.id

            session.add(SavedKeyword(
                site_id="example.com", site_pk=self.site_pk, keyword="event staffing",
                location="United States", search_volume=320,
            ))
            # Written under a DIFFERENT spelling of the same site, which is exactly what a
            # connector handed the property URL instead of the canonical site_url produces.
            session.add(KeywordRanking(
                date=self.measured, site_id="https://example.com/", keyword="event staffing",
                position=4, location="United States",
            ))
            session.commit()

    def test_ranking_distribution_sees_rows_stored_under_another_spelling(self):
        from apps.dashboard.services.shared_queries import _get_ranking_distribution

        dist = _get_ranking_distribution(
            "example.com", self.measured - timedelta(days=7), self.measured + timedelta(days=1),
            location="United States", site_pk=self.site_pk,
        )

        # One tracked keyword, measured at position 4 -> it is in the top-10 bucket and the
        # visibility figure is a real number, not None.
        self.assertEqual(dist["total"], 1)
        self.assertEqual(dist["top10"], 1)
        self.assertIsNotNone(dist["visibility"])

    def test_the_anchor_and_the_reads_agree(self):
        """`latest_ranking_anchor` already matched every spelling. When the reads did not, the
        page re-anchored onto a measurement it could then not display."""
        from apps.api.views import latest_ranking_anchor
        from apps.dashboard.services.shared_queries import _get_ranking_distribution

        # The anchor is deliberately `max(date) + 1 day`, so the caller's `anchor - 1`
        # arithmetic lands the window END exactly on the measurement.
        anchor = latest_ranking_anchor("example.com", "United States")
        self.assertEqual(anchor, self.measured + timedelta(days=1))

        dist = _get_ranking_distribution(
            "example.com", anchor - timedelta(days=7), anchor - timedelta(days=1),
            location="United States", site_pk=self.site_pk,
        )
        self.assertEqual(dist["top10"], 1)

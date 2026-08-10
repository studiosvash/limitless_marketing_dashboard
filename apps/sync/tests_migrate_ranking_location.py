"""`manage.py migrate_ranking_location` — moving a project's ranking history to a new market.

WHY THIS COMMAND EXISTS. Every positioning read filters on the project's CURRENT
`sites.location` (`shared_queries._location_clause`), and every ranking row carries the
location it was measured in. So editing a project's location silently makes 100% of its
measured history unreadable: Rankings Overview blanks, the whole tracked list moves into
"Newly Added Keywords — Not Tracked Yet", and the next sync re-buys every keyword from
DataForSEO. The rows are still there, under the old string.

The approved design is isolate-and-warn: the UI warns before the change, and this command is
the deliberate, reviewable way to carry the history across afterwards. It is dry-run by
default, like `normalize_site_urls`.
"""
import tempfile
from datetime import date, timedelta
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from sqlalchemy import select

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import (
    CompetitorKeywordRanking, KeywordRanking, Site, init_db,
)
from pipeline.utils.db_connection import get_session

OLD = "United States - New York"
NEW = "United States - Washington, DC"


class MigrateRankingLocationTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.day = date.today() - timedelta(days=1)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff",
                             slug="staff", location=NEW, is_active=1))
            for kw, pos in (("event staffing", 4), ("brand ambassadors", 17)):
                session.add(KeywordRanking(date=self.day, site_id="premierstaff.com",
                                           keyword=kw, location=OLD, position=pos,
                                           rank_checked_at=self.day))
            session.add(CompetitorKeywordRanking(
                date=self.day, site_id="premierstaff.com", keyword="event staffing",
                competitor_domain="eventstaff.com", location=OLD, position=2))

    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command("migrate_ranking_location", *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    def _locations(self):
        with get_session() as session:
            return sorted(session.execute(
                select(KeywordRanking.keyword, KeywordRanking.location)
            ).all())

    def test_dry_run_writes_nothing(self):
        out = self._run("staff", "--from", OLD, "--to", NEW)
        self.assertIn("Dry run", out)
        self.assertEqual([loc for _kw, loc in self._locations()], [OLD, OLD])

    def test_apply_moves_the_rows(self):
        self._run("staff", "--from", OLD, "--to", NEW, "--apply")
        self.assertEqual([loc for _kw, loc in self._locations()], [NEW, NEW])

    def test_competitor_rows_move_too(self):
        """Half a migration is worse than none: the grid reads both tables on `location`."""
        self._run("staff", "--from", OLD, "--to", NEW, "--apply")
        with get_session() as session:
            locs = session.execute(select(CompetitorKeywordRanking.location)).scalars().all()
        self.assertEqual(locs, [NEW])

    def test_a_colliding_row_is_skipped_and_reported_not_overwritten(self):
        """A row already measured in the NEW market for the same (date, keyword) wins.

        Overwriting it would destroy a real measurement to make room for an older one from a
        different city — the two are different facts about different SERPs.
        """
        with get_session() as session:
            session.add(KeywordRanking(date=self.day, site_id="premierstaff.com",
                                       keyword="event staffing", location=NEW, position=9,
                                       rank_checked_at=self.day))
            session.commit()

        out = self._run("staff", "--from", OLD, "--to", NEW, "--apply")
        self.assertIn("skip", out.lower())
        with get_session() as session:
            rows = session.execute(
                select(KeywordRanking.keyword, KeywordRanking.location, KeywordRanking.position)
                .where(KeywordRanking.keyword == "event staffing")
                .order_by(KeywordRanking.location)
            ).all()
        self.assertEqual(
            sorted((r.location, r.position) for r in rows),
            sorted([(NEW, 9), (OLD, 4)]),
            "the colliding pair must both survive — the new row untouched, the old one left "
            "where it was rather than overwriting it",
        )
        # The non-colliding keyword still moves.
        self.assertIn(("brand ambassadors", NEW), self._locations())

    def test_refuses_when_a_sibling_project_still_uses_the_old_location(self):
        """Two projects on one domain share `site_id`; the rows do not say which is whose.

        Moving them would take the sibling's measurements with them, and the sibling's page
        would blank exactly the way the project being migrated did.
        """
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff NY",
                             slug="staff-ny", location=OLD, is_active=1))
            session.commit()

        with self.assertRaises(CommandError):
            self._run("staff", "--from", OLD, "--to", NEW, "--apply")
        self.assertEqual([loc for _kw, loc in self._locations()], [OLD, OLD])

    def test_unknown_slug_is_an_error(self):
        with self.assertRaises(CommandError):
            self._run("no-such-project", "--from", OLD, "--to", NEW)

    def test_identical_from_and_to_is_an_error(self):
        with self.assertRaises(CommandError):
            self._run("staff", "--from", NEW, "--to", NEW)

    def test_idempotent(self):
        self._run("staff", "--from", OLD, "--to", NEW, "--apply")
        out = self._run("staff", "--from", OLD, "--to", NEW, "--apply")
        self.assertIn("Nothing to do", out)

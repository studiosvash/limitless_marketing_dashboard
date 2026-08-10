"""`project_naming.find_project_name_conflicts` — the soft duplicate-name warning (C3d).

Nothing in this codebase has ever checked `site_name` for uniqueness. That is defensible on
its own: registering one domain as several projects, one per city, is a supported workflow
(`add_site(allow_duplicate=True)`), and those siblings legitimately want related names.

What is not defensible is two projects on one domain carrying the SAME name, because the
project switcher, the workspace header and every export label a project by its name. Two
identically-named rows are indistinguishable in the UI, and the operations that go wrong on a
duplicated domain — a settings save landing on the wrong sibling, a location edit blanking a
page — are exactly the ones the user then cannot attribute to the right project.

A same-(domain, location) pair is worse still: those two projects share `site_id` AND the
location filter, so they read the same `keyword_rankings` rows and will report identical
numbers under two names forever.

Both are WARNINGS. Neither is a block: a user who means it must be able to continue.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from apps.dashboard.services.project_naming import find_project_name_conflicts
from pipeline.db.engine import get_engine
from pipeline.db.schema import Site, init_db
from pipeline.utils.db_connection import get_session


class ProjectNamingTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff NY",
                             slug="staff-ny", location="United States - New York",
                             is_active=1))
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location="United States - Washington, DC",
                             is_active=1))
            session.add(Site(site_url="fusehealth.com", site_name="Premierstaff DC",
                             slug="fuse", location="United States - Washington, DC",
                             is_active=1))

    def test_a_distinct_name_on_the_domain_is_clean(self):
        out = find_project_name_conflicts("premierstaff.com", "Premierstaff Austin",
                                          location="United States - Austin, TX")
        self.assertEqual(out["name"], [])
        self.assertEqual(out["location"], [])
        self.assertEqual(out["warning"], "")

    def test_an_exact_name_match_on_the_same_domain_warns(self):
        out = find_project_name_conflicts("premierstaff.com", "Premierstaff DC",
                                          location="United States - Austin, TX")
        self.assertEqual([c["slug"] for c in out["name"]], ["staff-dc"])
        self.assertIn("Premierstaff DC", out["warning"])

    def test_the_match_is_case_and_whitespace_folded(self):
        out = find_project_name_conflicts("premierstaff.com", "  premierstaff dc  ",
                                          location="United States - Austin, TX")
        self.assertEqual([c["slug"] for c in out["name"]], ["staff-dc"])

    def test_the_same_name_on_a_DIFFERENT_domain_is_not_a_conflict(self):
        """Two clients can both have a 'Main site'. Only siblings on one domain collide."""
        out = find_project_name_conflicts("driphydration.com", "Premierstaff DC",
                                          location="United States - Washington, DC")
        self.assertEqual(out["name"], [])
        self.assertEqual(out["location"], [])

    def test_www_and_bare_are_one_domain(self):
        """`normalize_domain` is the registration rule — skills.md §3."""
        out = find_project_name_conflicts("https://www.premierstaff.com/", "Premierstaff DC",
                                          location="United States - Austin, TX")
        self.assertEqual([c["slug"] for c in out["name"]], ["staff-dc"])

    def test_a_same_domain_same_location_pair_warns_even_with_a_distinct_name(self):
        """Those two projects share site_id AND the location filter — same rows, two names."""
        out = find_project_name_conflicts("premierstaff.com", "Premierstaff Capital",
                                          location="United States - Washington, DC")
        self.assertEqual(out["name"], [])
        self.assertEqual([c["slug"] for c in out["location"]], ["staff-dc"])
        self.assertIn("same rankings", out["warning"].lower())

    def test_a_project_never_conflicts_with_itself(self):
        out = find_project_name_conflicts("premierstaff.com", "Premierstaff DC",
                                          location="United States - Washington, DC",
                                          exclude_site_pk=self._pk("staff-dc"))
        self.assertEqual(out["name"], [])
        self.assertEqual(out["location"], [])

    def test_it_is_a_warning_and_never_a_block(self):
        """The shape carries no 'blocked'/'ok' verdict on purpose — the caller decides."""
        out = find_project_name_conflicts("premierstaff.com", "Premierstaff DC")
        self.assertEqual(sorted(out.keys()), ["location", "name", "warning"])

    def test_a_blank_name_asks_nothing(self):
        out = find_project_name_conflicts("premierstaff.com", "   ")
        self.assertEqual(out["name"], [])

    def test_a_database_failure_degrades_to_no_warning(self):
        """A service function catches, logs and returns a safe shape — skills.md rule 6.

        A naming hint must never be the reason a save cannot proceed.
        """
        db_connection._SessionFactory = None
        with override_settings(ANALYTICS_DB_PATH="/nonexistent/dir/nope.db"):
            out = find_project_name_conflicts("premierstaff.com", "Premierstaff DC")
        self.assertEqual(out, {"name": [], "location": [], "warning": ""})

    def _pk(self, slug):
        from sqlalchemy import select
        with get_session() as session:
            return session.execute(select(Site.id).where(Site.slug == slug)).scalar()

"""The tracked-keyword list belongs to ONE PROJECT, identified by `saved_keywords.site_pk`.

Position Tracking registers one domain as several projects (`add_site(allow_duplicate=True)`),
and every one of them carries the same `site_url`. Until `site_pk` existed the list was read by
`site_id` alone, so a brand-new project opened with every sibling's keywords already in it —
28 of them in Positioning's "Newly Added Keywords — Not Tracked Yet" card, on a project whose
user had added none.

`location` was the first discriminator tried and could not be one: two projects on a domain may
track the same market, and the wizard defaults every project to "United States". Every test
below therefore gives its two projects the SAME location — the case that has to work.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.schema import (
    SavedKeyword, Site, UNOWNED_SITE_PK, ensure_saved_keyword_project, init_db,
)
from pipeline.services.saved_keyword_service import (
    clear_saved_keywords, delete_saved_keyword, list_saved_keywords, save_keywords,
)
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session
from pipeline.utils.keywords import load_tracked_keywords

SITE = "premierstaff.com"
LOC = "United States"          # deliberately identical for both projects


def _new_analytics_db(test_case):
    """A fresh temp analytics DB per test — the analytics DB is process-global."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)


def _two_projects_on_one_domain() -> tuple[int, int]:
    """Two `sites` rows, same domain, same location. Returns (older_pk, newer_pk)."""
    with get_session() as session:
        older = Site(site_url=SITE, site_name="Premierstaff", slug="premierstaff",
                     location=LOC, is_active=1)
        newer = Site(site_url=SITE, site_name="Premierstaff DC", slug="staff-dc",
                     location=LOC, is_active=1)
        session.add_all([older, newer])
        session.commit()
        return older.id, newer.id


class ProjectScopedTrackedListTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)
        self.older, self.newer = _two_projects_on_one_domain()
        save_keywords(SITE, [{"keyword": "event staffing", "search_volume": 6600},
                             {"keyword": "usher staff"}],
                      location=LOC, site_pk=self.older)

    def test_a_new_project_on_an_existing_domain_starts_empty(self):
        """The reported bug. The sibling's two keywords must not appear here."""
        self.assertEqual(list_saved_keywords(SITE, site_pk=self.newer), [])
        self.assertEqual(load_tracked_keywords(SITE, location=LOC, site_pk=self.newer), [])

    def test_each_project_sees_only_its_own(self):
        save_keywords(SITE, [{"keyword": "brand ambassador agency"}],
                      location=LOC, site_pk=self.newer)

        self.assertEqual(sorted(k["keyword"] for k in list_saved_keywords(SITE, site_pk=self.older)),
                         ["event staffing", "usher staff"])
        self.assertEqual([k["keyword"] for k in list_saved_keywords(SITE, site_pk=self.newer)],
                         ["brand ambassador agency"])

    def test_two_projects_can_track_the_same_keyword_in_the_same_market(self):
        """Impossible under the old (site_id, keyword, location) key — the second project's
        save silently UPDATED the first project's row instead of creating its own."""
        save_keywords(SITE, [{"keyword": "event staffing", "search_volume": 1200}],
                      location=LOC, site_pk=self.newer)

        newer_rows = list_saved_keywords(SITE, site_pk=self.newer)
        older_rows = list_saved_keywords(SITE, site_pk=self.older)
        self.assertEqual([r["keyword"] for r in newer_rows], ["event staffing"])
        self.assertEqual(newer_rows[0]["search_volume"], 1200)
        # The sibling keeps its own copy, with its own metrics.
        self.assertEqual(len(older_rows), 2)
        self.assertEqual(next(r for r in older_rows if r["keyword"] == "event staffing")
                         ["search_volume"], 6600)

    def test_resaving_updates_in_place_for_the_same_project(self):
        save_keywords(SITE, [{"keyword": "event staffing", "search_volume": 9900}],
                      location=LOC, site_pk=self.older)
        rows = list_saved_keywords(SITE, site_pk=self.older)
        self.assertEqual(len(rows), 2)
        self.assertEqual(next(r for r in rows if r["keyword"] == "event staffing")
                         ["search_volume"], 9900)

    def test_rows_under_another_spelling_of_the_domain_stay_visible(self):
        """`site_pk` is scoped on ALONE, never ANDed with `site_id`: one site is stored under
        several spellings, and ANDing hid the rows filed under the others."""
        with get_session() as session:
            session.add(SavedKeyword(site_id="https://premierstaff.com/", site_pk=self.older,
                                     keyword="festival staffing", location=LOC))
            session.commit()

        self.assertIn("festival staffing",
                      [k["keyword"] for k in list_saved_keywords(SITE, site_pk=self.older)])
        self.assertEqual(list_saved_keywords(SITE, site_pk=self.newer), [])

    def test_bulk_replace_does_not_wipe_a_sibling(self):
        """`clear_saved_keywords` used to be a raw delete-by-site_id in the PUT handler, so one
        project saving its own list destroyed every sibling's."""
        save_keywords(SITE, [{"keyword": "crowd management"}], location=LOC, site_pk=self.newer)

        self.assertEqual(clear_saved_keywords(SITE, site_pk=self.newer), 1)
        self.assertEqual(list_saved_keywords(SITE, site_pk=self.newer), [])
        self.assertEqual(len(list_saved_keywords(SITE, site_pk=self.older)), 2)

    def test_a_domain_wide_clear_is_refused(self):
        self.assertEqual(clear_saved_keywords(SITE), 0)
        self.assertEqual(len(list_saved_keywords(SITE, site_pk=self.older)), 2)

    def test_delete_ignores_a_stale_location(self):
        """A project whose tracking location was edited still holds rows under the old one;
        matching on `location` made those keywords undeletable from the UI."""
        self.assertTrue(delete_saved_keyword(SITE, "usher staff", "Las Vegas, NV",
                                             site_pk=self.older))
        self.assertEqual([k["keyword"] for k in list_saved_keywords(SITE, site_pk=self.older)],
                         ["event staffing"])

    def test_unscoped_read_still_spans_the_domain(self):
        """`site_pk=None` is a real answer for a caller with no project (a maintenance
        command), not a bug — it must keep returning the whole domain."""
        save_keywords(SITE, [{"keyword": "crowd management"}], location=LOC, site_pk=self.newer)
        self.assertEqual(len(list_saved_keywords(SITE)), 3)


class SavedKeywordMigrationTests(TestCase):
    """`ensure_saved_keyword_project` has to work on a database written before `site_pk`."""

    def setUp(self):
        _new_analytics_db(self)
        self.older, self.newer = _two_projects_on_one_domain()

    def _legacy_row(self, keyword, site_id=SITE, location=LOC):
        """A row as the old code wrote it: no owning project."""
        with get_session() as session:
            session.add(SavedKeyword(site_id=site_id, keyword=keyword, location=location,
                                     site_pk=UNOWNED_SITE_PK))
            session.commit()

    def test_legacy_rows_are_adopted_by_the_oldest_project_on_the_domain(self):
        self._legacy_row("event staffing")

        with get_session() as session:
            ensure_saved_keyword_project(session)
            session.commit()

        self.assertEqual([k["keyword"] for k in list_saved_keywords(SITE, site_pk=self.older)],
                         ["event staffing"])
        self.assertEqual(list_saved_keywords(SITE, site_pk=self.newer), [])

    def test_a_location_match_beats_the_oldest_project(self):
        """When the previous location-based scheme had actually separated two projects, that
        separation is preserved rather than collapsed onto the oldest one."""
        with get_session() as session:
            session.get(Site, self.newer).location = "United States - Washington, DC"
            session.commit()
        self._legacy_row("staffing dc", location="United States - Washington, DC")

        with get_session() as session:
            ensure_saved_keyword_project(session)
            session.commit()

        self.assertEqual([k["keyword"] for k in list_saved_keywords(SITE, site_pk=self.newer)],
                         ["staffing dc"])
        self.assertEqual(list_saved_keywords(SITE, site_pk=self.older), [])

    def test_a_row_whose_domain_has_no_project_is_left_unowned(self):
        """Not adopted by a guess: re-keying a site_id is normalize_site_urls' job, and
        inventing an owner here could hand one site's keywords to another."""
        self._legacy_row("orphan kw", site_id="eventstaff.com")

        with get_session() as session:
            ensure_saved_keyword_project(session)
            session.commit()
            row = session.query(SavedKeyword).filter_by(keyword="orphan kw").one()
            self.assertEqual(row.site_pk, UNOWNED_SITE_PK)

        self.assertEqual(list_saved_keywords(SITE, site_pk=self.older), [])
        self.assertEqual(list_saved_keywords(SITE, site_pk=self.newer), [])

    def test_migration_is_idempotent(self):
        self._legacy_row("event staffing")
        with get_session() as session:
            self.assertTrue(ensure_saved_keyword_project(session))
            session.commit()
        with get_session() as session:
            self.assertFalse(ensure_saved_keyword_project(session))


class PositionsResponseScopingTests(TestCase):
    """End-to-end on the payload the screenshot came from: `rankings` rows tagged
    `source: "new"` are exactly the "Newly Added Keywords — Not Tracked Yet" card."""

    def setUp(self):
        _new_analytics_db(self)
        self.older, self.newer = _two_projects_on_one_domain()
        save_keywords(SITE, [{"keyword": "office cleaning contractors", "search_volume": 6600},
                             {"keyword": "stadium staffing"}],
                      location=LOC, site_pk=self.older)

    def _new_rows(self, site_pk):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response(SITE, date(2026, 7, 1), date(2026, 8, 1),
                                        date(2026, 6, 1), date(2026, 6, 30),
                                        location=LOC, site_pk=site_pk)
        return [r["kw"] for r in body["rankings"] if r.get("source") == "new"]

    def test_the_new_project_card_is_empty(self):
        self.assertEqual(self._new_rows(self.newer), [])

    def test_the_owning_project_still_sees_its_own(self):
        self.assertEqual(sorted(self._new_rows(self.older)),
                         ["office cleaning contractors", "stadium staffing"])

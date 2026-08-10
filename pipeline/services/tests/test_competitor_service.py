"""Project scoping for tracked_competitors (report bug C3a, second half).

One domain can be registered as several projects (`add_site(allow_duplicate=True)`), and
`tracked_competitors` used to be keyed on `site_id` alone — so one project's competitor edit
replaced every sibling's list, and reads couldn't tell whose override they were returning.
These tests pin the per-project contract: `site_pk` scopes alone when given; rows written
before the column existed are backfilled to the oldest project on the domain.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class TrackedCompetitorProjectScopeTests(TestCase):
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

        with get_session() as session:
            a = Site(site_url="dup.com", site_name="Dup A", slug="dup", is_active=1)
            b = Site(site_url="dup.com", site_name="Dup B", slug="dup-2", is_active=1)
            session.add_all([a, b])
            session.commit()
            self.pk_a, self.pk_b = a.id, b.id

    def test_siblings_keep_independent_competitor_sets(self):
        from pipeline.services.competitor_service import (
            get_tracked_competitors, set_tracked_competitors,
        )
        set_tracked_competitors("dup.com", ["comp-a.com"], site_pk=self.pk_a)
        set_tracked_competitors("dup.com", ["comp-b.com"], site_pk=self.pk_b)

        self.assertEqual(get_tracked_competitors("dup.com", site_pk=self.pk_a), ["comp-a.com"])
        self.assertEqual(get_tracked_competitors("dup.com", site_pk=self.pk_b), ["comp-b.com"])

    def test_setting_one_sibling_does_not_clear_the_other(self):
        from pipeline.services.competitor_service import (
            get_tracked_competitors, set_tracked_competitors,
        )
        set_tracked_competitors("dup.com", ["comp-a.com"], site_pk=self.pk_a)
        # B clears its own (empty) override — A's must survive.
        set_tracked_competitors("dup.com", [], site_pk=self.pk_b)
        self.assertEqual(get_tracked_competitors("dup.com", site_pk=self.pk_a), ["comp-a.com"])

    def test_is_overridden_is_per_project(self):
        from pipeline.services.competitor_service import is_overridden, set_tracked_competitors
        set_tracked_competitors("dup.com", ["comp-a.com"], site_pk=self.pk_a)
        self.assertTrue(is_overridden("dup.com", site_pk=self.pk_a))
        self.assertFalse(is_overridden("dup.com", site_pk=self.pk_b))

    def test_legacy_rows_backfill_to_the_oldest_project(self):
        """A row written before site_pk existed (UNOWNED) belongs to the oldest project on the
        domain — the project that existed when it was written — and must stay readable both
        with that pk and via the pk-less fallback path."""
        from sqlalchemy import text

        from pipeline.db.schema import ensure_tracked_competitor_project
        from pipeline.services.competitor_service import get_tracked_competitors

        with get_session() as session:
            # Simulate the pre-migration state: a bare (site_id, domain) row, no site_pk value.
            session.execute(text(
                "INSERT INTO tracked_competitors (site_id, competitor_domain, site_pk) "
                "VALUES ('dup.com', 'legacy-comp.com', 0)"
            ))
            session.commit()

        with get_session() as session:
            ensure_tracked_competitor_project(session)
            session.commit()

        self.assertEqual(get_tracked_competitors("dup.com", site_pk=self.pk_a),
                         ["legacy-comp.com"])
        self.assertEqual(get_tracked_competitors("dup.com", site_pk=self.pk_b), [])
        # pk-less caller (maintenance path) still sees the domain's rows.
        self.assertEqual(get_tracked_competitors("dup.com"), ["legacy-comp.com"])

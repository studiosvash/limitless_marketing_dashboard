"""keyword_opportunities belongs to a PROJECT, not a domain (report bug P2).

`persist_keyword_opportunities` scoped its stale-row DELETE on `site_id` alone, and it runs on
every `GET /positions`. Two projects on one domain (`add_site(allow_duplicate=True)`) therefore
deleted each other's rows on every page render: project B opening its Positioning page wiped
every opportunity row of project A whose keyword B does not track, and A's next render did the
same back. A destructive cross-project write, triggered by a read.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from sqlalchemy import select

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, KeywordOpportunity, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


def _opportunity(keyword, score=50.0):
    return {"keyword": keyword, "position": 12, "volume": 100, "kd": 30.0, "cpc": 1.0,
            "score": score, "type": "striking_distance", "estimated_traffic_gain": 5.0,
            "rationale": "test row"}


class KeywordOpportunityProjectScopeTests(TestCase):
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

    def _keywords_for(self, site_pk):
        with get_session() as session:
            return sorted(session.execute(
                select(KeywordOpportunity.keyword)
                .where(KeywordOpportunity.site_pk == site_pk)
            ).scalars().all())

    def test_one_project_persisting_does_not_delete_its_siblings_rows(self):
        from apps.dashboard.services.positioning_service import persist_keyword_opportunities

        persist_keyword_opportunities("dup.com", [_opportunity("alpha"), _opportunity("beta")],
                                      site_pk=self.pk_a)
        persist_keyword_opportunities("dup.com", [_opportunity("gamma")], site_pk=self.pk_b)

        self.assertEqual(self._keywords_for(self.pk_a), ["alpha", "beta"])
        self.assertEqual(self._keywords_for(self.pk_b), ["gamma"])

    def test_the_same_keyword_can_be_scored_by_two_projects(self):
        """The old unique key was (site_id, keyword), so the second project's upsert silently
        OVERWROTE the first's score for a shared keyword instead of storing its own."""
        from apps.dashboard.services.positioning_service import persist_keyword_opportunities

        persist_keyword_opportunities("dup.com", [_opportunity("shared", score=90.0)],
                                      site_pk=self.pk_a)
        persist_keyword_opportunities("dup.com", [_opportunity("shared", score=10.0)],
                                      site_pk=self.pk_b)

        with get_session() as session:
            rows = session.execute(
                select(KeywordOpportunity.site_pk, KeywordOpportunity.opportunity_score)
                .where(KeywordOpportunity.keyword == "shared")
            ).all()
        by_pk = {r[0]: r[1] for r in rows}
        self.assertEqual(by_pk[self.pk_a], 90.0)
        self.assertEqual(by_pk[self.pk_b], 10.0)

    def test_a_projects_own_stale_rows_are_still_dropped(self):
        """The snapshot behaviour must survive the scoping fix: a keyword that no longer scores
        for THIS project goes away, so the table stays a current answer and not a log."""
        from apps.dashboard.services.positioning_service import persist_keyword_opportunities

        persist_keyword_opportunities("dup.com", [_opportunity("alpha"), _opportunity("beta")],
                                      site_pk=self.pk_a)
        persist_keyword_opportunities("dup.com", [_opportunity("alpha")], site_pk=self.pk_a)

        self.assertEqual(self._keywords_for(self.pk_a), ["alpha"])

"""A stored answer must never be a trap you cannot get out of.

Reported: analysing a blog post "does not run" and shows nothing, while the data is in the
database. Both halves were true, and together they were a bug I introduced with the store:

  * the page had been analysed once BEFORE the trailing-slash fix, so what got stored was the
    empty answer that bug produced;
  * `runDomainOverview` never sent `refresh`, so Analyze read that stored empty answer forever
    and there was no way, from the UI, to ask for a new one.

A cache you cannot bust is worse than no cache: it turns one bad lookup into a permanent
wrong answer. Every stored block is now re-fetchable, and a block served from the store says
so, so "nothing happened" reads as "this is the saved answer" instead.
"""
import tempfile
from pathlib import Path
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from apps.dashboard.services import domain_overview_service as svc
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db

EMPTY = {"status": "ok", "metrics": {}, "keywords": [], "cost": 0.015}
FULL = {"status": "ok", "metrics": {"ranked_keywords": 46},
        "keywords": [{"keyword": "wedding bartender cost per hour", "position": 2}],
        "cost": 0.015}


class ReanalyzeTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None
        cache.clear()
        self.addCleanup(cache.clear)

    def _conn(self):
        return mock.patch(
            "pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector")

    def test_a_stored_empty_answer_can_be_replaced_by_re_analysing(self):
        """The reported case, end to end: an empty answer stored by the slash bug, then the
        fix, then a Re-analyze press that must actually reach DataForSEO."""
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = EMPTY
            first = svc.fetch_keywords_block("premierstaff.com/blog/x", "United States")
        self.assertEqual(first["keywords"], [])

        cache.clear()
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = FULL
            again = svc.fetch_keywords_block("premierstaff.com/blog/x", "United States",
                                             refresh=True)
            c.return_value.get_domain_overview.assert_called_once()
        self.assertEqual(len(again["keywords"]), 1)

        # And the replacement is what is stored from then on.
        cache.clear()
        with self._conn() as c:
            stored = svc.fetch_keywords_block("premierstaff.com/blog/x", "United States")
            c.return_value.get_domain_overview.assert_not_called()
        self.assertEqual(stored["metrics"]["ranked_keywords"], 46)

    def test_a_served_block_says_it_came_from_the_store(self):
        """Without this the UI cannot explain why pressing Analyze appears to do nothing."""
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = FULL
            svc.fetch_keywords_block("premierstaff.com", "United States")
        cache.clear()
        with self._conn():
            served = svc.fetch_keywords_block("premierstaff.com", "United States")
        self.assertTrue(served["fromStore"])
        self.assertIsNotNone(served["storedAt"])
        self.assertIsNotNone(served["ageDays"])

    def test_a_freshly_fetched_block_is_not_marked_as_stored(self):
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = FULL
            fresh = svc.fetch_keywords_block("premierstaff.com", "United States")
        self.assertFalse(fresh.get("fromStore"))

    def test_run_domain_overview_passes_refresh_to_the_keywords_block(self):
        with mock.patch.object(svc, "fetch_keywords_block",
                               return_value={"status": "ok"}) as kw, \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **k: r), \
             mock.patch.object(svc, "recent_lookups", return_value=[]):
            svc.run_domain_overview("premierstaff.com", refresh=True)
        self.assertTrue(kw.call_args.kwargs["refresh"])

    def test_the_endpoint_forwards_the_refresh_flag(self):
        """Exercised through a real request rather than by inspecting the function: the point
        is that a body the SPA can send reaches the service, and only a request proves that."""
        from django.contrib.auth import get_user_model
        from rest_framework.authtoken.models import Token
        from rest_framework.test import APIClient

        user = get_user_model().objects.create_user("reanalyze-tester", password="x")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {Token.objects.get(user=user).key}")

        with mock.patch.object(svc, "run_domain_overview", return_value={"status": "ok"}) as run:
            client.post("/api/domain-overview",
                        {"target": "premierstaff.com", "refresh": True}, format="json")

        self.assertTrue(run.call_args.kwargs["refresh"])

"""An empty answer is not worth keeping, and must never block a better one.

Reported: after the trailing-slash fix shipped, the same blog post STILL showed
"0 keywords · No organic keywords returned for this target".

The slash retry was never reached. The earlier, pre-fix lookup had returned nothing, that
nothing was persisted, and the read order — store, then cache, then network — served it back
for good. A stored "we found nothing" is the one answer that should never be sticky: it costs
nothing to re-derive, and it is exactly the answer most likely to be wrong, whether because a
bug produced it, because DataForSEO had not indexed the page yet, or because the target was a
slash away from the right one.

So an empty result is returned to the caller and NOT stored. The next Analyze asks again.
"""
import tempfile
from pathlib import Path
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from apps.dashboard.services import domain_overview_service as svc
from apps.dashboard.services.domain_lookup_store import load_block
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db

EMPTY = {"status": "ok", "metrics": {}, "keywords": [], "cost": 0.015}
FULL = {"status": "ok", "metrics": {"ranked_keywords": 46},
        "keywords": [{"keyword": "wedding bartender cost per hour", "position": 2}],
        "cost": 0.015}


class EmptyResultTests(TestCase):
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

    def test_an_empty_answer_is_not_persisted(self):
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = EMPTY
            svc.fetch_keywords_block("premierstaff.com/blog/x", "United States")
        self.assertIsNone(load_block("premierstaff.com/blog/x", "keywords",
                                     location="United States"),
                          "an empty answer must not be kept and served back")

    def test_a_later_lookup_can_still_find_what_the_empty_one_missed(self):
        """The reported case: the pre-fix empty result must not outlive the fix."""
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = EMPTY
            first = svc.fetch_keywords_block("premierstaff.com/blog/x", "United States")
        self.assertEqual(first["keywords"], [])

        cache.clear()
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = FULL
            second = svc.fetch_keywords_block("premierstaff.com/blog/x", "United States")
            c.return_value.get_domain_overview.assert_called_once()
        self.assertEqual(len(second["keywords"]), 1)

    def test_a_real_answer_is_still_persisted(self):
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = FULL
            svc.fetch_keywords_block("premierstaff.com/blog/x", "United States")
        stored = load_block("premierstaff.com/blog/x", "keywords", location="United States")
        self.assertIsNotNone(stored)
        self.assertEqual(len(stored["keywords"]), 1)

    def test_an_empty_questions_answer_is_not_persisted_either(self):
        """Same reasoning: nothing to serve, and the domain may simply not be indexed yet."""
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value={"status": "ok", "rows": [], "total": 0, "cost": 0.2,
                                      "domain": "premierstaff.com", "platforms": ["chat_gpt"],
                                      "partial": None}):
            svc.fetch_questions_block("premierstaff.com")
        self.assertIsNone(load_block("premierstaff.com", "questions:chat_gpt"))

    def test_refresh_re_buys_even_when_a_real_answer_is_stored(self):
        with self._conn() as c:
            c.return_value.get_domain_overview.return_value = FULL
            svc.fetch_keywords_block("premierstaff.com", "United States")

            c.return_value.get_domain_overview.return_value = {
                **FULL, "metrics": {"ranked_keywords": 99}}
            fresh = svc.fetch_keywords_block("premierstaff.com", "United States", refresh=True)
        self.assertEqual(fresh["metrics"]["ranked_keywords"], 99)

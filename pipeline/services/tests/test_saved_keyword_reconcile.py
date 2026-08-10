"""Name-keyed reconcile for the tracked-keyword bulk save (report bug C3c).

`PUT /api/projects/<slug>/keywords` used to clear the project's whole list and rewrite it from
the request body. The Edit Project modal sends only keyword NAMES -- it fills every metric with
`{volume: 0, kd: null, cpc: null, intent: 'Informational'}` because it has no metrics to send --
so every "Save Settings" press overwrote each tracked keyword's real search volume with a
fabricated 0 and wiped its difficulty, CPC and intent. The zero was worse than a null: it reads
as a known measurement, and `_volume_coverage` counts only nulls, so the response then reported
full volume coverage over invented data.

The reconcile inserts what is missing and deletes what was removed, and NEVER touches a
surviving row -- so a save that changes nothing is a no-op, and a save from a caller with no
metrics cannot destroy metrics a sync paid for.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class ReconcileSavedKeywordsTests(TestCase):
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
            site = Site(site_url="example.com", site_name="Example", slug="example",
                        location="United States", is_active=1)
            session.add(site)
            session.commit()
            self.site_pk = site.id

        from pipeline.services.saved_keyword_service import save_keywords
        save_keywords("example.com", [
            {"keyword": "festival staffing", "search_volume": 480,
             "keyword_difficulty": 42.0, "cpc": 3.25, "intent": "Commercial"},
            {"keyword": "event staff hire", "search_volume": 210,
             "keyword_difficulty": 31.0, "cpc": 2.10, "intent": "Transactional"},
        ], "United States", site_pk=self.site_pk)

    def _stored(self):
        from pipeline.services.saved_keyword_service import list_saved_keywords
        return {r["keyword"]: r for r in list_saved_keywords("example.com", site_pk=self.site_pk)}

    def test_surviving_keywords_keep_their_metrics(self):
        """The Edit-modal shape: names only, no metrics. Nothing stored may be overwritten."""
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        result = reconcile_saved_keywords(
            "example.com",
            [{"keyword": "festival staffing"}, {"keyword": "event staff hire"}],
            "United States", site_pk=self.site_pk,
        )

        rows = self._stored()
        self.assertEqual(rows["festival staffing"]["search_volume"], 480)
        self.assertEqual(rows["festival staffing"]["keyword_difficulty"], 42.0)
        self.assertEqual(rows["festival staffing"]["cpc"], 3.25)
        self.assertEqual(rows["festival staffing"]["intent"], "Commercial")
        self.assertEqual(result, {"added": 0, "removed": 0, "kept": 2})

    def test_a_new_keyword_is_added_with_unknown_not_zero_volume(self):
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        result = reconcile_saved_keywords(
            "example.com",
            [{"keyword": "festival staffing"}, {"keyword": "event staff hire"},
             {"keyword": "brand ambassador agency"}],
            "United States", site_pk=self.site_pk,
        )

        rows = self._stored()
        self.assertIn("brand ambassador agency", rows)
        # Unknown, not a confident zero -- zero and unknown are different facts.
        self.assertIsNone(rows["brand ambassador agency"]["search_volume"])
        self.assertEqual(result["added"], 1)
        self.assertEqual(result["kept"], 2)

    def test_an_omitted_keyword_is_removed(self):
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        result = reconcile_saved_keywords(
            "example.com", [{"keyword": "festival staffing"}],
            "United States", site_pk=self.site_pk,
        )

        rows = self._stored()
        self.assertNotIn("event staff hire", rows)
        self.assertIn("festival staffing", rows)
        self.assertEqual(result["removed"], 1)

    def test_case_and_whitespace_variants_are_the_same_keyword(self):
        """A cosmetic edit must not become delete-and-reinsert -- that would drop the metrics
        by the back door, which is the very thing this function exists to prevent."""
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        result = reconcile_saved_keywords(
            "example.com",
            [{"keyword": "  Festival Staffing "}, {"keyword": "event staff hire"}],
            "United States", site_pk=self.site_pk,
        )

        rows = self._stored()
        self.assertEqual(result, {"added": 0, "removed": 0, "kept": 2})
        self.assertEqual(rows["festival staffing"]["search_volume"], 480)

    def test_is_idempotent(self):
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        payload = [{"keyword": "festival staffing"}, {"keyword": "new keyword"}]
        first = reconcile_saved_keywords("example.com", payload, "United States",
                                         site_pk=self.site_pk)
        second = reconcile_saved_keywords("example.com", payload, "United States",
                                          site_pk=self.site_pk)

        self.assertEqual(first["added"], 1)
        self.assertEqual(second, {"added": 0, "removed": 0, "kept": 2})

    def test_a_new_keyword_carrying_real_metrics_stores_them(self):
        """The Keyword Explorer's send-to-project flow DOES have metrics, and they must land."""
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        reconcile_saved_keywords(
            "example.com",
            [{"keyword": "festival staffing"}, {"keyword": "event staff hire"},
             {"keyword": "crowd management", "search_volume": 90,
              "keyword_difficulty": 12.0, "cpc": 1.4, "intent": "Informational"}],
            "United States", site_pk=self.site_pk,
        )

        rows = self._stored()
        self.assertEqual(rows["crowd management"]["search_volume"], 90)
        self.assertEqual(rows["crowd management"]["intent"], "Informational")

    def test_duplicate_names_in_one_payload_collapse(self):
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        result = reconcile_saved_keywords(
            "example.com",
            [{"keyword": "festival staffing"}, {"keyword": "festival staffing"},
             {"keyword": "event staff hire"}],
            "United States", site_pk=self.site_pk,
        )
        self.assertEqual(result, {"added": 0, "removed": 0, "kept": 2})

    def test_an_empty_payload_clears_the_list(self):
        """Legal (the modal confirms first), and it must report what it removed."""
        from pipeline.services.saved_keyword_service import reconcile_saved_keywords

        result = reconcile_saved_keywords("example.com", [], "United States",
                                          site_pk=self.site_pk)
        self.assertEqual(result["removed"], 2)
        self.assertEqual(self._stored(), {})

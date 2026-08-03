import unittest

from sqlalchemy import inspect

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db


def _cols(insp, table):
    return {c["name"] for c in insp.get_columns(table)}


def _unique_col_sets(insp, table):
    return [set(uc["column_names"]) for uc in insp.get_unique_constraints(table)]


class KeptSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = get_engine(":memory:")
        init_db(cls.engine)
        cls.insp = inspect(cls.engine)
        cls.tables = set(cls.insp.get_table_names())

    def test_core_tables_present(self):
        for t in [
            "sites", "seo_daily", "keyword_rankings", "pages", "ad_metrics_daily",
            "backlinks", "competitor_visibility", "competitor_domains",
            "technical_issues", "page_speed", "indexing_status", "seo_aggregates",
            "ai_summaries", "anomalies", "comparative_metrics",
        ]:
            self.assertIn(t, self.tables, f"missing table {t}")

    def test_rehomed_tables_dropped(self):
        for t in ["users", "sync_log", "refresh_jobs", "insights"]:
            self.assertNotIn(t, self.tables, f"{t} should be re-homed to Django, not in analytics DB")

    def test_data_source_columns_removed(self):
        for t in ["seo_daily", "keyword_rankings", "ad_metrics_daily", "page_speed", "indexing_status"]:
            self.assertNotIn("data_source", _cols(self.insp, t), f"{t} still has data_source")

    def test_site_id_added_to_anomalies_and_comparative(self):
        self.assertIn("site_id", _cols(self.insp, "anomalies"))
        self.assertIn("site_id", _cols(self.insp, "comparative_metrics"))

    def test_technical_issues_has_upsert_key(self):
        self.assertIn(
            {"site_id", "url", "issue_type"},
            _unique_col_sets(self.insp, "technical_issues"),
        )


class PredictionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = get_engine(":memory:")
        init_db(cls.engine)
        cls.insp = inspect(cls.engine)
        cls.tables = set(cls.insp.get_table_names())

    def test_prediction_tables_present(self):
        """keyword_opportunities is the one prediction-layer table something actually
        writes (positioning_service). metric_forecasts and risk_signals were removed
        2026-08-03: months in the schema with no writer, no reader and no UI. If they
        come back, they come back WITH the service that fills them — at which point this
        list grows again."""
        self.assertIn("keyword_opportunities", self.tables)

    def test_phantom_prediction_tables_stay_gone(self):
        """Guards the removal: re-adding the bare schema without a writer regresses the
        2026-08-03 surfacing audit (phantom entities cost review time and invite code
        that reads tables nothing fills)."""
        self.assertNotIn("metric_forecasts", self.tables)
        self.assertNotIn("risk_signals", self.tables)

    def test_keyword_opportunity_unique_key(self):
        keys = [set(uc["column_names"]) for uc in self.insp.get_unique_constraints("keyword_opportunities")]
        self.assertIn({"site_id", "keyword"}, keys)


if __name__ == "__main__":
    unittest.main()

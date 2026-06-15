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
        for t in ["metric_forecasts", "keyword_opportunities", "risk_signals"]:
            self.assertIn(t, self.tables, f"missing prediction table {t}")

    def test_metric_forecast_has_accuracy_columns(self):
        cols = {c["name"] for c in self.insp.get_columns("metric_forecasts")}
        self.assertTrue({"predicted_value", "lower_bound", "upper_bound",
                         "actual_value", "error_pct"} <= cols)

    def test_metric_forecast_unique_key(self):
        keys = [set(uc["column_names"]) for uc in self.insp.get_unique_constraints("metric_forecasts")]
        self.assertIn(
            {"site_id", "metric_type", "period_type", "target_date", "model_name"}, keys
        )

    def test_keyword_opportunity_unique_key(self):
        keys = [set(uc["column_names"]) for uc in self.insp.get_unique_constraints("keyword_opportunities")]
        self.assertIn({"site_id", "keyword"}, keys)


if __name__ == "__main__":
    unittest.main()

import tempfile
from datetime import date, datetime
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class AlertsRawQueryTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add_all([
                Anomaly(date=date(2026, 6, 28), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_clicks", actual_value=50, baseline_value=100,
                        deviation_pct=-50.0, severity="high",
                        description="Clicks dropped 50%.", is_acknowledged=0),
                Anomaly(date=date(2026, 6, 20), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_impressions", actual_value=900, baseline_value=800,
                        deviation_pct=12.5, severity="info",
                        description="Impressions up 12.5%.", is_acknowledged=1),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                               issue_type="not_found_404", severity="high",
                               description="404 detected"),
            ])

    def test_query_alert_anomalies_raw_returns_all_including_acknowledged(self):
        from apps.dashboard.services.alerts_service import query_alert_anomalies_raw
        rows = query_alert_anomalies_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 2)
        acked = [r for r in rows if r["is_acknowledged"]]
        self.assertEqual(len(acked), 1)

    def test_query_alert_technical_issues_raw_returns_all(self):
        from apps.dashboard.services.alerts_service import query_alert_technical_issues_raw
        rows = query_alert_technical_issues_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["issue_type"], "not_found_404")

    def test_query_alert_anomalies_raw_returns_empty_list_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import alerts_service
        with mock.patch.object(alerts_service, "get_session", side_effect=RuntimeError("boom")):
            self.assertEqual(alerts_service.query_alert_anomalies_raw("x"), [])


class BuildAlertsResponseTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add_all([
                Anomaly(date=date(2026, 6, 28), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_clicks", actual_value=50, baseline_value=100,
                        deviation_pct=-50.0, severity="high",
                        description="Clicks dropped 50%.", is_acknowledged=0),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                               issue_type="not_found_404", severity="high",
                               description="404 detected"),
            ])

    def test_feed_has_both_kinds_with_source_prefixed_ids(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        self.assertIn("feed", body)
        kinds = {item["kind"] for item in body["feed"]}
        self.assertEqual(kinds, {"anomaly", "technical"})
        ids = {item["id"] for item in body["feed"]}
        self.assertTrue(any(i.startswith("anomaly-") for i in ids))
        self.assertTrue(any(i.startswith("issue-") for i in ids))

    def test_anomaly_item_has_real_acknowledged_state(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        anomaly_item = next(i for i in body["feed"] if i["kind"] == "anomaly")
        self.assertFalse(anomaly_item["acknowledged"])

    def test_technical_item_always_reports_unacknowledged(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        issue_item = next(i for i in body["feed"] if i["kind"] == "technical")
        self.assertFalse(issue_item["acknowledged"])

    def test_feed_item_shape(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        for item in body["feed"]:
            for key in ["id", "ts", "kind", "severity", "title", "detail", "acknowledged"]:
                self.assertIn(key, item)

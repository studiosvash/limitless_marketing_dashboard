"""The weekly guard is the cost control: one API call per project per week, no matter how
many times anyone presses Refresh."""
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings

from pipeline.connectors.dataforseo_llm_mentions import (
    DataForSEOLLMMentionsConnector, week_start_for,
)
from pipeline.db.schema import init_db
from pipeline.db.writer import upsert_llm_mention_metrics
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session

SITE = "fusehealth.com"


class WeekStartTests(SimpleTestCase):
    def test_monday_of_the_iso_week(self):
        self.assertEqual(week_start_for(date(2026, 7, 31)), date(2026, 7, 27))  # Friday
        self.assertEqual(week_start_for(date(2026, 7, 27)), date(2026, 7, 27))  # Monday
        self.assertEqual(week_start_for(date(2026, 8, 2)), date(2026, 7, 27))   # Sunday


@override_settings()
class WeeklyGuardTests(SimpleTestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        patcher = mock.patch.dict(
            "os.environ",
            {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _connector(self):
        c = DataForSEOLLMMentionsConnector()
        # Targets come from Django's AITarget; stub the lookup so this test stays about the guard.
        c._load_targets = mock.Mock(return_value=("fusehealth", ["FuseHealth"], ["driphydration.com"]))
        c._resolve_site_url = mock.Mock(return_value=SITE)
        return c

    def test_second_fetch_in_the_same_week_makes_no_http_call(self):
        week = week_start_for(date.today())
        with get_session() as s:
            upsert_llm_mention_metrics(s, [{
                "site_id": SITE, "week_start": week, "subject_domain": "fusehealth.com",
                "subject_type": "you", "platform": "google",
                "mentions": 1, "ai_search_volume": 50,
            }])
            s.commit()

        c = self._connector()
        with mock.patch.object(c, "_call_cross_aggregation") as api:
            records = c.fetch(site_id=SITE)

        api.assert_not_called()
        self.assertEqual(records, [], "an already-stored week must return no records")

    def test_first_fetch_of_a_week_does_call_the_api(self):
        c = self._connector()
        with mock.patch.object(c, "_call_cross_aggregation", return_value={}) as api, \
             mock.patch.object(c, "_call_top_pages", return_value={}):
            c.fetch(site_id=SITE)
        api.assert_called_once()

    def test_project_with_no_brand_and_no_competitors_is_skipped(self):
        c = self._connector()
        c._load_targets = mock.Mock(return_value=("", [], []))
        with mock.patch.object(c, "_call_cross_aggregation") as api:
            records = c.fetch(site_id=SITE)
        api.assert_not_called()
        self.assertEqual(records, [])

    def test_project_with_a_brand_but_no_competitors_makes_no_cross_aggregation_call(self):
        # cross_aggregation_metrics requires at least 2 targets; sending one would 400 and
        # still be billed. Own-mentions-only is Task 3's aggregation_metrics path.
        c = self._connector()
        c._load_targets = mock.Mock(return_value=("FuseHealth", [], []))
        with mock.patch.object(c, "_call_cross_aggregation") as api:
            c.fetch(site_id=SITE)
        api.assert_not_called()

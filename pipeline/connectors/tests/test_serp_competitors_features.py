"""SERP-feature capture on the competitor connector: AI Overview citations, local pack
and featured snippet parsed from an ADVANCED task_get response, plus the project's
device reaching the task_post payload.

Nothing here touches the network: `requests` is stubbed where a request would happen,
and `_normalize_task` / `_extract_feature_records` are exercised as pure functions on
handcrafted advanced `task_data` fixtures.
"""
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings

from pipeline.connectors import dataforseo_serp as serp_mod
from pipeline.connectors import dataforseo_serp_competitors as comp_mod

DAY = date(2026, 8, 17)
SITE = "premierstaff.com"
LOC = "United States - Los Angeles, CA"


def _connector():
    with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l",
                                        "DATAFORSEO_PASSWORD": "p"}, clear=False):
        return comp_mod.DataForSEOSerpCompetitorsConnector()


def _advanced_task(items):
    return {"data": {"keyword": "event staffing"}, "result": [{"items": items}]}


class NormalizeTaskFeatureTests(SimpleTestCase):
    def setUp(self):
        self.connector = _connector()

    def _features(self, items, competitors=frozenset({"eventstaff.com"})):
        self.connector._feature_records = []
        records = self.connector._normalize_task(
            _advanced_task(items), DAY, set(competitors), SITE, LOC)
        return records, self.connector._feature_records

    def test_organic_items_still_yield_competitor_records(self):
        records, feats = self._features([
            {"type": "ai_overview", "references": [], "items": []},
            {"type": "organic", "rank_absolute": 2, "domain": "eventstaff.com",
             "url": "https://eventstaff.com/la"},
        ])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["competitor_domain"], "eventstaff.com")
        self.assertEqual(records[0]["position"], 2)
        self.assertEqual(feats, [], "an empty AI Overview yields no feature rows")

    def test_aio_slots_follow_first_appearance_across_top_level_then_nested(self):
        records, feats = self._features([{
            "type": "ai_overview",
            "references": [
                {"domain": "premierstaff.com", "url": "https://premierstaff.com/g",
                 "title": "Guide", "source": "Premier Staff"},
                {"domain": "other.com", "url": "https://other.com/p",
                 "title": "Post", "source": "Other"},
            ],
            "items": [
                {"type": "ai_overview_element",
                 "references": [{"domain": "juliavaller.com",
                                 "url": "https://juliavaller.com/x",
                                 "title": "X", "source": "Julia Valler"}]},
            ],
        }])
        self.assertEqual(records, [], "an ai_overview item is not an organic rank")
        by_domain = {f["domain"]: f for f in feats}
        self.assertEqual(by_domain["premierstaff.com"]["slot"], 1)
        self.assertEqual(by_domain["other.com"]["slot"], 2)
        self.assertEqual(by_domain["juliavaller.com"]["slot"], 3)
        for f in feats:
            self.assertEqual(f["feature_type"], "ai_overview")
            self.assertEqual(f["date"], DAY)
            self.assertEqual(f["site_id"], SITE)
            self.assertEqual(f["location"], LOC)
            self.assertEqual(f["keyword"], "event staffing")
        self.assertEqual(by_domain["premierstaff.com"]["url"], "https://premierstaff.com/g")
        self.assertEqual(by_domain["premierstaff.com"]["title"], "Guide")

    def test_repeated_domain_keeps_the_slot_of_its_first_appearance(self):
        _, feats = self._features([{
            "type": "ai_overview",
            "references": [
                {"domain": "premierstaff.com", "url": "https://premierstaff.com/a"},
                {"domain": "other.com", "url": "https://other.com/b"},
                {"domain": "premierstaff.com", "url": "https://premierstaff.com/c"},
            ],
            "items": [],
        }])
        premier = [f for f in feats if f["domain"] == "premierstaff.com"]
        self.assertEqual(len(premier), 1, "one row per distinct referenced domain")
        self.assertEqual(premier[0]["slot"], 1)
        self.assertEqual(premier[0]["url"], "https://premierstaff.com/a",
                         "first appearance wins, later repeats are ignored")

    def test_features_are_not_filtered_by_the_tracked_competitor_set(self):
        # The table stores EVERY referenced domain (share-of-AIO-citations needs the full
        # denominator; matching to tracked domains is read-time). "wikipedia.org" is
        # nobody's tracked competitor and must still be stored.
        _, feats = self._features([{
            "type": "ai_overview",
            "references": [{"domain": "wikipedia.org", "url": "https://wikipedia.org/w"}],
            "items": [],
        }], competitors=frozenset({"eventstaff.com"}))
        self.assertEqual(len(feats), 1)
        self.assertEqual(feats[0]["domain"], "wikipedia.org")

    def test_local_pack_slots_come_from_rank_group(self):
        _, feats = self._features([
            {"type": "local_pack", "rank_group": 1, "domain": "eventstaff.com",
             "url": "https://eventstaff.com", "title": "Event Staff"},
            {"type": "local_pack", "rank_group": 2, "domain": "premierstaff.com",
             "title": "Premier Staff"},              # no url — still a row
            {"type": "local_pack", "rank_group": 3},  # no domain — no row to key on
        ])
        self.assertEqual(len(feats), 2)
        by_domain = {f["domain"]: f for f in feats}
        self.assertEqual(by_domain["eventstaff.com"]["slot"], 1)
        self.assertEqual(by_domain["premierstaff.com"]["slot"], 2)
        for f in feats:
            self.assertEqual(f["feature_type"], "local_pack")

    def test_featured_snippet_is_one_row_at_slot_1(self):
        _, feats = self._features([
            {"type": "featured_snippet", "domain": "premierstaff.com",
             "url": "https://premierstaff.com/faq", "title": "FAQ"},
        ])
        self.assertEqual(len(feats), 1)
        self.assertEqual(feats[0]["feature_type"], "featured_snippet")
        self.assertEqual(feats[0]["slot"], 1)
        self.assertEqual(feats[0]["domain"], "premierstaff.com")


class SubmitAndFetchWiringTests(SimpleTestCase):
    def setUp(self):
        self.connector = _connector()

    @mock.patch.object(comp_mod.requests, "post")
    def test_task_post_asks_for_the_ai_overview(self, post):
        resp = mock.Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"cost": 0.01, "tasks": [{"id": "t1"}]}
        post.return_value = resp
        self.connector._submit_tasks(["event staffing"], LOC)
        sent = post.call_args.kwargs["json"][0]
        self.assertIs(sent["load_async_ai_overview"], True)

    @mock.patch.object(comp_mod.requests, "post")
    def test_task_post_carries_the_resolved_device(self, post):
        resp = mock.Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"cost": 0.01, "tasks": [{"id": "t1"}]}
        post.return_value = resp
        self.connector._submit_tasks(["event staffing"], LOC,
                                     device="mobile", os_name="android")
        sent = post.call_args.kwargs["json"][0]
        self.assertEqual(sent["device"], "mobile")
        self.assertEqual(sent["os"], "android")

    @mock.patch.object(comp_mod.requests, "post")
    def test_task_post_defaults_to_desktop(self, post):
        resp = mock.Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"cost": 0.01, "tasks": [{"id": "t1"}]}
        post.return_value = resp
        self.connector._submit_tasks(["event staffing"], LOC)
        sent = post.call_args.kwargs["json"][0]
        self.assertEqual(sent["device"], "desktop")
        self.assertEqual(sent["os"], "windows")

    @mock.patch.object(comp_mod.requests, "get")
    def test_poll_fetches_the_advanced_endpoint(self, get):
        # The regular endpoint renders no ai_overview items at all — polling it would
        # silently drop every citation while everything else kept working.
        resp = mock.Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"cost": 0.0, "tasks": [{
            "status_code": comp_mod.TASK_OK,
            "data": {"keyword": "event staffing"},
            "result": [{"items": []}],
        }]}
        get.return_value = resp
        self.connector._poll_and_fetch(["task-123"], {"eventstaff.com"}, SITE, LOC,
                                       max_polls=1, poll_interval=0)
        url = get.call_args.args[0]
        self.assertIn("/task_get/advanced/", url)
        self.assertNotIn("/task_get/regular/", url)


class ResolveDeviceTests(SimpleTestCase):
    """`_resolve_device` reads the PROJECT's sites.device — Mobile means the mobile SERP."""

    def setUp(self):
        from pipeline.db.schema import init_db
        from pipeline.utils import db_connection
        from pipeline.utils.db_connection import get_engine
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def _add_site(self, site_url, device):
        from pipeline.db.schema import Site
        from pipeline.utils.db_connection import get_session
        with get_session() as session:
            site = Site(site_url=site_url, site_name=site_url,
                        slug=site_url.replace(".", "-"), is_active=1, device=device)
            session.add(site)
            session.flush()
            return site.id

    def test_mobile_project_resolves_to_mobile_android(self):
        pk = self._add_site("premierstaff.com", "Mobile")
        self.assertEqual(serp_mod._resolve_device(pk, "premierstaff.com"),
                         ("mobile", "android"))

    def test_device_match_is_case_insensitive(self):
        pk = self._add_site("premierstaff.com", "MOBILE")
        self.assertEqual(serp_mod._resolve_device(pk, "premierstaff.com"),
                         ("mobile", "android"))

    def test_desktop_project_resolves_to_desktop_windows(self):
        pk = self._add_site("premierstaff.com", "Desktop")
        self.assertEqual(serp_mod._resolve_device(pk, "premierstaff.com"),
                         ("desktop", "windows"))

    def test_site_id_fallback_when_no_pk(self):
        self._add_site("premierstaff.com", "Mobile")
        self.assertEqual(serp_mod._resolve_device(None, "premierstaff.com"),
                         ("mobile", "android"))

    def test_unknown_project_defaults_to_desktop_and_never_raises(self):
        self.assertEqual(serp_mod._resolve_device(None, "nobody.example"),
                         ("desktop", "windows"))

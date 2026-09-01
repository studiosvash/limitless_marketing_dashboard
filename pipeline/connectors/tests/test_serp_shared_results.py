"""One SERP purchase per keyword per run (2026-09-01).

The own-domain connector used to buy the top-30 SERP and keep only its own row; the
competitor connector then bought the IDENTICAL SERP (same keyword, city, device, depth) to
read the other 29 rows. On the live account that was $7.59 of $25 over 90 days — the single
largest line — for nothing the first purchase did not already contain.

Now `dataforseo_serp` (a) asks for the AI Overview at task_post, (b) reads the ADVANCED
rendering so feature items are present, and (c) publishes every completed SERP into the
run's shared context; `dataforseo_serp_competitors` reads competitor ranks and SERP features
off those and posts nothing of its own. It only buys its own tasks when no own-domain SERP
ran in the same process (a standalone call), so nothing that used to work stops working.

Also here: the scheduled-run pricing. A cron run has nobody watching a progress bar, so it
takes the normal-priority queue (half the per-query price) and waits longer for it.
"""
from unittest import mock

from django.test import SimpleTestCase

from pipeline.connectors import dataforseo_serp as serp_mod
from pipeline.connectors import dataforseo_serp_competitors as comp_mod

SITE = "premierstaff.com"
LOC = "United States - Charlotte, NC"


def _serp_connector(scheduled=False):
    with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l", "DATAFORSEO_PASSWORD": "p"}):
        c = serp_mod.DataForSEOSERPConnector()
    c.run_shared = {}
    c.scheduled = scheduled
    return c


def _comp_connector(shared=None):
    with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l", "DATAFORSEO_PASSWORD": "p"}):
        c = comp_mod.DataForSEOSerpCompetitorsConnector()
    c.run_shared = shared if shared is not None else {}
    return c


def _ok_task(keyword="event staffing", items=None):
    return {
        "status_code": 20000,
        "data": {"keyword": keyword},
        "result": [{"items": items if items is not None else [
            {"type": "organic", "rank_absolute": 1, "domain": "premierstaff.com",
             "url": "https://premierstaff.com/charlotte"},
            {"type": "organic", "rank_absolute": 4, "domain": "eventstaff.com",
             "url": "https://eventstaff.com/nc"},
            {"type": "ai_overview", "references": [
                {"domain": "eventstaff.com", "url": "https://eventstaff.com/g", "title": "G"}],
             "items": []},
        ]}],
    }


def _resp(json_body):
    r = mock.Mock()
    r.json.return_value = json_body
    r.raise_for_status.return_value = None
    return r


class SerpTaskPostTests(SimpleTestCase):
    @mock.patch.object(serp_mod.requests, "post")
    def test_task_post_asks_for_the_ai_overview(self, post):
        post.return_value = _resp({"tasks": [{"status_code": 20100, "id": "t1"}], "cost": 0.003})
        _serp_connector()._submit_tasks(["event staffing"], SITE, LOC)
        task = post.call_args.kwargs["json"][0]
        self.assertTrue(task.get("load_async_ai_overview"),
                        "the competitor connector needs the AI Overview off THIS purchase")

    @mock.patch.object(serp_mod.requests, "post")
    def test_a_watched_run_keeps_the_priority_queue(self, post):
        post.return_value = _resp({"tasks": [{"status_code": 20100, "id": "t1"}]})
        _serp_connector(scheduled=False)._submit_tasks(["event staffing"], SITE, LOC)
        self.assertEqual(post.call_args.kwargs["json"][0]["priority"], serp_mod.TASK_PRIORITY)

    @mock.patch.object(serp_mod.requests, "post")
    def test_a_scheduled_run_uses_the_normal_priority_queue(self, post):
        post.return_value = _resp({"tasks": [{"status_code": 20100, "id": "t1"}]})
        _serp_connector(scheduled=True)._submit_tasks(["event staffing"], SITE, LOC)
        self.assertEqual(post.call_args.kwargs["json"][0]["priority"], serp_mod.NORMAL_PRIORITY)
        self.assertLess(serp_mod.NORMAL_PRIORITY, serp_mod.TASK_PRIORITY)

    def test_a_scheduled_run_waits_longer_for_the_slower_queue(self):
        manual_polls, manual_interval = _serp_connector(scheduled=False)._poll_budget()
        sched_polls, sched_interval = _serp_connector(scheduled=True)._poll_budget()
        self.assertGreaterEqual(sched_polls * sched_interval, 2 * manual_polls * manual_interval)


class SerpPublishesResultsTests(SimpleTestCase):
    @mock.patch.object(serp_mod.time, "sleep", lambda *_: None)
    @mock.patch.object(serp_mod.requests, "get")
    def test_poll_reads_the_advanced_rendering_and_publishes_each_serp(self, get):
        get.return_value = _resp({"tasks": [_ok_task()]})
        c = _serp_connector()
        records = c._poll_and_fetch(["t1"], SITE, SITE, LOC)
        self.assertIn("/task_get/advanced/", get.call_args.args[0])
        self.assertEqual(records[0]["position"], 1, "own-domain rank still comes out")
        self.assertEqual(len(c.run_shared["serp_tasks"]), 1)
        self.assertEqual(c.run_shared["serp_tasks"][0]["data"]["keyword"], "event staffing")

    @mock.patch.object(serp_mod.requests, "get")
    def test_drained_leftovers_are_published_too(self, get):
        get.side_effect = [
            _resp({"tasks": [{"result": [{"id": "old1", "tag": "fusehealth_2026-08-30"}]}]}),
            _resp({"tasks": [_ok_task("stadium staffing")]}),
        ]
        c = _serp_connector()
        c._drain_ready_tasks(SITE, SITE, LOC)
        self.assertEqual([t["data"]["keyword"] for t in c.run_shared["serp_tasks"]],
                         ["stadium staffing"])

    @mock.patch.object(serp_mod.time, "sleep", lambda *_: None)
    @mock.patch.object(serp_mod.requests, "get")
    def test_a_connector_with_no_shared_context_still_works(self, get):
        """Standalone use (scripts, tests) never attached `run_shared`."""
        get.return_value = _resp({"tasks": [_ok_task()]})
        with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l", "DATAFORSEO_PASSWORD": "p"}):
            c = serp_mod.DataForSEOSERPConnector()
        records = c._poll_and_fetch(["t1"], SITE, SITE, LOC)
        self.assertEqual(len(records), 1)


class CompetitorsReuseTests(SimpleTestCase):
    def _fetch(self, connector, post, get):
        with mock.patch("pipeline.services.competitor_service.get_tracked_competitors",
                        return_value=["eventstaff.com"]), \
             mock.patch.object(connector, "_resolve_site_id", return_value=SITE), \
             mock.patch.object(connector, "_resolve_location", return_value=LOC), \
             mock.patch.object(connector, "_load_keywords", return_value=["event staffing"]), \
             mock.patch.object(comp_mod, "record_cost") as cost, \
             mock.patch.object(comp_mod.time, "sleep", lambda *_: None):
            records = connector.fetch(SITE)
        return records, cost

    @mock.patch.object(comp_mod.requests, "get")
    @mock.patch.object(comp_mod.requests, "post")
    def test_reuses_the_own_domain_serps_and_buys_nothing(self, post, get):
        # tasks_ready (leftover drain) is still consulted and is empty.
        get.return_value = _resp({"tasks": [{"result": []}]})
        c = _comp_connector(shared={"serp_tasks": [_ok_task()]})
        records, cost = self._fetch(c, post, get)
        post.assert_not_called()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["competitor_domain"], "eventstaff.com")
        self.assertEqual(records[0]["position"], 4)
        self.assertEqual(records[0]["location"], LOC)
        self.assertEqual([f["feature_type"] for f in c._feature_records], ["ai_overview"])
        # No spend event for a purchase that did not happen.
        self.assertTrue(all(call.args[2] == 0 for call in cost.call_args_list))

    @mock.patch.object(comp_mod.requests, "get")
    @mock.patch.object(comp_mod.requests, "post")
    def test_buys_its_own_serps_when_no_own_domain_serp_ran_in_this_process(self, post, get):
        get.side_effect = [
            _resp({"tasks": [{"result": []}]}),                       # tasks_ready: nothing
            _resp({"tasks": [_ok_task()]}),                           # its own task_get
        ]
        post.return_value = _resp({"tasks": [{"status_code": 20100, "id": "own1"}]})
        c = _comp_connector(shared={})             # engine attached a context, serp never ran
        records, _ = self._fetch(c, post, get)
        post.assert_called_once()
        self.assertEqual(records[0]["competitor_domain"], "eventstaff.com")

    @mock.patch.object(comp_mod.requests, "get")
    @mock.patch.object(comp_mod.requests, "post")
    def test_an_empty_shared_serp_list_means_nothing_to_read_not_buy_again(self, post, get):
        """The own-domain connector ran but every task was still pending at the end of its
        poll window. Those SERPs are paid for and will be drained next run; buying them
        again now is the exact double spend this change removes."""
        get.return_value = _resp({"tasks": [{"result": []}]})
        c = _comp_connector(shared={"serp_tasks": []})
        records, _ = self._fetch(c, post, get)
        post.assert_not_called()
        self.assertEqual(records, [])

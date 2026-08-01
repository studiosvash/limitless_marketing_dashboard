"""Parsing real DataForSEO LLM Mentions responses.

Fixtures here are trimmed from real API captures under
.superpowers/sdd/2026-07-31-llm-mentions-ai-visibility/ (real-agg.json, real-cross.json,
real-pages.json -- captured 2026-08-01), not hand-written from documentation. An earlier
version of these fixtures was built from the Task 3 brief's own invented shape (one extra
`"items": [{ ... }]` wrapper around the block that tasks[0].result[0] actually is), and every
parser was written to match that wrong shape -- so the tests passed while the real API returned
zero rows for every real sync. Where a real capture doesn't naturally exercise a documented edge
case (a fully zero/omitted 'mentions' key, a www.-collision), a minimal fixture is hand-built in
the *same real envelope shape* instead, and is labelled as constructed rather than captured.
"""
from datetime import date
from unittest import mock

from django.test import SimpleTestCase

from pipeline.connectors.dataforseo_llm_mentions import DataForSEOLLMMentionsConnector

WEEK = date(2026, 7, 27)
SITE = "fusehealth.com"

# Trimmed from a real cross_aggregated_metrics/live response for premierstaff.com (own) +
# eventstaff.com (competitor), captured 2026-08-01:
# .superpowers/sdd/2026-07-31-llm-mentions-ai-visibility/real-cross.json
# Every mentions/ai_search_volume number below is real. Two things were trimmed out (the
# location/language/search_results_domain/brand_entities_* groups, which this connector never
# reads) and one entry was added by hand: "www.eventstaff.com" in total.sources_domain -- the
# real response never happened to return a www. duplicate of a tracked domain, so that one case
# needs a constructed line to be exercised at all.
CROSS_AGG = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "total": {
                "platform": [
                    {"type": "group_element", "key": "chat_gpt", "mentions": 58, "ai_search_volume": 6446},
                    {"type": "group_element", "key": "google", "mentions": 27, "ai_search_volume": 11480},
                ],
                "sources_domain": [
                    {"type": "group_element", "key": "eventstaff.com", "mentions": 38, "ai_search_volume": 11605},
                    {"type": "group_element", "key": "premierstaff.com", "mentions": 27, "ai_search_volume": 4116},
                    {"type": "group_element", "key": "fash.com", "mentions": 15, "ai_search_volume": 471},
                    # Hand-added (not in the capture) -- see module docstring.
                    {"type": "group_element", "key": "www.eventstaff.com", "mentions": 5, "ai_search_volume": 50},
                ],
            },
            "items": [
                {"key": "premierstaff.com", "platform": [
                    {"type": "group_element", "key": "chat_gpt", "mentions": 18, "ai_search_volume": 976},
                    {"type": "group_element", "key": "google", "mentions": 2, "ai_search_volume": 160},
                ]},
                {"key": "eventstaff.com", "platform": [
                    {"type": "group_element", "key": "chat_gpt", "mentions": 43, "ai_search_volume": 5496},
                    {"type": "group_element", "key": "google", "mentions": 25, "ai_search_volume": 11320},
                ]},
            ],
        }],
    }],
}

# Hand-constructed (not from a capture), in the same real envelope shape as CROSS_AGG above.
# The real cross-aggregation capture never returned a subject with a fully zero/omitted
# 'mentions' key on either platform -- both premierstaff.com and eventstaff.com had real
# mentions on both platforms -- so this fixture exists solely to exercise DataForSEO's
# documented "a group_element omits 'mentions' entirely when the value is zero" behaviour and
# confirm a zero-mentions subject is still recorded, not dropped.
CROSS_AGG_ZERO_CASE = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "total": {"sources_domain": []},
            "items": [
                {"key": "premierstaff.com", "platform": [
                    {"type": "group_element", "key": "google", "mentions": 1, "ai_search_volume": 50},
                    {"type": "group_element", "key": "chat_gpt"},          # zero -> no 'mentions' key
                ]},
                {"key": "eventstaff.com", "platform": [
                    {"type": "group_element", "key": "google"},            # no data at all
                    {"type": "group_element", "key": "chat_gpt"},
                ]},
            ],
        }],
    }],
}

# Trimmed from a real top_pages/live response for driphydration.com, captured 2026-08-01:
# .superpowers/sdd/2026-07-31-llm-mentions-ai-visibility/real-pages.json
# Real numbers throughout. The real response had a third item (a second driphydration.com
# page); it's dropped here only so "exactly one URL survives the own-host filter" stays an
# exact assertion instead of a set-membership one.
TOP_PAGES = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "items": [
                {"key": "https://driphydration.com/blog/wolverine-stack-injury-recovery/", "platform": [
                    {"type": "group_element", "key": "google", "mentions": 397, "ai_search_volume": 305020},
                ]},
                {"key": "https://www.perfectb.com/wolverine-peptide-bpc-157-tb-500/", "platform": [
                    {"type": "group_element", "key": "google", "mentions": 171, "ai_search_volume": 138610},
                ]},
            ],
        }],
    }],
}


class CrossAggregationParsingTests(SimpleTestCase):
    def _connector(self):
        with mock.patch.dict("os.environ",
                             {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"}):
            return DataForSEOLLMMentionsConnector()

    def test_own_domain_is_tagged_you_and_competitors_competitor(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "premierstaff.com", ["eventstaff.com"], WEEK)
        by = {(r["subject_domain"], r["platform"]): r for r in recs if r["_table"] == "metrics"}
        self.assertEqual(by[("premierstaff.com", "google")]["subject_type"], "you")
        self.assertEqual(by[("eventstaff.com", "google")]["subject_type"], "competitor")

    def test_missing_mentions_key_reads_as_zero_not_a_crash(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG_ZERO_CASE, SITE, "premierstaff.com", ["eventstaff.com"], WEEK)
        by = {(r["subject_domain"], r["platform"]): r for r in recs if r["_table"] == "metrics"}
        self.assertEqual(by[("premierstaff.com", "chat_gpt")]["mentions"], 0)
        self.assertEqual(by[("eventstaff.com", "google")]["mentions"], 0)

    def test_zero_data_competitor_is_still_recorded(self):
        # Absence is information: eventstaff.com at 0 must appear, not vanish.
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG_ZERO_CASE, SITE, "premierstaff.com", ["eventstaff.com"], WEEK)
        domains = {r["subject_domain"] for r in recs if r["_table"] == "metrics"}
        self.assertIn("eventstaff.com", domains)

    def test_discovered_domains_come_from_total_sources_domain(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "premierstaff.com", ["eventstaff.com"], WEEK)
        discovered = {r["subject_domain"] for r in recs
                      if r["_table"] == "metrics" and r["subject_type"] == "discovered"}
        self.assertIn("fash.com", discovered)
        # A domain already tracked must NOT be duplicated as 'discovered'.
        self.assertNotIn("eventstaff.com", discovered)

    def test_non_success_status_returns_no_records(self):
        bad = {"tasks": [{"status_code": 40501, "status_message": "nope", "result": []}]}
        self.assertEqual(
            self._connector()._parse_cross_aggregation(bad, SITE, "premierstaff.com", [], WEEK), [])

    def test_a_tracked_competitors_www_host_is_not_double_counted_as_discovered(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "premierstaff.com", ["eventstaff.com"], WEEK)
        discovered = {r["subject_domain"] for r in recs if r["subject_type"] == "discovered"}
        self.assertNotIn("www.eventstaff.com", discovered)

    def test_a_zero_mention_week_still_writes_rows_for_every_tracked_subject(self):
        # Otherwise nothing is written, the weekly guard never trips, and the next Refresh
        # re-buys the same paid call.
        empty = {"tasks": [{"status_code": 20000, "result": [{"total": {}, "items": None}]}]}
        recs = self._connector()._parse_cross_aggregation(
            empty, SITE, "fusehealth.com", ["driphydration.com"], WEEK)
        metrics = [r for r in recs if r["_table"] == "metrics"]
        self.assertEqual(len(metrics), 4, "2 subjects x 2 platforms, all at zero")
        self.assertTrue(all(r["mentions"] == 0 for r in metrics))
        self.assertEqual({r["subject_domain"] for r in metrics},
                         {"fusehealth.com", "driphydration.com"})

    def test_a_competitor_absent_from_items_is_still_listed_at_zero(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "neverseen.com"], WEEK)
        domains = {r["subject_domain"] for r in recs if r["_table"] == "metrics"}
        self.assertIn("neverseen.com", domains)


class TopPagesParsingTests(SimpleTestCase):
    def _connector(self):
        with mock.patch.dict("os.environ",
                             {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"}):
            return DataForSEOLLMMentionsConnector()

    def test_only_pages_on_our_own_host_are_kept(self):
        recs = self._connector()._parse_top_pages(TOP_PAGES, SITE, "driphydration.com", WEEK)
        urls = [r["url"] for r in recs]
        self.assertEqual(urls, ["https://driphydration.com/blog/wolverine-stack-injury-recovery/"])

    def test_page_record_carries_mentions_volume_and_platforms(self):
        rec = self._connector()._parse_top_pages(TOP_PAGES, SITE, "driphydration.com", WEEK)[0]
        self.assertEqual(rec["_table"], "pages")
        self.assertEqual(rec["mentions"], 397)
        self.assertEqual(rec["ai_search_volume"], 305020)
        self.assertIn("google", rec["platforms"])


# Real real-agg.json (aggregated_metrics/live for fusehealth.com, captured 2026-08-01) returned
# a totally empty week: every field under "total" is JSON null, and "items" is null too -- not
# an empty list, not a missing key. Kept close to verbatim (trimmed to the fields the parser
# reads) because this null-vs-missing-vs-empty distinction is exactly the kind of real-world
# shape a hand-written fixture would not have thought to include.
AGG_REAL_EMPTY = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "total": {
                "platform": None,
                "sources_domain": None,
            },
            "items": None,
        }],
    }],
}

# Hand-constructed (not from a capture), in the same real envelope shape as AGG_REAL_EMPTY
# above (aggregated_metrics puts everything in "total"; "items" is always empty/null for this
# endpoint). The real capture had zero mentions everywhere, which can't exercise "own mentions
# are recorded" or "our own www host is filtered out of discovered" -- both need actual
# non-zero data, so this fixture supplies it by hand.
AGG_ONLY = {
    "tasks": [{
        "status_code": 20000,
        "result": [{
            "total": {
                "platform": [
                    {"type": "group_element", "key": "google", "mentions": 1, "ai_search_volume": 50},
                    {"type": "group_element", "key": "chat_gpt"},
                ],
                "sources_domain": [
                    {"type": "group_element", "key": "www.fusehealth.com", "mentions": 1, "ai_search_volume": 50},
                    {"type": "group_element", "key": "www.rxpnow.com", "mentions": 1, "ai_search_volume": 50},
                ],
            },
            "items": [],
        }],
    }],
}


class AggregationFallbackParsingTests(SimpleTestCase):
    def _connector(self):
        with mock.patch.dict("os.environ",
                             {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"}):
            return DataForSEOLLMMentionsConnector()

    def test_own_mentions_are_recorded_for_both_platforms(self):
        recs = self._connector()._parse_aggregation(AGG_ONLY, SITE, "fusehealth.com", WEEK)
        mine = {r["platform"]: r for r in recs if r["subject_type"] == "you"}
        self.assertEqual(mine["google"]["mentions"], 1)
        self.assertEqual(mine["chat_gpt"]["mentions"], 0)

    def test_our_own_www_host_is_not_listed_as_a_rival(self):
        recs = self._connector()._parse_aggregation(AGG_ONLY, SITE, "fusehealth.com", WEEK)
        discovered = {r["subject_domain"] for r in recs if r["subject_type"] == "discovered"}
        self.assertNotIn("www.fusehealth.com", discovered)
        self.assertIn("www.rxpnow.com", discovered)

    def test_all_null_total_reads_as_zero_not_a_crash(self):
        # Real capture: total.platform / total.sources_domain / items are all JSON null when a
        # project has no AI mentions at all that week, not an empty list or a missing key.
        recs = self._connector()._parse_aggregation(AGG_REAL_EMPTY, SITE, "fusehealth.com", WEEK)
        mine = {r["platform"]: r for r in recs if r["subject_type"] == "you"}
        self.assertEqual(mine["google"]["mentions"], 0)
        self.assertEqual(mine["chat_gpt"]["mentions"], 0)
        self.assertEqual([r for r in recs if r["subject_type"] == "discovered"], [])


class EndpointUrlTests(SimpleTestCase):
    """The URLs cannot be exercised by a fixture-based test, and all three were wrong in the
    first implementation: they 404'd against the real API and every test still passed. These
    assertions pin the values verified live on 2026-08-01."""

    def test_endpoints_use_the_verified_rest_paths(self):
        from pipeline.connectors import dataforseo_llm_mentions as m
        self.assertTrue(m.CROSS_AGG_ENDPOINT.endswith(
            "/ai_optimization/llm_mentions/cross_aggregated_metrics/live"))
        self.assertTrue(m.AGG_ENDPOINT.endswith(
            "/ai_optimization/llm_mentions/aggregated_metrics/live"))
        self.assertTrue(m.TOP_PAGES_ENDPOINT.endswith(
            "/ai_optimization/llm_mentions/top_pages/live"))

    def test_every_endpoint_is_a_live_path(self):
        # The `/live` suffix is what makes these instant rather than task_post/task_get.
        from pipeline.connectors import dataforseo_llm_mentions as m
        for url in (m.CROSS_AGG_ENDPOINT, m.AGG_ENDPOINT, m.TOP_PAGES_ENDPOINT):
            self.assertTrue(url.endswith("/live"), url)

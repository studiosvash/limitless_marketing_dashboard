"""Parsing real DataForSEO LLM Mentions responses (captured 2026-07-31)."""
from datetime import date
from unittest import mock

from django.test import SimpleTestCase

from pipeline.connectors.dataforseo_llm_mentions import DataForSEOLLMMentionsConnector

WEEK = date(2026, 7, 27)
SITE = "fusehealth.com"

CROSS_AGG = {"tasks": [{"status_code": 20000, "result": [{"items": [{
    "total": {
        "platform": [
            {"type": "group_element", "key": "google", "mentions": 5785, "ai_search_volume": 2698980},
            {"type": "group_element", "key": "chat_gpt", "mentions": 115, "ai_search_volume": 2907},
        ],
        "sources_domain": [
            {"type": "group_element", "key": "driphydration.com", "mentions": 3633, "ai_search_volume": 1617742},
            {"type": "group_element", "key": "www.youtube.com", "mentions": 1916, "ai_search_volume": 962270},
        ],
    },
    "items": [
        {"key": "fusehealth.com", "platform": [
            {"type": "group_element", "key": "google", "mentions": 1, "ai_search_volume": 50},
            {"type": "group_element", "key": "chat_gpt"},          # zero -> no 'mentions' key
        ]},
        {"key": "driphydration.com", "platform": [
            {"type": "group_element", "key": "google", "mentions": 3632, "ai_search_volume": 1617710},
            {"type": "group_element", "key": "chat_gpt", "mentions": 1, "ai_search_volume": 32},
        ]},
        {"key": "restoreiv.com", "platform": [
            {"type": "group_element", "key": "google"},            # no data at all
            {"type": "group_element", "key": "chat_gpt"},
        ]},
    ],
}]}]}]}

TOP_PAGES = {"tasks": [{"status_code": 20000, "result": [{"items": [{
    "items": [
        {"key": "https://fusehealth.com/locations/dallas", "platform": [
            {"type": "group_element", "key": "google", "mentions": 36, "ai_search_volume": 1627}]},
        {"key": "https://www.perfectb.com/some-article/", "platform": [
            {"type": "group_element", "key": "google", "mentions": 171, "ai_search_volume": 138610}]},
    ],
}]}]}]}


class CrossAggregationParsingTests(SimpleTestCase):
    def _connector(self):
        with mock.patch.dict("os.environ",
                             {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"}):
            return DataForSEOLLMMentionsConnector()

    def test_own_domain_is_tagged_you_and_competitors_competitor(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        by = {(r["subject_domain"], r["platform"]): r for r in recs if r["_table"] == "metrics"}
        self.assertEqual(by[("fusehealth.com", "google")]["subject_type"], "you")
        self.assertEqual(by[("driphydration.com", "google")]["subject_type"], "competitor")

    def test_missing_mentions_key_reads_as_zero_not_a_crash(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        by = {(r["subject_domain"], r["platform"]): r for r in recs if r["_table"] == "metrics"}
        self.assertEqual(by[("fusehealth.com", "chat_gpt")]["mentions"], 0)
        self.assertEqual(by[("restoreiv.com", "google")]["mentions"], 0)

    def test_zero_data_competitor_is_still_recorded(self):
        # Absence is information: restoreiv.com at 0 must appear, not vanish.
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        domains = {r["subject_domain"] for r in recs if r["_table"] == "metrics"}
        self.assertIn("restoreiv.com", domains)

    def test_discovered_domains_come_from_total_sources_domain(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        discovered = {r["subject_domain"] for r in recs
                      if r["_table"] == "metrics" and r["subject_type"] == "discovered"}
        self.assertIn("www.youtube.com", discovered)
        # A domain already tracked must NOT be duplicated as 'discovered'.
        self.assertNotIn("driphydration.com", discovered)

    def test_non_success_status_returns_no_records(self):
        bad = {"tasks": [{"status_code": 40501, "status_message": "nope", "result": []}]}
        self.assertEqual(
            self._connector()._parse_cross_aggregation(bad, SITE, "fusehealth.com", [], WEEK), [])


class TopPagesParsingTests(SimpleTestCase):
    def _connector(self):
        with mock.patch.dict("os.environ",
                             {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"}):
            return DataForSEOLLMMentionsConnector()

    def test_only_pages_on_our_own_host_are_kept(self):
        recs = self._connector()._parse_top_pages(TOP_PAGES, SITE, "fusehealth.com", WEEK)
        urls = [r["url"] for r in recs]
        self.assertEqual(urls, ["https://fusehealth.com/locations/dallas"])

    def test_page_record_carries_mentions_volume_and_platforms(self):
        rec = self._connector()._parse_top_pages(TOP_PAGES, SITE, "fusehealth.com", WEEK)[0]
        self.assertEqual(rec["_table"], "pages")
        self.assertEqual(rec["mentions"], 36)
        self.assertEqual(rec["ai_search_volume"], 1627)
        self.assertIn("google", rec["platforms"])

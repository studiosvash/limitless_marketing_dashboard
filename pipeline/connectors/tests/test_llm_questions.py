"""Which AI questions does this URL turn up in?

`llm_mentions/search/live` answers exactly that: one row per question an answer engine was
asked, carrying the question text, the answer, how often it is asked, and the pages the engine
retrieved or cited. Verified against the live API for premierstaff.com — 62 questions on
chat_gpt alone.

Two constraints found by calling it, not by reading docs:

  * `target[].domain` REJECTS a path — `premierstaff.com/blog/x` comes back 40501 "must be a
    valid domain". So a page-level question is answered by querying the DOMAIN and filtering
    locally on the URL.
  * the filter list (`ai_optimization_llm_mentions_filters`) offers platform, location,
    language, ai_search_volume, the two timestamps and model_name — and NO url field, so that
    local filter is the only way to do it.

The distinction this module refuses to flatten: `sources[]` is what the engine CITED in its
answer, `search_results[]` is what it merely RETRIEVED. On the live account every one of
premierstaff.com's pages was retrieved and none were cited, which is the single most useful
thing the endpoint says — collapsing both into "mentioned" would destroy it.
"""
from unittest import mock

from django.test import SimpleTestCase

from pipeline.connectors.dataforseo_llm_questions import (
    domain_of, parse_questions, url_matches,
)

# Trimmed from a real response captured 2026-08-11 (premierstaff.com, chat_gpt).
LIVE_ITEM = {
    "platform": "chat_gpt",
    "model_name": "gpt-5-5",
    "location_code": 2840,
    "question": "how many bartenders do you need for 50 guests?",
    "answer": "For **50 guests**, **1 bartender is usually enough**...",
    "sources": [
        {"source_name": "Rimdrip Bartending", "title": "How many bartenders do you need?",
         "domain": "www.rimdrip.co", "url": "https://www.rimdrip.co/blog/how-many?utm_source=chatgpt.com"},
    ],
    "search_results": [
        {"title": "How Many Bartenders Do I Need?", "domain": "nyeventsny.com",
         "url": "https://nyeventsny.com/blog/how-many-bartenders-do-i-need/?utm_source=chatgpt.com"},
        {"title": "How Many Bartenders Do You Need For An Event?", "domain": "premierstaff.com",
         "url": "https://premierstaff.com/blog/shorts/how-many-bartenders-for-an-event/?utm_source=chatgpt.com"},
    ],
    "ai_search_volume": 82,
    "monthly_searches": {"2026-07": 82, "2026-06": 85},
    "first_response_at": "2025-11-05 19:28:34 +00:00",
    "last_response_at": "2026-08-05 23:12:16 +00:00",
    "fan_out_queries": ["bartender to guest ratio events 50 guests"],
}

CITED_ITEM = {
    "platform": "google",
    "question": "who staffs corporate events in los angeles?",
    "answer": "Premierstaff is one option...",
    "sources": [
        {"title": "Event staffing", "domain": "premierstaff.com",
         "url": "https://premierstaff.com/services/?utm_source=chatgpt.com"},
    ],
    "search_results": [],
    "ai_search_volume": 12,
}


def _envelope(items):
    return {"tasks": [{"result": [{"total_count": len(items), "items": items}]}]}


class DomainOfTests(SimpleTestCase):
    def test_a_blog_url_reduces_to_its_domain(self):
        self.assertEqual(
            domain_of("https://premierstaff.com/blog/shorts/how-many-bartenders-for-an-event/"),
            "premierstaff.com")

    def test_a_bare_domain_is_unchanged(self):
        self.assertEqual(domain_of("premierstaff.com"), "premierstaff.com")

    def test_www_is_stripped_so_the_api_accepts_it(self):
        self.assertEqual(domain_of("https://www.premierstaff.com/"), "premierstaff.com")


class UrlMatchTests(SimpleTestCase):
    """The page filter. Tracking parameters must not stop a URL matching itself."""

    def test_the_chatgpt_tracking_parameter_is_ignored(self):
        self.assertTrue(url_matches(
            "https://premierstaff.com/blog/x/?utm_source=chatgpt.com",
            "https://premierstaff.com/blog/x/"))

    def test_a_trailing_slash_difference_still_matches(self):
        self.assertTrue(url_matches("https://premierstaff.com/blog/x",
                                    "https://premierstaff.com/blog/x/"))

    def test_a_different_page_does_not_match(self):
        self.assertFalse(url_matches("https://premierstaff.com/blog/other/",
                                     "https://premierstaff.com/blog/x/"))

    def test_a_different_host_does_not_match(self):
        self.assertFalse(url_matches("https://notpremierstaff.com/blog/x/",
                                     "https://premierstaff.com/blog/x/"))


class ParseTests(SimpleTestCase):
    def test_a_retrieved_page_is_reported_as_seen_not_cited(self):
        rows = parse_questions(_envelope([LIVE_ITEM]), "premierstaff.com")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["question"], "how many bartenders do you need for 50 guests?")
        self.assertTrue(row["retrieved"])
        self.assertFalse(row["cited"], "it was in search_results, not sources")
        # Stored canonical — no tracking parameter, no trailing slash. Canonical rather than
        # verbatim on purpose: the same page arrives with and without the slash across
        # `sources` and `search_results`, and storing both spellings would list one page twice.
        # It still resolves when clicked.
        self.assertEqual(row["our_url"],
                         "https://premierstaff.com/blog/shorts/how-many-bartenders-for-an-event")

    def test_a_cited_page_is_reported_as_cited(self):
        row = parse_questions(_envelope([CITED_ITEM]), "premierstaff.com")[0]
        self.assertTrue(row["cited"])
        self.assertEqual(row["our_url"], "https://premierstaff.com/services")

    def test_the_tracking_parameter_is_stripped_from_the_stored_url(self):
        row = parse_questions(_envelope([LIVE_ITEM]), "premierstaff.com")[0]
        self.assertNotIn("utm_source", row["our_url"])

    def test_a_question_where_we_appear_nowhere_is_dropped(self):
        other = {**LIVE_ITEM, "sources": [], "search_results": [
            {"domain": "rival.com", "url": "https://rival.com/x"}]}
        self.assertEqual(parse_questions(_envelope([other]), "premierstaff.com"), [])

    def test_volume_and_trend_and_dates_survive(self):
        row = parse_questions(_envelope([LIVE_ITEM]), "premierstaff.com")[0]
        self.assertEqual(row["ai_search_volume"], 82)
        self.assertEqual(row["monthly_searches"]["2026-07"], 82)
        self.assertEqual(row["first_response_at"], "2025-11-05 19:28:34 +00:00")
        self.assertEqual(row["fan_out_queries"], ["bartender to guest ratio events 50 guests"])

    def test_filtering_to_one_page_keeps_only_that_page_s_questions(self):
        rows = parse_questions(
            _envelope([LIVE_ITEM, CITED_ITEM]), "premierstaff.com",
            page_url="https://premierstaff.com/blog/shorts/how-many-bartenders-for-an-event/")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["question"], "how many bartenders do you need for 50 guests?")

    def test_no_page_filter_returns_every_question_for_the_domain(self):
        self.assertEqual(len(parse_questions(_envelope([LIVE_ITEM, CITED_ITEM]),
                                             "premierstaff.com")), 2)

    def test_an_empty_or_malformed_envelope_is_not_fatal(self):
        for junk in ({}, {"tasks": []}, {"tasks": [{"result": []}]}, {"tasks": [{"result": None}]}):
            self.assertEqual(parse_questions(junk, "premierstaff.com"), [])

    def test_a_missing_ai_search_volume_stays_unknown_rather_than_zero(self):
        row = parse_questions(_envelope([{**LIVE_ITEM, "ai_search_volume": None}]),
                              "premierstaff.com")[0]
        self.assertIsNone(row["ai_search_volume"])

    def test_rows_come_back_most_asked_first(self):
        rows = parse_questions(_envelope([CITED_ITEM, LIVE_ITEM]), "premierstaff.com")
        self.assertEqual([r["ai_search_volume"] for r in rows], [82, 12])


class FetchTests(SimpleTestCase):
    """The HTTP shape: a path in the target is the caller's error to avoid, not the API's."""

    def test_the_request_sends_a_bare_domain_even_when_given_a_deep_url(self):
        from pipeline.connectors.dataforseo_llm_questions import fetch_llm_questions

        with mock.patch("pipeline.connectors.dataforseo_llm_questions.requests.post") as post:
            post.return_value = mock.Mock(
                raise_for_status=mock.Mock(return_value=None),
                json=mock.Mock(return_value=_envelope([LIVE_ITEM])))
            with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l",
                                                "DATAFORSEO_PASSWORD": "p"}):
                fetch_llm_questions(
                    "https://premierstaff.com/blog/shorts/how-many-bartenders-for-an-event/")

            sent = post.call_args.kwargs["json"][0]
            self.assertEqual(sent["target"][0]["domain"], "premierstaff.com",
                             "a path here is a hard 40501 from DataForSEO")

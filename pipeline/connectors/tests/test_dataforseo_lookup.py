"""Tests for DataForSEOKeywordsConnector.lookup_keywords — the read-only ad-hoc
Keyword Explorer path. The live API is never hit; requests.post is mocked."""
import unittest
from unittest.mock import patch, MagicMock

from pipeline.connectors.dataforseo_keywords import DataForSEOKeywordsConnector


def _overview_response(items):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"tasks": [{"result": [{"items": items}]}]}
    return resp


def _connector():
    c = DataForSEOKeywordsConnector()
    # Force credentials so lookup doesn't short-circuit on missing creds.
    c.login, c.password = "user", "pass"
    c.auth = ("user", "pass")
    return c


SAMPLE_ITEM = {
    "keyword": "seo agency",
    "keyword_info": {"search_volume": 1000, "cpc": 12.5, "competition": 0.8, "competition_level": "HIGH"},
    "keyword_properties": {"keyword_difficulty": 45},
    "search_intent_info": {"main_intent": "commercial"},
    "serp_info": {"serp_item_types": ["organic", "people_also_ask"]},
}


class LookupKeywordsTests(unittest.TestCase):
    @patch("pipeline.connectors.dataforseo_keywords.requests.post")
    def test_parses_all_eight_columns(self, mock_post):
        mock_post.return_value = _overview_response([SAMPLE_ITEM])
        result = _connector().lookup_keywords(["seo agency"], "United States")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["rows"]), 1)
        row = result["rows"][0]
        self.assertEqual(row["keyword"], "seo agency")
        self.assertEqual(row["search_volume"], 1000)
        self.assertEqual(row["keyword_difficulty"], 45)
        self.assertEqual(row["cpc"], 12.5)
        self.assertEqual(row["competition"], "HIGH")
        self.assertEqual(row["intent"], "Commercial")
        self.assertEqual(row["serp_features"], "organic, people_also_ask")
        self.assertEqual(row["location"], "United States")

    @patch("pipeline.connectors.dataforseo_keywords.requests.post")
    def test_missing_nested_keys_are_safe(self, mock_post):
        mock_post.return_value = _overview_response([{"keyword": "bare keyword"}])
        result = _connector().lookup_keywords(["bare keyword"])
        row = result["rows"][0]
        self.assertEqual(row["keyword"], "bare keyword")
        self.assertIsNone(row["search_volume"])
        self.assertIsNone(row["keyword_difficulty"])
        self.assertIsNone(row["intent"])
        self.assertEqual(row["serp_features"], "")

    @patch("pipeline.connectors.dataforseo_keywords.requests.post")
    def test_keywords_without_data_go_to_no_data(self, mock_post):
        # API returns data only for "seo agency"; the other two are reported as no_data.
        mock_post.return_value = _overview_response([SAMPLE_ITEM])
        result = _connector().lookup_keywords(["seo agency", "missing one", "missing two"])
        self.assertEqual(len(result["rows"]), 1)
        self.assertCountEqual(result["no_data"], ["missing one", "missing two"])

    @patch("pipeline.connectors.dataforseo_keywords.requests.post")
    def test_input_is_trimmed_and_deduped(self, mock_post):
        mock_post.return_value = _overview_response([SAMPLE_ITEM])
        _connector().lookup_keywords([" seo agency ", "SEO AGENCY", "", "  "])
        sent = mock_post.call_args.kwargs["json"][0]["keywords"]
        self.assertEqual(sent, ["seo agency"])  # trimmed, case-deduped, blanks dropped

    def test_empty_input_returns_error_without_calling_api(self):
        with patch("pipeline.connectors.dataforseo_keywords.requests.post") as mock_post:
            result = _connector().lookup_keywords(["", "   "])
            self.assertEqual(result["status"], "error")
            mock_post.assert_not_called()

    def test_missing_credentials_returns_error(self):
        c = DataForSEOKeywordsConnector()
        c.login, c.password = None, None
        result = c.lookup_keywords(["seo agency"])
        self.assertEqual(result["status"], "error")
        self.assertIn("credentials", result["error"].lower())

    @patch("pipeline.connectors.dataforseo_keywords.requests.post")
    def test_api_failure_degrades_gracefully(self, mock_post):
        mock_post.side_effect = RuntimeError("network down")
        result = _connector().lookup_keywords(["seo agency"])
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["rows"], [])
        self.assertIn("seo agency", result["no_data"])

    @patch("pipeline.connectors.dataforseo_keywords.requests.post")
    def test_competition_falls_back_to_numeric_when_no_level(self, mock_post):
        item = dict(SAMPLE_ITEM)
        item["keyword_info"] = {"search_volume": 10, "competition": 0.5}  # no competition_level
        mock_post.return_value = _overview_response([item])
        row = _connector().lookup_keywords(["seo agency"])["rows"][0]
        self.assertEqual(row["competition"], "0.5")


if __name__ == "__main__":
    unittest.main()

"""The keyword fields we already pay for and were discarding.

`dataforseo_labs/google/ranked_keywords/live` returns roughly forty fields per keyword. The
parser kept seven and dropped the rest on the floor — including keyword difficulty, the
12-month search trend, rank movement and featured-snippet wins, all of which arrive in the
same billed response. Keeping them costs nothing: no extra call, no extra row, no extra cent.

The fixture below is trimmed from the real envelope this endpoint returns, not from
documentation — a fixture built from a tool's rendering of a response is how three parsers in
this codebase came to read a nesting level that does not exist (skills.md §9).
"""
from django.test import SimpleTestCase

from pipeline.connectors.dataforseo_domain_overview import parse_keyword_item, parse_metrics

ITEM = {
    "keyword_data": {
        "keyword": "event staffing agency",
        "keyword_info": {
            "search_volume": 2400,
            "cpc": 8.42,
            "competition": 0.61,
            "competition_level": "MEDIUM",
            "monthly_searches": [
                {"year": 2026, "month": 7, "search_volume": 2400},
                {"year": 2026, "month": 6, "search_volume": 1900},
            ],
        },
        "keyword_properties": {"keyword_difficulty": 47},
        "search_intent_info": {"main_intent": "commercial"},
    },
    "ranked_serp_element": {
        "serp_item": {
            "rank_group": 4,
            "rank_absolute": 5,
            "url": "https://premierstaff.com/services",
            "title": "Event Staffing Agency",
            "etv": 312.5,
            "is_featured_snippet": True,
            "rank_changes": {"is_new": False, "is_up": True, "is_down": False, "is_lost": False},
        }
    },
}


class KeywordFieldTests(SimpleTestCase):
    def test_the_seven_fields_that_already_worked_still_do(self):
        row = parse_keyword_item(ITEM)
        self.assertEqual(row["keyword"], "event staffing agency")
        self.assertEqual(row["intent"], "Commercial")
        self.assertEqual(row["position"], 4)
        self.assertEqual(row["volume"], 2400)
        self.assertEqual(row["cpc"], 8.42)
        self.assertEqual(row["traffic"], 312.5)
        self.assertEqual(row["url"], "https://premierstaff.com/services")

    def test_keyword_difficulty_survives(self):
        self.assertEqual(parse_keyword_item(ITEM)["kd"], 47)

    def test_an_absent_difficulty_is_unknown_not_easy(self):
        """0 would render green and read as "trivial to rank for"."""
        item = {**ITEM, "keyword_data": {**ITEM["keyword_data"], "keyword_properties": {}}}
        self.assertIsNone(parse_keyword_item(item)["kd"])

    def test_the_twelve_month_trend_survives_newest_last(self):
        row = parse_keyword_item(ITEM)
        self.assertEqual(row["monthly"], [1900, 2400],
                         "oldest first, so a sparkline reads left to right")

    def test_an_absent_trend_is_an_empty_list(self):
        item = {**ITEM, "keyword_data": {**ITEM["keyword_data"],
                                         "keyword_info": {"search_volume": 10}}}
        self.assertEqual(parse_keyword_item(item)["monthly"], [])

    def test_rank_movement_is_reported(self):
        self.assertEqual(parse_keyword_item(ITEM)["movement"], "up")

    def test_movement_is_unknown_when_the_api_did_not_say(self):
        item = {**ITEM, "ranked_serp_element": {"serp_item": {"rank_group": 4}}}
        self.assertIsNone(parse_keyword_item(item)["movement"],
                          "flat and unknown are different; do not invent 'flat'")

    def test_each_movement_flag_maps_to_its_own_word(self):
        for flag, word in (("is_new", "new"), ("is_up", "up"),
                           ("is_down", "down"), ("is_lost", "lost")):
            item = {**ITEM, "ranked_serp_element": {
                "serp_item": {"rank_group": 4, "rank_changes": {flag: True}}}}
            self.assertEqual(parse_keyword_item(item)["movement"], word)

    def test_a_featured_snippet_win_is_reported(self):
        self.assertTrue(parse_keyword_item(ITEM)["featuredSnippet"])

    def test_competition_level_and_absolute_rank_survive(self):
        row = parse_keyword_item(ITEM)
        self.assertEqual(row["competition"], "MEDIUM")
        self.assertEqual(row["rankAbsolute"], 5)

    def test_the_serp_title_survives(self):
        self.assertEqual(parse_keyword_item(ITEM)["title"], "Event Staffing Agency")


class MetricsTests(SimpleTestCase):
    """`metrics.organic` carries a full position distribution; three of sixteen were read."""

    RAW = {"organic": {
        "etv": 1200.0, "count": 380, "estimated_paid_traffic_cost": 5400.0,
        "pos_1": 4, "pos_2_3": 9, "pos_4_10": 42, "pos_11_20": 60, "pos_21_30": 55,
        "pos_31_40": 40, "pos_41_50": 30, "pos_51_60": 25, "pos_61_70": 20,
        "pos_71_80": 15, "pos_81_90": 10, "pos_91_100": 5,
        "is_new": 12, "is_up": 30, "is_down": 18, "is_lost": 6,
    }}

    def test_the_three_headline_numbers_are_unchanged(self):
        m = parse_metrics(self.RAW)
        self.assertEqual(m["organic_traffic"], 1200.0)
        self.assertEqual(m["traffic_value"], 5400.0)
        self.assertEqual(m["ranked_keywords"], 380)

    def test_the_position_distribution_survives(self):
        dist = parse_metrics(self.RAW)["distribution"]
        self.assertEqual(dist["pos_1"], 4)
        self.assertEqual(dist["pos_4_10"], 42)
        self.assertEqual(dist["pos_91_100"], 5)

    def test_the_movement_totals_survive(self):
        moved = parse_metrics(self.RAW)["movement"]
        self.assertEqual(moved["new"], 12)
        self.assertEqual(moved["up"], 30)
        self.assertEqual(moved["down"], 18)
        self.assertEqual(moved["lost"], 6)

    def test_an_empty_metrics_block_yields_zeros_not_a_crash(self):
        m = parse_metrics({})
        self.assertEqual(m["organic_traffic"], 0)
        self.assertEqual(m["distribution"], {})

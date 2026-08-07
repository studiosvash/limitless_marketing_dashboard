"""The location a SERP is measured in must be the PROJECT's, and must reach both the API and
the stored row.

These are regression tests for a bug that survived several attempted fixes because every one of
them was made in the frontend. The actual defects were:

  1. Both SERP connectors posted a literal `location_name="United States"` and never read
     `sites.location`, so a project configured for Las Vegas was measured against the national
     SERP. `pipeline/db/schema.py`'s Site model documented this ("NOT YET A SYNC PARAMETER").
  2. `keyword_rankings` had no `location` column and keyed on (date, site_id, keyword), so the
     several projects that share one `site_url` — Position Tracking registers a domain once per
     city — wrote into and read from a single set of rows.

Nothing here touches the network: `requests` is stubbed throughout.
"""
from datetime import date
from unittest import mock

from django.test import SimpleTestCase

from pipeline.connectors import dataforseo_serp as serp_mod
from pipeline.connectors import dataforseo_serp_competitors as comp_mod
from pipeline.connectors.dataforseo_live_serp import country_of, normalize_location_name


def _task_post_response(task_ids=("t1",)):
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"cost": 0.01,
                              "tasks": [{"id": tid} for tid in task_ids]}
    return resp


class CountryOfTests(SimpleTestCase):
    """DataForSEO Labs accepts country locations only; `country_of` is what keeps a
    city-configured project from sending one and getting `Invalid Field: 'location_name'`."""

    def test_country_only_value_is_unchanged(self):
        self.assertEqual(country_of("United States"), "United States")
        self.assertEqual(country_of("United Kingdom"), "United Kingdom")

    def test_spa_city_form_degrades_to_its_country(self):
        self.assertEqual(country_of("United States - New York, NY"), "United States")
        self.assertEqual(country_of("United States - Austin, TX"), "United States")

    def test_spa_state_form_degrades_to_its_country(self):
        self.assertEqual(country_of("United States - Texas"), "United States")

    def test_dataforseo_wire_form_degrades_to_its_country(self):
        self.assertEqual(country_of("Austin,Texas,United States"), "United States")

    def test_empty_falls_back_to_the_default(self):
        self.assertEqual(country_of(""), "United States")


class SerpConnectorLocationTests(SimpleTestCase):
    def setUp(self):
        with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l",
                                            "DATAFORSEO_PASSWORD": "p"}, clear=False):
            self.connector = serp_mod.DataForSEOSERPConnector()

    @mock.patch.object(serp_mod.requests, "post")
    def test_project_city_is_sent_to_the_api_in_dataforseo_form(self, post):
        post.return_value = _task_post_response()

        self.connector._submit_tasks(["event staffing"], "premierstaff.com",
                                     "United States - Las Vegas, NV")

        sent = post.call_args.kwargs["json"][0]
        # The SPA's dash form is rejected by the API outright -- it must arrive converted.
        self.assertEqual(sent["location_name"], "Las Vegas,Nevada,United States")
        self.assertEqual(sent["keyword"], "event staffing")

    @mock.patch.object(serp_mod.requests, "post")
    def test_default_location_still_posts_the_country(self, post):
        post.return_value = _task_post_response()
        self.connector._submit_tasks(["event staffing"], "premierstaff.com")
        self.assertEqual(post.call_args.kwargs["json"][0]["location_name"], "United States")

    def test_ranked_row_carries_the_location_it_was_measured_in(self):
        task_data = {
            "data": {"keyword": "event staffing"},
            "result": [{"items": [
                {"type": "organic", "rank_absolute": 3,
                 "url": "https://premierstaff.com/event-staffing-agency-nyc/"},
            ]}],
        }
        rows = self.connector._normalize_task(
            task_data, date(2026, 8, 6), "premierstaff.com", "premierstaff.com",
            "United States - New York, NY",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["location"], "United States - New York, NY")
        self.assertEqual(rows[0]["position"], 3)

    def test_not_ranking_row_also_carries_the_location(self):
        # A "checked, not in the top 30" row is a real measurement OF THAT CITY. Without the
        # stamp it would collide with another city's row for the same keyword and date.
        task_data = {"data": {"keyword": "event staffing"}, "result": [{"items": []}]}
        rows = self.connector._normalize_task(
            task_data, date(2026, 8, 6), "premierstaff.com", "premierstaff.com",
            "United States - Las Vegas, NV",
        )
        self.assertEqual(rows[0]["location"], "United States - Las Vegas, NV")
        self.assertIsNone(rows[0]["position"])

    def test_two_cities_produce_distinct_rows_for_one_keyword_and_date(self):
        """The upsert key is (date, site_id, keyword, location). Same domain, same day, same
        keyword, two cities => two rows, not one overwriting the other."""
        task_data = {
            "data": {"keyword": "event staffing"},
            "result": [{"items": [{"type": "organic", "rank_absolute": 3,
                                   "url": "https://premierstaff.com/"}]}],
        }
        ny = self.connector._normalize_task(task_data, date(2026, 8, 6), "premierstaff.com",
                                            "premierstaff.com", "United States - New York, NY")[0]
        lv = self.connector._normalize_task(task_data, date(2026, 8, 6), "premierstaff.com",
                                            "premierstaff.com", "United States - Las Vegas, NV")[0]
        key = lambda r: (r["date"], r["site_id"], r["keyword"], r["location"])
        self.assertNotEqual(key(ny), key(lv))


class SerpCompetitorsConnectorLocationTests(SimpleTestCase):
    def setUp(self):
        with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l",
                                            "DATAFORSEO_PASSWORD": "p"}, clear=False):
            self.connector = comp_mod.DataForSEOSerpCompetitorsConnector()

    @mock.patch.object(comp_mod.requests, "post")
    def test_project_city_is_sent_to_the_api(self, post):
        post.return_value = _task_post_response()
        self.connector._submit_tasks(["event staffing"], "United States - Miami, FL")
        self.assertEqual(post.call_args.kwargs["json"][0]["location_name"],
                         "Miami,Florida,United States")

    def test_competitor_row_carries_the_location(self):
        task_data = {
            "data": {"keyword": "event staffing"},
            "result": [{"items": [
                {"type": "organic", "rank_absolute": 2, "domain": "eventstaff.com",
                 "url": "https://eventstaff.com/nyc"},
            ]}],
        }
        rows = self.connector._normalize_task(
            task_data, date(2026, 8, 6), {"eventstaff.com"}, "premierstaff.com",
            "United States - New York, NY",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["location"], "United States - New York, NY")
        self.assertEqual(rows[0]["competitor_domain"], "eventstaff.com")


class NormalizeLocationNameTests(SimpleTestCase):
    """Guards the conversion the connectors now depend on for city tracking to work at all."""

    def test_spa_city_form(self):
        self.assertEqual(normalize_location_name("United States - Austin, TX"),
                         "Austin,Texas,United States")

    def test_already_correct_value_is_untouched(self):
        self.assertEqual(normalize_location_name("Texas,United States"), "Texas,United States")

    def test_empty_falls_back_to_the_default(self):
        self.assertEqual(normalize_location_name(""), "United States")

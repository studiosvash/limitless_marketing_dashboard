"""`"items": null` is a real DataForSEO answer, and `.get("items", [])` does not survive it.

Reported live: analysing a blog post that has no backlinks of its own put a Python TypeError
on screen —

    DataForSEO could not return backlinks for this target: object of type 'NoneType' has no len()

A default in `.get(key, default)` applies only when the KEY IS ABSENT. DataForSEO sends the key
with an explicit null for a target it has nothing for, so `.get("items", [])` returns None,
`len(None)` raises, and the exception surfaces as if the API had failed.

`or []` is the fix, and it is the shape every parser in this codebase should use for a list it
did not create.
"""
from unittest import mock

from django.test import SimpleTestCase


def _envelope(items):
    return {"tasks": [{"status_code": 20000, "result": [{"items": items, "total_count": None}]}]}


class NullItemsTests(SimpleTestCase):
    def setUp(self):
        patcher = mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l",
                                                 "DATAFORSEO_PASSWORD": "p"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _backlinks(self, payload):
        from pipeline.connectors.dataforseo_backlinks import DataForSEOBacklinksConnector
        conn = DataForSEOBacklinksConnector.__new__(DataForSEOBacklinksConnector)
        conn.login, conn.password, conn.auth = "l", "p", ("l", "p")
        import logging
        conn.logger = logging.getLogger("test")
        with mock.patch("pipeline.connectors.dataforseo_backlinks.requests.post") as post:
            post.return_value = mock.Mock(raise_for_status=mock.Mock(return_value=None),
                                          json=mock.Mock(return_value=payload))
            return conn.fetch(site_id="premierstaff.com/blog/x")

    def test_a_null_items_list_is_an_empty_result_not_a_crash(self):
        """The exact live failure: a page with no backlinks of its own."""
        self.assertEqual(self._backlinks(_envelope(None)), [])

    def test_an_absent_items_key_still_works(self):
        payload = {"tasks": [{"status_code": 20000, "result": [{"total_count": None}]}]}
        self.assertEqual(self._backlinks(payload), [])

    def test_a_null_result_is_an_empty_result(self):
        payload = {"tasks": [{"status_code": 20000, "result": None}]}
        self.assertEqual(self._backlinks(payload), [])

    def test_a_null_tasks_list_is_an_empty_result(self):
        self.assertEqual(self._backlinks({"tasks": None}), [])

    def test_real_items_still_come_through(self):
        rows = self._backlinks(_envelope([{"url_from": "https://a.com/p",
                                           "domain_from": "a.com",
                                           "url_to": "https://premierstaff.com/blog/x"}]))
        self.assertEqual(len(rows), 1)

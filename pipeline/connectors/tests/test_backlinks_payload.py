"""What the Backlinks connector actually ASKS DataForSEO for.

Every assertion here is on the request payload, because that is where two silent
product bugs lived and neither was visible from the response-parsing side:

  * `filters: [["dofollow", "=", True]]` was hardcoded, so the stored profile was
    dofollow-only. The Backlinks page has a "Nofollow" filter chip and the referring-domain
    rollup has a Follow column, and both could only ever render the dofollow half of reality
    -- the chip's empty state was structural, not a property of any site's link profile.
  * `mode` was unset. DataForSEO's default is `as_is` (all backlinks), but the other two
    values are `one_per_domain` and `one_per_anchor`, and `one_per_domain` would have handed
    back exactly one row per referring domain -- which would defeat the per-source-page unique
    key entirely while looking like a healthy sync. It is now sent explicitly, so the answer
    does not depend on a remote default nobody here controls.

`requests.post` is replaced with a stub that RECORDS the payload; a test that forgets to stub
it would make a real, billed call, which is why the connector-test convention (see
test_dataforseo_expand.py) is to patch it in setUp rather than per-test.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from pipeline.connectors.dataforseo_backlinks import DataForSEOBacklinksConnector


def _response(items):
    resp = MagicMock()
    resp.json.return_value = {
        "cost": 0.02,
        "tasks": [{"status_code": 20000, "cost": 0.02,
                   "result": [{"total": len(items), "items": items}]}],
    }
    resp.raise_for_status.return_value = None
    return resp


def _item(**kw):
    base = {
        "domain_from": "blog.com",
        "url_from": "https://blog.com/post",
        "url_to": "https://a.com/",
        "anchor": "click",
        "dofollow": True,
        "domain_from_rank": 500,
        "page_from_rank": 300,
        "backlink_spam_score": 12,
        "first_seen": "2026-01-01 00:00:00 +00:00",
        "last_seen": "2026-08-01 00:00:00 +00:00",
        "is_lost": False,
    }
    base.update(kw)
    return base


class BacklinksPayloadTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p",
                                      "DATAFORSEO_TARGET_DOMAIN": "a.com"})
        env.start()
        self.addCleanup(env.stop)
        # record_cost appends a connector_costs row through a real analytics session. A unit
        # test has no business writing to the developer's fusehealth.db.
        cost = patch("pipeline.connectors.dataforseo_backlinks.record_cost")
        cost.start()
        self.addCleanup(cost.stop)
        self.post = patch("pipeline.connectors.dataforseo_backlinks.requests.post").start()
        self.addCleanup(patch.stopall)
        self.post.return_value = _response([_item()])

    def _fetch(self, **kw):
        c = DataForSEOBacklinksConnector()
        records = c.fetch(site_id="a.com", **kw)
        return self.post.call_args.kwargs["json"][0], records

    def test_the_sync_no_longer_filters_nofollow_away(self):
        payload, _ = self._fetch()
        self.assertNotIn("filters", payload)

    def test_mode_is_stated_explicitly_as_as_is(self):
        """`one_per_domain` would return one row per referring domain, which is precisely the
        collapse the per-source-page unique key was introduced to stop."""
        payload, _ = self._fetch()
        self.assertEqual(payload["mode"], "as_is")

    def test_a_caller_can_still_ask_for_dofollow_only(self):
        payload, _ = self._fetch(dofollow_only=True)
        self.assertEqual(payload["filters"], [["dofollow", "=", True]])

    def test_the_requested_limit_is_what_gets_sent(self):
        payload, _ = self._fetch(limit=250)
        self.assertEqual(payload["limit"], 250)

    def test_a_nofollow_link_is_stored_as_a_nofollow_link(self):
        """The flag was already parsed correctly -- it just never had a nofollow row to parse."""
        self.post.return_value = _response([
            _item(dofollow=True, url_from="https://blog.com/a"),
            _item(dofollow=False, url_from="https://blog.com/b"),
        ])
        _, records = self._fetch()
        self.assertEqual([r["dofollow"] for r in records], [1, 0])

    def test_two_pages_of_one_domain_are_two_records(self):
        self.post.return_value = _response([
            _item(url_from="https://blog.com/a"),
            _item(url_from="https://blog.com/b"),
        ])
        _, records = self._fetch()
        self.assertEqual([r["url_from"] for r in records],
                         ["https://blog.com/a", "https://blog.com/b"])

    def test_a_missing_url_from_becomes_empty_string_not_none(self):
        """`url_from` is part of the upsert key; a None there bypasses ON CONFLICT on Postgres
        and duplicates the row on every sync (skills.md section 9)."""
        self.post.return_value = _response([_item(url_from=None)])
        _, records = self._fetch()
        self.assertEqual(records[0]["url_from"], "")


if __name__ == "__main__":
    unittest.main()

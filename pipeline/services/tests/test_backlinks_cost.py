"""The Backlinks aggregate calls must book what they spend.

`pipeline/services/backlinks_service._post` is the single request helper behind
`backlinks/summary/live`, `referring_domains/live`, `anchors/live` and `history/live`. It
never called `record_cost`, so four billed DataForSEO endpoints were completely invisible to
Settings -> Usage & Budget, and to the budget notifications that read the same rows.

Written as unittest TestCases on purpose: the sibling module in this package is five bare
pytest functions, pytest is not installed here, and `manage.py test` collects TestCase
subclasses only -- so those tests have never run (skills.md 9). No test here touches the
network; `requests.post` is replaced outright.
"""
from unittest.mock import patch

from django.test import TestCase

from pipeline.services import backlinks_service as bl


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _envelope(items=None, cost=0.02, extra=None):
    result = {"items": items if items is not None else []}
    result.update(extra or {})
    return {"cost": cost, "tasks": [{"cost": cost, "status_code": 20000, "result": [result]}]}


class BacklinksPostCostTests(TestCase):
    def test_post_records_the_charge_the_response_reports(self):
        recorded = []
        with patch.object(bl.requests, "post", return_value=FakeResponse(_envelope(cost=0.032))), \
             patch.object(bl, "record_cost", side_effect=lambda *a, **kw: recorded.append((a, kw))):
            bl._post("summary/live", {"target": "example.com"}, site_id="example.com")

        self.assertEqual(len(recorded), 1, "the summary call booked nothing")
        args, kwargs = recorded[0]
        self.assertTrue(args[0].startswith("dataforseo"),
                        "connector name must carry the dataforseo prefix the budget check reads")
        self.assertEqual(args[1], "example.com")   # attributed to the site that asked
        self.assertAlmostEqual(args[2], 0.032)
        self.assertIn("summary/live", kwargs.get("notes", ""))

    def test_a_failed_call_still_books_what_it_cost(self):
        """The request is billed by the time the envelope is parsed. An empty or errored
        task must not swallow the charge."""
        recorded = []
        broken = {"cost": 0.011, "tasks": [{"cost": 0.011, "status_code": 40501, "result": None}]}
        with patch.object(bl.requests, "post", return_value=FakeResponse(broken)), \
             patch.object(bl, "record_cost", side_effect=lambda *a, **kw: recorded.append((a, kw))):
            out = bl._post("anchors/live", {"target": "example.com"})

        self.assertEqual(out, {})
        self.assertEqual(len(recorded), 1)
        self.assertAlmostEqual(recorded[0][0][2], 0.011)

    def test_units_are_none_not_zero(self):
        """Four endpoints meter four different things under one connector name, so there is
        no single denominator. None says 'we do not know the rate'; 0 would claim we measured
        one and found nothing."""
        recorded = []
        with patch.object(bl.requests, "post",
                          return_value=FakeResponse(_envelope(items=[{"anchor": "a"}]))), \
             patch.object(bl, "record_cost", side_effect=lambda *a, **kw: recorded.append((a, kw))):
            bl._post("anchors/live", {"target": "example.com"})

        self.assertIsNone(recorded[0][1].get("units"))

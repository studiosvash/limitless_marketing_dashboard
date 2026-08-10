"""Zero and unknown are different facts, on the Keyword Explorer path too.

The tracked-keywords path has always been honest: `to_api_keyword` passes
`row.get("search_volume")` straight through and the SPA renders `null` as an em dash. The
Keyword Explorer path coerced unknown to `0` in three places on the way to the same table, so
a keyword DataForSEO has no volume data for was ASSERTED on screen as a keyword nobody
searches for — and, worse, the volume-min filter then hid it as if that were a measurement.
"""
from django.test import SimpleTestCase

from apps.dashboard.services.keyword_research_service import _enrich_expanded_row, _to_spa_row


class ExplorerRowVolumeTests(SimpleTestCase):
    def test_expanded_row_keeps_unknown_volume_null(self):
        row = _enrich_expanded_row({"kw": "brand new phrase", "volume": None}, set())
        self.assertIsNone(row["volume"])

    def test_expanded_row_keeps_a_real_zero(self):
        row = _enrich_expanded_row({"kw": "nobody searches this", "volume": 0}, set())
        self.assertEqual(row["volume"], 0)

    def test_exact_lookup_row_keeps_unknown_volume_null(self):
        row = _to_spa_row({"keyword": "brand new phrase", "search_volume": None}, set())
        self.assertIsNone(row["volume"])

    def test_exact_lookup_row_keeps_a_real_zero(self):
        row = _to_spa_row({"keyword": "nobody searches this", "search_volume": 0}, set())
        self.assertEqual(row["volume"], 0)



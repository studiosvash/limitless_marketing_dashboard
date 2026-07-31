"""Keyword normalisation on the save path.

Found in production data: all 16 `saved_keywords` rows for one project were stored as
`"festival staffing,"`, `"arena ushering staff,"` — every one carrying a trailing comma from a
pasted comma-separated list that was split on newlines only. `_clean_row` called `.strip()`,
which removes whitespace but not punctuation, so the comma reached DataForSEO inside the
queried phrase and 11 of the 16 came back with `ai_search_volume = 0`. The keyword was simply
not the keyword anyone meant to track — and each one still cost money to look up.

Only LEADING/TRAILING separators are stripped. A comma inside a phrase ("austin, tx event
staff") is a real keyword and must survive.
"""
from django.test import SimpleTestCase

from pipeline.services.saved_keyword_service import _clean_row


class CleanRowKeywordNormalisationTests(SimpleTestCase):
    def test_strips_a_trailing_comma(self):
        self.assertEqual(_clean_row({"keyword": "festival staffing,"}, None)["keyword"],
                         "festival staffing")

    def test_strips_a_leading_comma_and_surrounding_whitespace(self):
        self.assertEqual(_clean_row({"keyword": "  , brand ambassador agency ,  "}, None)["keyword"],
                         "brand ambassador agency")

    def test_keeps_a_comma_inside_the_phrase(self):
        self.assertEqual(_clean_row({"keyword": "austin, tx event staff"}, None)["keyword"],
                         "austin, tx event staff")

    def test_strips_a_trailing_semicolon_too(self):
        self.assertEqual(_clean_row({"keyword": "crowd management;"}, None)["keyword"],
                         "crowd management")

    def test_a_keyword_that_is_only_separators_is_rejected(self):
        # Would otherwise become an empty keyword that still costs a metered lookup.
        self.assertIsNone(_clean_row({"keyword": " , ; "}, None))

    def test_missing_keyword_is_still_rejected(self):
        self.assertIsNone(_clean_row({"keyword": ""}, None))
        self.assertIsNone(_clean_row({}, None))

    def test_normalisation_does_not_disturb_the_other_fields(self):
        rec = _clean_row(
            {"keyword": "event staffing,", "location": "United States", "search_volume": "1200"},
            None,
        )
        self.assertEqual(rec["keyword"], "event staffing")
        self.assertEqual(rec["location"], "United States")
        self.assertEqual(rec["search_volume"], 1200)

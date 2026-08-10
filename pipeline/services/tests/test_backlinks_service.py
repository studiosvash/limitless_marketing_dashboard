"""Unit tests for the Backlinks service's pure shaping helpers (no live HTTP).

THIS MODULE HAD NEVER RUN. Every test below was a bare `def test_*()` pytest function, and
pytest is not installed in this project -- `python manage.py test` uses unittest, which
collects `TestCase` subclasses only, so `manage.py test
pipeline.services.tests.test_backlinks_service` printed "Found 0 test(s)" and passed. That is
the same rot found in `test_dataforseo_expand.py` (skills.md section 9), where the module that
never ran was also hiding a real failure. A green suite that collected zero tests looks
identical to a green suite that passed: a new test must be a `TestCase`, and it must be RUN
once before anyone trusts it.

Run once converted, these assertions all held.
"""
import unittest

from pipeline.services import backlinks_service as bl


class AuthorityScaleTests(unittest.TestCase):
    def test_as_scales_1000_to_100_and_clamps(self):
        """DataForSEO ranks are 0-1000; every "AS" surface in the UI is a 0-100 scale."""
        self.assertEqual(bl._as(1000), 100)
        self.assertEqual(bl._as(100), 10)
        self.assertEqual(bl._as(0), 0)
        self.assertEqual(bl._as(None), 0)
        self.assertEqual(bl._as("bad"), 0)
        self.assertEqual(bl._as(5000), 100)


class AnchorClassificationTests(unittest.TestCase):
    def test_classify_anchor(self):
        self.assertEqual(bl._classify_anchor("", "fusehealth"), "Empty")
        self.assertEqual(bl._classify_anchor("fusehealth.com", "fusehealth"), "Branded")
        self.assertEqual(bl._classify_anchor("click here", "fusehealth"), "Generic")
        self.assertEqual(bl._classify_anchor("best iv therapy clinic", "fusehealth"), "Keyword")


class DomainCleaningTests(unittest.TestCase):
    def test_clean_domain_strips_scheme_and_scdomain(self):
        self.assertEqual(bl._clean_domain("https://fusehealth.com/"), "fusehealth.com")
        self.assertEqual(bl._clean_domain("sc-domain:fusehealth.com"), "fusehealth.com")


class EmptyPayloadTests(unittest.TestCase):
    def test_empty_payload_has_all_keys(self):
        """The SPA reads every one of these keys unconditionally; a missing one is a render
        crash, not a blank card."""
        p = bl.empty_backlinks_payload()
        for key in ("summary", "months", "types", "asBuckets", "anchors", "refDomains",
                    "links", "competitors", "gapDomains"):
            self.assertIn(key, p)
        self.assertEqual(p["summary"]["backlinks"], 0)


if __name__ == "__main__":
    unittest.main()

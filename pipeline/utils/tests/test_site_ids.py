"""One site, several spellings — the join key is a string, so every spelling must resolve.

The bug these tests exist for: `sites.site_url` for a project was `premierstaff.com`, but
`dataforseo_ai_keywords` had written its 16 `ai_keyword_data` rows under
`https://premierstaff.com/`, and `saved_keywords` was split across BOTH (24 rows / 16 rows).
The old two-line helper only knew the `sc-domain:` prefix, so the AI Optimization page looked
up `premierstaff.com`, matched neither URL-shaped key, and rendered an empty page over data
that was sitting right there.
"""
from django.test import SimpleTestCase

from pipeline.utils.site_ids import canonical_domain, resolve_site_ids


class CanonicalDomainTests(SimpleTestCase):
    def test_strips_scheme_trailing_slash_and_sc_domain_prefix(self):
        for raw in [
            "premierstaff.com",
            "https://premierstaff.com/",
            "https://premierstaff.com",
            "http://premierstaff.com/",
            "sc-domain:premierstaff.com",
            "  HTTPS://PremierStaff.com/  ",
        ]:
            self.assertEqual(canonical_domain(raw), "premierstaff.com", raw)

    def test_keeps_www_distinct_but_normalises_the_rest(self):
        # www.x.com and x.com are different hosts to Search Console, so they are NOT merged.
        self.assertEqual(canonical_domain("https://www.premierstaff.com/"), "www.premierstaff.com")

    def test_drops_a_path_because_the_join_key_is_a_host(self):
        self.assertEqual(canonical_domain("https://premierstaff.com/careers"), "premierstaff.com")

    def test_empty_input_is_empty(self):
        self.assertEqual(canonical_domain(""), "")
        self.assertEqual(canonical_domain(None), "")


class ResolveSiteIdsTests(SimpleTestCase):
    def test_bare_domain_also_matches_the_url_and_sc_domain_spellings(self):
        got = resolve_site_ids("premierstaff.com")
        for expected in [
            "premierstaff.com",
            "sc-domain:premierstaff.com",
            "https://premierstaff.com/",
            "https://premierstaff.com",
            "http://premierstaff.com/",
            "http://premierstaff.com",
        ]:
            self.assertIn(expected, got)

    def test_url_form_also_matches_the_bare_and_sc_domain_spellings(self):
        got = resolve_site_ids("https://premierstaff.com/")
        self.assertIn("premierstaff.com", got)
        self.assertIn("sc-domain:premierstaff.com", got)

    def test_sc_domain_form_still_matches_the_bare_spelling(self):
        # The behaviour the old helper had — it must not regress.
        got = resolve_site_ids("sc-domain:fusehealth.com")
        self.assertIn("sc-domain:fusehealth.com", got)
        self.assertIn("fusehealth.com", got)

    def test_the_exact_input_is_always_first(self):
        # Callers pass this straight to `.in_(...)`; an exact match must never be reordered away.
        self.assertEqual(resolve_site_ids("https://premierstaff.com/")[0], "https://premierstaff.com/")

    def test_no_duplicates(self):
        got = resolve_site_ids("premierstaff.com")
        self.assertEqual(len(got), len(set(got)))

    def test_empty_input_yields_nothing_to_match(self):
        # `.in_([])` is a valid empty result; `.in_([""])` would be a silent full-table miss.
        self.assertEqual(resolve_site_ids(""), [])

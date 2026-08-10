"""A domain that is a real CITED SOURCE is visible, even when the prose never names it.

Reported from the live dashboard: Perplexity answered "How many bartenders do you need for 50
guests?" citing premierstaff.com among its sources, and the Answer Inspector said "You are not
mentioned in this answer" — the grid and the Overview agreed with it.

The chain: `analyze_answer` scored the answer from its TEXT only, and `check_prompt` attached
the provider's citations AFTERWARDS (`analysis["citations"] = citations`) without ever
reconsidering the verdict. So an answer whose prose never spells the brand but whose sources
link straight to it scored "absent".

That is backwards. Being an actual source an answer engine drew on is the STRONGEST form of AI
visibility available -- stronger than being name-dropped in a sentence -- and it was the one
form the page could not see.

Matching is on the citation URL's HOST, not a substring of it: `premierstaff.com` must not be
found inside `notpremierstaff.com`, and a real subdomain (`blog.premierstaff.com`) must be.
"""
from django.test import SimpleTestCase

from pipeline.services.ai_visibility_service import analyze_answer

BRAND = "Premierstaff"
ALIASES = ["premierstaff.com"]          # what _target_for_run now appends automatically

# The real answer from the report -- note it never writes the brand anywhere.
ANSWER = (
    "For 50 guests, a good starting point is 1 bartender.[1][2][3]\n\n"
    "If the bar is cocktail-heavy, the venue is compressed, or everyone will order at once, "
    "some event guides recommend 2 bartenders for smoother service.[1][4][8]\n\n"
    "If you want, I can also give you a quick recommendation based on whether you're serving "
    "beer/wine only or a full bar."
)

CITATIONS = [
    {"title": "How Many Bartenders Do You Need? Staffing Guide", "url": "https://makeitadoublellc.com/guide"},
    {"title": "How Many Bartenders Do I Need? Guest Count Guide", "url": "https://platinumbartender.com/x"},
    {"title": "Event Staffing Ratios", "url": "https://www.premierstaff.com/blog/bartender-ratios"},
]


class CitationVerdictTests(SimpleTestCase):
    def test_a_cited_source_counts_even_when_the_prose_never_names_us(self):
        result = analyze_answer(ANSWER, BRAND, ALIASES, citations=CITATIONS)
        self.assertTrue(result["cited"], "a provider-verified citation to our domain is a citation")
        self.assertTrue(result["mentioned"], "cited implies present in the answer")
        self.assertEqual(result["verdict"], "cited")

    def test_the_citation_ordinal_is_the_real_source_number(self):
        result = analyze_answer(ANSWER, BRAND, ALIASES, citations=CITATIONS)
        # Third source in the list the provider returned -- a real property of the answer,
        # not an estimate.
        self.assertEqual(result["position"], 3)

    def test_no_citation_to_us_still_reads_absent(self):
        others = [c for c in CITATIONS if "premierstaff" not in c["url"]]
        result = analyze_answer(ANSWER, BRAND, ALIASES, citations=others)
        self.assertEqual(result["verdict"], "absent")
        self.assertFalse(result["cited"])

    def test_a_lookalike_host_is_not_us(self):
        impostor = [{"title": "x", "url": "https://notpremierstaff.com/blog"}]
        result = analyze_answer(ANSWER, BRAND, ALIASES, citations=impostor)
        self.assertEqual(result["verdict"], "absent",
                         "host matching must not be a substring test")

    def test_a_subdomain_of_ours_is_us(self):
        sub = [{"title": "x", "url": "https://blog.premierstaff.com/post"}]
        self.assertTrue(analyze_answer(ANSWER, BRAND, ALIASES, citations=sub)["cited"])

    def test_prose_mention_still_wins_its_richer_snippet(self):
        """A text hit already carries the sentence it appeared in; a citation hit cannot.
        When both exist the text hit's snippet is the more useful one."""
        prose = "For a 50-guest event, Premierstaff recommends 2 bartenders."
        result = analyze_answer(prose, BRAND, ALIASES, citations=CITATIONS)
        self.assertTrue(result["cited"])
        self.assertIn("Premierstaff", result["snippet"])

    def test_citations_are_optional_and_default_to_nothing(self):
        """The pure-text contract is unchanged for every existing caller."""
        result = analyze_answer(ANSWER, BRAND, ALIASES)
        self.assertEqual(result["verdict"], "absent")

    def test_competitors_are_detected_in_citations_too(self):
        """Otherwise the domain filter and the competitor chips under-report for exactly the
        same reason our own domain did."""
        result = analyze_answer(ANSWER, BRAND, ALIASES,
                                competitors=["platinumbartender.com"], citations=CITATIONS)
        names = [c["name"] for c in result["competitors"]]
        self.assertIn("platinumbartender.com", names)

    def test_a_malformed_citation_is_skipped_not_fatal(self):
        junk = [{"title": "x"}, {"url": None}, {}, {"url": "not a url"},
                {"url": "https://premierstaff.com/ok"}]
        result = analyze_answer(ANSWER, BRAND, ALIASES, citations=junk)
        self.assertTrue(result["cited"])

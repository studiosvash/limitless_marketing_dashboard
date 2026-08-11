"""A project shows the competitors ITS OWN user added — nothing else.

Reported from the live server: the Position Tracking "Share of voice" panel listed
nyeventsny.com, elev8.la and two premierstaff.com/<path> entries for a project whose Edit
Settings modal showed four completely different competitors.

Three separate causes, all in the READ path:

  1. `get_tracked_competitors(site_id)` was called without `site_pk` from the competitor map,
     the competitor grid, the backlinks comparison and the SERP-competitors connector. The
     storage was made per-project earlier; these four readers were never updated, so every
     sibling project on the domain saw every other one's competitors. The Settings modal read
     scoped, which is exactly why the modal and the panel disagreed.
  2. With no explicit competitors the code fell back to DataForSEO's AUTO-DISCOVERED list —
     domain-keyed, so shared by all siblings, and full of youtube.com / facebook.com /
     indeed.com / linkedin.com.
  3. `_get_competitor_grid` went further and hardcoded
     ["linkedin.com", "instagram.com", "facebook.com", "youtube.com", "reddit.com"]
     when that came back empty — inventing a competitive set outright.

The rule these tests pin: only what the user chose for THIS project. No siblings, no
auto-discovery, no invented defaults. A project with no competitors gets an honest empty
state, which the UI already knows how to render.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import (
    CompetitorDomain, CompetitorKeywordRanking, KeywordRanking, SavedKeyword, Site, init_db,
)
from pipeline.utils.db_connection import get_session

DOMAIN = "premierstaff.com"
NY = "United States - New York"
DC = "United States - Washington, DC"
DAY = date(2026, 8, 1)
KW = "event staffing agency"


class CompetitorProjectScopeTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None

        with get_session() as s:
            ny = Site(site_url=DOMAIN, site_name="PS NY", slug="ps-ny", is_active=1, location=NY)
            dc = Site(site_url=DOMAIN, site_name="PS DC", slug="ps-dc", is_active=1, location=DC)
            s.add_all([ny, dc])
            s.flush()
            self.ny_pk, self.dc_pk = ny.id, dc.id

            # Both projects track the same keyword in their own market.
            for pk, loc in ((self.ny_pk, NY), (self.dc_pk, DC)):
                s.add(SavedKeyword(site_pk=pk, site_id=DOMAIN, keyword=KW, location=loc))
                s.add(KeywordRanking(date=DAY, site_id=DOMAIN, keyword=KW, location=loc,
                                     position=12))

            # DataForSEO's auto-discovery — domain-keyed, so it belongs to no project in
            # particular. This is where youtube.com et al came from.
            for d in ("youtube.com", "facebook.com", "indeed.com", "nyeventsny.com"):
                s.add(CompetitorDomain(site_id=DOMAIN, competitor_domain=d, intersections=40))

            # Captured SERP rows exist for the auto-discovered domains too, so the map has
            # data it COULD show if it were still reading them.
            for d in ("eventstaff.com", "nyeventsny.com", "youtube.com"):
                for loc in (NY, DC):
                    s.add(CompetitorKeywordRanking(date=DAY, site_id=DOMAIN, keyword=KW,
                                                   competitor_domain=d, position=5,
                                                   location=loc))
            s.commit()

        from pipeline.services.competitor_service import set_tracked_competitors
        set_tracked_competitors(DOMAIN, ["eventstaff.com"], site_pk=self.ny_pk)
        # The DC project has chosen nothing.

    def _map(self, site_pk, location):
        from apps.dashboard.services.shared_queries import _get_competitor_map
        return _get_competitor_map(DOMAIN, location=location, site_pk=site_pk)

    def _grid(self, site_pk, location):
        from apps.dashboard.services.shared_queries import _get_competitor_grid
        return _get_competitor_grid(DOMAIN, location=location, site_pk=site_pk)

    def test_the_map_shows_only_this_project_s_chosen_competitors(self):
        domains = {d["domain"] for d in self._map(self.ny_pk, NY)["domains"]}
        self.assertIn("eventstaff.com", domains)
        self.assertNotIn("nyeventsny.com", domains, "auto-discovered domains are not chosen")
        self.assertNotIn("youtube.com", domains)

    def test_the_grid_shows_only_this_project_s_chosen_competitors(self):
        cols = set(self._grid(self.ny_pk, NY)["competitors"])
        self.assertEqual(cols, {"eventstaff.com"})

    def test_a_project_with_no_competitors_gets_an_empty_state_not_invented_ones(self):
        """The grid used to hardcode linkedin/instagram/facebook/youtube/reddit here."""
        grid = self._grid(self.dc_pk, DC)
        self.assertEqual(grid["competitors"], [])
        for invented in ("linkedin.com", "instagram.com", "facebook.com", "youtube.com",
                         "reddit.com", "nyeventsny.com"):
            self.assertNotIn(invented, grid["competitors"])

    def test_a_project_with_no_competitors_reports_that_state_in_the_map(self):
        self.assertEqual(self._map(self.dc_pk, DC)["status"], "no_competitors")

    def test_one_project_s_competitor_never_leaks_into_its_sibling(self):
        from pipeline.services.competitor_service import set_tracked_competitors
        set_tracked_competitors(DOMAIN, ["rival-dc.com"], site_pk=self.dc_pk)

        ny_cols = set(self._grid(self.ny_pk, NY)["competitors"])
        dc_cols = set(self._grid(self.dc_pk, DC)["competitors"])
        self.assertEqual(ny_cols, {"eventstaff.com"})
        self.assertEqual(dc_cols, {"rival-dc.com"})


class CompetitorDomainNormalisationTests(TestCase):
    """A pasted URL is a URL, not a domain.

    `_bare()` stripped the scheme and a trailing slash but NOT the path, so pasting
    `https://premierstaff.com/event-staffing-agency-las-vegas` stored that whole string as a
    "competitor domain" — which is how the user's own landing pages ended up listed as rivals
    in Share of Voice.
    """

    def test_a_pasted_url_is_stored_as_its_domain(self):
        from pipeline.services.competitor_service import _bare
        self.assertEqual(_bare("https://premierstaff.com/event-staffing-agency-las-vegas"),
                         "premierstaff.com")

    def test_www_and_trailing_slash_and_case_all_collapse(self):
        from pipeline.services.competitor_service import _bare
        self.assertEqual(_bare("HTTPS://WWW.EventStaff.com/"), "eventstaff.com")

    def test_a_bare_domain_is_unchanged(self):
        from pipeline.services.competitor_service import _bare
        self.assertEqual(_bare("eventstaff.com"), "eventstaff.com")

    def test_a_query_string_is_dropped(self):
        from pipeline.services.competitor_service import _bare
        self.assertEqual(_bare("eventstaff.com/pricing?ref=x"), "eventstaff.com")

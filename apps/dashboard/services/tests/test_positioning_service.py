import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import (init_db, KeywordRanking, CompetitorKeywordRanking,
                                CompetitorDomain, SavedKeyword, TrackedCompetitor)
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class BuildPositionsResponseTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add_all([
                # The Positioning page is Position TRACKING: build_positions_response reads
                # get_keyword_intelligence_raw(..., tracked_only=True), which bounds every
                # figure to the site's saved_keywords list (documented in
                # .claude/api-reference.md §positions). Without these rows
                # load_tracked_keywords() finds nothing in the DB and falls back to the repo's
                # legacy keywords.txt, so the seeded rankings below match nothing and every
                # assertion sees an empty response.
                SavedKeyword(site_id="sc-domain:fusehealth.com", keyword="iv therapy"),
                SavedKeyword(site_id="sc-domain:fusehealth.com", keyword="mobile iv drip"),
                # top3
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy", position=2, clicks=40, impressions=500,
                               search_volume=3000, keyword_difficulty=30, cpc=5.0,
                               intent="commercial", url="/iv-therapy"),
                # improved mover: pos 6 now, was 12 previously (delta = 12-6 = +6, improved)
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=6, clicks=10, impressions=150,
                               search_volume=800, keyword_difficulty=18, intent="informational",
                               url="/mobile"),
                KeywordRanking(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=12, clicks=4, impressions=90),
                # competitor ranking for the same keyword
                CompetitorKeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                          keyword="iv therapy", competitor_domain="driphydration.com",
                                          position=8),
                # _get_competitor_grid resolves its column set via get_tracked_competitors(),
                # which reads tracked_competitors — the domains THIS PROJECT'S USER CHOSE —
                # and NOT competitor_keyword_rankings directly. Without these rows the grid has
                # no columns even though ranking data exists for the domain above.
                #
                # These were CompetitorDomain (auto-discovery) rows until 2026-08-11. That
                # relied on the auto-seed fallback, which was removed: a domain DataForSEO
                # merely noticed is a suggestion, not a competitive set the user picked, and
                # filling the grid from it showed people "competitors" (youtube.com,
                # indeed.com) they had never chosen. The alignment this test is really about
                # is unchanged.
                TrackedCompetitor(site_id="sc-domain:fusehealth.com",
                                  competitor_domain="driphydration.com"),
                # second tracked domain with NO ranking data for "iv therapy" — proves the
                # comps array is positionally aligned to domains (None in its own slot), not
                # just "the one value we have, wherever it lands".
                TrackedCompetitor(site_id="sc-domain:fusehealth.com",
                                  competitor_domain="otherdomain.com"),
            ])

    def test_top_level_keys(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        for key in ["kpis", "distribution", "movement", "competitors", "movers"]:
            self.assertIn(key, body)

    def test_kpis_and_distribution_use_real_data(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        self.assertEqual(body["kpis"]["tracked"], 2)
        self.assertEqual(body["distribution"]["top3"], 1)  # "iv therapy" at pos 2

    def test_movers_have_full_keyword_shape_not_a_summary(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        mover_ids = {m["id"] for m in body["movers"]}
        self.assertIn("mobile iv drip", mover_ids)
        mover = next(m for m in body["movers"] if m["id"] == "mobile iv drip")
        for key in ["kw", "intent", "pos", "prevPos", "volume", "kd", "clicks",
                    "impressions", "ctr", "url", "monthly", "source", "serpFeatures"]:
            self.assertIn(key, mover)
        self.assertEqual(mover["prevPos"], 12.0)

    def test_avg_pos_excludes_null_position_keywords_from_denominator(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        with get_session() as session:
            session.add_all([
                SavedKeyword(site_id="sc-domain:fusehealth.com",
                             keyword="untracked position kw"),
                # tracked via GSC clicks/impressions but with no matched DataForSEO
                # position in the period -> func.avg(position) groups to SQL NULL.
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                keyword="untracked position kw", position=None,
                                clicks=5, impressions=80),
            ])
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        # 3 keywords are now grouped in the period: "iv therapy" (pos 2), "mobile iv
        # drip" (pos 6), and "untracked position kw" (pos None). The NULL-position row
        # must still count toward "tracked" (total keywords) but must NOT be counted
        # in the avg_pos denominator: correct average = (2 + 6) / 2 = 4.0, not
        # (2 + 6) / 3 = 2.7 (the deflated, buggy result).
        self.assertEqual(body["kpis"]["tracked"], 3)
        self.assertEqual(body["kpis"]["avg_pos"], 4.0)

    def test_competitors_rows_align_positionally_with_domains(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        domains = body["competitors"]["domains"]
        self.assertIn("driphydration.com", domains)
        self.assertIn("otherdomain.com", domains)
        drip_idx = domains.index("driphydration.com")
        other_idx = domains.index("otherdomain.com")
        self.assertNotEqual(drip_idx, other_idx)
        row = next(r for r in body["competitors"]["rows"] if r["kw"] == "iv therapy")
        # positional proof: driphydration.com HAS data for this keyword (8), otherdomain.com
        # does NOT (None) — a naive "whatever value we have, in list order" implementation
        # would misplace these; this only passes if comps[i] corresponds to domains[i].
        #
        # A populated cell is an OBJECT, not a bare number: api-reference.md §positions
        # documents `rows: [{kw, you: cell, comps: [cell|null]}]`, and positioning.js reads
        # `r.you.pos` and matches competitor cells by `c.domain`. The cell carries its own
        # domain precisely so a mis-ordered list is detectable rather than silently wrong,
        # so assert both the slot AND the identity the slot claims.
        self.assertEqual(row["comps"][drip_idx]["pos"], 8)
        self.assertEqual(row["comps"][drip_idx]["domain"], "driphydration.com")
        self.assertEqual(row["you"]["pos"], 2)

        # otherdomain.com is tracked but was never captured for this keyword. Two shapes are
        # legal (api-reference.md §positions says `comps: [cell|null]`): an absent cell, or a
        # cell naming the domain with `pos: None`. What must NEVER appear is a number —
        # competitor positions were once synthesised from an MD5 of keyword+domain, and
        # because that was deterministic it looked stable and therefore real. See the honesty
        # contract on overview_service.build_positioning_overview.
        other_cell = row["comps"][other_idx]
        if other_cell is not None:
            self.assertEqual(other_cell["domain"], "otherdomain.com")
            self.assertIsNone(other_cell["pos"],
                              "an uncaptured competitor position must never be a number")

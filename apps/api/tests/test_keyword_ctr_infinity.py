"""P9: a CTR over zero impressions is `inf`, not a number, and `fillna` never saw it.

`keywords_service` computed `(clicks / impressions * 100).fillna(0)`. `fillna` catches the
0/0 -> NaN case and nothing else; n/0 is +/-inf and sailed through into the "High Imp, Low
CTR" segment comparison and into the JSON payload, where `json.dumps` emits a bare `Infinity`
literal that is not valid JSON.
"""
import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd
from django.test import SimpleTestCase, override_settings

from pipeline.db.schema import KeywordRanking, Site, init_db
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session


class KeywordCtrTests(unittest.TestCase):
    """`(clicks / impressions * 100).fillna(0)` catches 0/0 -> NaN but NOT n/0 -> inf."""

    def test_fillna_does_not_catch_infinity(self):
        # The shape of the original line, pinned so the reason for the fix stays legible.
        df = pd.DataFrame({"clicks": [3, 0], "impressions": [0, 0]})
        naive = (df["clicks"] / df["impressions"] * 100).fillna(0)
        self.assertEqual(naive[1], 0.0)                 # 0/0 -> NaN -> 0
        self.assertEqual(naive[0], float("inf"))        # 3/0 -> inf, straight through

    def test_service_masks_non_finite_ctr(self):
        from apps.dashboard.services.keywords_service import _safe_ctr
        out = _safe_ctr(pd.Series([3, 0, 5]), pd.Series([0, 0, 100]))
        self.assertTrue(pd.isna(out[0]), "clicks over zero impressions is not a ratio")
        self.assertEqual(out[1], 0.0)
        self.assertEqual(out[2], 5.0)


class KeywordIntelligenceCtrTests(SimpleTestCase):
    """End to end: a keyword with clicks and zero impressions must not put `Infinity` in the
    JSON payload. json.dumps emits a bare `Infinity` literal, which is not valid JSON and
    which no strict parser will accept."""

    databases = set()

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
            session.add(Site(site_url="example.com", site_name="Example",
                             slug="example", is_active=1))
            session.add(KeywordRanking(
                date=date(2026, 6, 10), site_id="example.com", keyword="ghost keyword",
                position=5.0, clicks=4, impressions=0, search_volume=None,
            ))

    def test_zero_impression_row_reports_no_ctr_rather_than_infinity(self):
        import json

        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw

        out = get_keyword_intelligence_raw(
            "example.com", date(2026, 6, 1), date(2026, 6, 30),
            date(2026, 5, 1), date(2026, 5, 31),
        )
        row = next(r for r in out["all_keywords"] if r["keyword"] == "ghost keyword")
        self.assertIsNone(row["ctr"])
        # A non-finite float survives json.dumps as a bare `Infinity` token.
        self.assertNotIn("Infinity", json.dumps(out["all_keywords"]))

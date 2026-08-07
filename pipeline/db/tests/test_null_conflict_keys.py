"""Tests for _coerce_null_keys — the guard against NULL conflict-key duplication.

Neither Postgres nor SQLite treats NULL as equal to NULL in a unique index, so a record
carrying NULL in a conflict-key column slips past ON CONFLICT DO UPDATE and inserts a fresh
duplicate on every re-sync. The Google Ads search-terms connector really does emit
campaign_id=None (google_ads_search_terms.py), so this is a live path, not just defensive.

The integration tests below reproduce the duplication on SQLite (which shares the
NULL-never-conflicts semantics), proving the coercion is wired into the two upserts with
nullable key columns: upsert_ad_search_terms and upsert_seo_daily.
"""
import unittest
from datetime import date

from sqlalchemy import select

from pipeline.db.engine import get_engine, get_sessionmaker
from pipeline.db.schema import AdSearchTerm, SEODaily
from pipeline.db.writer import _coerce_null_keys, upsert_ad_search_terms, upsert_seo_daily


class CoerceNullKeysTests(unittest.TestCase):
    """Pure-function contract."""

    def test_none_becomes_empty_string_only_in_key_columns(self):
        records = [{"a": None, "b": None, "c": 5}]
        _coerce_null_keys(records, ("a",))
        self.assertEqual(records, [{"a": "", "b": None, "c": 5}])

    def test_a_missing_key_column_is_added_as_empty_string(self):
        records = [{"b": 1}]
        _coerce_null_keys(records, ("a",))
        self.assertEqual(records, [{"a": "", "b": 1}])

    def test_real_values_are_untouched(self):
        records = [{"a": "x", "b": 0}]
        _coerce_null_keys(records, ("a", "b"))
        self.assertEqual(records, [{"a": "x", "b": 0}])


class AdSearchTermsNullCampaignIdTests(unittest.TestCase):
    """A search term with no campaign id must update in place on re-sync, not duplicate."""

    def setUp(self):
        self.engine = get_engine(":memory:")
        self.Session = get_sessionmaker(":memory:")
        self.Session.configure(bind=self.engine)
        AdSearchTerm.__table__.create(self.engine)

    def _row(self, **overrides):
        row = {"date": date(2026, 8, 1), "term": "physio near me", "campaign_id": None,
               "campaign": "Brand", "impressions": 10, "clicks": 2, "cost": 1.5}
        row.update(overrides)
        return row

    def test_resync_with_null_campaign_id_does_not_duplicate(self):
        with self.Session() as s:
            upsert_ad_search_terms(s, [self._row()], site_id="a.com")
            s.commit()
        with self.Session() as s:
            upsert_ad_search_terms(s, [self._row(clicks=7)], site_id="a.com")
            s.commit()

        with self.Session() as s:
            rows = s.execute(select(AdSearchTerm)).scalars().all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].clicks, 7)
        self.assertEqual(rows[0].campaign_id, "")


class SEODailyNullDimensionTests(unittest.TestCase):
    """A seo_daily row missing a dimension must update in place on re-sync, not duplicate."""

    def setUp(self):
        self.engine = get_engine(":memory:")
        self.Session = get_sessionmaker(":memory:")
        self.Session.configure(bind=self.engine)
        SEODaily.__table__.create(self.engine)

    def test_resync_with_null_dimensions_does_not_duplicate(self):
        row = {"date": date(2026, 8, 1), "country": None, "device": None,
               "landing_page": "/x", "clicks": 3, "impressions": 100}
        with self.Session() as s:
            upsert_seo_daily(s, [dict(row)], site_id="a.com")
            s.commit()
        with self.Session() as s:
            upsert_seo_daily(s, [dict(row, clicks=9)], site_id="a.com")
            s.commit()

        with self.Session() as s:
            rows = s.execute(select(SEODaily)).scalars().all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].clicks, 9)
        self.assertEqual(rows[0].country, "")
        self.assertEqual(rows[0].device, "")

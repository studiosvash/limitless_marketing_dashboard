"""SERP-feature snapshots must update in place, never accumulate duplicates.

serp_feature_rankings is written on every competitor SERP sync, so the upsert key
(date, site_id, keyword, location, domain, feature_type) is what keeps a re-run of the
same day from doubling every AI Overview citation row.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import SimpleTestCase
from sqlalchemy import select

from pipeline.db.schema import SerpFeatureRanking, init_db
from pipeline.db.writer import upsert_serp_feature_rankings
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session

DAY = date(2026, 8, 17)
SITE = "fusehealth.com"


class SerpFeatureWriterTests(SimpleTestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        self.db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(self.db_path))
        from django.test import override_settings
        self._ctx = override_settings(ANALYTICS_DB_PATH=self.db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def _record(self, domain="premierstaff.com", feature_type="ai_overview",
                slot=1, url="https://premierstaff.com/guide", title="Guide",
                keyword="event staffing"):
        return {
            "date": DAY, "site_id": SITE, "keyword": keyword,
            "location": "United States", "domain": domain,
            "feature_type": feature_type, "slot": slot, "url": url, "title": title,
        }

    def test_same_keys_update_instead_of_duplicating(self):
        with get_session() as s:
            upsert_serp_feature_rankings(s, [self._record(slot=3, url="https://old")])
            s.commit()
        with get_session() as s:
            upsert_serp_feature_rankings(s, [self._record(slot=1, url="https://new",
                                                          title="New title")])
            s.commit()
        with get_session() as s:
            rows = s.execute(select(SerpFeatureRanking)).scalars().all()
        self.assertEqual(len(rows), 1, "re-sync of the same capture must UPDATE, not duplicate")
        self.assertEqual(rows[0].slot, 1, "slot must update on conflict")
        self.assertEqual(rows[0].url, "https://new", "url must update on conflict")
        self.assertEqual(rows[0].title, "New title")

    def test_feature_types_are_separate_rows_for_one_domain(self):
        # One domain can hold an AIO citation AND the featured snippet on the same SERP —
        # feature_type is part of the identity, so both survive.
        with get_session() as s:
            upsert_serp_feature_rankings(s, [
                self._record(feature_type="ai_overview", slot=2),
                self._record(feature_type="featured_snippet", slot=1),
            ])
            s.commit()
        with get_session() as s:
            rows = s.execute(select(SerpFeatureRanking)).scalars().all()
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.feature_type for r in rows}, {"ai_overview", "featured_snippet"})

    def test_duplicate_conflict_keys_in_one_batch_are_collapsed(self):
        # Without _dedupe_by_keys this raises CardinalityViolation on Postgres and rolls
        # back the entire batch. SQLite hides it, so this test documents the contract.
        with get_session() as s:
            n = upsert_serp_feature_rankings(s, [
                self._record(slot=1),
                self._record(slot=4),
            ])
            s.commit()
        self.assertEqual(n, 1, "duplicates on the conflict key must collapse before the insert")
        with get_session() as s:
            rows = s.execute(select(SerpFeatureRanking)).scalars().all()
        self.assertEqual(rows[0].slot, 4, "last occurrence wins")

    def test_missing_location_defaults_rather_than_null_bypassing_the_key(self):
        # location is a conflict-key column; NULL there would bypass ON CONFLICT on
        # Postgres and duplicate on every sync. The writer defaults it.
        rec = self._record()
        rec.pop("location")
        with get_session() as s:
            upsert_serp_feature_rankings(s, [rec])
            s.commit()
        with get_session() as s:
            row = s.execute(select(SerpFeatureRanking)).scalars().first()
        self.assertEqual(row.location, "United States")

    def test_site_id_param_fills_missing_site_id(self):
        rec = self._record()
        rec.pop("site_id")
        with get_session() as s:
            upsert_serp_feature_rankings(s, [rec], site_id=SITE)
            s.commit()
        with get_session() as s:
            row = s.execute(select(SerpFeatureRanking)).scalars().first()
        self.assertEqual(row.site_id, SITE)

    def test_empty_records_write_nothing(self):
        with get_session() as s:
            self.assertEqual(upsert_serp_feature_rankings(s, []), 0)

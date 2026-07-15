"""The tracked-keyword list must come from the DATABASE (saved_keywords -- what the admin
tracks from the Keyword Explorer), not the legacy keywords.txt file.

Regression: the paid per-keyword connectors (SERP position tracking, AI keyword volume) read
their keyword list from keywords.txt, which does not exist -- so they silently fetched nothing
and those pages could never fill. Now the admin manages the list from the dashboard, and the
file is only a fallback.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SavedKeyword
from pipeline.utils.db_connection import get_session
from pipeline.utils.keywords import load_tracked_keywords
import pipeline.utils.db_connection as db_connection

SITE = "sc-domain:fusehealth.com"
OTHER = "other-project.com"


class LoadTrackedKeywordsTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)

        # a keywords.txt that must be IGNORED whenever the DB has tracked keywords
        self.file_path = str(Path(tmp) / "keywords.txt")
        Path(self.file_path).write_text("from-the-file\n", encoding="utf-8")

        with get_session() as session:
            session.add_all([
                SavedKeyword(site_id=SITE, keyword="iv therapy", location="United States"),
                SavedKeyword(site_id=SITE, keyword="mobile iv drip", location="United States"),
                # another project's keyword must never leak into this site's list
                SavedKeyword(site_id=OTHER, keyword="not yours", location="United States"),
            ])

    def test_keywords_come_from_db_not_the_file(self):
        kws = load_tracked_keywords(SITE, path=self.file_path)
        self.assertEqual(sorted(kws), ["iv therapy", "mobile iv drip"])
        self.assertNotIn("from-the-file", kws)   # DB wins over the legacy file

    def test_other_projects_keywords_are_excluded(self):
        self.assertNotIn("not yours", load_tracked_keywords(SITE, path=self.file_path))

    def test_falls_back_to_file_when_site_has_no_tracked_keywords(self):
        kws = load_tracked_keywords("site-with-nothing.com", path=self.file_path)
        self.assertEqual(kws, ["from-the-file"])

    def test_no_site_id_uses_the_file(self):
        self.assertEqual(load_tracked_keywords(path=self.file_path), ["from-the-file"])

    def test_missing_file_and_no_db_rows_is_empty_not_a_crash(self):
        self.assertEqual(
            load_tracked_keywords("site-with-nothing.com", path="/no/such/keywords.txt"), []
        )

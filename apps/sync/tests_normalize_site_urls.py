"""`manage.py normalize_site_urls` — bring pre-2026-08-02 project rows onto the one rule.

The command rewrites `sites.site_url` to `normalize_domain()`'s output. What makes it worth
testing is not the rename itself but everything that has to move WITH it: `site_url` is the join
key, and seven Django models are keyed on the same string. Renaming the site row alone would
strand the project's settings blob, acknowledged alerts, ads overrides and entire sync history
under the old key — the UI would then report a configured, freshly-synced project as unconfigured
and never-synced, with no error anywhere to explain it.
"""
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings
from sqlalchemy import select

from apps.dashboard.models import AITarget, ProjectSettings
from apps.sync.models import SyncLog, SyncStatus
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class NormalizeSiteUrlsCommandTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)

    def _seed(self, *site_urls):
        with get_session() as session:
            for i, url in enumerate(site_urls, start=1):
                session.add(Site(site_url=url, site_name=url, slug=f"site-{i}", is_active=1))

    def _urls(self):
        with get_session() as session:
            return [s.site_url for s in session.execute(select(Site).order_by(Site.id)).scalars()]

    def test_dry_run_changes_nothing(self):
        self._seed("www.fusehealth.com")
        ProjectSettings.objects.create(site_url="www.fusehealth.com", data={"k": "v"})

        call_command("normalize_site_urls")

        self.assertEqual(self._urls(), ["www.fusehealth.com"])
        self.assertTrue(ProjectSettings.objects.filter(site_url="www.fusehealth.com").exists())

    def test_apply_rewrites_the_site_url(self):
        self._seed("www.fusehealth.com", "https://www.eventstaff.com/", "sc-domain:premierstaff.com")

        call_command("normalize_site_urls", apply=True)

        self.assertEqual(
            self._urls(), ["fusehealth.com", "eventstaff.com", "premierstaff.com"]
        )

    def test_django_rows_move_with_the_site(self):
        self._seed("www.fusehealth.com")
        ProjectSettings.objects.create(site_url="www.fusehealth.com", data={"alertAcks": ["a1"]})
        AITarget.objects.create(site_url="www.fusehealth.com", brand="FuseHealth")
        SyncLog.objects.create(connector="gsc", site_url="www.fusehealth.com",
                               status=SyncStatus.SUCCESS, records_written=42)

        call_command("normalize_site_urls", apply=True)

        self.assertEqual(ProjectSettings.objects.get(site_url="fusehealth.com").data,
                         {"alertAcks": ["a1"]})
        self.assertEqual(AITarget.objects.get(site_url="fusehealth.com").brand, "FuseHealth")
        self.assertEqual(SyncLog.objects.get(site_url="fusehealth.com").records_written, 42)
        self.assertFalse(ProjectSettings.objects.filter(site_url="www.fusehealth.com").exists())

    def test_the_slug_is_left_alone(self):
        # The slug is the public project id — in every URL, in the SPA's fh_selected_project
        # localStorage key, and in whatever the team has bookmarked.
        self._seed("www.fusehealth.com")
        call_command("normalize_site_urls", apply=True)
        with get_session() as session:
            self.assertEqual(session.execute(select(Site)).scalars().one().slug, "site-1")

    def test_two_projects_for_one_site_are_refused_not_merged(self):
        # Picking a winner would silently discard the loser's settings, acked alerts and ads
        # overrides. That is a human's call.
        self._seed("premierstaff.com", "www.premierstaff.com")

        call_command("normalize_site_urls", apply=True)

        self.assertEqual(sorted(self._urls()), ["premierstaff.com", "www.premierstaff.com"])

    def test_idempotent(self):
        self._seed("www.fusehealth.com")
        call_command("normalize_site_urls", apply=True)
        call_command("normalize_site_urls", apply=True)  # must not raise
        self.assertEqual(self._urls(), ["fusehealth.com"])

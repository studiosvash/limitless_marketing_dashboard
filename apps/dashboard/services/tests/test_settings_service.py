import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import Role, UserProfile
from apps.dashboard.models import ProjectSettings
from apps.sync.models import SyncLog, SyncStatus
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db
from pipeline.services.site_service import add_site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_ID = "https://example.com"


def _new_analytics_db(test_case):
    """Point the SQLAlchemy analytics DB at a fresh temp sqlite file for the duration of a
    test, matching the established pattern in test_ai_service.py/test_offsite_service.py.
    Registers cleanup so tests don't leak global state into each other."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)


class QueryConnectorsRawTests(TestCase):
    def setUp(self):
        SyncLog.objects.create(
            connector="gsc", site_url=SITE_ID, status=SyncStatus.SUCCESS,
            records_written=120, error_message=None,
        )
        SyncLog.objects.create(
            connector="ga4", site_url=SITE_ID, status=SyncStatus.ERROR,
            records_written=0, error_message="401 Unauthorized: token expired",
        )
        # Different site's row -- must never leak into this site's response.
        SyncLog.objects.create(
            connector="gsc", site_url="https://other-project.com", status=SyncStatus.SUCCESS,
            records_written=999,
        )

    def test_reshapes_both_rows_including_error_message(self):
        from apps.dashboard.services.settings_service import query_connectors_raw
        rows = query_connectors_raw(SITE_ID)
        by_name = {r["name"]: r for r in rows}

        self.assertEqual(len(rows), 2)
        self.assertEqual(by_name["gsc"]["status"], SyncStatus.SUCCESS)
        self.assertEqual(by_name["gsc"]["records"], 120)
        self.assertIsNone(by_name["gsc"]["error"])
        self.assertEqual(by_name["ga4"]["status"], SyncStatus.ERROR)
        self.assertEqual(by_name["ga4"]["records"], 0)
        self.assertEqual(by_name["ga4"]["error"], "401 Unauthorized: token expired")

    def test_excludes_other_sites_rows(self):
        from apps.dashboard.services.settings_service import query_connectors_raw
        rows = query_connectors_raw(SITE_ID)
        self.assertNotIn("other-project.com", [r.get("name", "") for r in rows])
        other_rows = query_connectors_raw("https://other-project.com")
        self.assertEqual(len(other_rows), 1)


class QueryConnectorsRawEmptyTests(TestCase):
    def setUp(self):
        pass  # deliberately no seeded rows

    def test_empty_case_returns_empty_list(self):
        from apps.dashboard.services.settings_service import query_connectors_raw
        self.assertEqual(query_connectors_raw(SITE_ID), [])


class QueryTeamRawTests(TestCase):
    """Real seeded users matching apps/accounts/management/commands/seed_users.py's shape
    (founder/seo/ads, no email set, roles from apps.accounts.models.Role) -- not a fabricated
    team list."""

    def setUp(self):
        self.founder = User.objects.create_user(username="founder")
        UserProfile.objects.filter(user=self.founder).update(role=Role.FOUNDER)
        self.founder.last_login = timezone.now()
        self.founder.save(update_fields=["last_login"])

        self.seo = User.objects.create_user(username="seo")
        UserProfile.objects.filter(user=self.seo).update(role=Role.SEO)
        # seo user has never logged in -- last_login stays None.

        self.ads = User.objects.create_user(username="ads", email="ads@limitlesshold.com")
        UserProfile.objects.filter(user=self.ads).update(role=Role.ADS)

    def test_reflects_real_seeded_users_with_real_roles(self):
        from apps.dashboard.services.settings_service import query_team_raw
        rows = query_team_raw()
        by_name = {r["name"]: r for r in rows}

        self.assertEqual(len(rows), 3)
        self.assertEqual(by_name["founder"]["role"], Role.FOUNDER)
        self.assertEqual(by_name["seo"]["role"], Role.SEO)
        self.assertEqual(by_name["ads"]["role"], Role.ADS)
        for r in rows:
            self.assertEqual(r["status"], "active")

    def test_email_honestly_blank_when_unset(self):
        from apps.dashboard.services.settings_service import query_team_raw
        by_name = {r["name"]: r for r in query_team_raw()}
        self.assertEqual(by_name["founder"]["email"], "")
        self.assertEqual(by_name["seo"]["email"], "")

    def test_email_reflects_real_value_when_set(self):
        from apps.dashboard.services.settings_service import query_team_raw
        by_name = {r["name"]: r for r in query_team_raw()}
        self.assertEqual(by_name["ads"]["email"], "ads@limitlesshold.com")

    def test_last_active_none_for_never_logged_in_user_no_crash(self):
        from apps.dashboard.services.settings_service import query_team_raw
        by_name = {r["name"]: r for r in query_team_raw()}
        self.assertIsNone(by_name["seo"]["last_active"])
        self.assertIsNotNone(by_name["founder"]["last_active"])

    def test_initials_derived_from_username(self):
        from apps.dashboard.services.settings_service import query_team_raw
        by_name = {r["name"]: r for r in query_team_raw()}
        self.assertEqual(by_name["founder"]["initials"], "FO")
        self.assertEqual(by_name["seo"]["initials"], "SE")
        self.assertEqual(by_name["ads"]["initials"], "AD")


class BuildSettingsResponseNoRowTests(TestCase):
    """No ProjectSettings row, no Site row, no SyncLog rows, no users -- every blob-backed
    group must come back as DEFAULT_SETTINGS_BLOB's exact honest values, not the fixture's
    fabricated workspace/2FA/connector numbers."""

    def setUp(self):
        _new_analytics_db(self)

    def test_no_settings_row_returns_exact_default_blob(self):
        from apps.dashboard.services.settings_service import (
            DEFAULT_SETTINGS_BLOB, build_settings_response,
        )
        body = build_settings_response(SITE_ID)

        for key, default in DEFAULT_SETTINGS_BLOB.items():
            self.assertEqual(body[key], default, f"{key} did not match honest default")

    def test_no_settings_row_real_project_credentials_connectors_team(self):
        from apps.dashboard.services.settings_service import build_settings_response
        body = build_settings_response(SITE_ID)

        self.assertIsNone(body["project"]["id"])
        self.assertEqual(body["project"]["domain"], SITE_ID)
        self.assertEqual(body["project"]["competitors"], [])
        self.assertEqual(body["credentials"], {
            "gsc_property": "", "ga4_property_id": "", "dataforseo_target_domain": "",
        })
        self.assertEqual(body["connectors"], [])
        self.assertEqual(body["team"], [])

    def test_usage_and_sync_honest_shape_no_crash(self):
        """usage/sync are unguarded, required reads in the SPA's Settings render code
        (index.html:6314/6424) that neither the design spec nor the plan's shape sketch
        mentioned -- verified against the SPA's own (stale) mock backend
        (static/spa/app/api.js settingsView/usageView) as the real required shape."""
        from apps.dashboard.services.settings_service import build_settings_response
        body = build_settings_response(SITE_ID)

        self.assertEqual(body["sync"], {"next_run": None, "day": None, "last_run": None})
        self.assertEqual(body["usage"]["budget"], 0)
        self.assertEqual(body["usage"]["currency"], "USD")
        self.assertEqual(body["usage"]["month_to_date"], 0)
        self.assertEqual(body["usage"]["est_monthly"], 0)
        modules = {i["module"] for i in body["usage"]["items"]}
        self.assertEqual(modules, {
            "Position tracking (SERP Standard)", "Backlinks summary + new/lost deltas",
            "Site audit crawl (OnPage)", "Keyword volume refresh (Labs)",
        })
        for item in body["usage"]["items"]:
            self.assertIsNone(item["est"])


class BuildSettingsResponsePartialBlobTests(TestCase):
    """A real, partially-saved blob (only `notifications` ever saved) must NOT wipe out
    honest defaults for every other group -- proves per-key merge-with-defaults, not
    "return whatever's saved and nothing else"."""

    def setUp(self):
        _new_analytics_db(self)
        ProjectSettings.objects.create(
            site_url=SITE_ID,
            data={"notifications": {"weekly_digest": True, "recipients": "a@b.com"}},
        )

    def test_saved_key_merges_over_defaults(self):
        from apps.dashboard.services.settings_service import (
            DEFAULT_SETTINGS_BLOB, build_settings_response,
        )
        body = build_settings_response(SITE_ID)

        expected = {**DEFAULT_SETTINGS_BLOB["notifications"],
                    "weekly_digest": True, "recipients": "a@b.com"}
        self.assertEqual(body["notifications"], expected)

    def test_other_keys_still_get_honest_defaults(self):
        from apps.dashboard.services.settings_service import (
            DEFAULT_SETTINGS_BLOB, build_settings_response,
        )
        body = build_settings_response(SITE_ID)

        for key, default in DEFAULT_SETTINGS_BLOB.items():
            if key == "notifications":
                continue
            self.assertEqual(body[key], default, f"{key} was not left at its honest default")


class ApplySettingsUpdateCredentialsTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)
        add_site(
            site_url=SITE_ID, site_name="Example", gsc_property="sc-domain:old.com",
            ga4_property_id="old-ga4", dataforseo_target_domain="old.com",
        )

    def test_credentials_update_reflects_on_next_build_call(self):
        from apps.dashboard.services.settings_service import (
            apply_settings_update, build_settings_response,
        )
        result = apply_settings_update(SITE_ID, {"credentials": {
            "gsc_property": "sc-domain:new.com", "ga4_property_id": "new-ga4",
            "dataforseo_target_domain": "new.com",
        }})
        self.assertEqual(result, {"ok": True})

        body = build_settings_response(SITE_ID)
        self.assertEqual(body["credentials"], {
            "gsc_property": "sc-domain:new.com", "ga4_property_id": "new-ga4",
            "dataforseo_target_domain": "new.com",
        })


class ApplySettingsUpdateBudgetTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)

    def test_budget_cap_and_enforce_merge_without_clobbering_quotas(self):
        from apps.dashboard.services.settings_service import (
            DEFAULT_SETTINGS_BLOB, apply_settings_update, build_settings_response,
        )
        apply_settings_update(SITE_ID, {"budgetCap": 50})
        body = build_settings_response(SITE_ID)
        self.assertEqual(body["budget"]["cap"], 50)
        self.assertEqual(body["budget"]["quotas"], DEFAULT_SETTINGS_BLOB["budget"]["quotas"])

        apply_settings_update(SITE_ID, {"budgetEnforce": True})
        body2 = build_settings_response(SITE_ID)
        self.assertEqual(body2["budget"]["cap"], 50)  # not clobbered by the enforce-only call
        self.assertIs(body2["budget"]["enforce"], True)
        self.assertEqual(body2["budget"]["quotas"], DEFAULT_SETTINGS_BLOB["budget"]["quotas"])


class ApplySettingsUpdatePerKeyMergeTests(TestCase):
    """A second PUT touching only `notifications` must not erase a `workspace` value saved
    by a prior call -- proves per-key top-level merge, not a whole-blob overwrite."""

    def setUp(self):
        _new_analytics_db(self)

    def test_second_call_with_different_key_preserves_first(self):
        from apps.dashboard.services.settings_service import (
            apply_settings_update, build_settings_response,
        )
        apply_settings_update(SITE_ID, {"workspace": {"name": "Acme Co"}})
        apply_settings_update(SITE_ID, {"notifications": {"weekly_digest": True}})

        body = build_settings_response(SITE_ID)
        self.assertEqual(body["workspace"]["name"], "Acme Co")
        self.assertIs(body["notifications"]["weekly_digest"], True)


class ApplySettingsUpdateTeamSecurityRejectedTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)

    def test_team_update_rejected_and_persists_nothing(self):
        from apps.dashboard.services.settings_service import apply_settings_update
        result = apply_settings_update(SITE_ID, {"team": [{"id": 1, "role": "Owner"}]})
        self.assertEqual(result, {"error": "not_yet_available"})
        self.assertFalse(ProjectSettings.objects.filter(site_url=SITE_ID).exists())

    def test_security_update_rejected_and_persists_nothing(self):
        from apps.dashboard.services.settings_service import apply_settings_update
        result = apply_settings_update(SITE_ID, {"security": {"twofa": True}})
        self.assertEqual(result, {"error": "not_yet_available"})
        self.assertFalse(ProjectSettings.objects.filter(site_url=SITE_ID).exists())

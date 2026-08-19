import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import Role, UserProfile
from apps.dashboard.models import ProjectSettings
from apps.dashboard.services.settings_service import DEFAULT_SETTINGS_BLOB, LIVE_ROLES
from apps.sync.models import SyncLog, SyncStatus
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


SITE_URL = "sc-domain:fusehealth.com"


def _bootstrap_settings_test_env(test_case):
    """Point the SQLAlchemy analytics DB at a fresh temp sqlite file, seed the `Site` row
    resolve_project_or_404 needs, and hand back an authenticated APIClient -- same pattern as
    test_ai.py's `_bootstrap_ai_test_env` (a plain function, not a shared TestCase subclass,
    matching this project's test-class-hygiene rule: every test class inherits directly from
    APITestCase, never a sibling test class)."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)

    with get_session() as session:
        session.add(Site(site_url=SITE_URL, site_name="FuseHealth",
                          slug="fusehealth", is_active=1))

    user = get_user_model().objects.create_user("founder1", password="x")
    token = Token.objects.get(user=user)
    client_auth = APIClient()
    client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client_auth


class SettingsGetEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_settings_test_env(self)

    def test_get_returns_real_connectors_and_team(self):
        SyncLog.objects.create(
            connector="gsc", site_url=SITE_URL, status=SyncStatus.SUCCESS,
            records_written=120, error_message=None,
        )
        SyncLog.objects.create(
            connector="ga4", site_url=SITE_URL, status=SyncStatus.ERROR,
            records_written=0, error_message="401 Unauthorized: token expired",
        )
        # Stored with the retired Role vocabulary on purpose: every database seeded before
        # seed_users.py was corrected still holds these, and the endpoint must not hand the
        # SPA a role string its team table has no concept of.
        seo_user = get_user_model().objects.create_user("seo1")
        UserProfile.objects.filter(user=seo_user).update(role=Role.SEO)

        resp = self.client_auth.get("/api/projects/fusehealth/settings")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        connectors_by_name = {c["name"]: c for c in body["connectors"]}
        self.assertEqual(connectors_by_name["gsc"]["status"], SyncStatus.SUCCESS)
        self.assertEqual(connectors_by_name["gsc"]["records"], 120)
        self.assertEqual(connectors_by_name["ga4"]["status"], SyncStatus.ERROR)
        self.assertEqual(connectors_by_name["ga4"]["error"], "401 Unauthorized: token expired")

        team_by_name = {m["name"]: m for m in body["team"]}
        self.assertIn("founder1", team_by_name)
        self.assertIn("seo1", team_by_name)
        # Healed to the live vocabulary on the way out — "seo" reaches the SPA as "Admin",
        # the access that row already had (check_owner_admin refuses only "Analyst").
        self.assertEqual(team_by_name["seo1"]["role"], "Admin")
        for member in body["team"]:
            self.assertIn(member["role"], LIVE_ROLES)

    def test_get_fresh_project_is_honest_not_a_crash(self):
        # No ProjectSettings row, no SyncLog rows beyond the auth user's own profile --
        # every blob-backed key (incl. usage/sync, which neither the design spec nor the
        # plan's original sketch mentioned but which Task 2 found are unguarded SPA reads)
        # must still come back as a real, non-crashing, honestly-defaulted shape.
        resp = self.client_auth.get("/api/projects/fusehealth/settings")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        for key, default in DEFAULT_SETTINGS_BLOB.items():
            self.assertEqual(body[key], default, f"{key} did not match honest default")
        self.assertEqual(body["connectors"], [])
        # The three header keys the SPA dereferences unguarded — all None on a project with no
        # run history, because there is no honest date to give. Asserted key-by-key rather than
        # as the whole dict: `sync` is additive (it gained `modules` on 2026-08-18), and an
        # equality check on the whole shape turns every future addition into a failure here
        # without saying anything about the honesty this test is actually about.
        self.assertEqual(
            {k: body["sync"][k] for k in ("next_run", "day", "last_run")},
            {"next_run": None, "day": None, "last_run": None},
        )
        # Same honesty rule one level down: a module that has never run reports null, not a
        # fabricated date, for both its last run and its next one.
        for row in body["sync"]["modules"]:
            self.assertIsNone(row["last_success"], f"{row['module']} invented a last run")
            self.assertIsNone(row["next_run"], f"{row['module']} invented a next run")
        self.assertEqual(body["usage"]["budget"], 0)
        self.assertEqual(body["usage"]["month_to_date"], 0)
        self.assertEqual(body["credentials"], {
            "gsc_property": "", "ga4_property_id": "", "dataforseo_target_domain": "",
        })

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/settings")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/settings")
        self.assertEqual(resp.status_code, 401)


class SettingsPutCredentialsTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_settings_test_env(self)

    def test_put_credentials_persists_on_next_get(self):
        payload = {"credentials": {
            "gsc_property": "sc-domain:new.com",
            "ga4_property_id": "999888777",
            "dataforseo_target_domain": "new.com",
        }}
        resp = self.client_auth.put("/api/projects/fusehealth/settings", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["credentials"], payload["credentials"])

        get_resp = self.client_auth.get("/api/projects/fusehealth/settings")
        self.assertEqual(get_resp.json()["credentials"], payload["credentials"])

    def test_ga4_properties_prefix_is_stripped_on_save(self):
        """GA4's own admin UI displays 'properties/123456789', and that is what people paste.
        Every request builder does f"properties/{id}", so storing the prefixed form produced
        properties/properties/123456789 and an INVALID_ARGUMENT hours later. It must be
        normalised at the write, not just tolerated at read."""
        resp = self.client_auth.put("/api/projects/fusehealth/settings", {
            "credentials": {"ga4_property_id": "properties/123456789"}
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["credentials"]["ga4_property_id"], "123456789")

    def test_non_numeric_ga4_property_id_is_rejected_not_stored_verbatim(self):
        """A Measurement ID (G-XXXXXXX) or free text used to save cleanly and fail only when a
        sync actually queried GA4. It must not be silently persisted as if it were valid."""
        resp = self.client_auth.put("/api/projects/fusehealth/settings", {
            "credentials": {"ga4_property_id": "G-ABC1234"}
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["credentials"]["ga4_property_id"], "")

    def test_saving_gsc_and_ga4_does_not_blank_the_dataforseo_target(self):
        """Regression: saveCreds only ever sent gsc_property + ga4_property_id (the only two
        fields the UI has ever shown inputs for), but apply_settings_update used to forward
        dataforseo_target_domain=None unconditionally on every save, which _bare_domain(None)
        turned into "" -- silently blanking an explicitly configured DataForSEO target on
        every single GSC/GA4 save."""
        self.client_auth.put("/api/projects/fusehealth/settings", {
            "credentials": {"dataforseo_target_domain": "explicit-target.com"}
        }, format="json")

        resp = self.client_auth.put("/api/projects/fusehealth/settings", {
            "credentials": {"gsc_property": "sc-domain:new.com", "ga4_property_id": "111222333"}
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["credentials"]["dataforseo_target_domain"], "explicit-target.com")


class SettingsPutPerKeyMergeTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_settings_test_env(self)

    def test_budget_cap_then_notifications_do_not_clobber_each_other(self):
        cap_resp = self.client_auth.put(
            "/api/projects/fusehealth/settings", {"budgetCap": 50}, format="json"
        )
        self.assertEqual(cap_resp.status_code, 200)

        notif_resp = self.client_auth.put(
            "/api/projects/fusehealth/settings",
            {"notifications": {"weekly_digest": True, "recipients": "a@b.com"}},
            format="json",
        )
        self.assertEqual(notif_resp.status_code, 200)

        get_resp = self.client_auth.get("/api/projects/fusehealth/settings")
        body = get_resp.json()
        # the budgetCap save must still be there after the notifications-only save
        self.assertEqual(body["budget"]["cap"], 50)
        self.assertEqual(body["budget"]["quotas"], DEFAULT_SETTINGS_BLOB["budget"]["quotas"])
        # and the notifications save landed, merged over defaults rather than replacing them
        self.assertIs(body["notifications"]["weekly_digest"], True)
        self.assertEqual(body["notifications"]["recipients"], "a@b.com")
        self.assertEqual(body["notifications"]["digest_day"],
                          DEFAULT_SETTINGS_BLOB["notifications"]["digest_day"])


class SettingsPutTeamTests(APITestCase):
    """`team` is a real mutation now (commit d699575, documented in
    .claude/api-reference.md §PUT /settings) — it used to be a flat 400. The service-level
    contract is covered in test_settings_service.ApplySettingsUpdateTeamTests; this pins the
    endpoint half: a 200 rather than the old rejection, and the role actually landing."""

    def setUp(self):
        self.client_auth = _bootstrap_settings_test_env(self)
        # Second user: _bootstrap_settings_test_env's "founder1" is the first profile by id
        # and query_team_raw pins that one to Owner, which team updates deliberately skip.
        self.member = get_user_model().objects.create_user("analyst1")
        UserProfile.objects.filter(user=self.member).update(role="Analyst")

    def test_put_team_applies_the_role(self):
        resp = self.client_auth.put(
            "/api/projects/fusehealth/settings",
            {"team": [{"id": self.member.id, "role": "Admin"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.role, "Admin")


class SettingsPutRejectedKeysTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_settings_test_env(self)

    def test_put_security_is_a_clean_400_and_persists_nothing(self):
        resp = self.client_auth.put(
            "/api/projects/fusehealth/settings",
            {"security": {"twofa": True}},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(ProjectSettings.objects.filter(site_url=SITE_URL).exists())


class SettingsPutAuthAndSlugTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_settings_test_env(self)

    def test_unauthenticated_put_is_401(self):
        resp = APIClient().put(
            "/api/projects/fusehealth/settings", {"budgetCap": 10}, format="json"
        )
        self.assertEqual(resp.status_code, 401)

    def test_unknown_slug_put_is_404(self):
        resp = self.client_auth.put(
            "/api/projects/does-not-exist/settings", {"budgetCap": 10}, format="json"
        )
        self.assertEqual(resp.status_code, 404)


class SiblingProjectSettingsWriteTests(APITestCase):
    """A settings write must land on the project the caller opened, not on whichever project
    happens to be first on the domain.

    The read path resolved by primary key while the write path resolved by
    `select(Site).where(site_url == ...).first()`. One domain can be registered as several
    projects (`add_site(allow_duplicate=True)`), so editing the newer sibling's location, name,
    device, engine or language silently rewrote the OLDEST sibling's row -- and because every
    positioning read filters on the project's current location, that sibling's rankings then
    resolved to zero rows and its whole tracked list rendered as "not tracked yet". The user's
    report was "editing a project's location removed my keywords", on a project they never
    opened. Report bug C3a.
    """

    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)

        with get_session() as session:
            older = Site(site_url="dup.com", site_name="Dup Older", slug="dup",
                         location="United States", is_active=1)
            newer = Site(site_url="dup.com", site_name="Dup Newer", slug="dup-2",
                         location="United States", is_active=1)
            session.add_all([older, newer])
            session.commit()
            self.older_pk, self.newer_pk = older.id, newer.id

        user = get_user_model().objects.create_user("founder2", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def _locations(self):
        from sqlalchemy import select as sa_select
        with get_session() as session:
            rows = session.execute(
                sa_select(Site.id, Site.location, Site.site_name).order_by(Site.id)
            ).all()
        return {r[0]: (r[1], r[2]) for r in rows}

    def test_editing_the_newer_sibling_does_not_move_the_older_one(self):
        resp = self.client_auth.put(
            "/api/projects/dup-2/settings",
            {"project": {"location": "United States - Las Vegas, NV", "name": "Dup Newer"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

        rows = self._locations()
        self.assertEqual(rows[self.newer_pk][0], "United States - Las Vegas, NV")
        self.assertEqual(rows[self.older_pk][0], "United States")

    def test_editing_the_older_sibling_still_works(self):
        resp = self.client_auth.put(
            "/api/projects/dup/settings",
            {"project": {"location": "United States - Austin, TX"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

        rows = self._locations()
        self.assertEqual(rows[self.older_pk][0], "United States - Austin, TX")
        self.assertEqual(rows[self.newer_pk][0], "United States")

    def test_competitor_edit_is_also_per_project(self):
        from pipeline.services.competitor_service import get_tracked_competitors

        self.client_auth.put(
            "/api/projects/dup/settings",
            {"project": {"competitors": ["older-comp.com"]}}, format="json",
        )
        self.client_auth.put(
            "/api/projects/dup-2/settings",
            {"project": {"competitors": ["newer-comp.com"]}}, format="json",
        )

        self.assertEqual(get_tracked_competitors("dup.com", site_pk=self.older_pk),
                         ["older-comp.com"])
        self.assertEqual(get_tracked_competitors("dup.com", site_pk=self.newer_pk),
                         ["newer-comp.com"])

    def test_credentials_write_also_targets_the_opened_project(self):
        from sqlalchemy import select as sa_select

        resp = self.client_auth.put(
            "/api/projects/dup-2/settings",
            {"credentials": {"gsc_property": "sc-domain:dup.com"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

        with get_session() as session:
            rows = session.execute(
                sa_select(Site.id, Site.gsc_property).order_by(Site.id)
            ).all()
        by_pk = {r[0]: r[1] for r in rows}
        self.assertEqual(by_pk[self.newer_pk], "sc-domain:dup.com")
        self.assertIsNone(by_pk[self.older_pk])

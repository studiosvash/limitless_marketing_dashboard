"""Mutation endpoints (HANDOFF_SPEC 1): alert ack, audit toggle-check, ads write-back
intent, unknown-task contract. All must persist per project and be immediately visible
in subsequent GETs (spec 8 'Mutation -> refetch')."""
import tempfile
from datetime import date, datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Anomaly, Site, TechnicalIssue
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE = "sc-domain:fusehealth.com"


class MutationTestBase(APITestCase):
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
            session.add(Site(site_url=SITE, site_name="FuseHealth",
                             slug="fusehealth", is_active=1))
            session.add(Anomaly(date=date(2026, 6, 28), site_id=SITE,
                                metric_type="seo_clicks", actual_value=50, baseline_value=100,
                                deviation_pct=-50.0, severity="high",
                                description="Clicks dropped 50%.", is_acknowledged=0))
            session.add(TechnicalIssue(site_id=SITE, url="https://fusehealth.com/a",
                                       issue_type="not_found_404", severity="high",
                                       description="404 page", detected_at=datetime(2026, 7, 1, 12)))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")


class AlertAckTests(MutationTestBase):
    def _feed(self):
        return self.client_auth.get("/api/projects/fusehealth/alerts").json()["feed"]

    def test_ack_persists_and_feed_reflects_it(self):
        feed = self._feed()
        self.assertTrue(all(not item["acknowledged"] for item in feed))
        anomaly_id = next(i["id"] for i in feed if i["kind"] == "anomaly")

        resp = self.client_auth.post(f"/api/alerts/{anomaly_id}/ack")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})

        acked = {i["id"]: i["acknowledged"] for i in self._feed()}
        self.assertTrue(acked[anomaly_id])

    def test_ack_technical_issue_survives_row_rebuild(self):
        issue_id = next(i["id"] for i in self._feed() if i["kind"] == "technical")
        self.client_auth.post(f"/api/alerts/{issue_id}/ack")

        # Simulate the post-sync rebuild: delete + reinsert the row (new PK).
        with get_session() as session:
            session.query(TechnicalIssue).delete()
            session.add(TechnicalIssue(site_id=SITE, url="https://fusehealth.com/a",
                                       issue_type="not_found_404", severity="high",
                                       description="404 page", detected_at=datetime(2026, 7, 2, 9)))

        feed = self._feed()
        rebuilt = next(i for i in feed if i["kind"] == "technical")
        self.assertEqual(rebuilt["id"], issue_id)  # content-hash id is stable
        self.assertTrue(rebuilt["acknowledged"])

    def test_ack_is_idempotent(self):
        feed_id = self._feed()[0]["id"]
        for _ in range(3):
            self.assertEqual(self.client_auth.post(f"/api/alerts/{feed_id}/ack").status_code, 200)


class AlertUnackTests(MutationTestBase):
    """Undo for an acknowledgement. Every case here is "the feed must say unacknowledged
    again", because that flag is what the row, the sidebar badge and the bell all read."""

    def _feed(self):
        return self.client_auth.get("/api/projects/fusehealth/alerts").json()["feed"]

    def _by_kind(self, kind):
        return next(i for i in self._feed() if i["kind"] == kind)

    def test_unack_reverses_an_anomaly_ack_including_the_mirror(self):
        anomaly_id = self._by_kind("anomaly")["id"]
        self.client_auth.post(f"/api/alerts/{anomaly_id}/ack")
        self.assertTrue(self._by_kind("anomaly")["acknowledged"])

        resp = self.client_auth.post(f"/api/alerts/{anomaly_id}/unack")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})

        self.assertFalse(self._by_kind("anomaly")["acknowledged"])
        # The feed ORs alertAcks with Anomaly.is_acknowledged, so the mirror must be cleared
        # too -- clearing only the state list would leave the row acknowledged forever.
        with get_session() as session:
            row = session.query(Anomaly).one()
            self.assertFalse(bool(row.is_acknowledged))

    def test_unack_reverses_a_technical_ack(self):
        issue_id = self._by_kind("technical")["id"]
        self.client_auth.post(f"/api/alerts/{issue_id}/ack")
        self.assertTrue(self._by_kind("technical")["acknowledged"])

        self.client_auth.post(f"/api/alerts/{issue_id}/unack")
        self.assertFalse(self._by_kind("technical")["acknowledged"])

    def test_unack_reverses_acknowledge_all(self):
        ids = [i["id"] for i in self._feed()]
        self.client_auth.post("/api/alerts/ack", {"ids": ids, "project": "fusehealth"},
                              format="json")
        self.assertTrue(all(i["acknowledged"] for i in self._feed()))

        self.client_auth.post(f"/api/alerts/{ids[0]}/unack")
        after = {i["id"]: i["acknowledged"] for i in self._feed()}
        self.assertFalse(after[ids[0]])
        self.assertTrue(all(after[i] for i in ids[1:]))  # only the one row came back

    def test_unack_is_idempotent_and_safe_on_a_never_acked_alert(self):
        feed_id = self._feed()[0]["id"]
        for _ in range(3):
            self.assertEqual(self.client_auth.post(f"/api/alerts/{feed_id}/unack").status_code, 200)
        self.assertFalse(self._feed()[0]["acknowledged"])

    def test_ack_after_unack_acknowledges_again(self):
        feed_id = self._by_kind("anomaly")["id"]
        self.client_auth.post(f"/api/alerts/{feed_id}/ack")
        self.client_auth.post(f"/api/alerts/{feed_id}/unack")
        self.client_auth.post(f"/api/alerts/{feed_id}/ack")
        self.assertTrue(self._by_kind("anomaly")["acknowledged"])

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().post("/api/alerts/anomaly-1/unack").status_code, 401)


class AuditToggleCheckTests(MutationTestBase):
    def test_toggle_hides_check_and_recomputes_totals(self):
        before = self.client_auth.get("/api/projects/fusehealth/audit").json()
        self.assertEqual(before["totals"]["errors"], 1)

        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-check",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"hidden": ["not_found_404"]})

        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check["hidden"])
        self.assertEqual(after["totals"]["errors"], 0)  # spec 2.4: totals over non-hidden only

    def test_second_toggle_restores(self):
        self.client_auth.post("/api/projects/fusehealth/audit/toggle-check",
                              {"checkId": "not_found_404"}, format="json")
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-check",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.json(), {"hidden": []})

    def test_missing_checkid_is_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-check", {}, format="json")
        self.assertEqual(resp.status_code, 400)


class AuditToggleResolvedTests(MutationTestBase):
    def test_toggle_resolves_check_and_excludes_it_from_totals(self):
        before = self.client_auth.get("/api/projects/fusehealth/audit").json()
        self.assertEqual(before["totals"]["errors"], 1)

        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-resolved",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"resolved": ["not_found_404"]})

        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check["resolved"])
        self.assertEqual(after["totals"]["errors"], 0)  # excluded from totals like hidden checks

    def test_second_toggle_unresolves(self):
        self.client_auth.post("/api/projects/fusehealth/audit/toggle-resolved",
                              {"checkId": "not_found_404"}, format="json")
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-resolved",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.json(), {"resolved": []})

    def test_missing_checkid_is_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-resolved", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_recurrence_auto_unresolves(self):
        """A resolved check whose affected pages changed since it was marked resolved (the
        issue recurred, or a new page tripped the same check) must render active again on
        the next read -- it must not silently stay buried in the Resolved tab."""
        self.client_auth.post("/api/projects/fusehealth/audit/toggle-resolved",
                              {"checkId": "not_found_404"}, format="json")
        resolved = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in resolved["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check["resolved"])

        # A new page trips the same check -- simulates the next crawl finding a fresh 404
        # under an issue_type that was previously marked resolved with a different page set.
        with get_session() as session:
            session.add(TechnicalIssue(site_id=SITE, url="https://fusehealth.com/b",
                                       issue_type="not_found_404", severity="high",
                                       description="404 page", detected_at=datetime(2026, 7, 3, 9)))

        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check_after = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertFalse(check_after["resolved"])
        self.assertEqual(after["totals"]["errors"], 2)  # both pages counted again


class AuditTogglePageResolvedTests(MutationTestBase):
    def test_toggle_resolves_single_page(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                                     format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"resolved": ["https://fusehealth.com/a"]})

        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in after["checks"] if c["id"] == "not_found_404")
        page = next(p for p in check["pages"] if p["url"] == "https://fusehealth.com/a")
        self.assertTrue(page["resolved"])

    def test_second_toggle_unresolves_the_page(self):
        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                              format="json")
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                                     format="json")
        self.assertEqual(resp.json(), {"resolved": []})

    def test_missing_url_is_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_missing_checkid_is_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"url": "https://fusehealth.com/a"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_check_resolves_once_every_current_page_is_acknowledged(self):
        """Fixture seeds ONE not_found_404 page (see MutationTestBase.setUp). Add a second
        so the check has two current pages, then confirm it only flips to resolved once
        BOTH are acknowledged -- not on the first one."""
        with get_session() as session:
            session.add(TechnicalIssue(site_id=SITE, url="https://fusehealth.com/b",
                                       issue_type="not_found_404", severity="high",
                                       description="404 page", detected_at=datetime(2026, 7, 3, 9)))

        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                              format="json")
        mid = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check_mid = next(c for c in mid["checks"] if c["id"] == "not_found_404")
        self.assertFalse(check_mid["resolved"])  # /b still unacknowledged
        page_a = next(p for p in check_mid["pages"] if p["url"] == "https://fusehealth.com/a")
        self.assertTrue(page_a["resolved"])

        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/b"},
                              format="json")
        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check_after = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check_after["resolved"])
        self.assertEqual(after["totals"]["errors"], 0)

    def test_whole_check_resolve_still_works(self):
        """Regression: the existing bulk 'Mark as resolved' button must still resolve a
        check in one call after is_resolved switches from equality to a subset check."""
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-resolved",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.status_code, 200)
        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check["resolved"])

    def test_resolved_check_reverts_when_a_new_unacknowledged_page_appears(self):
        """A check fully resolved page-by-page must drop back to active the moment a later
        crawl adds a page under it that was never acknowledged -- while the page that WAS
        acknowledged keeps its own resolved:true. Mirrors AuditToggleResolvedTests'
        test_recurrence_auto_unresolves, but for the per-page path."""
        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                              format="json")
        resolved = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in resolved["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check["resolved"])

        with get_session() as session:
            session.add(TechnicalIssue(site_id=SITE, url="https://fusehealth.com/c",
                                       issue_type="not_found_404", severity="high",
                                       description="404 page", detected_at=datetime(2026, 7, 4, 9)))

        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check_after = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertFalse(check_after["resolved"])
        page_a = next(p for p in check_after["pages"] if p["url"] == "https://fusehealth.com/a")
        page_c = next(p for p in check_after["pages"] if p["url"] == "https://fusehealth.com/c")
        self.assertTrue(page_a["resolved"])
        self.assertFalse(page_c["resolved"])


class AdsMutationTests(MutationTestBase):
    def test_budget_rounds_to_int_min_1(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ads/budget",
                                     {"campaignId": "c1", "budgetDaily": 0.2}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "budgetDaily": 1})

        resp = self.client_auth.post("/api/projects/fusehealth/ads/budget",
                                     {"campaignId": "c1", "budgetDaily": 38.6}, format="json")
        self.assertEqual(resp.json()["budgetDaily"], 39)

    def test_budget_non_number_is_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ads/budget",
                                     {"campaignId": "c1", "budgetDaily": "abc"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_status_validates_enum(self):
        ok = self.client_auth.post("/api/projects/fusehealth/ads/status",
                                   {"campaignId": "c1", "status": "paused"}, format="json")
        self.assertEqual(ok.json(), {"ok": True, "status": "paused"})
        bad = self.client_auth.post("/api/projects/fusehealth/ads/status",
                                    {"campaignId": "c1", "status": "deleted"}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_negatives_persist_dedupe_and_show_in_ads_get(self):
        for _ in range(2):
            resp = self.client_auth.post("/api/projects/fusehealth/ads/negatives",
                                         {"term": "free iv", "matchType": "phrase"}, format="json")
            self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["negatives"]), 1)

        ads = self.client_auth.get("/api/projects/fusehealth/ads?range=30d").json()
        self.assertEqual(ads["negatives"],
                         [{"term": "free iv", "matchType": "phrase", "campaignId": None}])

    def test_promote_returns_spec_keyword_shape(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ads/promote",
                                     {"term": "iv therapy near me"}, format="json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["keyword"]["kw"], "iv therapy near me")
        self.assertEqual(body["keyword"]["source"], "ads_term")


class TaskContractTests(MutationTestBase):
    def test_unknown_task_returns_done_true(self):
        resp = self.client_auth.get("/api/tasks/999999")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["done"])

"""Tests for POST /api/domain-overview and its service layer.

Domain Overview is one of the four sanctioned live-lookup endpoints (a human pressed a
button). Everything here therefore either patches the connector away or asserts that it was
never constructed -- no test in this module may reach the network. The fake connector class
below is the whole mechanism: it records its calls and returns a fixed payload, mirroring
`pipeline/connectors/tests/test_gsc_property.py`'s injection pattern.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session

SITE_URL = "example.com"

_OK_PAYLOAD = {
    "status": "ok",
    "metrics": {"organic_traffic": 1234.5, "traffic_value": 987.0, "ranked_keywords": 42},
    "keywords": [
        {"keyword": "widget repair", "intent": "Commercial", "position": 3,
         "volume": 900, "cpc": 1.25, "traffic": 120.0, "url": "https://example.com/a"},
        {"keyword": "blue widgets", "intent": "Informational", "position": 11,
         "volume": 300, "cpc": 0.4, "traffic": 12.0, "url": "https://example.com/b"},
    ],
    "target": "example.com",
    "domain": "example.com",
    "path": "",
    "location": "United States",
    "requested_location": "United States",
    "location_downgraded": False,
    "cost": 0.011,
}


class FakeOverviewConnector:
    """Stands in for DataForSEODomainOverviewConnector. Never touches the network."""

    instances = []

    def __init__(self):
        self.calls = []
        FakeOverviewConnector.instances.append(self)

    def get_domain_overview(self, target, location_name="United States", limit=50, site_id=""):
        self.calls.append({"target": target, "location_name": location_name,
                           "limit": limit, "site_id": site_id})
        return dict(_OK_PAYLOAD)


class ExplodingOverviewConnector:
    """Constructing this is a test failure -- used to prove a call was refused/served
    from cache before any DataForSEO request could be made."""

    def __init__(self):
        raise AssertionError("DataForSEO connector must not be constructed here")


def _bootstrap(test_case):
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)

    with get_session() as session:
        session.add(Site(site_url=SITE_URL, site_name="Example", slug="example", is_active=1))

    cache.clear()
    test_case.addCleanup(cache.clear)
    FakeOverviewConnector.instances = []

    user = get_user_model().objects.create_user("do_tester", password="x")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {Token.objects.get(user=user).key}")
    return client


class DomainOverviewEndpointTests(APITestCase):
    """The refactor that moved the cache + tracked-flag join out of the view and into
    apps/dashboard/services/domain_overview_service.py must be invisible from outside."""

    def setUp(self):
        self.client_auth = _bootstrap(self)

    def test_missing_target_is_400(self):
        resp = self.client_auth.post("/api/domain-overview", {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.json())

    @patch("pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
           FakeOverviewConnector)
    def test_response_shape_is_unchanged(self):
        resp = self.client_auth.post("/api/domain-overview",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ("status", "metrics", "keywords", "target", "domain", "path",
                    "location", "requested_location", "location_downgraded", "cost"):
            self.assertIn(key, body, f"{key} disappeared from the domain-overview response")
        self.assertEqual(body["metrics"]["ranked_keywords"], 42)
        self.assertEqual(len(body["keywords"]), 2)
        # No project in the body -> no tracked flag at all (absent, not False).
        self.assertNotIn("tracked", body["keywords"][0])

    @patch("pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
           FakeOverviewConnector)
    def test_second_lookup_is_served_from_the_24h_cache(self):
        for _ in range(2):
            resp = self.client_auth.post("/api/domain-overview",
                                         {"target": "example.com"}, format="json")
            self.assertEqual(resp.status_code, 200)
        # One connector instance, one billed call -- the second press cost nothing.
        self.assertEqual(len(FakeOverviewConnector.instances), 1)
        self.assertEqual(len(FakeOverviewConnector.instances[0].calls), 1)

    @patch("pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
           FakeOverviewConnector)
    def test_project_attributes_the_spend_and_joins_tracked_keywords(self):
        from pipeline.services.saved_keyword_service import save_keywords
        with get_session() as session:
            site = session.query(Site).filter(Site.slug == "example").first()
            site_pk = site.id
        save_keywords(SITE_URL, [{"keyword": "widget repair"}], site_pk=site_pk)

        resp = self.client_auth.post(
            "/api/domain-overview", {"target": "example.com", "project": "example"}, format="json")
        self.assertEqual(resp.status_code, 200)
        rows = {r["keyword"]: r for r in resp.json()["keywords"]}
        self.assertTrue(rows["widget repair"]["tracked"])
        self.assertFalse(rows["blue widgets"]["tracked"])
        # The metered call is booked against the project, not the unattributed "" site.
        self.assertEqual(FakeOverviewConnector.instances[0].calls[0]["site_id"], SITE_URL)

    def test_unknown_project_slug_404s(self):
        resp = self.client_auth.post(
            "/api/domain-overview", {"target": "example.com", "project": "nope"}, format="json")
        self.assertEqual(resp.status_code, 404)


class DomainOverviewBudgetGateTests(APITestCase):
    """`record_cost` only ever NOTIFIED on a budget crossing; nothing refused a call. A
    repeatedly-pressed live lookup was therefore an uncapped spend vector."""

    def setUp(self):
        self.client_auth = _bootstrap(self)

    @patch("pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
           ExplodingOverviewConnector)
    @patch("apps.dashboard.services.budget_service.budget_status")
    def test_lookup_is_refused_once_the_configured_cap_is_crossed(self, mock_status):
        mock_status.return_value = {"cap": 100.0, "spent": 141.2, "remaining": 0.0,
                                    "pct": 100.0, "red": True, "exceeded": True,
                                    "balance": None, "balance_checked_at": None}
        resp = self.client_auth.post("/api/domain-overview",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "error")
        self.assertIn("Monthly DataForSEO budget reached", body["error"])
        self.assertTrue(body.get("budget_exceeded"))

    @patch("pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
           FakeOverviewConnector)
    @patch("apps.dashboard.services.budget_service.budget_status")
    def test_no_cap_configured_changes_nothing(self, mock_status):
        # cap <= 0 means "no cap configured" -- the deployment opted out, so the lookup runs
        # exactly as it did before this gate existed.
        mock_status.return_value = {"cap": 0.0, "spent": 999.0, "remaining": 0.0,
                                    "pct": 0.0, "red": False, "exceeded": True,
                                    "balance": None, "balance_checked_at": None}
        resp = self.client_auth.post("/api/domain-overview",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.json()["status"], "ok")

    @patch("pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
           FakeOverviewConnector)
    @patch("apps.dashboard.services.budget_service.budget_status")
    def test_under_the_cap_runs_normally(self, mock_status):
        mock_status.return_value = {"cap": 100.0, "spent": 12.0, "remaining": 88.0,
                                    "pct": 12.0, "red": False, "exceeded": False,
                                    "balance": None, "balance_checked_at": None}
        resp = self.client_auth.post("/api/domain-overview",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.json()["status"], "ok")

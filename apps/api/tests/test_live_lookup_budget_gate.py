"""Every metered live-lookup endpoint refuses once the configured cap is crossed.

`record_cost` -> `check_and_notify_budget` only ever NOTIFIED; nothing refused a call. So a
repeatedly-pressed live lookup was an uncapped spend vector — the budget page could watch the
number climb past the cap and had no way to stop it.

Phase 7 added `ensure_budget()` and wired it into `/api/domain-overview`. The Keyword Explorer
(`/api/research`) is the MOST expensive of the four — one press fans out to keyword_ideas,
related_keywords, keyword_suggestions and question ideas, several of them one task per seed —
and `/api/live-serp` is metered per press too. Both were left ungated, which is the hole this
closes.

`/api/connection-check` is deliberately NOT gated: its DataForSEO probe is the free
`appendix/user_data` balance call, so refusing it would block credential setup to save nothing.

A cap of 0 means NO CAP IS CONFIGURED and nothing is ever refused — that is the opt-out, and it
is what every deployment that has not set one gets.
"""
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import Site, init_db
from pipeline.utils.db_connection import get_session

SITE_URL = "example.com"

_EXCEEDED = {"cap": 100.0, "spent": 140.0, "exceeded": True, "pct": 140}
_HEADROOM = {"cap": 100.0, "spent": 12.0, "exceeded": False, "pct": 12}
_NO_CAP = {"cap": 0, "spent": 400.0, "exceeded": True, "pct": 0}


class LiveLookupBudgetGateTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None

        with get_session() as session:
            session.add(Site(site_url=SITE_URL, site_name="Example", slug="example",
                             is_active=1))
            session.commit()

        user = get_user_model().objects.create_user("budgettester", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    @staticmethod
    def _budget(status):
        return mock.patch(
            "apps.dashboard.services.budget_service.budget_status", return_value=status
        )

    def test_research_refuses_over_cap_without_calling_dataforseo(self):
        # Patched where the VIEW looks it up, not where it is defined: views.py imports the
        # name at module load, so patching the source module would leave the view holding the
        # original function and the assertion would pass for the wrong reason.
        with self._budget(_EXCEEDED), \
             mock.patch("apps.api.views.run_keyword_research") as run:
            resp = self.client_auth.post(
                "/api/research",
                {"project": "example", "keywords": ["event staffing"]},
                format="json",
            )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body.get("status"), "error")
        self.assertTrue(body.get("budget_exceeded"))
        run.assert_not_called()

    def test_live_serp_refuses_over_cap_without_calling_dataforseo(self):
        with self._budget(_EXCEEDED), \
             mock.patch("pipeline.connectors.dataforseo_live_serp.DataForSEOLiveSERPConnector") as conn:
            resp = self.client_auth.post(
                "/api/live-serp", {"keyword": "event staffing"}, format="json",
            )

        body = resp.json()
        self.assertTrue(body.get("budget_exceeded"))
        conn.assert_not_called()

    def test_a_cap_with_headroom_does_not_refuse(self):
        with self._budget(_HEADROOM), \
             mock.patch("apps.api.views.run_keyword_research",
                        return_value={"rows": [], "cost": 0.0, "location": "United States",
                                      "status": "ok"}) as run:
            resp = self.client_auth.post(
                "/api/research",
                {"project": "example", "keywords": ["event staffing"]},
                format="json",
            )

        self.assertNotIn("budget_exceeded", resp.json())
        run.assert_called_once()

    def test_no_configured_cap_never_refuses(self):
        """cap <= 0 is the documented opt-out, even with spend far above it."""
        with self._budget(_NO_CAP), \
             mock.patch("apps.api.views.run_keyword_research",
                        return_value={"rows": [], "cost": 0.0, "location": "United States",
                                      "status": "ok"}) as run:
            resp = self.client_auth.post(
                "/api/research",
                {"project": "example", "keywords": ["event staffing"]},
                format="json",
            )

        self.assertNotIn("budget_exceeded", resp.json())
        run.assert_called_once()

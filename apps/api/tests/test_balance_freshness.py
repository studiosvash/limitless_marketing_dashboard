"""The account balance must reflect spend from ANY page, not just from a sync.

Reported from Settings -> Usage & Budget: "Available balance $16.45 · Checked 4d ago". The
balance was re-probed in exactly one place -- `sync_engine`, after a sync run -- so every
metered call made outside a sync left the figure untouched. A Domain Overview lookup, a
Keyword Explorer search, a live SERP check and an AI prompt run all spend real money, and the
balance beside them could sit days out of date while claiming to be the account's state.

The fix deliberately does NOT probe inside `record_cost`. That is the one chokepoint every
metered call flows through, but it also runs inside sync loops and inside the request cycle of
the live lookups -- adding a network round-trip there would slow the user's own request down to
report on the money it had just spent. Instead:

  * spend WRITES a row into `connector_costs` with `run_at` (it already did);
  * the balance read asks "is there spend newer than my last probe?" and re-probes if so.

So no schema change, nothing to keep in sync, and the staleness question is answered by the
data itself rather than by a flag someone has to remember to set.

`ensure_budget()` (the spend gate) is deliberately left alone: it needs `spent`, which is
already live from the cost table, and it must not turn every gated lookup into a probe.
"""
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone as dj_timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

import pipeline.utils.db_connection as db_connection
from apps.dashboard.models import BudgetState
from pipeline.db.engine import get_engine
from pipeline.db.schema import ConnectorCost, init_db
from pipeline.utils.db_connection import get_session

SITE = "example.com"


class BalanceFreshnessTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None

        user = get_user_model().objects.create_user("balancetester", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    @staticmethod
    def _spend(when):
        """One metered call, recorded the way record_cost records it."""
        with get_session() as session:
            session.add(ConnectorCost(site_id=SITE, connector="dataforseo_domain_overview",
                                      run_at=when, cost=0.02, units=50))
            session.commit()

    def _state(self, checked_at, balance=16.45):
        BudgetState.objects.update_or_create(
            pk=1, defaults={"dataforseo_balance": balance, "balance_checked_at": checked_at})

    def test_spend_since_the_last_probe_triggers_a_refresh(self):
        four_days_ago = dj_timezone.now() - timedelta(days=4)
        self._state(four_days_ago)
        # A Domain Overview lookup an hour ago -- money spent, balance never re-read.
        self._spend(datetime.now().replace(microsecond=0) - timedelta(hours=1))

        with mock.patch("pipeline.connectors.dataforseo_probe.fetch_balance",
                        return_value=12.10) as probe:
            body = self.client_auth.get("/api/budget-status").json()

        probe.assert_called_once()
        self.assertEqual(body["balance"], 12.10)

    def test_no_spend_since_the_last_probe_does_not_re_probe(self):
        """The balance costs nothing to read, but it is still a network round-trip; a page
        refresh with no spend in between must not make one."""
        self._state(dj_timezone.now() - timedelta(minutes=5))
        self._spend(datetime.now().replace(microsecond=0) - timedelta(days=2))

        with mock.patch("pipeline.connectors.dataforseo_probe.fetch_balance",
                        return_value=99.0) as probe:
            body = self.client_auth.get("/api/budget-status").json()

        probe.assert_not_called()
        self.assertEqual(body["balance"], 16.45)

    def test_a_balance_never_probed_is_fetched_once(self):
        BudgetState.objects.filter(pk=1).delete()
        with mock.patch("pipeline.connectors.dataforseo_probe.fetch_balance",
                        return_value=20.0) as probe:
            body = self.client_auth.get("/api/budget-status").json()
        probe.assert_called_once()
        self.assertEqual(body["balance"], 20.0)

    def test_a_failed_probe_keeps_the_last_known_figure(self):
        """A probe that cannot be read must not blank a real number the user was relying on."""
        self._state(dj_timezone.now() - timedelta(days=4))
        self._spend(datetime.now().replace(microsecond=0))

        with mock.patch("pipeline.connectors.dataforseo_probe.fetch_balance",
                        return_value=None):
            body = self.client_auth.get("/api/budget-status").json()

        self.assertEqual(body["balance"], 16.45)

    def test_the_gate_does_not_probe(self):
        """ensure_budget() runs on every live lookup and needs only `spent`. Probing there
        would add a network call to each one, which is the latency this design avoids."""
        from pipeline.connectors.dataforseo_cost import ensure_budget

        self._state(dj_timezone.now() - timedelta(days=4))
        self._spend(datetime.now().replace(microsecond=0))

        with mock.patch("pipeline.connectors.dataforseo_probe.fetch_balance",
                        return_value=1.0) as probe:
            ensure_budget()

        probe.assert_not_called()

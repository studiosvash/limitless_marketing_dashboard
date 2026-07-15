# Phase B4 — Alerts Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the Alerts page through `GET /api/projects/<slug>/alerts`, extract the
shared range/period-resolve helper B3's final review recommended, and close a gap Phase A
deliberately left open (Overview's `priority[]` field, empty since "Alerts feed is Phase B").
Completing this phase closes out Phase B (SEO, Keywords, Position Tracking, Alerts) entirely.

**Architecture:** Task 1 is a small cross-cutting refactor. Tasks 2-4 follow the established
extract → build API shape → wire endpoint pattern. Task 5 wires Overview's `priority` field
using Task 3's new alerts builder — the first real cross-page reuse in this project (Overview
consuming Alerts' data), closing the loop Phase A intentionally left open.

**Tech Stack:** Django 6.0, DRF, SQLAlchemy 2.x.

## Global Constraints

- Never call an external API from a page-rendering or API-reading view — DB-only reads.
- Route: `GET /api/projects/<slug>/alerts`, no trailing slash, **no `range` param** — alerts
  are current-state, not period-scoped (per `HANDOFF_SPEC.md`'s endpoint table).
- Feed item `id` is source-prefixed: `f"anomaly-{Anomaly.id}"` / `f"issue-{TechnicalIssue.id}"`
  — must stay unique and stable across the two source tables.
- `acknowledged` is real `Anomaly.is_acknowledged` for `kind="anomaly"` items; honestly
  hardcoded `false` for `kind="technical"` items (no ack column exists on `TechnicalIssue` —
  this is not fabrication, it's an accurate reflection of current capability).
- The new unlimited raw-query functions (`query_alert_anomalies_raw`,
  `query_alert_technical_issues_raw`) are NEW, separate from the existing display-capped
  `_get_all_anomalies`/`_get_technical_issues` — do NOT modify those (they stay serving the
  old page's capped display tables, unchanged).
- `POST /api/alerts/<id>/ack` mutation is explicitly OUT of scope for this plan.
- `pipeline.utils.db_connection.get_session()` memoizes its engine per-process — every test
  needing an isolated temp DB must reset `db_connection._SessionFactory = None` in
  `setUp`/`addCleanup`.
- **Test-class inheritance footgun** (hit multiple times across this project): any new test
  class must have its OWN `setUp()`, inherit `TestCase`/`APITestCase` directly, never a
  sibling test class. Verify with `-v 2` before committing that every test name appears
  exactly once.

---

### Task 1: Extract `resolve_range_periods` shared helper, retrofit Overview + Positions

**Files:**
- Modify: `apps/api/views.py`
- Modify: `apps/api/tests/test_overview.py`

**Interfaces:**
- Produces: `resolve_range_periods(request, slug: str) -> tuple[str, date, date, date, date]`
  — returns `(site_id, curr_start, curr_end, prev_start, prev_end)`. Wraps
  `resolve_project_or_404` + `OverviewQuerySerializer` validation + `latest_data_anchor` +
  `range_to_period_dates` in one call. Consumed by `ProjectOverviewView`, `ProjectPositionsView`
  (retrofitted here) and any future range-taking endpoint.

This is a pure refactor — zero behavior change to either existing endpoint's response.

- [ ] **Step 1: Write the failing test**

Add to `apps/api/tests/test_overview.py` (reuse the imports already present in the file, same
as the existing `ResolveProjectHelperTests` class does):

```python
class ResolveRangePeriodsTests(APITestCase):
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
            session.add(Site(site_url="sc-domain:fusehealth.com", site_name="FuseHealth",
                              slug="fusehealth", is_active=1))
            session.add(SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                  clicks=1, impressions=1, ctr=0.1, avg_position=1.0))

    def test_resolves_site_id_and_period_dates(self):
        from django.test import RequestFactory
        from apps.api.views import resolve_range_periods

        request = RequestFactory().get("/api/projects/fusehealth/positions", {"range": "7d"})
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, "fusehealth")
        self.assertEqual(site_id, "sc-domain:fusehealth.com")
        self.assertEqual((curr_end - curr_start).days, 6)

    def test_defaults_range_to_30d_when_absent(self):
        from django.test import RequestFactory
        from apps.api.views import resolve_range_periods

        request = RequestFactory().get("/api/projects/fusehealth/positions")
        _, curr_start, curr_end, _, _ = resolve_range_periods(request, "fusehealth")
        self.assertEqual((curr_end - curr_start).days, 29)

    def test_unknown_slug_raises_404(self):
        from django.http import Http404
        from django.test import RequestFactory
        from apps.api.views import resolve_range_periods

        request = RequestFactory().get("/api/projects/does-not-exist/positions")
        with self.assertRaises(Http404):
            resolve_range_periods(request, "does-not-exist")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.api.tests.test_overview.ResolveRangePeriodsTests`
Expected: FAIL — `ImportError: cannot import name 'resolve_range_periods'`.

- [ ] **Step 3: Implement the helper**

In `apps/api/views.py`, add after `latest_data_anchor` (before the `login_not_required`
comment block):

```python
def resolve_range_periods(request, slug: str):
    """Resolve a range-taking view's full request context in one call: site lookup (404 on
    unknown slug), `range` query param validation (default 30d), and period-date resolution
    anchored to the latest data date. Returns (site_id, curr_start, curr_end, prev_start,
    prev_end). Used by every apps.api view that takes both a `slug` and a `range` param."""
    site_id = resolve_project_or_404(slug).site_url

    query = OverviewQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    range_key = query.validated_data["range"]

    anchor = latest_data_anchor(site_id)
    curr_start, curr_end, prev_start, prev_end = range_to_period_dates(range_key, anchor)
    return site_id, curr_start, curr_end, prev_start, prev_end
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.api.tests.test_overview.ResolveRangePeriodsTests`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 5: Retrofit `ProjectOverviewView` and `ProjectPositionsView`**

In `ProjectOverviewView.get`, replace:

```python
        site_id = resolve_project_or_404(slug).site_url

        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        range_key = query.validated_data["range"]

        anchor = latest_data_anchor(site_id)

        curr_start, curr_end, prev_start, prev_end = range_to_period_dates(range_key, anchor)
```

with:

```python
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)
```

In `ProjectPositionsView.get`, replace:

```python
        site_id = resolve_project_or_404(slug).site_url

        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        range_key = query.validated_data["range"]

        anchor = latest_data_anchor(site_id)
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates(range_key, anchor)
```

with:

```python
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)
```

- [ ] **Step 6: Run the full test suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all tests pass (baseline 108 + 3 new = 111). `apps.api.tests.test_overview`'s and
`apps.api.tests.test_positions`'s EXISTING tests must pass completely unchanged — this proves
the retrofit is behavior-preserving.

- [ ] **Step 7: Commit**

```bash
git add apps/api/views.py apps/api/tests/test_overview.py
git commit -m "refactor(api): extract resolve_range_periods, retrofit Overview + Positions"
```

---

### Task 2: Extract unlimited alerts raw calculators

**Files:**
- Create: `apps/dashboard/services/alerts_service.py`
- Create: `apps/dashboard/services/tests/test_alerts_service.py`

**Interfaces:**
- Produces: `query_alert_anomalies_raw(site_id: str) -> list[dict]` — ALL (unlimited)
  `Anomaly` rows for the site, not just unacknowledged/capped-at-N like the old page's
  helpers. Fields: `id, date, metric_type, severity, deviation_pct, actual_value,
  baseline_value, description, is_acknowledged, direction`.
- Produces: `query_alert_technical_issues_raw(site_id: str) -> list[dict]` — ALL (unlimited)
  `TechnicalIssue` rows. Fields: `id, url, issue_type, severity, description, detected_at`.
- Consumed by: Task 3's `build_alerts_response`.

This task creates NEW functions — it does not touch `_get_all_anomalies` or
`_get_technical_issues` in `apps/dashboard/views.py` (those keep serving the old page's
capped display tables, unmodified).

- [ ] **Step 1: Write the failing tests**

Create `apps/dashboard/services/tests/test_alerts_service.py`:

```python
import tempfile
from datetime import date, datetime
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class AlertsRawQueryTests(TestCase):
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
            session.add_all([
                Anomaly(date=date(2026, 6, 28), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_clicks", actual_value=50, baseline_value=100,
                        deviation_pct=-50.0, severity="high",
                        description="Clicks dropped 50%.", is_acknowledged=0),
                Anomaly(date=date(2026, 6, 20), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_impressions", actual_value=900, baseline_value=800,
                        deviation_pct=12.5, severity="info",
                        description="Impressions up 12.5%.", is_acknowledged=1),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                               issue_type="not_found_404", severity="high",
                               description="404 detected"),
            ])

    def test_query_alert_anomalies_raw_returns_all_including_acknowledged(self):
        from apps.dashboard.services.alerts_service import query_alert_anomalies_raw
        rows = query_alert_anomalies_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 2)
        acked = [r for r in rows if r["is_acknowledged"]]
        self.assertEqual(len(acked), 1)

    def test_query_alert_technical_issues_raw_returns_all(self):
        from apps.dashboard.services.alerts_service import query_alert_technical_issues_raw
        rows = query_alert_technical_issues_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["issue_type"], "not_found_404")

    def test_query_alert_anomalies_raw_returns_empty_list_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import alerts_service
        with mock.patch.object(alerts_service, "get_session", side_effect=RuntimeError("boom")):
            self.assertEqual(alerts_service.query_alert_anomalies_raw("x"), [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_alerts_service`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Create the service module**

Create `apps/dashboard/services/alerts_service.py`:

```python
"""Alerts page data — raw calculators for the new API's unified feed[]. These are NEW,
unlimited-count functions — separate from apps.dashboard.views' _get_all_anomalies/
_get_technical_issues, which stay capped for the old page's display tables and are
unmodified by this module. See
docs/superpowers/specs/2026-07-11-phaseB4-alerts-design.md for the feed field mapping."""

from sqlalchemy import select

from pipeline.db.schema import Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session


def query_alert_anomalies_raw(site_id: str) -> list[dict]:
    """All Anomaly rows for the site (not just unacknowledged, not capped) — the new
    alerts feed shows full history, filtering/paging is a frontend concern."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(Anomaly).where(Anomaly.site_id == site_id).order_by(Anomaly.date.desc())
            ).scalars().all()
            out = []
            for r in rows:
                up = r.actual_value >= r.baseline_value
                out.append({
                    "id": r.id,
                    "date": r.date,
                    "metric_type": r.metric_type,
                    "severity": r.severity,
                    "direction": "up" if up else "down",
                    "deviation_pct": r.deviation_pct,
                    "description": r.description or "",
                    "is_acknowledged": bool(r.is_acknowledged),
                })
            return out
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_alert_anomalies_raw error: {e}", exc_info=True)
        return []


def query_alert_technical_issues_raw(site_id: str) -> list[dict]:
    """All TechnicalIssue rows for the site (unlimited — the old page's _get_technical_issues
    caps at 15 for its own display table; this is a separate, unlimited function)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(TechnicalIssue).where(TechnicalIssue.site_id == site_id)
                .order_by(TechnicalIssue.detected_at.desc())
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "url": r.url,
                    "issue_type": r.issue_type,
                    "severity": r.severity or "medium",
                    "description": r.description or "",
                    "detected_at": r.detected_at,
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_alert_technical_issues_raw error: {e}", exc_info=True)
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_alerts_service`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass (111 baseline + 3 new = 114).

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/alerts_service.py apps/dashboard/services/tests/test_alerts_service.py
git commit -m "feat(dashboard): add unlimited alerts raw calculators (alerts_service.py)"
```

---

### Task 3: `build_alerts_response` builder

**Files:**
- Modify: `apps/dashboard/services/alerts_service.py`
- Modify: `apps/dashboard/services/tests/test_alerts_service.py`

**Interfaces:**
- Consumes: `query_alert_anomalies_raw`, `query_alert_technical_issues_raw` (Task 2).
- Produces: `build_alerts_response(site_id: str) -> dict` — `{feed: [...]}`, each item
  `{id, ts, kind, severity, title, detail, acknowledged}`, source-prefixed `id`, sorted by
  date descending then severity (high → medium/info → low... use `{"high": 0, "medium": 1,
  "info": 2, "low": 3}` as the severity rank, matching the existing `sevRank` convention
  already used in the real SPA's own overview-priority-feed logic). Consumed by Task 4's
  endpoint AND Task 5's Overview `priority` field.

- [ ] **Step 1: Write the failing tests**

Append to `apps/dashboard/services/tests/test_alerts_service.py` (new class, own `setUp`
duplicating `AlertsRawQueryTests`'s fixture — do NOT inherit from it):

```python
class BuildAlertsResponseTests(TestCase):
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
            session.add_all([
                Anomaly(date=date(2026, 6, 28), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_clicks", actual_value=50, baseline_value=100,
                        deviation_pct=-50.0, severity="high",
                        description="Clicks dropped 50%.", is_acknowledged=0),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                               issue_type="not_found_404", severity="high",
                               description="404 detected"),
            ])

    def test_feed_has_both_kinds_with_source_prefixed_ids(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        self.assertIn("feed", body)
        kinds = {item["kind"] for item in body["feed"]}
        self.assertEqual(kinds, {"anomaly", "technical"})
        ids = {item["id"] for item in body["feed"]}
        self.assertTrue(any(i.startswith("anomaly-") for i in ids))
        self.assertTrue(any(i.startswith("issue-") for i in ids))

    def test_anomaly_item_has_real_acknowledged_state(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        anomaly_item = next(i for i in body["feed"] if i["kind"] == "anomaly")
        self.assertFalse(anomaly_item["acknowledged"])

    def test_technical_item_always_reports_unacknowledged(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        issue_item = next(i for i in body["feed"] if i["kind"] == "technical")
        self.assertFalse(issue_item["acknowledged"])

    def test_feed_item_shape(self):
        from apps.dashboard.services.alerts_service import build_alerts_response
        body = build_alerts_response("sc-domain:fusehealth.com")
        for item in body["feed"]:
            for key in ["id", "ts", "kind", "severity", "title", "detail", "acknowledged"]:
                self.assertIn(key, item)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_alerts_service.BuildAlertsResponseTests`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

Add to `apps/dashboard/services/alerts_service.py`:

```python
_METRIC_LABELS = {
    "seo_clicks": "Clicks", "seo_impressions": "Impressions",
    "seo_ctr": "CTR", "seo_avg_position": "Avg. position",
    "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
    "ad_impressions": "Ad impressions", "ad_conversions": "Conversions",
}
_ISSUE_LABELS = {
    "not_found_404": "404 — Not found",
    "crawled_not_indexed": "Crawled, not indexed",
    "page_with_redirect": "Redirect",
    "long_url": "Long URL",
}
_SEVERITY_RANK = {"high": 0, "medium": 1, "info": 2, "low": 3}


def build_alerts_response(site_id: str) -> dict:
    """HANDOFF_SPEC.md `alerts` view shape: {feed: [{id, ts, kind, severity, title, detail,
    acknowledged}]}. See docs/superpowers/specs/2026-07-11-phaseB4-alerts-design.md."""
    anomalies = query_alert_anomalies_raw(site_id)
    issues = query_alert_technical_issues_raw(site_id)

    feed = []
    for a in anomalies:
        metric_label = _METRIC_LABELS.get(a["metric_type"], a["metric_type"])
        pct = f"{'+' if a['direction'] == 'up' else '-'}{abs(a['deviation_pct']):.0f}%"
        feed.append({
            "id": f"anomaly-{a['id']}",
            "ts": str(a["date"]),
            "kind": "anomaly",
            "severity": a["severity"],
            "title": f"{metric_label} {'up' if a['direction'] == 'up' else 'dropped'} {pct}",
            "detail": a["description"],
            "acknowledged": a["is_acknowledged"],
        })
    for i in issues:
        issue_label = _ISSUE_LABELS.get(i["issue_type"], i["issue_type"].replace("_", " ").title())
        short_url = (i["url"] or "").split("//")[-1][:55]
        feed.append({
            "id": f"issue-{i['id']}",
            "ts": str(i["detected_at"].date()) if i["detected_at"] else "",
            "kind": "technical",
            "severity": i["severity"],
            "title": f"{issue_label}: {short_url}",
            "detail": i["description"],
            "acknowledged": False,  # honest — TechnicalIssue has no ack mechanism yet
        })

    feed.sort(key=lambda item: (item["ts"], -_SEVERITY_RANK.get(item["severity"], 9)), reverse=True)

    return {"feed": feed}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_alerts_service`
Expected: all pass (3 from Task 2 + 4 new = 7).

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/alerts_service.py apps/dashboard/services/tests/test_alerts_service.py
git commit -m "feat(dashboard): add build_alerts_response API-shaped builder"
```

---

### Task 4: `GET /api/projects/<slug>/alerts` endpoint

**Files:**
- Modify: `apps/api/views.py`
- Modify: `apps/api/urls.py`
- Create: `apps/api/tests/test_alerts.py`

**Interfaces:**
- Consumes: `build_alerts_response` (Task 3), `resolve_project_or_404`.
- Produces: `GET /api/projects/<slug>/alerts` → `{feed: [...]}`.

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_alerts.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, Anomaly
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class AlertsEndpointTests(APITestCase):
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
            session.add(Site(site_url="sc-domain:fusehealth.com", site_name="FuseHealth",
                              slug="fusehealth", is_active=1))
            session.add(Anomaly(date=date(2026, 6, 28), site_id="sc-domain:fusehealth.com",
                                 metric_type="seo_clicks", actual_value=50, baseline_value=100,
                                 deviation_pct=-50.0, severity="high",
                                 description="Clicks dropped 50%.", is_acknowledged=0))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_alerts_returns_real_feed(self):
        resp = self.client_auth.get("/api/projects/fusehealth/alerts")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("feed", body)
        self.assertEqual(len(body["feed"]), 1)
        self.assertEqual(body["feed"][0]["kind"], "anomaly")

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/alerts")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/alerts")
        self.assertEqual(resp.status_code, 401)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_alerts`
Expected: FAIL — `404`.

- [ ] **Step 3: Implement the view**

Add to `apps/api/views.py`:

```python
from apps.dashboard.services.alerts_service import build_alerts_response


@method_decorator(login_not_required, name="dispatch")
class ProjectAlertsView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_alerts_response(site_id))
```

- [ ] **Step 4: Wire the route**

In `apps/api/urls.py`, add:

```python
    path("projects/<slug:slug>/alerts", views.ProjectAlertsView.as_view(), name="project-alerts"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_alerts`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 6: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add apps/api/views.py apps/api/urls.py apps/api/tests/test_alerts.py
git commit -m "feat(api): add GET /api/projects/<slug>/alerts"
```

---

### Task 5: Wire Overview's `priority[]` field to real alerts data

**Files:**
- Modify: `apps/dashboard/services/overview_service.py`
- Modify: `apps/api/views.py`
- Modify: `apps/dashboard/services/tests/test_overview_service.py`
- Modify: `apps/api/tests/test_overview.py`

**Interfaces:**
- Produces: `build_priority_feed(feed: list[dict], limit: int = 6) -> list[dict]` in
  `overview_service.py` — filters `feed` (Task 3's shape) to unacknowledged items, sorts by
  severity, caps at `limit`, and tags each with its owning `module` per the
  `HANDOFF_SPEC.md`-documented kind→module map: `anomaly→seo, technical→pages` (the only two
  kinds this system currently produces — `ranking→positioning, backlink→backlinks, ads→ads,
  ai→ai, system→alerts` are mapped for forward-compatibility but unreachable today since
  those alert kinds don't exist yet).
- Consumed by: `ProjectOverviewView`, replacing the hardcoded `"priority": []`.

- [ ] **Step 1: Write the failing tests**

Append to `apps/dashboard/services/tests/test_overview_service.py`:

```python
class BuildPriorityFeedTests(TestCase):
    def test_filters_out_acknowledged_items(self):
        from apps.dashboard.services.overview_service import build_priority_feed
        feed = [
            {"id": "anomaly-1", "ts": "2026-06-28", "kind": "anomaly", "severity": "high",
             "title": "Clicks dropped", "detail": "...", "acknowledged": False},
            {"id": "anomaly-2", "ts": "2026-06-27", "kind": "anomaly", "severity": "high",
             "title": "Already handled", "detail": "...", "acknowledged": True},
        ]
        priority = build_priority_feed(feed)
        self.assertEqual(len(priority), 1)
        self.assertEqual(priority[0]["id"], "anomaly-1")

    def test_tags_each_item_with_its_owning_module(self):
        from apps.dashboard.services.overview_service import build_priority_feed
        feed = [
            {"id": "anomaly-1", "ts": "2026-06-28", "kind": "anomaly", "severity": "high",
             "title": "x", "detail": "y", "acknowledged": False},
            {"id": "issue-1", "ts": "2026-06-28", "kind": "technical", "severity": "high",
             "title": "x", "detail": "y", "acknowledged": False},
        ]
        priority = build_priority_feed(feed)
        by_id = {p["id"]: p for p in priority}
        self.assertEqual(by_id["anomaly-1"]["module"], {"label": "SEO", "target": "seo"})
        self.assertEqual(by_id["issue-1"]["module"], {"label": "Page Health", "target": "pages"})

    def test_caps_at_limit(self):
        from apps.dashboard.services.overview_service import build_priority_feed
        feed = [
            {"id": f"anomaly-{i}", "ts": "2026-06-28", "kind": "anomaly", "severity": "high",
             "title": "x", "detail": "y", "acknowledged": False}
            for i in range(10)
        ]
        priority = build_priority_feed(feed, limit=6)
        self.assertEqual(len(priority), 6)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_overview_service.BuildPriorityFeedTests`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

Add to `apps/dashboard/services/overview_service.py`:

```python
_KIND_MODULE_MAP = {
    "anomaly": {"label": "SEO", "target": "seo"},
    "ranking": {"label": "Positioning", "target": "positioning"},
    "backlink": {"label": "Backlinks", "target": "backlinks"},
    "technical": {"label": "Page Health", "target": "pages"},
    "ads": {"label": "Ads", "target": "ads"},
    "ai": {"label": "AI Optimization", "target": "ai"},
    "system": {"label": "Alerts", "target": "alerts"},
}


def build_priority_feed(feed: list[dict], limit: int = 6) -> list[dict]:
    """HANDOFF_SPEC.md overview `priority[≤6]` — unacknowledged alerts, severity-sorted,
    each tagged with its owning module. `feed` is apps.dashboard.services.alerts_service
    .build_alerts_response(...)['feed'] — the caller (ProjectOverviewView) passes it in
    rather than this module importing alerts_service directly, keeping overview_service
    free of a hard dependency on a sibling page's service module."""
    severity_rank = {"high": 0, "medium": 1, "info": 2, "low": 3}
    unacked = [item for item in feed if not item["acknowledged"]]
    unacked.sort(key=lambda item: (severity_rank.get(item["severity"], 9), item["ts"]), reverse=False)

    out = []
    for item in unacked[:limit]:
        module = _KIND_MODULE_MAP.get(item["kind"], {"label": "Alerts", "target": "alerts"})
        out.append({**item, "module": module})
    return out
```

- [ ] **Step 4: Wire it into `ProjectOverviewView`**

In `apps/api/views.py`, add the import:

```python
from apps.dashboard.services.overview_service import build_priority_feed
from apps.dashboard.services.alerts_service import build_alerts_response
```

(add these to the existing `from apps.dashboard.services.overview_service import (...)`
block and as a new import line respectively — check the current import block first with
`grep -n "from apps.dashboard.services.overview_service import" apps/api/views.py` and add
`build_priority_feed` to that existing tuple rather than creating a duplicate import line.)

In `ProjectOverviewView.get`, replace:

```python
        return Response({
            "kpis": kpis,
            "pillars": pillars,
            "modules": modules,
            "priority": [],  # Alerts feed is Phase B — no fake data, empty until built
            "signals": signals,
            "trend": trend,
            "summary": summary,
            "topPages": top_pages,
        })
```

with:

```python
        priority = build_priority_feed(build_alerts_response(site_id)["feed"])

        return Response({
            "kpis": kpis,
            "pillars": pillars,
            "modules": modules,
            "priority": priority,
            "signals": signals,
            "trend": trend,
            "summary": summary,
            "topPages": top_pages,
        })
```

- [ ] **Step 5: Update Overview's existing endpoint test**

In `apps/api/tests/test_overview.py`, find the test that currently asserts `priority == []`
(search `grep -n "priority" apps/api/tests/test_overview.py`) — if one exists asserting the
empty list, update it to seed a real `Anomaly` row (in the test's `setUp`, following the same
pattern as `test_alerts.py`) and assert `priority` now contains that item with the correct
`module` tag, instead of asserting emptiness. If no such assertion currently exists, ADD one
new test method (do not skip this — Overview's response now genuinely changed and must be
covered):

```python
    def test_priority_reflects_real_unacknowledged_alerts(self):
        with get_session() as session:
            session.add(Anomaly(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                 metric_type="seo_clicks", actual_value=50, baseline_value=100,
                                 deviation_pct=-50.0, severity="high",
                                 description="Clicks dropped.", is_acknowledged=0))
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        body = resp.json()
        self.assertEqual(len(body["priority"]), 1)
        self.assertEqual(body["priority"][0]["module"]["target"], "seo")
```

(Add the `Anomaly` import to the file's existing `from pipeline.db.schema import ...` line if
not already present.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_overview_service apps.api.tests.test_overview`
Expected: all pass.

- [ ] **Step 7: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 8: Manual verification**

Start the dev server (check port hygiene first — `netstat -ano | grep :8000`, clean up any
stray process), log in, visit `/app/`, confirm: (a) the Alerts tab loads real data, (b) the
Overview tab's priority/notification feed now shows real unacknowledged alerts instead of
being empty.

- [ ] **Step 9: Update the checklist and commit**

Add a "PHASE B4 — Alerts ✅ (closes Phase B)" note to `.claude/checklist.md`, summarizing all
four Phase B sub-projects as complete. Add `apps/dashboard/services/alerts_service.py` to
`.claude/FILE_INDEX.md`.

```bash
git add apps/dashboard/services/overview_service.py apps/api/views.py apps/dashboard/services/tests/test_overview_service.py apps/api/tests/test_overview.py .claude/checklist.md .claude/FILE_INDEX.md
git commit -m "feat(api): wire Overview priority[] to real alerts data, closing the Phase A gap"
```

## Self-review notes

- **Spec coverage:** every field in the design spec's target shape has a task producing it,
  plus the Overview `priority` gap-closing addition caught during plan-writing (a natural
  consequence of Alerts now existing).
- **No duplication:** `alerts_service.py`'s new unlimited raw queries are separate from the
  old page's capped display helpers — same "reuse where it fits, add new where the shapes
  genuinely differ" discipline as every prior Phase B task.
- **Honest data throughout:** `acknowledged: false` for technical-issue-kind items is
  disclosed as an accurate reflection of missing capability, not fabrication; PageSpeed/
  Indexing/Backlinks/Ads/AI kinds are omitted entirely rather than faked.
- **This closes Phase B.** After this task, all 4 sub-projects (SEO, Keywords, Position
  Tracking, Alerts) are complete — the roadmap's next phase (C) begins fresh feature work
  (Backlinks, Site Audit, Off-site SEO, Ads) rather than more page-porting.

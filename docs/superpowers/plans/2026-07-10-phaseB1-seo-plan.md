# Phase B1 — SEO Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the SEO page's already-computed data through a real
`GET /api/projects/<slug>/seo` endpoint matching the approved SPA's verified shape, with
zero behavior change to the old Django-rendered SEO page.

**Architecture:** Extract `apps/dashboard/views.py`'s SEO query functions into a new
`apps/dashboard/services/seo_service.py` (raw calculators + old-template formatters, same
split Phase A used for Overview), rewire the old `seo()` view to import from there, then add
new API-shaped builders and a DRF endpoint on top — pure mapping, no new connectors or DB
tables (this page has no unbuilt sub-features).

**Tech Stack:** Django 6.0, DRF, SQLAlchemy 2.x (existing analytics layer).

## Global Constraints

- Never call an external API from a page-rendering or API-reading view — DB-only reads.
- Route has **no trailing slash**: `/api/projects/<slug>/seo`.
- `kpis.critical` = unlimited count of `TechnicalIssue` rows where `issue_type ==
  "not_found_404"` — **not** a passthrough of any existing "high severity" concept, and
  **not** derived from `_get_technical_issues()` (which caps at `limit=15` and would
  undercount). Verified against the real fixture in `Limitless marketing
  dashboard2/app/api.js`'s `seoView()`.
- `kpis.total_issues` = `count_technical_issues(site_id) + len(anomalies) + len(low_ctr_pages)`
  — a fresh sum, not the old page's `attention["issue_count"]`.
- Raw query functions must wrap their DB access in `try/except Exception` with a safe
  fallback (empty list/dict), matching the established pattern elsewhere in this codebase —
  do NOT drop error handling during extraction (this was a real regression caught in Phase A).
- `pipeline.utils.db_connection.get_session()` memoizes its engine per-process
  (`_SessionFactory` global) — every test needing an isolated temp DB must reset
  `db_connection._SessionFactory = None` in `setUp`/`addCleanup`.
- `Anomaly.description` (a real, existing column) is the source for the new `anomalies[].detail`
  field — no synthesis needed.
- No fake data: this page has no unbuilt sub-features, so there are no `state:"setup"` cases
  here (unlike Phase C/D work) — every field must come from a real query.

---

### Task 1: Extract SEO raw calculators into `seo_service.py`, rewire the old page

**Files:**
- Create: `apps/dashboard/services/seo_service.py`
- Modify: `apps/dashboard/views.py`
- Create: `apps/dashboard/services/tests/test_seo_service.py`

**Interfaces:**
- Produces: `query_low_ctr_pages_raw(site_id, start_date, end_date, min_impressions=100,
  max_ctr=0.02, limit=15) -> list[dict]` — same fields as the old `_get_low_ctr_pages`
  (`url, url_short, clicks, impressions, ctr, avg_position`), numeric, not strings.
- Produces: `query_seo_by_dimension_raw(site_id, start_date, end_date) -> dict` —
  `{"by_country": [...], "by_device": [...]}`, each row numeric (not pre-formatted strings):
  country rows `{country, clicks, impressions, ctr, avg_position}`, device rows
  `{device, clicks, impressions, ctr}`.
- Produces: `query_seo_anomalies_raw(site_id, limit=10) -> list[dict]` — full fields:
  `{id, metric_type, severity, deviation_pct, actual_value, baseline_value, date,
  description, direction}` (superset of what `_get_recent_anomalies` selected — adds `id`
  and `description`, needed by Task 2's API builder).
- Produces: `count_technical_issues(site_id, issue_type=None) -> int` — unlimited
  `COUNT(*)`, optionally filtered by `issue_type`.
- Produces: `count_quick_win_keywords(site_id, start_date, end_date) -> int` — count of
  keywords (grouped) with avg position 4–10 and summed clicks > 0 in the period.
- Consumed by: Task 2's `build_seo_response`.

- [ ] **Step 1: Write the pinning tests (capture current raw-query behavior)**

Create `apps/dashboard/services/tests/test_seo_service.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, Anomaly, TechnicalIssue, KeywordRanking
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class SeoServiceTests(TestCase):
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
                SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                         clicks=5, impressions=800, ctr=0.006, avg_position=8.2,
                         landing_page="https://fusehealth.com/low-ctr-page",
                         country="United States", device="mobile"),
                Anomaly(date=date(2026, 6, 29), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_clicks", actual_value=50, baseline_value=100,
                        deviation_pct=-50.0, severity="high",
                        description="Clicks dropped 50% vs. baseline.", is_acknowledged=0),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                               issue_type="not_found_404", severity="high", description="404"),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/redir",
                               issue_type="page_with_redirect", severity="medium", description="redirect"),
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=6, clicks=12, impressions=200),
            ])

    def test_query_low_ctr_pages_raw_returns_numbers(self):
        from apps.dashboard.services.seo_service import query_low_ctr_pages_raw
        pages = query_low_ctr_pages_raw("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["clicks"], 5)
        self.assertIsInstance(pages[0]["clicks"], int)

    def test_query_seo_by_dimension_raw_has_both_dimensions(self):
        from apps.dashboard.services.seo_service import query_seo_by_dimension_raw
        result = query_seo_by_dimension_raw("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(result["by_country"][0]["country"], "United States")
        self.assertEqual(result["by_device"][0]["device"], "mobile")

    def test_query_seo_anomalies_raw_includes_id_and_description(self):
        from apps.dashboard.services.seo_service import query_seo_anomalies_raw
        rows = query_seo_anomalies_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 1)
        self.assertIsNotNone(rows[0]["id"])
        self.assertEqual(rows[0]["description"], "Clicks dropped 50% vs. baseline.")

    def test_count_technical_issues_unlimited_and_filterable(self):
        from apps.dashboard.services.seo_service import count_technical_issues
        self.assertEqual(count_technical_issues("sc-domain:fusehealth.com"), 2)
        self.assertEqual(count_technical_issues("sc-domain:fusehealth.com", issue_type="not_found_404"), 1)

    def test_count_quick_win_keywords(self):
        from apps.dashboard.services.seo_service import count_quick_win_keywords
        n = count_quick_win_keywords("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(n, 1)  # position=6 (in 4-10), clicks=12 (>0)

    def test_query_low_ctr_pages_raw_returns_empty_list_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import seo_service
        with mock.patch.object(seo_service, "get_session", side_effect=RuntimeError("boom")):
            self.assertEqual(seo_service.query_low_ctr_pages_raw("x", date(2026, 6, 30), date(2026, 6, 30)), [])

    def test_count_technical_issues_returns_zero_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import seo_service
        with mock.patch.object(seo_service, "get_session", side_effect=RuntimeError("boom")):
            self.assertEqual(seo_service.count_technical_issues("x"), 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_seo_service`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.dashboard.services.seo_service'`.

- [ ] **Step 3: Create the service module**

Create `apps/dashboard/services/seo_service.py`:

```python
"""SEO page data — raw calculators (shared by the old Django view and the new DRF API
view) plus the old view's presentation formatters. See
docs/superpowers/specs/2026-07-10-phaseB1-seo-design.md for the field mapping."""

from datetime import date

from sqlalchemy import func, select

from pipeline.db.schema import SEODaily, Anomaly, TechnicalIssue, KeywordRanking
from pipeline.utils.db_connection import get_session


def query_low_ctr_pages_raw(site_id: str, start_date: date, end_date: date,
                             min_impressions: int = 100, max_ctr: float = 0.02,
                             limit: int = 15) -> list[dict]:
    """Pages that get seen but not clicked: high impressions, low CTR."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page,
                    func.sum(SEODaily.clicks).label("clicks"),
                    func.sum(SEODaily.impressions).label("impressions"),
                    func.avg(SEODaily.avg_position).label("avg_position"),
                )
                .where(
                    SEODaily.site_id == site_id,
                    SEODaily.date >= start_date, SEODaily.date <= end_date,
                    SEODaily.landing_page.isnot(None),
                )
                .group_by(SEODaily.landing_page)
                .having(func.sum(SEODaily.impressions) >= min_impressions)
            ).all()

            out = []
            for r in rows:
                impr = int(r.impressions or 0)
                clicks = int(r.clicks or 0)
                ctr = (clicks / impr) if impr else 0
                if ctr <= max_ctr:
                    out.append({
                        "url": r.landing_page,
                        "url_short": (r.landing_page or "").split("//")[-1][:55],
                        "clicks": clicks,
                        "impressions": impr,
                        "ctr": round(ctr * 100, 2),
                        "avg_position": round(r.avg_position or 0, 1),
                    })
            out.sort(key=lambda x: x["impressions"], reverse=True)
            return out[:limit]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_low_ctr_pages_raw error: {e}", exc_info=True)
        return []


def query_seo_by_dimension_raw(site_id: str, start_date: date, end_date: date) -> dict:
    """Raw numeric SEO metrics by country and device for the period."""
    try:
        with get_session() as session:
            by_country = session.execute(
                select(
                    SEODaily.country,
                    func.sum(SEODaily.clicks).label("total_clicks"),
                    func.sum(SEODaily.impressions).label("total_impressions"),
                    func.avg(SEODaily.ctr).label("avg_ctr"),
                    func.avg(SEODaily.avg_position).label("avg_position"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date, SEODaily.country.isnot(None))
                .group_by(SEODaily.country)
                .order_by(func.sum(SEODaily.clicks).desc())
                .limit(5)
            ).all()

            by_device = session.execute(
                select(
                    SEODaily.device,
                    func.sum(SEODaily.clicks).label("total_clicks"),
                    func.sum(SEODaily.impressions).label("total_impressions"),
                    func.avg(SEODaily.ctr).label("avg_ctr"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date, SEODaily.device.isnot(None))
                .group_by(SEODaily.device)
                .order_by(func.sum(SEODaily.clicks).desc())
            ).all()

            return {
                "by_country": [
                    {"country": r.country or "Unknown", "clicks": int(r.total_clicks or 0),
                     "impressions": int(r.total_impressions or 0),
                     "ctr": round((r.avg_ctr or 0) * 100, 2), "avg_position": round(r.avg_position or 0, 1)}
                    for r in by_country
                ],
                "by_device": [
                    {"device": r.device or "Unknown", "clicks": int(r.total_clicks or 0),
                     "impressions": int(r.total_impressions or 0), "ctr": round((r.avg_ctr or 0) * 100, 2)}
                    for r in by_device
                ],
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_seo_by_dimension_raw error: {e}", exc_info=True)
        return {"by_country": [], "by_device": []}


def query_seo_anomalies_raw(site_id: str, limit: int = 10) -> list[dict]:
    """Raw unacknowledged anomalies, full fields (id + description included, needed by
    the new API shape — the old page's formatter historically dropped both)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(Anomaly)
                .where(Anomaly.site_id == site_id, Anomaly.is_acknowledged == 0)
                .order_by(Anomaly.date.desc())
                .limit(limit)
            ).scalars().all()

            out = []
            for r in rows:
                up = r.actual_value >= r.baseline_value
                out.append({
                    "id": r.id,
                    "metric_type": r.metric_type,
                    "severity": r.severity,
                    "direction": "up" if up else "down",
                    "deviation_pct": r.deviation_pct,
                    "actual_value": r.actual_value,
                    "baseline_value": r.baseline_value,
                    "date": r.date,
                    "description": r.description or "",
                })
            return out
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_seo_anomalies_raw error: {e}", exc_info=True)
        return []


def count_technical_issues(site_id: str, issue_type: str | None = None) -> int:
    """Unlimited COUNT(*) of technical issues, optionally filtered by type. NOT the same
    as len(_get_technical_issues(...)), which caps at limit=15 for display purposes."""
    try:
        with get_session() as session:
            q = select(func.count()).select_from(TechnicalIssue).where(TechnicalIssue.site_id == site_id)
            if issue_type is not None:
                q = q.where(TechnicalIssue.issue_type == issue_type)
            return session.execute(q).scalar() or 0
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"count_technical_issues error: {e}", exc_info=True)
        return 0


def count_quick_win_keywords(site_id: str, start_date: date, end_date: date) -> int:
    """Count of keywords ranking 4-10 (page 1, not yet top-3) with real clicks in the period —
    same 'quick win' rule used elsewhere (e.g. the Keywords page's action buckets)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("avg_position"),
                    func.sum(KeywordRanking.clicks).label("total_clicks"),
                )
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= start_date, KeywordRanking.date <= end_date)
                .group_by(KeywordRanking.keyword)
            ).all()
            return sum(
                1 for r in rows
                if r.avg_position is not None and 4 <= r.avg_position <= 10 and (r.total_clicks or 0) > 0
            )
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"count_quick_win_keywords error: {e}", exc_info=True)
        return 0


def format_recent_anomalies(raw_anomalies: list[dict]) -> list[dict]:
    """Old dashboard/seo.html template shape — human labels, formatted strings."""
    labels = {
        "seo_clicks": "Clicks", "seo_impressions": "Impressions",
        "seo_ctr": "CTR", "seo_avg_position": "Avg. position",
        "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
        "ad_impressions": "Ad impressions", "ad_conversions": "Conversions",
    }
    out = []
    for r in raw_anomalies:
        out.append({
            "metric": labels.get(r["metric_type"], r["metric_type"]),
            "severity": r["severity"],
            "direction": r["direction"],
            "deviation": f"{'+' if r['direction'] == 'up' else '-'}{abs(r['deviation_pct']):.0f}%",
            "actual": f"{r['actual_value']:,.0f}",
            "baseline": f"{r['baseline_value']:,.0f}",
            "date": str(r["date"]),
        })
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.dashboard.services.tests.test_seo_service`
Expected: `Ran 7 tests in ...s\n\nOK`

- [ ] **Step 5: Rewire the old `seo()` view to use the service module**

In `apps/dashboard/views.py`:

1. Delete the function bodies of `_get_seo_by_dimension`, `_get_recent_anomalies`,
   `_get_low_ctr_pages` (confirm exact current line numbers first with
   `grep -n "^def _get_seo_by_dimension\|^def _get_recent_anomalies\|^def _get_low_ctr_pages" apps/dashboard/views.py` — do NOT delete `_get_technical_issues`, it's still used
   as-is by the Alerts page (`alerts()` view, out of this task's scope) for its own
   15-row-limited display table.

2. Add this import near the top of the file, alongside the existing
   `apps.dashboard.services.overview_service` import:

```python
from apps.dashboard.services.seo_service import (
    query_low_ctr_pages_raw, query_seo_by_dimension_raw, query_seo_anomalies_raw,
    count_technical_issues, format_recent_anomalies,
)
```

3. In the `seo(request)` view function, replace:

```python
    seo_by_dim = _get_seo_by_dimension(site_id, curr_start, curr_end)
    anomalies = _get_recent_anomalies(site_id)
    issues = _get_technical_issues(site_id)
    low_ctr = _get_low_ctr_pages(site_id, curr_start, curr_end)

    # Attention summary — counts that tell the user where to look first.
    high_sev_issues = sum(1 for i in issues if i.get("severity") == "high")
    attention = {
        "low_ctr_count": len(low_ctr),
        "anomaly_count": len(anomalies),
        "issue_count": len(issues),
        "high_sev_issues": high_sev_issues,
    }

    context = {
        "active": "seo",
        "seo_by_country": seo_by_dim["by_country"],
        "seo_by_device": seo_by_dim["by_device"],
        "anomalies": anomalies,
        "technical_issues": issues,
        "low_ctr_pages": low_ctr,
        "attention": attention,
        "last_sync": _get_last_sync_time(site_id),
    }
```

with:

```python
    seo_by_dim_raw = query_seo_by_dimension_raw(site_id, curr_start, curr_end)
    seo_by_country = [
        {"country": r["country"], "clicks": f"{r['clicks']:,.0f}", "impressions": f"{r['impressions']:,.0f}",
         "ctr": f"{r['ctr']:.2f}%", "position": f"{r['avg_position']:.1f}"}
        for r in seo_by_dim_raw["by_country"]
    ]
    seo_by_device = [
        {"device": r["device"], "clicks": f"{r['clicks']:,.0f}", "impressions": f"{r['impressions']:,.0f}",
         "ctr": f"{r['ctr']:.2f}%"}
        for r in seo_by_dim_raw["by_device"]
    ]
    anomalies_raw = query_seo_anomalies_raw(site_id)
    anomalies = format_recent_anomalies(anomalies_raw)
    issues = _get_technical_issues(site_id)
    low_ctr_raw = query_low_ctr_pages_raw(site_id, curr_start, curr_end)
    low_ctr = [
        {"url": p["url"], "url_short": p["url_short"], "clicks": p["clicks"],
         "impressions": p["impressions"], "ctr": p["ctr"], "avg_position": p["avg_position"]}
        for p in low_ctr_raw
    ]

    # Attention summary — counts that tell the user where to look first.
    high_sev_issues = sum(1 for i in issues if i.get("severity") == "high")
    attention = {
        "low_ctr_count": len(low_ctr),
        "anomaly_count": len(anomalies),
        "issue_count": len(issues),
        "high_sev_issues": high_sev_issues,
    }

    context = {
        "active": "seo",
        "seo_by_country": seo_by_country,
        "seo_by_device": seo_by_device,
        "anomalies": anomalies,
        "technical_issues": issues,
        "low_ctr_pages": low_ctr,
        "attention": attention,
        "last_sync": _get_last_sync_time(site_id),
    }
```

(`count_technical_issues` isn't used by the old view — it's imported for Task 2's builder,
which lives in the same service module; the old page keeps using `_get_technical_issues()`
for its capped display table, unchanged.)

4. `_get_seo_by_dimension` has a SECOND call site: `export_csv`'s `table_name ==
   "seo_country"` branch (confirmed via `grep -n "_get_seo_by_dimension" apps/dashboard/views.py`
   — `_get_low_ctr_pages` and `_get_recent_anomalies` have no other call sites, only the one
   inside `seo()` just updated above). Find this branch (search for
   `elif table_name == "seo_country":`) and replace:

```python
        elif table_name == "seo_country":
            data = _get_seo_by_dimension(site_id, curr_start, curr_end)["by_country"]
```

with:

```python
        elif table_name == "seo_country":
            country_raw = query_seo_by_dimension_raw(site_id, curr_start, curr_end)["by_country"]
            data = [
                {"country": r["country"], "clicks": f"{r['clicks']:,.0f}", "impressions": f"{r['impressions']:,.0f}",
                 "ctr": f"{r['ctr']:.2f}%", "position": f"{r['avg_position']:.1f}"}
                for r in country_raw
            ]
```

(matching the exact string-formatted shape the CSV export previously wrote, so the
downloaded CSV's columns/formatting are unchanged.)

- [ ] **Step 6: Verify the old SEO page still renders identically**

Run: `python manage.py test apps.dashboard` — expected: existing dashboard tests pass.

Then manually: start the dev server, log in, open `/seo/`, confirm the low-CTR pages table,
anomalies list, technical issues list, and country/device tables render the same as before
this refactor (spot-check a few real values against what you'd see before the change, or
compare via `git stash` before/after like Phase A's Task 5 did).

- [ ] **Step 7: Run the full test suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all tests pass (baseline + 7 new).

- [ ] **Step 8: Commit**

```bash
git add apps/dashboard/services/seo_service.py apps/dashboard/services/tests/test_seo_service.py apps/dashboard/views.py
git commit -m "refactor(dashboard): extract SEO page query logic into seo_service.py"
```

---

### Task 2: API-shaped `build_seo_response` builder

**Files:**
- Modify: `apps/dashboard/services/seo_service.py`
- Modify: `apps/dashboard/services/tests/test_seo_service.py`

**Interfaces:**
- Consumes: everything Task 1 produced.
- Produces: `build_seo_response(site_id, curr_start, curr_end) -> dict` — the exact
  `{kpis, lowCtrPages, countries, anomalies, quickWinKws}` shape from the design spec.
  Consumed by Task 3's DRF view.

- [ ] **Step 1: Write the failing tests**

Append to `apps/dashboard/services/tests/test_seo_service.py` (reuse the same seeded data
from `setUp` — it already has one low-CTR page, one anomaly, two technical issues [one
`not_found_404`], and one quick-win keyword):

```python
class BuildSeoResponseTests(SeoServiceTests):
    def test_top_level_keys(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        for key in ["kpis", "lowCtrPages", "countries", "anomalies", "quickWinKws"]:
            self.assertIn(key, body)

    def test_kpis_match_spec_semantics(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        # low_ctr: 1 seeded low-CTR page
        self.assertEqual(body["kpis"]["low_ctr"], 1)
        # anomalies: 1 seeded unacknowledged anomaly
        self.assertEqual(body["kpis"]["anomalies"], 1)
        # critical: 1 of the 2 seeded technical issues is not_found_404 — NOT high_sev_issues (which would be 1 too here by
        # coincidence since both seeded issues are severity="high"/"medium" — this assertion specifically pins the
        # 404-count semantics, not a severity count, per the corrected spec mapping)
        self.assertEqual(body["kpis"]["critical"], 1)
        # total_issues: 2 technical issues + 1 anomaly + 1 low_ctr page = 4
        self.assertEqual(body["kpis"]["total_issues"], 4)

    def test_low_ctr_pages_shape(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        page = body["lowCtrPages"][0]
        for key in ["url", "impressions", "clicks", "ctr", "avg_pos"]:
            self.assertIn(key, page)
        self.assertNotIn("url_short", page)

    def test_anomalies_shape(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        a = body["anomalies"][0]
        self.assertEqual(set(a.keys()), {"id", "metric", "severity", "deviation", "date", "detail"})
        self.assertEqual(a["detail"], "Clicks dropped 50% vs. baseline.")
        self.assertEqual(a["deviation"], "-50%")

    def test_quick_win_kws_is_a_count_not_a_list(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(body["quickWinKws"], 1)
        self.assertIsInstance(body["quickWinKws"], int)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_seo_service.BuildSeoResponseTests`
Expected: FAIL — `ImportError: cannot import name 'build_seo_response'`.

- [ ] **Step 3: Implement**

Add to `apps/dashboard/services/seo_service.py`:

```python
def build_seo_response(site_id: str, curr_start: date, curr_end: date) -> dict:
    """HANDOFF_SPEC.md `seo` view shape — verified against the real fixture's seoView()
    in Limitless marketing dashboard2/app/api.js. See
    docs/superpowers/specs/2026-07-10-phaseB1-seo-design.md for the field mapping and the
    kpis.critical/total_issues correction."""
    low_ctr_raw = query_low_ctr_pages_raw(site_id, curr_start, curr_end)
    by_dim = query_seo_by_dimension_raw(site_id, curr_start, curr_end)
    anomalies_raw = query_seo_anomalies_raw(site_id)
    critical_count = count_technical_issues(site_id, issue_type="not_found_404")
    total_issue_count = count_technical_issues(site_id)
    quick_win_count = count_quick_win_keywords(site_id, curr_start, curr_end)

    return {
        "kpis": {
            "low_ctr": len(low_ctr_raw),
            "anomalies": len(anomalies_raw),
            "critical": critical_count,
            "total_issues": total_issue_count + len(anomalies_raw) + len(low_ctr_raw),
        },
        "lowCtrPages": [
            {"url": p["url"], "impressions": p["impressions"], "clicks": p["clicks"],
             "ctr": p["ctr"], "avg_pos": p["avg_position"]}
            for p in low_ctr_raw
        ],
        "countries": by_dim["by_country"],
        "anomalies": [
            {
                "id": str(a["id"]),
                "metric": {"seo_clicks": "Clicks", "seo_impressions": "Impressions",
                           "seo_ctr": "CTR", "seo_avg_position": "Avg. position",
                           "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
                           "ad_impressions": "Ad impressions", "ad_conversions": "Conversions"
                           }.get(a["metric_type"], a["metric_type"]),
                "severity": a["severity"],
                "deviation": f"{'+' if a['direction'] == 'up' else '-'}{abs(a['deviation_pct']):.0f}%",
                "date": str(a["date"]),
                "detail": a["description"],
            }
            for a in anomalies_raw
        ],
        "quickWinKws": quick_win_count,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_seo_service`
Expected: `Ran 12 tests in ...s\n\nOK`

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/seo_service.py apps/dashboard/services/tests/test_seo_service.py
git commit -m "feat(dashboard): add build_seo_response API-shaped builder"
```

---

### Task 3: `GET /api/projects/<slug>/seo` endpoint

**Files:**
- Modify: `apps/api/views.py`
- Modify: `apps/api/urls.py`
- Create: `apps/api/tests/test_seo.py`

**Interfaces:**
- Consumes: `build_seo_response` (Task 2), `range_to_period_dates`-equivalent period
  resolution (this endpoint has no `range` param per `HANDOFF_SPEC.md` — reuse the same
  "anchor to latest data date" logic Phase A's Overview endpoint uses, but with a fixed
  30-day window, since the SEO page itself has no period selector in the new design either).
- Produces: `GET /api/projects/<slug>/seo` → the shape from Task 2.

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_seo.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, SEODaily, Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class SeoEndpointTests(APITestCase):
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
            session.add(SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                  clicks=5, impressions=800, ctr=0.006, avg_position=8.2,
                                  landing_page="https://fusehealth.com/low-ctr-page",
                                  country="United States", device="mobile"))
            session.add(TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                                        issue_type="not_found_404", severity="high"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_seo_returns_all_required_keys_with_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/seo")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "lowCtrPages", "countries", "anomalies", "quickWinKws"]:
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["critical"], 1)

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/seo")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/seo")
        self.assertEqual(resp.status_code, 401)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_seo`
Expected: FAIL — `404` (route doesn't exist).

- [ ] **Step 3: Implement the view**

Add to `apps/api/views.py`:

```python
from apps.dashboard.services.seo_service import build_seo_response


@method_decorator(login_not_required, name="dispatch")
class ProjectSEOView(APIView):
    def get(self, request, slug):
        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
        if site is None:
            from django.http import Http404
            raise Http404(f"No project with slug '{slug}'")
        site_id = site.site_url

        with get_session() as session:
            anchor = session.execute(
                select(func.max(SEODaily.date)).where(SEODaily.site_id == site_id)
            ).scalar() or date_cls.today()
        curr_start, curr_end, _, _ = range_to_period_dates("30d", anchor)

        return Response(build_seo_response(site_id, curr_start, curr_end))
```

(`select`, `Site`, `get_session`, `func`, `SEODaily`, `date_cls`, `range_to_period_dates`,
`login_not_required`, `method_decorator`, `Response`, `APIView` are all already imported in
`apps/api/views.py` from Phase A's Overview endpoint — no new imports needed beyond
`build_seo_response`.)

- [ ] **Step 4: Wire the route**

In `apps/api/urls.py`, add:

```python
    path("projects/<slug:slug>/seo", views.ProjectSEOView.as_view(), name="project-seo"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_seo`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 6: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all tests pass.

- [ ] **Step 7: Manual verification**

Start the dev server, log in, visit `/app/`, click the SEO tab — confirm it loads real data
(not a 404/error) and the numbers are plausible against what `/seo/` (the old page) shows.

- [ ] **Step 8: Update the checklist and commit**

Add a short "PHASE B1 — SEO ✅" note to `.claude/checklist.md` (same style as Phase A's
entry), and add `apps/dashboard/services/seo_service.py` to `.claude/FILE_INDEX.md`.

```bash
git add apps/api/views.py apps/api/urls.py apps/api/tests/test_seo.py .claude/checklist.md .claude/FILE_INDEX.md
git commit -m "feat(api): add GET /api/projects/<slug>/seo"
```

## Self-review notes

- **Spec coverage:** every field in the design spec's target shape has a task producing it.
- **Corrected mapping applied:** `kpis.critical`/`kpis.total_issues` use the corrected
  semantics (404-count, fresh sum) throughout — not the disproven `high_sev_issues`/
  `issue_count` passthrough from the first draft.
- **No duplication:** `_get_technical_issues()` (old page's capped display list) and
  `count_technical_issues()` (new unlimited count) are deliberately separate functions with
  different purposes — not accidental duplication.
- **Alerts page (`alerts()` view) is untouched** — it still uses `_get_technical_issues()`
  directly, unaffected by this plan. `_get_all_anomalies` (used by `alerts()`) is a
  **different, separate function** from `_get_recent_anomalies` (used by `seo()`, being
  extracted here) — confirmed via grep, must not be touched by this plan.
- **All call sites confirmed via grep before writing this plan** (not left for the
  implementer to discover): `_get_low_ctr_pages` and `_get_recent_anomalies` each have
  exactly one call site (inside `seo()`, both updated in Task 1 Step 5). `_get_seo_by_dimension`
  has TWO call sites — `seo()` and `export_csv`'s `"seo_country"` branch — both updated in
  Task 1 Step 5 (point 4). This mirrors Phase A's Task 5, which found `export_csv` had an
  extra, easy-to-miss call site for `_get_top_pages`.

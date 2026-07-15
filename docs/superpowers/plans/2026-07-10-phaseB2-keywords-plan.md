# Phase B2 — Keywords Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the Keywords page through `GET /api/projects/<slug>/keywords`, and extract
the shared slug-lookup/anchor-date logic in `apps/api/views.py` before a third endpoint
clones it.

**Architecture:** Task 1 is a small cross-cutting refactor (shared helper functions, retrofit
the two existing endpoints). Tasks 2-4 follow the same extract → build API shape → wire
endpoint pattern used in Phase B1.

**Tech Stack:** Django 6.0, DRF, SQLAlchemy 2.x, pandas (existing dependency, used by
`_get_keyword_intelligence`).

## Global Constraints

- Never call an external API from a page-rendering or API-reading view — DB-only reads.
- Route has **no trailing slash**: `/api/projects/<slug>/keywords`. No `range` query param
  (matches `HANDOFF_SPEC.md`'s endpoint table — same as the SEO endpoint).
- `pipeline.utils.db_connection.get_session()` memoizes its engine per-process — every test
  needing an isolated temp DB must reset `db_connection._SessionFactory = None` in
  `setUp`/`addCleanup`.
- **Test-class inheritance footgun** (hit twice already in this project): a new test class
  needing the same fixture as an existing test class must get its OWN `setUp()` (duplicate
  the body) and inherit from `TestCase`/`APITestCase` directly — never inherit from a sibling
  test class, which silently re-runs its tests under the new class name. Verify with `-v 2`
  before committing that every test name appears exactly once.
- `segments.{quick_wins,striking,declining,low_ctr}` are arrays of `id` strings, where
  `id` = the keyword's own text (already unique per aggregation group — no other natural
  unique identifier exists in this schema). Every ID referenced in `segments.*` must have a
  matching entry in `keywords[]`.
- `keywords[].monthly` and `keywords[].serpFeatures` are honest empty arrays `[]` — this
  system doesn't track either yet. Never fabricate values for them.
- Zero behavior change to the old Django-rendered Keywords page (`/keywords/`) — except the
  one deliberate, disclosed additive change in Task 2 (widening `all_keywords`'s row shape
  to include `prev_position`/`pos_change`, which the old template ignores).

---

### Task 1: Extract shared slug-lookup + anchor-date helpers in `apps/api/views.py`

**Files:**
- Modify: `apps/api/views.py`
- Modify: `apps/api/tests/test_overview.py`
- Modify: `apps/api/tests/test_seo.py`

**Interfaces:**
- Produces: `resolve_project_or_404(slug: str) -> Site` — raises Django's `Http404` if no
  match. Consumed by `ProjectOverviewView`, `ProjectSEOView` (retrofitted here) and Task 4's
  `ProjectKeywordsView`.
- Produces: `latest_data_anchor(site_id: str) -> date` — `max(SEODaily.date)` or `date.today()`
  fallback. Same consumers.

This is a pure refactor — no behavior change to either existing endpoint's response.

- [ ] **Step 1: Write the failing tests (pin current behavior of the helpers' logic)**

Add to `apps/api/tests/test_overview.py` (a new top-level test, not inside the existing
`OverviewEndpointTests` class — this tests the standalone helper functions directly):

```python
class ResolveProjectHelperTests(APITestCase):
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

    def test_resolve_project_or_404_finds_real_site(self):
        from apps.api.views import resolve_project_or_404
        site = resolve_project_or_404("fusehealth")
        self.assertEqual(site.site_url, "sc-domain:fusehealth.com")

    def test_resolve_project_or_404_raises_on_unknown_slug(self):
        from django.http import Http404
        from apps.api.views import resolve_project_or_404
        with self.assertRaises(Http404):
            resolve_project_or_404("does-not-exist")

    def test_latest_data_anchor_finds_max_date(self):
        from apps.api.views import latest_data_anchor
        anchor = latest_data_anchor("sc-domain:fusehealth.com")
        self.assertEqual(anchor, date(2026, 7, 1))

    def test_latest_data_anchor_falls_back_to_today_when_no_data(self):
        from datetime import date as date_cls
        from apps.api.views import latest_data_anchor
        anchor = latest_data_anchor("sc-domain:no-data-site.com")
        self.assertEqual(anchor, date_cls.today())
```

(This new test class needs the same imports already present at the top of
`apps/api/tests/test_overview.py` — `tempfile`, `Path`, `override_settings`, `get_engine`,
`init_db`, `Site`, `SEODaily`, `get_session`, `db_connection`, `date` — check they're already
imported before adding duplicates.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_overview.ResolveProjectHelperTests`
Expected: FAIL — `ImportError: cannot import name 'resolve_project_or_404'`.

- [ ] **Step 3: Implement the helpers**

In `apps/api/views.py`, add near the top (after imports, before `PingView`):

```python
from django.http import Http404


def resolve_project_or_404(slug: str) -> Site:
    """Look up a Site by its public slug (the API's project `id`). Raises Http404 if no
    active or inactive site matches — used by every apps.api view that takes a `slug` URL
    kwarg."""
    with get_session() as session:
        site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
    if site is None:
        raise Http404(f"No project with slug '{slug}'")
    return site


def latest_data_anchor(site_id: str) -> date_cls:
    """Most recent date we have SEO data for, or today if none — periods anchor to this so
    the API never defaults to a window that postdates the data."""
    with get_session() as session:
        return session.execute(
            select(func.max(SEODaily.date)).where(SEODaily.site_id == site_id)
        ).scalar() or date_cls.today()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_overview.ResolveProjectHelperTests`
Expected: `Ran 4 tests in ...s\n\nOK`

- [ ] **Step 5: Retrofit `ProjectOverviewView` and `ProjectSEOView` to use the helpers**

In `apps/api/views.py`, in `ProjectOverviewView.get`, replace:

```python
        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
        if site is None:
            from django.http import Http404
            raise Http404(f"No project with slug '{slug}'")
        site_id = site.site_url

        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        range_key = query.validated_data["range"]

        with get_session() as session:
            anchor = session.execute(
                select(func.max(SEODaily.date)).where(SEODaily.site_id == site_id)
            ).scalar() or date_cls.today()
```

with:

```python
        site_id = resolve_project_or_404(slug).site_url

        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        range_key = query.validated_data["range"]

        anchor = latest_data_anchor(site_id)
```

In `ProjectSEOView.get`, replace:

```python
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
```

with:

```python
        site_id = resolve_project_or_404(slug).site_url
        anchor = latest_data_anchor(site_id)
        curr_start, curr_end, _, _ = range_to_period_dates("30d", anchor)
```

- [ ] **Step 6: Run the full test suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all existing tests still pass (baseline 82 + 4 new = 86) — `ProjectOverviewView`'s
and `ProjectSEOView`'s own tests (`test_overview.py`, `test_seo.py`) must be unaffected by
this refactor since the response bodies are unchanged.

- [ ] **Step 7: Commit**

```bash
git add apps/api/views.py apps/api/tests/test_overview.py
git commit -m "refactor(api): extract resolve_project_or_404 + latest_data_anchor helpers"
```

---

### Task 2: Extract keyword intelligence into `keywords_service.py`, fix the missing `prevPos` gap

**Files:**
- Create: `apps/dashboard/services/keywords_service.py`
- Modify: `apps/dashboard/views.py`
- Create: `apps/dashboard/services/tests/test_keywords_service.py`

**Interfaces:**
- Produces: `get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start,
  prev_end) -> dict` — same top-level shape as the old `_get_keyword_intelligence`
  (`health_score, health_label, health_color, total_tracked, total_volume, avg_position,
  total_clicks, intent_distribution, kd_easy, kd_medium, kd_hard, quick_wins, striking,
  declining, low_ctr, all_keywords`), with `all_keywords` now built from `merged` (carries
  `prev_position`/`pos_change` on every row, not just segment members).
- Consumed by: Task 3's `build_keywords_response`.

- [ ] **Step 1: Write the pinning tests**

Create `apps/dashboard/services/tests/test_keywords_service.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, KeywordRanking
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class KeywordIntelligenceTests(TestCase):
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
                # quick-win: pos 6 (current), pos 9 (previous) -> improved, not "declining"
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=6, clicks=12,
                               impressions=200, search_volume=2400, keyword_difficulty=24,
                               cpc=4.2, intent="commercial", url="/services/iv-therapy"),
                KeywordRanking(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=9, clicks=8,
                               impressions=180),
                # a second keyword with NO previous-period row -> prevPos should be null, not crash
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=15, clicks=0,
                               impressions=60, search_volume=880, keyword_difficulty=18,
                               intent="informational", url="/services/mobile"),
            ])

    def test_all_keywords_includes_prev_position_for_every_row(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:fusehealth.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        by_kw = {row["keyword"]: row for row in result["all_keywords"]}
        self.assertEqual(len(result["all_keywords"]), 2)
        # the keyword WITH a previous-period row has a real prev_position
        self.assertEqual(by_kw["iv therapy near me"]["prev_position"], 9)
        # the keyword with NO previous-period row has prev_position None, not a crash/omission
        self.assertIsNone(by_kw["mobile iv drip"]["prev_position"])

    def test_quick_wins_segment_still_populated(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:fusehealth.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertEqual(len(result["quick_wins"]), 1)
        self.assertEqual(result["quick_wins"][0]["keyword"], "iv therapy near me")

    def test_empty_data_returns_safe_defaults(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:no-such-site.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertEqual(result["total_tracked"], 0)
        self.assertEqual(result["all_keywords"], [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_keywords_service`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Create the service module**

Create `apps/dashboard/services/keywords_service.py` — this is `_get_keyword_intelligence`'s
body moved verbatim, with ONE change: `all_keywords` is built from `merged` instead of `df`
(the fix for the missing `prevPos` gap identified in the design spec):

```python
"""Keywords page data — raw calculator (shared by the old Django view and the new DRF API
view) built on the existing keyword-intelligence pandas pipeline (health score, intent/KD
distribution, action-bucket segments). See
docs/superpowers/specs/2026-07-10-phaseB2-keywords-design.md for the all_keywords/prevPos fix."""

from datetime import date

import pandas as pd
from sqlalchemy import func, select

from pipeline.db.schema import KeywordRanking
from pipeline.utils.db_connection import get_session


def get_keyword_intelligence_raw(site_id: str, curr_start: date, curr_end: date,
                                  prev_start: date, prev_end: date) -> dict:
    """Keyword health score and action buckets. Identical to the pre-extraction
    _get_keyword_intelligence, except all_keywords is now built from `merged` (carries
    prev_position/pos_change on every row) instead of `df` (current period only) — the old
    version silently omitted prevPos for any keyword outside the top-15-per-segment lists."""
    try:
        with get_session() as session:
            def get_kw_df(start, end):
                rows = session.execute(
                    select(
                        KeywordRanking.keyword,
                        func.avg(KeywordRanking.position).label("position"),
                        func.sum(KeywordRanking.clicks).label("clicks"),
                        func.sum(KeywordRanking.impressions).label("impressions"),
                        func.max(KeywordRanking.search_volume).label("search_volume"),
                        func.max(KeywordRanking.keyword_difficulty).label("keyword_difficulty"),
                        func.max(KeywordRanking.cpc).label("cpc"),
                        func.max(KeywordRanking.intent).label("intent"),
                        func.max(KeywordRanking.url).label("url"),
                    )
                    .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= start, KeywordRanking.date <= end)
                    .group_by(KeywordRanking.keyword)
                ).all()
                if not rows:
                    return pd.DataFrame()
                df = pd.DataFrame([dict(r._mapping) for r in rows])
                df["ctr"] = (df["clicks"] / df["impressions"] * 100).fillna(0)
                return df

            df = get_kw_df(curr_start, curr_end)
            prev_df = get_kw_df(prev_start, prev_end)

            if df.empty:
                return {
                    "health_score": 0, "health_label": "No Data", "health_color": "#94a3b8",
                    "total_tracked": 0, "total_volume": 0, "avg_position": 0, "total_clicks": 0,
                    "intent_distribution": {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0},
                    "kd_easy": 0, "kd_medium": 0, "kd_hard": 0,
                    "quick_wins": [], "striking": [], "declining": [], "low_ctr": [],
                    "all_keywords": [],
                }

            with_clicks = df[df["clicks"] > 0]
            top10 = df[df["position"] <= 10]
            p1_ratio = len(top10) / len(df) if len(df) > 0 else 0
            click_ratio = len(with_clicks) / len(df) if len(df) > 0 else 0
            health_score = int((p1_ratio * 0.6 + click_ratio * 0.4) * 100)

            if health_score >= 70:
                health_color, health_label = "#10b981", "Excellent"
            elif health_score >= 40:
                health_color, health_label = "#f59e0b", "Needs Work"
            else:
                health_color, health_label = "#ef4444", "Critical"

            if not prev_df.empty and "position" in prev_df.columns:
                merged = df.merge(
                    prev_df[["keyword", "position"]].rename(columns={"position": "prev_position"}),
                    on="keyword", how="left"
                )
                merged["pos_change"] = merged["prev_position"] - merged["position"]
            else:
                merged = df.copy()
                merged["prev_position"] = None
                merged["pos_change"] = None

            quick_wins = merged[
                (merged["position"] >= 4) & (merged["position"] <= 10) & (merged["clicks"] > 0)
            ].sort_values("clicks", ascending=False).head(15)

            striking = merged[
                (merged["position"] >= 11) & (merged["position"] <= 20)
            ].sort_values(["impressions", "position"], ascending=[False, True]).head(15)

            if "pos_change" in merged.columns and merged["pos_change"].notna().any():
                declining = merged[merged["pos_change"] <= -3].sort_values("pos_change").head(15)
            else:
                declining = pd.DataFrame()

            low_ctr = merged[
                (merged["position"] <= 20) & (merged["impressions"] >= 50) & (merged["ctr"] < 2.0)
            ].sort_values("impressions", ascending=False).head(15)

            def df_to_dicts(data_df):
                if data_df.empty:
                    return []
                return data_df.where(pd.notna(data_df), None).to_dict('records')

            intent_counts = {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0}
            if "intent" in df.columns:
                for val in df["intent"].dropna():
                    key = str(val).lower().strip()
                    if key in intent_counts:
                        intent_counts[key] += 1
                    elif "info" in key:
                        intent_counts["informational"] += 1
                    elif "comm" in key:
                        intent_counts["commercial"] += 1
                    elif "trans" in key:
                        intent_counts["transactional"] += 1
                    elif "nav" in key:
                        intent_counts["navigational"] += 1

            kd_easy = kd_medium = kd_hard = 0
            if "keyword_difficulty" in df.columns:
                kd_vals = df["keyword_difficulty"].dropna()
                kd_easy = int((kd_vals < 30).sum())
                kd_medium = int(((kd_vals >= 30) & (kd_vals < 60)).sum())
                kd_hard = int((kd_vals >= 60).sum())

            total_volume = int(df["search_volume"].dropna().sum()) if "search_volume" in df.columns else 0
            avg_position = round(df["position"].mean(), 1) if "position" in df.columns and not df["position"].isna().all() else 0
            total_clicks = int(df["clicks"].sum()) if "clicks" in df.columns else 0

            return {
                "health_score": health_score,
                "health_label": health_label,
                "health_color": health_color,
                "total_tracked": len(df),
                "total_volume": total_volume,
                "avg_position": avg_position,
                "total_clicks": total_clicks,
                "intent_distribution": intent_counts,
                "kd_easy": kd_easy,
                "kd_medium": kd_medium,
                "kd_hard": kd_hard,
                "quick_wins": df_to_dicts(quick_wins),
                "striking": df_to_dicts(striking),
                "declining": df_to_dicts(declining),
                "low_ctr": df_to_dicts(low_ctr),
                "all_keywords": df_to_dicts(merged.sort_values("clicks", ascending=False).head(200)),
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"get_keyword_intelligence_raw error: {e}", exc_info=True)
        return {
            "health_score": 0, "health_label": "Error", "health_color": "#ef4444",
            "total_tracked": 0, "total_volume": 0, "avg_position": 0, "total_clicks": 0,
            "intent_distribution": {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0},
            "kd_easy": 0, "kd_medium": 0, "kd_hard": 0,
            "quick_wins": [], "striking": [], "declining": [], "low_ctr": [], "all_keywords": []
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_keywords_service`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 5: Rewire the old `keywords()` view**

In `apps/dashboard/views.py`:

1. Delete `_get_keyword_intelligence`'s function body (confirm exact line range with
   `grep -n "^def _get_keyword_intelligence" apps/dashboard/views.py` first — it has no
   other call sites, confirmed via `grep -n "_get_keyword_intelligence" apps/dashboard/views.py`
   during plan-writing: exactly one, inside `keywords()`).
2. Add the import:

```python
from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
```

3. In `keywords(request)`, replace the call `intelligence = _get_keyword_intelligence(...)`
   with `intelligence = get_keyword_intelligence_raw(...)` (identical arguments — this is a
   straight rename of the call, since the extracted function's top-level dict keys are
   unchanged; only `all_keywords`'s row shape gained two extra keys, which the template ignores).

- [ ] **Step 6: Verify the old Keywords page still renders correctly**

Run: `python manage.py test apps.dashboard` — expected: pass.

Then manually: start the dev server, log in, visit `/keywords/`, confirm the health score,
action buckets, and keyword table all render the same as before. Specifically check the
keyword table doesn't error or show garbage from the two new dict keys (`prev_position`,
`pos_change`) — Django templates silently ignore unrequested dict keys, so this should be a
non-event, but confirm it.

- [ ] **Step 7: Run the full suite and commit**

Run: `python manage.py test 2>&1 | tail -15` — expected: all pass.

```bash
git add apps/dashboard/services/keywords_service.py apps/dashboard/services/tests/test_keywords_service.py apps/dashboard/views.py
git commit -m "refactor(dashboard): extract keyword intelligence into keywords_service.py, fix missing prevPos on non-segment keywords"
```

---

### Task 3: API-shaped `build_keywords_response` builder

**Files:**
- Modify: `apps/dashboard/services/keywords_service.py`
- Modify: `apps/dashboard/services/tests/test_keywords_service.py`

**Interfaces:**
- Consumes: `get_keyword_intelligence_raw` (Task 2).
- Produces: `build_keywords_response(site_id, curr_start, curr_end, prev_start, prev_end) ->
  dict` — the exact `{kpis, intents, difficulty, segments, keywords}` shape. Consumed by
  Task 4's DRF view.

- [ ] **Step 1: Write the failing tests**

Append to `apps/dashboard/services/tests/test_keywords_service.py` (new class, own `setUp`
duplicating `KeywordIntelligenceTests`'s fixture — do NOT inherit from `KeywordIntelligenceTests`,
per the Global Constraints test-duplication warning):

```python
class BuildKeywordsResponseTests(TestCase):
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
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=6, clicks=12,
                               impressions=200, search_volume=2400, keyword_difficulty=24,
                               cpc=4.2, intent="commercial", url="/services/iv-therapy"),
                KeywordRanking(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=9, clicks=8, impressions=180),
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=15, clicks=0, impressions=60,
                               search_volume=880, keyword_difficulty=18, intent="informational",
                               url="/services/mobile"),
            ])

    def test_top_level_keys(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        for key in ["kpis", "intents", "difficulty", "segments", "keywords"]:
            self.assertIn(key, body)

    def test_segments_are_id_arrays_not_full_objects(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        self.assertEqual(body["segments"]["quick_wins"], ["iv therapy near me"])
        for seg_ids in body["segments"].values():
            for kw_id in seg_ids:
                self.assertIsInstance(kw_id, str)

    def test_every_segment_id_has_a_matching_keyword(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        known_ids = {k["id"] for k in body["keywords"]}
        for seg_ids in body["segments"].values():
            for kw_id in seg_ids:
                self.assertIn(kw_id, known_ids)

    def test_keyword_row_shape_and_prev_pos(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        by_id = {k["id"]: k for k in body["keywords"]}
        row = by_id["iv therapy near me"]
        for key in ["id", "kw", "intent", "pos", "prevPos", "volume", "kd", "cpc",
                    "clicks", "impressions", "ctr", "url", "monthly", "source", "serpFeatures"]:
            self.assertIn(key, row)
        self.assertEqual(row["prevPos"], 9)
        self.assertEqual(row["monthly"], [])
        self.assertEqual(row["serpFeatures"], [])
        self.assertEqual(row["source"], "sync")
        # the keyword with no previous-period row must have prevPos None, not a KeyError/crash
        self.assertIsNone(by_id["mobile iv drip"]["prevPos"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_keywords_service.BuildKeywordsResponseTests`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

Add to `apps/dashboard/services/keywords_service.py`:

```python
def build_keywords_response(site_id: str, curr_start: date, curr_end: date,
                             prev_start: date, prev_end: date) -> dict:
    """HANDOFF_SPEC.md `keywords` view shape — verified against the real fixture's
    keywordsView() in Limitless marketing dashboard2/app/api.js. See
    docs/superpowers/specs/2026-07-10-phaseB2-keywords-design.md for the field mapping."""
    intel = get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start, prev_end)

    def kw_id(row: dict) -> str:
        return row["keyword"]

    def to_api_keyword(row: dict) -> dict:
        return {
            "id": kw_id(row),
            "kw": row["keyword"],
            "intent": row.get("intent"),
            "pos": row.get("position"),
            "prevPos": row.get("prev_position"),
            "volume": row.get("search_volume"),
            "kd": row.get("keyword_difficulty"),
            "cpc": row.get("cpc"),
            "clicks": row.get("clicks"),
            "impressions": row.get("impressions"),
            "ctr": row.get("ctr"),
            "url": row.get("url"),
            "monthly": [],       # not tracked yet — honest empty, not fabricated
            "source": "sync",    # every currently-tracked keyword comes from the sync pipeline
            "serpFeatures": [],  # not tracked yet — honest empty, not fabricated
        }

    return {
        "kpis": {
            "total": intel["total_tracked"],
            "avg_pos": intel["avg_position"],
            "total_volume": intel["total_volume"],
            "total_clicks": intel["total_clicks"],
        },
        "intents": intel["intent_distribution"],
        "difficulty": {"easy": intel["kd_easy"], "medium": intel["kd_medium"], "hard": intel["kd_hard"]},
        "segments": {
            "quick_wins": [kw_id(r) for r in intel["quick_wins"]],
            "striking": [kw_id(r) for r in intel["striking"]],
            "declining": [kw_id(r) for r in intel["declining"]],
            "low_ctr": [kw_id(r) for r in intel["low_ctr"]],
        },
        "keywords": [to_api_keyword(r) for r in intel["all_keywords"]],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_keywords_service`
Expected: all pass (3 from Task 2 + 4 new = 7).

- [ ] **Step 5: Run the full suite and commit**

Run: `python manage.py test 2>&1 | tail -15` — expected: all pass.

```bash
git add apps/dashboard/services/keywords_service.py apps/dashboard/services/tests/test_keywords_service.py
git commit -m "feat(dashboard): add build_keywords_response API-shaped builder"
```

---

### Task 4: `GET /api/projects/<slug>/keywords` endpoint

**Files:**
- Modify: `apps/api/views.py`
- Modify: `apps/api/urls.py`
- Create: `apps/api/tests/test_keywords.py`

**Interfaces:**
- Consumes: `build_keywords_response` (Task 3), `resolve_project_or_404`,
  `latest_data_anchor` (Task 1).
- Produces: `GET /api/projects/<slug>/keywords` → the shape from Task 3.

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_keywords.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, KeywordRanking
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class KeywordsEndpointTests(APITestCase):
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
            session.add(KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                        keyword="iv therapy near me", position=6, clicks=12,
                                        impressions=200, search_volume=2400,
                                        keyword_difficulty=24, cpc=4.2, intent="commercial",
                                        url="/services/iv-therapy"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_keywords_returns_all_required_keys_with_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/keywords")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "intents", "difficulty", "segments", "keywords"]:
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["total"], 1)
        self.assertEqual(body["keywords"][0]["kw"], "iv therapy near me")

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/keywords")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/keywords")
        self.assertEqual(resp.status_code, 401)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_keywords`
Expected: FAIL — `404` (route doesn't exist).

- [ ] **Step 3: Implement the view**

Add to `apps/api/views.py`:

```python
from apps.dashboard.services.keywords_service import build_keywords_response


@method_decorator(login_not_required, name="dispatch")
class ProjectKeywordsView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        anchor = latest_data_anchor(site_id)
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates("30d", anchor)

        return Response(build_keywords_response(site_id, curr_start, curr_end, prev_start, prev_end))
```

- [ ] **Step 4: Wire the route**

In `apps/api/urls.py`, add:

```python
    path("projects/<slug:slug>/keywords", views.ProjectKeywordsView.as_view(), name="project-keywords"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_keywords`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 6: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all tests pass.

- [ ] **Step 7: Manual verification**

Start the dev server, log in, visit `/app/`, click the Keywords tab — confirm it loads real
data and the numbers are plausible against `/keywords/` (the old page).

- [ ] **Step 8: Update the checklist and commit**

Add a "PHASE B2 — Keywords ✅" note to `.claude/checklist.md` (same style as B1's entry),
and add `apps/dashboard/services/keywords_service.py` to `.claude/FILE_INDEX.md`.

```bash
git add apps/api/views.py apps/api/urls.py apps/api/tests/test_keywords.py .claude/checklist.md .claude/FILE_INDEX.md
git commit -m "feat(api): add GET /api/projects/<slug>/keywords"
```

## Self-review notes

- **Spec coverage:** every field in the design spec's target shape has a task producing it,
  including the honest-empty `monthly`/`serpFeatures` fields and the `all_keywords`/`prevPos`
  gap fix.
- **Shared helper (Task 1) genuinely de-duplicates**, not just moves code — confirmed both
  `ProjectOverviewView` and `ProjectSEOView` had byte-identical 11-line blocks before this task.
- **Test-class inheritance warning repeated explicitly** in Tasks 2, 3, and 4's briefs-to-be
  (via the Global Constraints section, inherited into every task brief) — this bug class has
  hit two tasks already in this project; every new test class in this plan is written with
  its own `setUp`, inheriting `TestCase`/`APITestCase` directly.
- **No duplication introduced:** `get_keyword_intelligence_raw` is a straight extraction (one
  deliberate, disclosed fix), `build_keywords_response` is a pure reshaping layer with no new
  query logic.

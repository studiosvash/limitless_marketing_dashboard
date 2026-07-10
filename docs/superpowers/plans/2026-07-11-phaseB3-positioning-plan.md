# Phase B3 — Position Tracking Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the Position Tracking page through `GET /api/projects/<slug>/positions?range=`,
reusing existing query functions as-is. Lowest-risk Phase B task so far — no existing
function bodies are modified, only additively extended or imported.

**Architecture:** Task 1 promotes `to_api_keyword` (B2) to a standalone function and adds a
`full_keywords` key to `get_keyword_intelligence_raw`'s return (both additive, zero behavior
change to existing callers). Task 2 builds the new API-shaped response, reusing
`_get_ranking_distribution`/`_get_position_changes`/`_get_competitor_grid` from
`apps/dashboard/views.py` as-is (imported, not moved — the old `positioning()` view uses
more functions than this API needs, and those extras stay put, out of scope). Task 3 wires
the endpoint.

**Tech Stack:** Django 6.0, DRF, SQLAlchemy 2.x, pandas.

## Global Constraints

- Never call an external API from a page-rendering or API-reading view — DB-only reads.
- Route: `GET /api/projects/<slug>/positions?range=7d|30d|90d`, no trailing slash — this
  endpoint DOES take `range` (per `HANDOFF_SPEC.md`'s endpoint table), unlike SEO/Keywords.
- `movers[]` must use the FULL keyword-object shape (same as the Keywords endpoint's
  `keywords[]` items) — never a truncated/lossy summary. Built from
  `get_keyword_intelligence_raw`'s new `full_keywords` key, not from
  `_get_position_changes`'s `improved`/`declined` lists (those are missing
  `intent`/`keyword_difficulty`/`cpc`/`impressions`).
- `competitors.rows[].comps` is a positional array aligned to `competitors.domains` — same
  order, `null` for any competitor with no ranking data for that keyword.
- `pipeline.utils.db_connection.get_session()` memoizes its engine per-process — every test
  needing an isolated temp DB must reset `db_connection._SessionFactory = None` in
  `setUp`/`addCleanup`.
- **Test-class inheritance footgun** (hit 3 times across this project already): any new test
  class must have its OWN `setUp()`, inherit `TestCase`/`APITestCase` directly, never a
  sibling test class. Verify with `-v 2` before committing that every test name appears
  exactly once.
- `_get_ranking_distribution`, `_get_position_changes`, `_get_competitor_grid` (and their
  transitive dependencies `_diff_label`, `pipeline.services.competitor_service`) are
  imported from `apps/dashboard/views.py` as-is — NOT moved/extracted, NOT modified. The old
  `positioning()` view continues to use them unchanged.

---

### Task 1: Promote `to_api_keyword`, add `full_keywords` to `get_keyword_intelligence_raw`

**Files:**
- Modify: `apps/dashboard/services/keywords_service.py`
- Modify: `apps/dashboard/services/tests/test_keywords_service.py`

**Interfaces:**
- Produces: `to_api_keyword(row: dict) -> dict` — promoted from a private closure inside
  `build_keywords_response` to a standalone, top-level function with the exact same body
  (zero logic change). Consumed by Task 2's `build_positions_response`.
- Produces: `get_keyword_intelligence_raw(...)`'s return dict gains one new key,
  `full_keywords: list[dict]` — the complete, uncapped `merged` frame (every tracked
  keyword, with `pos_change`/`prev_position` present on every row), sorted by clicks
  descending, via the same `df_to_dicts` helper already used for every other key. All
  EXISTING keys (`health_score`, `all_keywords`, `quick_wins`, etc.) are unchanged.
  Consumed by Task 2.

This task touches an already-approved, tested B2 module — treat it with the same care B2's
own tasks did. Existing B2 tests must pass completely unchanged (this is additive only).

- [ ] **Step 1: Write the failing tests**

Append to `apps/dashboard/services/tests/test_keywords_service.py` (reuse the existing
`KeywordIntelligenceTests` fixture data — do NOT add a new test class for this, these tests
belong logically with the existing raw-function tests):

```python
class KeywordIntelligenceTests(TestCase):
    # ... existing setUp and tests unchanged ...

    def test_full_keywords_includes_every_tracked_keyword(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:fusehealth.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertIn("full_keywords", result)
        full_ids = {row["keyword"] for row in result["full_keywords"]}
        self.assertEqual(full_ids, {"iv therapy near me", "mobile iv drip"})
        # every row must carry pos_change (real number or None), not be missing the key
        by_kw = {row["keyword"]: row for row in result["full_keywords"]}
        self.assertIn("pos_change", by_kw["iv therapy near me"])
        self.assertIsNotNone(by_kw["iv therapy near me"]["pos_change"])
```

(Add this as a new method inside the EXISTING `KeywordIntelligenceTests` class in the file —
find the class with `grep -n "class KeywordIntelligenceTests" apps/dashboard/services/tests/test_keywords_service.py`
and insert after its last existing test method, not as a new class.)

Also append, as its own standalone test (new small test, own class since it doesn't need the
seeded-DB fixture at all — it's a pure function of a plain dict):

```python
from apps.dashboard.services.keywords_service import to_api_keyword


class ToApiKeywordTests(TestCase):
    def test_shapes_a_raw_row_into_the_api_keyword_object(self):
        row = {
            "keyword": "iv therapy near me", "intent": "commercial", "position": 6.0,
            "prev_position": 9.0, "search_volume": 2400, "keyword_difficulty": 24.0,
            "cpc": 4.2, "clicks": 12, "impressions": 200, "ctr": 6.0,
            "url": "/services/iv-therapy",
        }
        api_kw = to_api_keyword(row)
        self.assertEqual(api_kw["id"], "iv therapy near me")
        self.assertEqual(api_kw["pos"], 6.0)
        self.assertEqual(api_kw["prevPos"], 9.0)
        self.assertEqual(api_kw["monthly"], [])
        self.assertEqual(api_kw["source"], "sync")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_keywords_service`
Expected: FAIL — `test_full_keywords_includes_every_tracked_keyword` fails with a `KeyError`
or `AssertionError` (key doesn't exist yet); `ToApiKeywordTests` fails with `ImportError`
(`to_api_keyword` isn't importable from module scope yet).

- [ ] **Step 3: Implement**

In `apps/dashboard/services/keywords_service.py`:

1. Move `to_api_keyword` (currently defined inside `build_keywords_response`, alongside
   `kw_id`) OUT to module level, placed after `get_keyword_intelligence_raw` and before
   `build_keywords_response`. Keep `kw_id` as a small standalone module-level function too
   (it's a one-liner `to_api_keyword` depends on):

```python
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
```

2. In `build_keywords_response`, DELETE the now-duplicate nested `def kw_id` and
   `def to_api_keyword` closures (they now exist at module level instead) — the rest of
   `build_keywords_response`'s body is unchanged, it just calls the module-level versions
   instead of nested ones (no call-site syntax change needed, Python resolves the name the
   same way).

3. In `get_keyword_intelligence_raw`, add ONE line to the return dict (both the success path
   and — for the new key only — optionally the error-fallback path; see below), right after
   the `"all_keywords"` line:

```python
                "all_keywords": df_to_dicts(all_keywords_df),
                "full_keywords": df_to_dicts(merged.sort_values("clicks", ascending=False)),
            }
```

   And in the `except Exception` fallback dict at the bottom of the function, add
   `"full_keywords": []` alongside the existing `"all_keywords": []`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_keywords_service`
Expected: all pass (7 existing B2 tests + 2 new = 9).

- [ ] **Step 5: Run the full suite — confirm zero regression to B2/B1/A**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all tests pass (baseline 97 + 2 new = 99). Specifically confirm
`apps.dashboard.services.tests.test_keywords_service` and `apps.api.tests.test_keywords`
(B2's endpoint tests, which call `build_keywords_response` transitively) still pass
unchanged — this proves the promotion + additive key didn't alter `build_keywords_response`'s
output.

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/keywords_service.py apps/dashboard/services/tests/test_keywords_service.py
git commit -m "refactor(dashboard): promote to_api_keyword to module scope, add full_keywords to keyword intelligence"
```

---

### Task 2: `build_positions_response` builder

**Files:**
- Create: `apps/dashboard/services/positioning_service.py`
- Create: `apps/dashboard/services/tests/test_positioning_service.py`

**Interfaces:**
- Consumes: `get_keyword_intelligence_raw`, `to_api_keyword` (Task 1); `_get_ranking_distribution`,
  `_get_position_changes`, `_get_competitor_grid` (imported as-is from `apps.dashboard.views`).
- Produces: `build_positions_response(site_id, curr_start, curr_end, prev_start, prev_end) ->
  dict` — the exact `{kpis, distribution, movement, competitors, movers}` shape. Consumed by
  Task 3's DRF view.

- [ ] **Step 1: Write the failing tests**

Create `apps/dashboard/services/tests/test_positioning_service.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, KeywordRanking, CompetitorKeywordRanking
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class BuildPositionsResponseTests(TestCase):
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
                # top3
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy", position=2, clicks=40, impressions=500,
                               search_volume=3000, keyword_difficulty=30, cpc=5.0,
                               intent="commercial", url="/iv-therapy"),
                # improved mover: pos 6 now, was 12 previously (delta = 12-6 = +6, improved)
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=6, clicks=10, impressions=150,
                               search_volume=800, keyword_difficulty=18, intent="informational",
                               url="/mobile"),
                KeywordRanking(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=12, clicks=4, impressions=90),
                # competitor ranking for the same keyword
                CompetitorKeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                          keyword="iv therapy", competitor_domain="driphydration.com",
                                          position=8),
            ])

    def test_top_level_keys(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        for key in ["kpis", "distribution", "movement", "competitors", "movers"]:
            self.assertIn(key, body)

    def test_kpis_and_distribution_use_real_data(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        self.assertEqual(body["kpis"]["tracked"], 2)
        self.assertEqual(body["distribution"]["top3"], 1)  # "iv therapy" at pos 2

    def test_movers_have_full_keyword_shape_not_a_summary(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        mover_ids = {m["id"] for m in body["movers"]}
        self.assertIn("mobile iv drip", mover_ids)
        mover = next(m for m in body["movers"] if m["id"] == "mobile iv drip")
        for key in ["kw", "intent", "pos", "prevPos", "volume", "kd", "clicks",
                    "impressions", "ctr", "url", "monthly", "source", "serpFeatures"]:
            self.assertIn(key, mover)
        self.assertEqual(mover["prevPos"], 12.0)

    def test_competitors_rows_align_positionally_with_domains(self):
        from apps.dashboard.services.positioning_service import build_positions_response
        body = build_positions_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                         date(2026, 6, 1), date(2026, 6, 1))
        self.assertIn("driphydration.com", body["competitors"]["domains"])
        idx = body["competitors"]["domains"].index("driphydration.com")
        row = next(r for r in body["competitors"]["rows"] if r["kw"] == "iv therapy")
        self.assertEqual(row["comps"][idx], 8)
        self.assertEqual(row["you"], 2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_positioning_service`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `apps/dashboard/services/positioning_service.py`:

```python
"""Position Tracking page — API-shaped builder. Reuses existing query functions
(_get_ranking_distribution, _get_position_changes, _get_competitor_grid) from
apps.dashboard.views AS-IS — they are not moved or modified, since the old positioning()
view uses more functions than this API needs. See
docs/superpowers/specs/2026-07-11-phaseB3-positioning-design.md for the field mapping."""

from datetime import date

from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw, to_api_keyword


def build_positions_response(site_id: str, curr_start: date, curr_end: date,
                              prev_start: date, prev_end: date) -> dict:
    """HANDOFF_SPEC.md `positions` view shape — verified against the real fixture's
    positionsView() in Limitless marketing dashboard2/app/api.js."""
    from apps.dashboard.views import _get_ranking_distribution, _get_position_changes, _get_competitor_grid

    dist = _get_ranking_distribution(site_id, curr_start, curr_end)
    changes = _get_position_changes(site_id, curr_start, curr_end, prev_start, prev_end)
    grid = _get_competitor_grid(site_id)

    kpis = {
        "tracked": dist["total"],
        "avg_pos": dist["avg_position"],
        "est_traffic": dist["total_clicks"],
        "impressions": dist["total_impressions"],
    }
    distribution = {
        "top3": dist["top3"],
        "p4_10": dist["top10"] - dist["top3"],
        "p11_20": dist["top20"] - dist["top10"],
        "p21_100": dist["total"] - dist["top20"],
    }
    movement = {
        "improved": changes["improved_count"],
        "declined": changes["declined_count"],
        "added": changes["new_count"],
        "lost": changes["lost_count"],
    }

    domains = grid.get("competitors", [])
    comp_rows = []
    for row in grid.get("rows", []):
        comps = [
            next((c["pos"] for c in row["cells"] if c["domain"] == dom), None)
            for dom in domains
        ]
        comp_rows.append({"kw": row["keyword"], "you": row["you"]["pos"], "comps": comps})
    competitors = {"domains": domains, "rows": comp_rows}

    intel = get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start, prev_end)
    movers_raw = [
        r for r in intel["full_keywords"]
        if r.get("pos_change") is not None and abs(r["pos_change"]) >= 2
    ]
    movers_raw.sort(key=lambda r: abs(r["pos_change"]), reverse=True)
    movers = [to_api_keyword(r) for r in movers_raw[:8]]

    return {
        "kpis": kpis,
        "distribution": distribution,
        "movement": movement,
        "competitors": competitors,
        "movers": movers,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_positioning_service`
Expected: `Ran 4 tests in ...s\n\nOK`

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/positioning_service.py apps/dashboard/services/tests/test_positioning_service.py
git commit -m "feat(dashboard): add build_positions_response API-shaped builder"
```

---

### Task 3: `GET /api/projects/<slug>/positions` endpoint

**Files:**
- Modify: `apps/api/views.py`
- Modify: `apps/api/urls.py`
- Create: `apps/api/tests/test_positions.py`

**Interfaces:**
- Consumes: `build_positions_response` (Task 2), `resolve_project_or_404`,
  `latest_data_anchor`, `range_to_period_dates` (already imported in `apps/api/views.py`
  from earlier phases).
- Produces: `GET /api/projects/<slug>/positions?range=7d|30d|90d` → the shape from Task 2.

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_positions.py`:

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


class PositionsEndpointTests(APITestCase):
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
                                        keyword="iv therapy", position=2, clicks=40,
                                        impressions=500, search_volume=3000, intent="commercial",
                                        url="/iv-therapy"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_positions_returns_all_required_keys_with_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/positions", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "distribution", "movement", "competitors", "movers"]:
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["tracked"], 1)

    def test_range_defaults_to_30d(self):
        resp = self.client_auth.get("/api/projects/fusehealth/positions")
        self.assertEqual(resp.status_code, 200)

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/positions")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/positions")
        self.assertEqual(resp.status_code, 401)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_positions`
Expected: FAIL — `404` (route doesn't exist).

- [ ] **Step 3: Implement the view**

Add to `apps/api/views.py`:

```python
from apps.dashboard.services.positioning_service import build_positions_response


@method_decorator(login_not_required, name="dispatch")
class ProjectPositionsView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url

        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        range_key = query.validated_data["range"]

        anchor = latest_data_anchor(site_id)
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates(range_key, anchor)

        return Response(build_positions_response(site_id, curr_start, curr_end, prev_start, prev_end))
```

(`OverviewQuerySerializer` is already imported in `apps/api/views.py` and already validates
`range` with a default of `"30d"` — reused as-is, this endpoint's range semantics are
identical to Overview's, unlike SEO/Keywords which hardcode `"30d"` with no param at all.)

- [ ] **Step 4: Wire the route**

In `apps/api/urls.py`, add:

```python
    path("projects/<slug:slug>/positions", views.ProjectPositionsView.as_view(), name="project-positions"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_positions`
Expected: `Ran 4 tests in ...s\n\nOK`

- [ ] **Step 6: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 7: Manual verification**

Start the dev server (kill any stray `runserver` processes on the target port first — this
project has repeatedly hit port collisions from leftover background servers; check
`netstat -ano | grep :8000` and clean up before starting a fresh one), log in, visit `/app/`,
click the Position Tracking tab — confirm it loads real data.

- [ ] **Step 8: Update the checklist and commit**

Add a "PHASE B3 — Position Tracking ✅" note to `.claude/checklist.md`, and add
`apps/dashboard/services/positioning_service.py` to `.claude/FILE_INDEX.md`.

```bash
git add apps/api/views.py apps/api/urls.py apps/api/tests/test_positions.py .claude/checklist.md .claude/FILE_INDEX.md
git commit -m "feat(api): add GET /api/projects/<slug>/positions"
```

## Self-review notes

- **Spec coverage:** every field in the design spec's target (corrected) shape has a task
  producing it, including the `movers[]` full-shape fix caught during plan-writing.
- **Lowest risk Phase B task**: no existing function body is modified (only imported/reused),
  the only "modified" existing code is one additive dict key on an already-thoroughly-tested
  B2 function.
- **`_get_competitor_grid`'s `rows[].you`/`cells[].pos` values can be `None`** (a keyword you
  don't rank for, or a competitor with no data) — `build_positions_response`'s reshaping
  preserves `None` as-is (matches the fixture's `null` for missing competitor data), not
  coerced to 0 or omitted.

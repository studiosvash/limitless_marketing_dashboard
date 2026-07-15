# Phase C2 — Site Audit Page Implementation Plan

Branch: `phase-c2-site-audit` (based on `phase-c1-backlinks`)
Design spec: `docs/superpowers/specs/2026-07-12-phaseC2-site-audit-design.md` — read it first for
the full field-by-field real-vs-`state:"setup"` mapping and rationale. This plan implements only
what that spec scoped as real.

## Global constraints (apply to every task)

- **No fake data, ever.** Every field not listed as "Real" in the design spec's mapping table
  must be `{"state": "setup"}` (objects) or `[]` (arrays) — never an invented number, string, or
  array entry. This is the single most important rule on this project.
- Match the exact pattern already used by `apps/dashboard/services/backlinks_service.py` and
  `apps/dashboard/services/alerts_service.py`: raw DB calculator functions (`query_*_raw`)
  separate from the API-shape builder (`build_site_audit_response`).
- Test-class hygiene: every new test class must define its own `setUp()` and inherit directly
  from `TestCase`/`APITestCase` — never inherit a sibling test class to reuse its `setUp()`
  (this silently re-runs the sibling's tests under the new class name and has caused inflated,
  wrong test counts multiple times already on this project).
- Every new endpoint test must assert real behavior: at minimum a real-data-returned case, a
  404-unknown-slug case, and a 401-unauthenticated case (copy the exact auth/session setup
  pattern from `apps/api/tests/test_backlinks.py`).
- Run the full suite (`python manage.py test`) after each task and report the pass count.

---

## Task 1: Extract raw `breakdown`/`cwv` calculators into `site_audit_service.py`

Create `apps/dashboard/services/site_audit_service.py` with two new query functions. These are
**new** query logic (not extracted from an existing view — there is no existing "site audit"
view in the MVP to preserve pixel-identical behavior for), so there's no "old page" to keep
unaffected, unlike every prior Phase B/C1 extraction task.

```python
"""Site Audit page (Phase C2) — real reshape of IndexingStatus + PageSpeed data plus honest
state:"setup" placeholders for everything requiring the still-blocked DataForSEO OnPage
connector (checks catalog, crawl metadata, historical snapshots). See
docs/superpowers/specs/2026-07-12-phaseC2-site-audit-design.md for the full field mapping and
why each field is scoped the way it is."""
import logging

from sqlalchemy import select

from pipeline.db.schema import IndexingStatus, PageSpeed
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def query_indexing_breakdown_raw(site_id: str) -> dict:
    """Bucket every IndexingStatus row for this site into one of five buckets, using only
    real GSC verdict/coverage_state/robots_txt_state values (no invented categories):
      - blocked: robots_txt_state == "DISALLOWED"
      - redirected: coverage_state contains "redirect" (case-insensitive)
      - broken: coverage_state contains "not found" or "404" (case-insensitive)
      - healthy: verdict == "PASS" and none of the above matched
      - withIssues: everything else (verdict NEUTRAL/FAIL not otherwise categorized)
    A row is checked against blocked/redirected/broken BEFORE the healthy/withIssues split,
    so e.g. a PASS-verdict page that's still robots-blocked lands in `blocked`, not `healthy`.
    """
    try:
        with get_session() as session:
            rows = session.execute(
                select(IndexingStatus).where(IndexingStatus.site_id == site_id)
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_indexing_breakdown_raw error: {e}", exc_info=True)
        return {"healthy": 0, "withIssues": 0, "broken": 0, "redirected": 0, "blocked": 0}

    breakdown = {"healthy": 0, "withIssues": 0, "broken": 0, "redirected": 0, "blocked": 0}
    for r in rows:
        coverage = (r.coverage_state or "").lower()
        robots = (r.robots_txt_state or "").upper()
        if robots == "DISALLOWED":
            breakdown["blocked"] += 1
        elif "redirect" in coverage:
            breakdown["redirected"] += 1
        elif "not found" in coverage or "404" in coverage:
            breakdown["broken"] += 1
        elif r.verdict == "PASS":
            breakdown["healthy"] += 1
        else:
            breakdown["withIssues"] += 1
    return breakdown


# Google's own published Core Web Vitals thresholds (web.dev/vitals) -- not invented.
_CWV_THRESHOLDS = {
    "lcp": {"good": 2.5, "poor": 4.0, "unit": "s"},
    "cls": {"good": 0.1, "poor": 0.25, "unit": ""},
}


def _cwv_metric(values: list[float], good: float, poor: float) -> dict:
    """p75 (nearest-rank, matching CrUX methodology) + good/mid/poor bucket counts for one
    metric's real per-page values. Returns None p75 if there's no data (never fabricates a
    value)."""
    if not values:
        return {"p75": None, "good": 0, "mid": 0, "poor": 0}
    ordered = sorted(values)
    idx = max(0, int(round(0.75 * len(ordered))) - 1)
    p75 = ordered[idx]
    good_n = sum(1 for v in values if v <= good)
    poor_n = sum(1 for v in values if v > poor)
    mid_n = len(values) - good_n - poor_n
    return {"p75": p75, "good": good_n, "mid": mid_n, "poor": poor_n}


def query_cwv_raw(site_id: str) -> dict:
    """Real LCP/CLS p75 + bucket counts from PageSpeed (mobile strategy only, matching how
    Google reports field/lab CWV data). PageSpeed has no tbt_ms column (only inp_ms, a
    different metric) so tbt is deliberately not computed here -- see design spec."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(PageSpeed).where(
                    PageSpeed.site_id == site_id, PageSpeed.strategy == "mobile"
                )
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_cwv_raw error: {e}", exc_info=True)
        rows = []

    lcp_values = [r.lcp_ms / 1000 for r in rows if r.lcp_ms is not None]
    cls_values = [r.cls for r in rows if r.cls is not None]

    lcp = _cwv_metric(lcp_values, _CWV_THRESHOLDS["lcp"]["good"], _CWV_THRESHOLDS["lcp"]["poor"])
    lcp.update({"unit": "s", "good_threshold": _CWV_THRESHOLDS["lcp"]["good"],
                "poor_threshold": _CWV_THRESHOLDS["lcp"]["poor"]})
    cls = _cwv_metric(cls_values, _CWV_THRESHOLDS["cls"]["good"], _CWV_THRESHOLDS["cls"]["poor"])
    cls.update({"unit": "", "good_threshold": _CWV_THRESHOLDS["cls"]["good"],
                "poor_threshold": _CWV_THRESHOLDS["cls"]["poor"]})

    return {"lcp": lcp, "cls": cls}
```

**Note on shape:** `query_cwv_raw`'s per-metric dict uses `p75`/`good`/`mid`/`poor`/`unit`/
`good_threshold`/`poor_threshold` keys — a superset of the SPA's sketch (`p75`/`unit`/`good`/
`poor`/`buckets:{good,mid,poor}`). Task 2's `build_site_audit_response` reshapes this into the
SPA's exact nested-`buckets` shape; keep the raw calculator's own return shape as-is (it's an
internal function, not the API response) so Task 2 has the flexibility to shape the final JSON
without re-querying.

**Tests** (new file `apps/dashboard/services/tests/test_site_audit_service.py`, follow the exact
`get_session`/temp-DB-per-test setup pattern from `apps/dashboard/services/tests/test_backlinks_service.py`):
- `query_indexing_breakdown_raw`: seed one `IndexingStatus` row per bucket (PASS/healthy,
  NEUTRAL/withIssues, coverage_state="Not found (404)"/broken, coverage_state="Page with
  redirect"/redirected, robots_txt_state="DISALLOWED"/blocked) and assert each count is 1.
  Also assert a robots_txt_state="DISALLOWED" row with verdict="PASS" still lands in `blocked`
  (priority-order case).
- `query_cwv_raw`: seed 4 `PageSpeed` mobile rows with lcp_ms values that land one in each of
  good/poor and cls values similarly; assert bucket counts and that `p75` is a real computed
  number (not None) given non-empty data. Also test the empty-data case returns `p75: None,
  good: 0, mid: 0, poor: 0` (not a crash, not a fabricated zero-value p75).
- Confirm `strategy="desktop"` rows are excluded from `query_cwv_raw` (seed one, assert it's
  not counted).

Report DONE with commit hash and test count after this task.

---

## Task 2: `build_site_audit_response` — real fields + honest `state:"setup"`

Add to `apps/dashboard/services/site_audit_service.py`:

```python
def build_site_audit_response(site_id: str) -> dict:
    """API-shaped Site Audit response. Real: breakdown, cwv.lcp, cwv.cls (reshaped from
    real IndexingStatus/PageSpeed data). Everything else is honestly state:"setup" --
    see docs/superpowers/specs/2026-07-12-phaseC2-site-audit-design.md for why each field
    is scoped the way it is (no rules catalog, crawl-run table, or snapshot history exists
    yet, and the one connector that would populate them is credential-blocked)."""
    breakdown = query_indexing_breakdown_raw(site_id)
    cwv_raw = query_cwv_raw(site_id)

    def _cwv_field(metric: dict) -> dict:
        return {
            "p75": metric["p75"],
            "unit": metric["unit"],
            "good": metric["good_threshold"],
            "poor": metric["poor_threshold"],
            "buckets": {"good": metric["good"], "mid": metric["mid"], "poor": metric["poor"]},
        }

    return {
        "score": {"state": "setup"},
        "crawl": {"state": "setup"},
        "domainChecks": [],
        "breakdown": breakdown,
        "catScore": {"state": "setup"},
        "cwv": {
            "lcp": _cwv_field(cwv_raw["lcp"]),
            "cls": _cwv_field(cwv_raw["cls"]),
            "tbt": {"state": "setup"},
        },
        "checks": [],
        "totals": {"errors": 0, "warnings": 0, "notices": 0},
        "crawledPages": [],
        "structure": [],
        "snapshots": [],
    }
```

**Tests** (new file `apps/dashboard/services/tests/test_site_audit_response.py`):
- Seed real `IndexingStatus`/`PageSpeed` rows, call `build_site_audit_response`, assert
  `breakdown` and `cwv.lcp`/`cwv.cls` match the raw calculators' output reshaped correctly.
- Exact-equality-assert every `state:"setup"` field: `score == {"state": "setup"}`,
  `crawl == {"state": "setup"}`, `domainChecks == []`, `catScore == {"state": "setup"}`,
  `cwv["tbt"] == {"state": "setup"}`, `checks == []`, `totals == {"errors": 0, "warnings": 0,
  "notices": 0}`, `crawledPages == []`, `structure == []`, `snapshots == []`. This is the test
  that actually enforces the no-fake-data contract — do not skip or weaken any of these
  assertions.
- Empty-DB case (no `IndexingStatus`/`PageSpeed` rows at all): assert `breakdown` is all zeros
  and `cwv.lcp.p75`/`cwv.cls.p75` are `None`, not a crash or a fabricated default.

Report DONE with commit hash and test count after this task.

---

## Task 3: `GET /api/projects/<slug>/audit` endpoint

In `apps/api/views.py`, add (following the exact pattern of `ProjectBacklinksView`):

```python
from apps.dashboard.services.site_audit_service import build_site_audit_response

@method_decorator(login_not_required, name="dispatch")
class ProjectSiteAuditView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_site_audit_response(site_id))
```

In `apps/api/urls.py`, add:
```python
path("projects/<slug:slug>/audit", views.ProjectSiteAuditView.as_view(), name="project-audit"),
```

**Tests** (new file `apps/api/tests/test_site_audit.py`, copy the exact structure/auth setup
from `apps/api/tests/test_backlinks.py`):
- Real-data case: seed one `IndexingStatus` + one `PageSpeed` row, `GET
  /api/projects/fusehealth/audit`, assert 200 and `breakdown` reflects the seeded row.
- `test_unknown_slug_is_404`
- `test_unauthenticated_is_401`

After this task: update `.claude/FILE_INDEX.md` (add `site_audit_service.py`, `test_site_audit.py`
entries, extend the `apps/api/views.py`/`urls.py`/`tests/` rows the same way C1 did) and
`.claude/checklist.md` (add a "PHASE C2 — Site Audit" section mirroring the C1 section's
structure: what's done, the honest-empty-states list, test count, scope-discipline note pointing
at the design spec).

Report DONE with commit hash and final full-suite test count after this task.

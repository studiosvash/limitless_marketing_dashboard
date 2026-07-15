# Phase C4 — Ads Implementation Plan

Branch: `phase-c4-ads` (based on `phase-c3-offsite-seo`)
Design spec: `docs/superpowers/specs/2026-07-13-phaseC4-ads-design.md` — read it first for the
full field-by-field real-vs-honest-empty mapping and rationale. This plan implements only what
that spec scoped as real.

## Global constraints (apply to every task)

- **No fake data, ever.** Every field not listed as "Real" in the design spec's mapping table
  must be `[]` (arrays) or an honest `0`/`None` inside a real, fully-keyed object — **never** a
  bare `{"state": "setup"}` sentinel for `totals`/`prev`/`pacing`/`syncMeta`/`window` (the SPA's
  Ads block has no setup-guard and will crash on `.toFixed()`/`.map()` calls against a sentinel
  object — this is the one hard rule specific to this phase, different from C1-C3).
- Match the exact pattern already used by `apps/dashboard/services/offsite_service.py`: raw DB
  calculator functions (`query_*_raw`) separate from the API-shape builder
  (`build_ads_response`).
- Do **not** port `_get_ads_overview`'s `roi` field (`apps/dashboard/views.py:130`) — it's an
  invented `$50/conversion` estimate, explicitly out of scope.
- Test-class hygiene: every new test class must define its own `setUp()` and inherit directly
  from `TestCase`/`APITestCase` — never inherit a sibling test class.
- Every new endpoint test must assert real behavior: a real-data-returned case proving period
  isolation (current vs. previous, like C3's offsite tests — not just a 200-OK check), a
  `range=7d`/`90d` boundary-shift case, a 404-unknown-slug case, a 401-unauthenticated case.
- Run the full suite (`python manage.py test`) after each task and report the pass count.

---

## Task 1: `ads_service.py` — real calculators + `build_ads_response`

Create `apps/dashboard/services/ads_service.py`:

```python
"""Ads page (Phase C4) — real reshape of AdMetricDaily + GA4 SEODaily data plus honest
empty/zero placeholders for everything requiring Google Ads credentials (currently blank in
.env) or schema that doesn't exist yet (SearchTerm/Attribution models, rich per-campaign
metadata). See docs/superpowers/specs/2026-07-13-phaseC4-ads-design.md for the full mapping.

IMPORTANT: unlike backlinks_service/site_audit_service/offsite_service, totals/prev/pacing/
syncMeta here must be REAL fully-keyed objects with honest zero/None values -- never a bare
{"state": "setup"} sentinel. The SPA's Ads block has no setup-guard anywhere and will crash
(TypeError on .toFixed()/.map()) if these are sentinel objects instead of real-shaped ones."""
import logging
import os
from datetime import date

from sqlalchemy import func, select

from pipeline.db.schema import AdMetricDaily, SEODaily
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def query_ads_totals_raw(site_id: str, start: date, end: date) -> dict:
    """Real AdMetricDaily aggregation (spend-weighted roas) + real GA4 conversions
    cross-reference from SEODaily. Honest 0 for conv_value/ga4_revenue (no such columns
    exist anywhere in this schema)."""
    try:
        with get_session() as session:
            row = session.execute(
                select(
                    func.sum(AdMetricDaily.spend).label("spend"),
                    func.sum(AdMetricDaily.clicks).label("clicks"),
                    func.sum(AdMetricDaily.impressions).label("impressions"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                ).where(AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
            ).first()
            spend = float(row.spend or 0)
            clicks = float(row.clicks or 0)
            impressions = float(row.impressions or 0)
            conversions = float(row.conversions or 0)

            weighted = session.execute(
                select(
                    func.sum(AdMetricDaily.spend * AdMetricDaily.roas).label("weighted_roas_sum"),
                ).where(
                    AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end,
                    AdMetricDaily.roas.isnot(None),
                )
            ).first()
            roas = float(weighted.weighted_roas_sum or 0) / spend if spend else 0.0

            ga4_row = session.execute(
                select(func.sum(SEODaily.conversions)).where(
                    SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end
                )
            ).scalar()
            ga4_key_events = float(ga4_row or 0)
    except Exception as e:
        logger.error(f"query_ads_totals_raw error: {e}", exc_info=True)
        return {"spend": 0.0, "clicks": 0.0, "impressions": 0.0, "conversions": 0.0,
                "cpc": 0.0, "roas": 0.0, "conv_value": 0.0, "ga4_key_events": 0.0, "ga4_revenue": 0.0}

    return {
        "spend": spend, "clicks": clicks, "impressions": impressions, "conversions": conversions,
        "cpc": spend / clicks if clicks else 0.0,
        "roas": roas,
        "conv_value": 0.0,  # no revenue/value column exists on AdMetricDaily
        "ga4_key_events": ga4_key_events,
        "ga4_revenue": 0.0,  # no revenue column exists on SEODaily
    }


def query_ads_trend_raw(site_id: str, start: date, end: date) -> list[dict]:
    """Real per-day spend/conversions + GA4 conversions cross-reference. Same shape/pattern
    as offsite_service.query_offsite_trend_raw."""
    try:
        with get_session() as session:
            ads_rows = session.execute(
                select(
                    AdMetricDaily.date,
                    func.sum(AdMetricDaily.spend).label("spend"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                ).where(AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
                .group_by(AdMetricDaily.date).order_by(AdMetricDaily.date)
            ).all()
            ads_by_date = {r.date: (float(r.spend or 0), float(r.conversions or 0)) for r in ads_rows}

            ga4_rows = session.execute(
                select(SEODaily.date, func.sum(SEODaily.conversions).label("conversions"))
                .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
                .group_by(SEODaily.date).order_by(SEODaily.date)
            ).all()
            ga4_by_date = {r.date: float(r.conversions or 0) for r in ga4_rows}
    except Exception as e:
        logger.error(f"query_ads_trend_raw error: {e}", exc_info=True)
        return []

    all_dates = sorted(set(ads_by_date) | set(ga4_by_date))
    return [
        {
            "date": d.isoformat(),
            "spend": ads_by_date.get(d, (0.0, 0.0))[0],
            "conversions": ads_by_date.get(d, (0.0, 0.0))[1],
            "ga4_key_events": ga4_by_date.get(d, 0.0),
        }
        for d in all_dates
    ]


def query_ads_pacing_raw(site_id: str) -> dict:
    """Real calendar-month-to-date spend + honest-zero budget/projection math. Always 'this
    calendar month' -- independent of the range param, matching the SPA's 'day X of Y' label."""
    today = date.today()
    month_start = today.replace(day=1)
    try:
        with get_session() as session:
            row = session.execute(
                select(func.sum(AdMetricDaily.spend)).where(
                    AdMetricDaily.site_id == site_id, AdMetricDaily.date >= month_start, AdMetricDaily.date <= today
                )
            ).scalar()
            mtd_spend = float(row or 0)
    except Exception as e:
        logger.error(f"query_ads_pacing_raw error: {e}", exc_info=True)
        mtd_spend = 0.0

    day_of_month = today.day
    if today.month == 12:
        days_in_month = 31
    else:
        next_month = today.replace(month=today.month + 1, day=1)
        days_in_month = (next_month - month_start).days

    monthly_budget = 0.0  # no budget-setting feature exists anywhere in this codebase
    projected = (mtd_spend / day_of_month * days_in_month) if day_of_month else 0.0
    pct = min(100, round(mtd_spend / monthly_budget * 100)) if monthly_budget else 0

    return {
        "monthly_budget": monthly_budget, "mtd_spend": mtd_spend, "projected": projected,
        "day_of_month": day_of_month, "days_in_month": days_in_month, "pct": pct,
        "channels": [],  # no per-platform budget data exists
    }


def build_ads_response(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date) -> dict:
    """API-shaped Ads response. Real: totals, prev, trend, pacing (all honest-zero today
    since AdMetricDaily has 0 rows), window. Honest []: campaigns, searchTerms, attribution,
    landingPages, negatives (no backing schema for the rich per-row fields the SPA's tabs
    need, or no model exists at all). syncMeta.connected reflects the real Google Ads
    credential state -- see docs/superpowers/specs/2026-07-13-phaseC4-ads-design.md."""
    totals = query_ads_totals_raw(site_id, curr_start, curr_end)
    prev = query_ads_totals_raw(site_id, prev_start, prev_end)
    trend = query_ads_trend_raw(site_id, curr_start, curr_end)
    pacing = query_ads_pacing_raw(site_id)

    connected = bool(os.getenv("GOOGLE_ADS_CUSTOMER_ID") and os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"))

    return {
        "totals": totals,
        "prev": prev,
        "trend": trend,
        "pacing": pacing,
        "campaigns": [],
        "searchTerms": [],
        "attribution": [],
        "landingPages": [],
        "negatives": [],
        "window": {"from": curr_start.isoformat(), "to": curr_end.isoformat(), "days": (curr_end - curr_start).days + 1},
        "syncMeta": {
            "connected": connected,
            "cadence": None, "last_pull": None, "next_pull": None,
            "ops_used": 0, "ops_limit": 0, "ga4_tokens_used": 0, "ga4_tokens_limit": 0,
        },
    }
```

**Note on credential check:** `GOOGLE_ADS_CUSTOMER_ID`/`GOOGLE_ADS_DEVELOPER_TOKEN` are not
exposed on Django `settings` anywhere in this codebase (confirmed) — read them via `os.getenv`
directly, exactly matching how `pipeline/connectors/google_ads.py` itself checks them.

**Tests** (new file `apps/dashboard/services/tests/test_ads_service.py`, follow the exact
`get_session`/temp-DB-per-test setup pattern from `test_offsite_service.py`):
- `query_ads_totals_raw`: seed 2 `AdMetricDaily` rows with different `roas` values, assert the
  spend-weighted average is correct (not a naive unweighted average — pick values where the two
  differ, e.g. weighted avg ≠ simple avg, to prove the weighting is real). Seed a `SEODaily` row
  in the same window, assert `ga4_key_events` reflects it. Assert `conv_value`/`ga4_revenue`
  are always `0.0` regardless of data (never fabricated). Empty-DB case: assert every field is
  a real `0.0`, not `None`/missing/a crash.
- `query_ads_trend_raw`: seed rows on different dates (some with only `AdMetricDaily`, some
  with only `SEODaily`, some with both), assert the per-day merge is correct and no date is
  silently dropped.
- `query_ads_pacing_raw`: seed an `AdMetricDaily` row dated the 1st of the real current month
  (use a date computed from `date.today()`, not a hardcoded date — the test must not break next
  month) and one dated last month (assert excluded from `mtd_spend`). Assert `monthly_budget`
  is `0.0`, `pct` is `0` (not a crash from the honest-zero budget), `projected` is the real
  `mtd_spend / day_of_month * days_in_month` formula result.
- `build_ads_response`: exact-equality-assert `campaigns == []`, `searchTerms == []`,
  `attribution == []`, `landingPages == []`, `negatives == []`, and every `syncMeta` field
  (`connected` real bool, everything else honest `0`/`None`) — this is the test that enforces
  the no-fake-data contract, do not skip or weaken it. Also assert `window` matches the real
  passed-in `curr_start`/`curr_end`.

Report DONE with commit hash and test count after this task.

---

## Task 2: `GET /api/projects/<slug>/ads` endpoint

In `apps/api/views.py`, add (following the exact pattern of `ProjectOffsiteView` — range-aware):

```python
from apps.dashboard.services.ads_service import build_ads_response

@method_decorator(login_not_required, name="dispatch")
class ProjectAdsView(APIView):
    def get(self, request, slug):
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)
        return Response(build_ads_response(site_id, curr_start, curr_end, prev_start, prev_end))
```

In `apps/api/urls.py`, add:
```python
path("projects/<slug:slug>/ads", views.ProjectAdsView.as_view(), name="project-ads"),
```

**Tests** (new file `apps/api/tests/test_ads.py`, copy the exact structure/period-isolation
rigor from `apps/api/tests/test_offsite.py` — that file's period-isolation and boundary-shift
test pattern is the template to match, not a weaker "assert 200" version):
- Real-data default-range case: seed `AdMetricDaily` rows in both a current-period and
  previous-period window, assert `totals`/`prev` each reflect only their own period.
- `range=7d` case: seed an out-of-window row, assert it's excluded.
- `test_unknown_slug_is_404`
- `test_unauthenticated_is_401`

After this task: update `.claude/FILE_INDEX.md` (add `ads_service.py`, `test_ads.py` entries,
extend the `apps/api/views.py`/`urls.py`/`tests/` rows the same way C1-C3 did) and
`.claude/checklist.md` (add a "PHASE C4 — Ads" section mirroring C1-C3's section structure).

Report DONE with commit hash and final full-suite test count after this task.

---

## Task 3: SPA fidelity fix — honest `syncMeta` timestamp + connection-status fallback

**Read the design spec's "SPA fidelity fix" section first.** Two narrow, localized fixes in
`static/spa/index.html` — NOT a whole-tab guard (unnecessary here; every array/object in the
Ads block is already crash-safe against the real response shape Task 1/2 ship):

1. **Fake-looking timestamp fix** (`static/spa/index.html`, inside `if
   (this.ADSTABS.includes(tab))`, the `vals.adsSync = {...}` block — grep `adsSync` to find the
   current line): `fmtTs(sm.last_pull)`/`fmtTs(sm.next_pull)` currently call
   `new Date(z).toLocaleString(...)` unconditionally. When `sm.last_pull`/`sm.next_pull` are
   `None` (the honest value per Task 1's `build_ads_response`), `new Date(null)` produces the
   epoch (`Jan 1, 1970`) — not a crash, but a fabricated-looking date. Fix `fmtTs` (or the two
   call sites) to return an honest placeholder (e.g. `'—'` or `'not yet synced'`) when the input
   is `null`/`undefined`, matching the pattern C3 used for `off.cadence`.
2. **Hardcoded "connected" indicator**: grep the Ads tab's header/source-line markup (near
   where `{{ adsSync.cadence }}` is rendered) for a hardcoded green status dot or "Connected"-
   style badge (verify its exact current markup — the design spec flags this by description,
   confirm the precise line at implementation time, same investigative step C3's Task 3 did for
   the LinkedIn card). Gate it on the real `data.syncMeta.connected` field this phase's
   `build_ads_response` adds specifically for this: green/"Connected" only when `true`, a muted
   "Not connected" state otherwise — same pattern as C3's `89f1954` LinkedIn-card fix. If a
   literal "$0.00 API cost"-style unbound string exists nearby (the design spec's research
   flagged one candidate), assess honestly whether it's a true statement (Google Ads API access
   itself has no per-call cost) or should also be gated — use judgment, don't guess if unsure,
   note it in your report for the reviewer either way.

**Verification** (no new automated test — JS-only template/render fix, no JS test harness,
same limitation noted in every prior phase's review):
- Manually trace: with `data.syncMeta = {"connected": false, "cadence": null, "last_pull":
  null, "next_pull": null, ...}` (the real payload from Task 1/2), confirm no fake "1970" date
  and no false "Connected" claim render.
- Confirm `<sc-if>`/`<sc-for>` tag-balance count is unchanged or increases by exactly the
  number of new guard tags you add (run the same Python regex tag-count check used in C1-C3's
  fixes).
- Run the full Python test suite once more to confirm it's unaffected (SPA-only change).
- Update `.claude/checklist.md`'s C4 section with a "SPA fidelity fix" note, same structure as
  C1-C3's entries.

Report DONE with commit hash after this task. This is the last task of Phase C — after this,
dispatch the final whole-branch review.

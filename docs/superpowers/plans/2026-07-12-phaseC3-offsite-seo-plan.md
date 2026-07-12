# Phase C3 — Off-site SEO Page Implementation Plan

Branch: `phase-c3-offsite-seo` (based on `phase-c2-site-audit`)
Design spec: `docs/superpowers/specs/2026-07-12-phaseC3-offsite-seo-design.md` — read it first for
the full field-by-field real-vs-`state:"setup"`/`[]` mapping and rationale. This plan implements
only what that spec scoped as real.

## Global constraints (apply to every task)

- **No fake data, ever.** Every array field not listed as "Real" in the design spec's mapping
  table must be a true `[]`. Every object field not listed as "Real" must be `{"state": "setup"}`.
  Never an invented number, string, or array entry. This is the single most important rule on
  this project.
- Match the exact pattern already used by `apps/dashboard/services/backlinks_service.py` /
  `site_audit_service.py`: raw DB calculator functions (`query_*_raw`) separate from the
  API-shape builder (`build_offsite_response`).
- This endpoint **takes a `range` param** (unlike C1/C2) — use the shared `resolve_range_periods`
  helper from `apps/api/views.py`, matching `ProjectOverviewView`/`ProjectPositionsView`, not
  `resolve_project_or_404` alone.
- Test-class hygiene: every new test class must define its own `setUp()` and inherit directly
  from `TestCase`/`APITestCase` — never inherit a sibling test class (this has caused inflated,
  wrong test counts multiple times already on this project).
- Every new endpoint test must assert real behavior: at minimum a real-data-returned case, a
  404-unknown-slug case, and a 401-unauthenticated case (copy the exact auth/session setup
  pattern from `apps/api/tests/test_backlinks.py`).
- Run the full suite (`python manage.py test`) after each task and report the pass count.

---

## Task 1: `offsite_service.py` raw calculators + `build_offsite_response`

Create `apps/dashboard/services/offsite_service.py`:

```python
"""Off-site SEO page (Phase C3) — real reshape of GA4-sourced SEODaily columns (sessions,
engagement_rate, conversions, users, landing_page) plus honest state:"setup"/[] placeholders
for everything requiring GA4 dimensions (channel, source) this codebase doesn't fetch yet, or
per-platform social connectors that don't exist/aren't credentialed. See
docs/superpowers/specs/2026-07-12-phaseC3-offsite-seo-design.md for the full field mapping."""
import logging

from sqlalchemy import func, select

from pipeline.db.schema import SEODaily
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def query_offsite_totals_raw(site_id: str, start, end) -> dict:
    """Real sessions/users/engagementRate/keyEvents/engagedSessions aggregated over the period.
    revenue/referringDomains are honest 0 (no GA4 revenue/source dimension exists yet) --
    included here, not left for the builder, so this function's return shape is already the
    complete real-data contract for `totals`/`prev`."""
    try:
        with get_session() as session:
            row = session.execute(
                select(
                    func.sum(SEODaily.sessions).label("sessions"),
                    func.sum(SEODaily.users).label("users"),
                    func.avg(SEODaily.engagement_rate).label("engagement_rate"),
                    func.sum(SEODaily.conversions).label("conversions"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
            ).first()
    except Exception as e:
        logger.error(f"query_offsite_totals_raw error: {e}", exc_info=True)
        row = None

    sessions = int(row.sessions or 0) if row else 0
    engagement_rate = float(row.engagement_rate or 0.0) if row else 0.0
    return {
        "sessions": sessions,
        "users": int(row.users or 0) if row else 0,
        "engagementRate": round(engagement_rate * 100, 1),
        "engagedSessions": round(sessions * engagement_rate),
        "keyEvents": int(row.conversions or 0) if row else 0,
        "revenue": 0,
        "referringDomains": 0,
    }


def query_offsite_trend_raw(site_id: str, start, end) -> list[dict]:
    """Real daily [{date, sessions, engagedSessions, keyEvents, revenue}] -- same pattern as
    overview_service.query_daily_traffic_raw. revenue honest 0 per day (see totals note)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.date,
                    func.sum(SEODaily.sessions).label("sessions"),
                    func.avg(SEODaily.engagement_rate).label("engagement_rate"),
                    func.sum(SEODaily.conversions).label("conversions"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
                .group_by(SEODaily.date)
                .order_by(SEODaily.date.asc())
            ).all()
    except Exception as e:
        logger.error(f"query_offsite_trend_raw error: {e}", exc_info=True)
        return []

    out = []
    for r in rows:
        sessions = int(r.sessions or 0)
        er = float(r.engagement_rate or 0.0)
        out.append({
            "date": str(r.date),
            "sessions": sessions,
            "engagedSessions": round(sessions * er),
            "keyEvents": int(r.conversions or 0),
            "revenue": 0,
        })
    return out


def query_offsite_landing_pages_raw(site_id: str, start, end) -> list[dict]:
    """Real [{url, topSource, sessions, engagedRate, keyEvents}], capped at 50 (matching the
    existing _get_page_health cap convention in apps/dashboard/views.py). topSource is honestly
    "" -- no GA4 source dimension exists yet to attribute it, see design spec."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page.label("url"),
                    func.sum(SEODaily.sessions).label("sessions"),
                    func.avg(SEODaily.engagement_rate).label("engagement_rate"),
                    func.sum(SEODaily.conversions).label("conversions"),
                )
                .where(
                    SEODaily.site_id == site_id,
                    SEODaily.date >= start,
                    SEODaily.date <= end,
                    SEODaily.landing_page.isnot(None),
                )
                .group_by(SEODaily.landing_page)
                .order_by(func.sum(SEODaily.sessions).desc())
                .limit(50)
            ).all()
    except Exception as e:
        logger.error(f"query_offsite_landing_pages_raw error: {e}", exc_info=True)
        return []

    return [
        {
            "url": r.url,
            "topSource": "",
            "sessions": int(r.sessions or 0),
            "engagedRate": round(float(r.engagement_rate or 0.0), 4),
            "keyEvents": int(r.conversions or 0),
        }
        for r in rows
    ]


def build_offsite_response(site_id: str, curr_start, curr_end, prev_start, prev_end) -> dict:
    """API-shaped Off-site SEO response. Real: totals, prev, trend, landingPages (reshaped from
    real SEODaily GA4 columns). channels/referrers/social honestly [] -- no channel/source GA4
    dimension or social-platform connector exists yet. connectors{} real (all currently false).
    syncMeta honestly state:"setup" -- no GA4 pull-metadata table exists. See design spec for why
    each field is scoped the way it is."""
    return {
        "totals": query_offsite_totals_raw(site_id, curr_start, curr_end),
        "prev": query_offsite_totals_raw(site_id, prev_start, prev_end),
        "trend": query_offsite_trend_raw(site_id, curr_start, curr_end),
        "channels": [],
        "referrers": [],
        "social": [],
        "landingPages": query_offsite_landing_pages_raw(site_id, curr_start, curr_end),
        "connectors": {
            "linkedin": False, "reddit": False, "youtube": False,
            "x": False, "facebook": False, "instagram": False,
        },
        "syncMeta": {"state": "setup"},
    }
```

**Tests** (new file `apps/dashboard/services/tests/test_offsite_service.py`, follow the exact
`get_session`/temp-DB-per-test setup pattern from `apps/dashboard/services/tests/test_backlinks_service.py`):
- `query_offsite_totals_raw`: seed 2 `SEODaily` rows in-period with known `sessions`/`users`/
  `engagement_rate`/`conversions`, assert `sessions`/`users`/`keyEvents` are the real sums,
  `engagementRate` is the real average *100 rounded to 1dp, `engagedSessions` matches
  `round(total_sessions * avg_engagement_rate)` computed by hand in the test, `revenue`/
  `referringDomains` are exactly `0`. Also seed one row OUTSIDE the period and assert it's
  excluded.
- `query_offsite_trend_raw`: seed 3 daily rows, assert one dict per date in ascending date order,
  each `engagedSessions` matching its own day's `round(sessions * engagement_rate)` (not the
  period average — this must be a genuinely per-day calculation, not accidentally reusing the
  totals figure).
- `query_offsite_landing_pages_raw`: seed 3 distinct `landing_page` values with different session
  counts, assert descending-by-sessions order and that `topSource` is exactly `""` for all rows
  (not fabricated). Seed a 4th row with `landing_page=None` and assert it's excluded.
- Empty-DB case for all three functions: assert `query_offsite_totals_raw` returns all-zero
  (not a crash), `query_offsite_trend_raw`/`query_offsite_landing_pages_raw` return `[]`.
- `build_offsite_response`: seed real data, call it, assert `totals`/`prev`/`trend`/
  `landingPages` match the raw calculators' output, and exact-equality-assert every
  honest-empty field: `channels == []`, `referrers == []`, `social == []`,
  `connectors == {"linkedin": False, "reddit": False, "youtube": False, "x": False,
  "facebook": False, "instagram": False}`, `syncMeta == {"state": "setup"}`. This is the test
  that actually enforces the no-fake-data contract — do not skip or weaken any of these
  assertions.

Report DONE with commit hash and test count after this task.

---

## Task 2: `GET /api/projects/<slug>/offsite?range=` endpoint

In `apps/api/views.py`, add (following the exact pattern of `ProjectPositionsView`, which is the
closest existing analogue: also takes `range` via `resolve_range_periods`):

```python
from apps.dashboard.services.offsite_service import build_offsite_response

@method_decorator(login_not_required, name="dispatch")
class ProjectOffsiteView(APIView):
    def get(self, request, slug):
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)
        return Response(build_offsite_response(site_id, curr_start, curr_end, prev_start, prev_end))
```

In `apps/api/urls.py`, add:
```python
path("projects/<slug:slug>/offsite", views.ProjectOffsiteView.as_view(), name="project-offsite"),
```

**Tests** (new file `apps/api/tests/test_offsite.py`, copy the exact structure/auth setup from
`apps/api/tests/test_positions.py` — this is the closest existing analogue since it also takes
`range`, not `apps/api/tests/test_backlinks.py`):
- Real-data case: seed `SEODaily` rows spanning both the current and previous 30d period,
  `GET /api/projects/fusehealth/offsite` (default range), assert 200 and `totals`/`trend`
  reflect the seeded current-period rows only (not previous-period bleed).
- `range=7d`/`range=90d` param cases: assert the period boundaries actually shift (at minimum,
  assert a row outside the requested range's window is excluded from `totals.sessions`).
- `test_unknown_slug_is_404`
- `test_unauthenticated_is_401`

After this task: update `.claude/FILE_INDEX.md` (add `offsite_service.py`, `test_offsite.py`
entries, extend the `apps/api/views.py`/`urls.py`/`tests/` rows the same way C1/C2 did).

Report DONE with commit hash and test count after this task.

---

## Task 3: SPA fidelity fix — honest `syncMeta` fallback (NOT a whole-tab guard)

**Read the design spec's "SPA fidelity fix" section first** — it explains in detail why this tab,
unlike C1's Backlinks and C2's Site Audit, does NOT need a whole-tab `state:"setup"` guard: every
array field this endpoint returns is a real (possibly-empty) `[]`, and `totals`/`prev`/`trend`/
`landingPages` are always real objects/arrays, so every `.map`/`.slice`/`.find`/`Math.max.apply`
call in the SPA's `if (tab === 'offsite')` block (`static/spa/index.html:4996-5090`) already
executes safely against empty data. Do not build a bigger guard than this task describes — that
would be scope creep past what the actual (verified) risk requires.

The one real fidelity gap: `static/spa/index.html` lines 5007-5008 currently read

```js
off.cadence = data.syncMeta.cadence;
off.tokens = data.syncMeta.ga4_tokens_used + ' / ' + this.fmt(data.syncMeta.ga4_tokens_limit) + ' GA4 tokens';
```

Since `data.syncMeta` is honestly `{"state": "setup"}`, this renders literal `"undefined / — GA4
tokens"` in the source banner. Fix:

```js
const syncSetup = data.syncMeta.state === 'setup';
off.cadence = syncSetup ? 'not yet connected' : data.syncMeta.cadence;
off.tokens = syncSetup ? '' : (data.syncMeta.ga4_tokens_used + ' / ' + this.fmt(data.syncMeta.ga4_tokens_limit) + ' GA4 tokens');
```

Check the template around where `{{ off.cadence }}`/`{{ off.tokens }}` are rendered (grep
`off.cadence` in the "source line" / header area of the Off-site SEO tab's markup, near the
`showOffsite` `sc-if`) — if `off.tokens` being an empty string would leave an awkward trailing
separator (e.g. `"· "` with nothing after it), wrap just that inline piece in an `<sc-if
value="{{ !off.tokensEmpty }}">` (add `off.tokensEmpty = syncSetup` to the JS above) rather than
restructuring the whole header. Keep this fix minimal and localized.

**Verification** (no new automated test — this is a JS-only template/render fix on a page with no
JS test harness, same limitation noted in C1/C2's reviews):
- Manually trace: with `data.syncMeta = {"state": "setup"}` (the real payload from Task 1/2),
  confirm `off.cadence`/`off.tokens` no longer produce the literal string `"undefined"`.
- Confirm `<sc-if>`/`<sc-for>` tag-balance count is unchanged (this fix adds no new tags, only
  modifies JS logic) — run the same Python regex tag-count check used in C1/C2's fixes as a
  sanity check that nothing else in the file was accidentally touched.
- Run the full Python test suite once more to confirm it's unaffected (SPA-only change).

After this task: update `.claude/checklist.md` (add a "PHASE C3 — Off-site SEO" section
mirroring C1/C2's structure: what's real, the honest-empty/setup fields, test count, scope
discipline note, and — since this is the first Phase C sub-project where the SPA did NOT need a
whole-tab guard — a short explicit note on why, so C4 doesn't assume every remaining tab needs
one either).

Report DONE with commit hash and final full-suite test count after this task.

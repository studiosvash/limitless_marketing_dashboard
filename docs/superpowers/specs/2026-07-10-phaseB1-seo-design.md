# Phase B1 — SEO Page Design Spec

> Status: approved 2026-07-10. First of four Phase B sub-projects (B1 SEO, B2 Keywords,
> B3 Position Tracking, B4 Alerts), each its own design → plan → build cycle, per the
> roadmap in `docs/superpowers/specs/2026-07-10-limitless-migration-roadmap-and-phaseA-design.md`.
> Builds on Phase A's DRF app, Bearer auth, and service-module extraction pattern
> (branched from `phase-a-foundation`, not `main`).

## Goal

Expose the SEO page's data — already fully computed by the old MVP — through a new
`GET /api/projects/<slug>/seo` endpoint matching the real SPA's expected shape, using the
exact same extraction pattern Phase A established for Overview: pull the query logic out of
`apps/dashboard/views.py`'s `seo()` view into a focused service module, keep the old page
working unchanged by importing from there, add new API-shaped builders on top.

This is a **pure mapping task** — every field the new design needs already has a real,
working query behind it in the old MVP. No new connectors, no new DB tables, no
`state:"setup"` cases (unlike Phases C/D, which build genuinely new features).

## Target response shape (verified against the real SPA source)

Confirmed directly from `Limitless marketing dashboard2/app/api.js`'s `seoView(fix)`
function (the fixture implementation the real API must match):

```jsonc
{
  "kpis": { "low_ctr": 4, "anomalies": 2, "critical": 1, "total_issues": 7 },
  "lowCtrPages": [
    { "url": "/services/iv-therapy", "impressions": 4200, "clicks": 42, "ctr": 1.0, "avg_pos": 8.4 }
  ],
  "countries": [
    { "country": "United States", "clicks": 610, "ctr": 4.2 }
  ],
  "anomalies": [
    { "id": "12", "metric": "Clicks", "severity": "high", "deviation": "-38%",
      "date": "2026-07-02", "detail": "Clicks dropped 38% vs. daily average" }
  ],
  "quickWinKws": 6
}
```

## Mapping — old MVP source → new shape

All sources are existing functions in `apps/dashboard/views.py`'s `seo()` view and its
helpers, already computing real data from `fusehealth.db`:

**Correction (2026-07-10, caught during plan-writing by re-checking the fixture's exact
source instead of trusting the earlier summary):** the first draft of this table mapped
`kpis.critical` to the old page's `attention["high_sev_issues"]`. That's wrong — the real
fixture (`seoView()` in `app/api.js`) defines `critical` as the count of pages with
`kind === 'gone'` (i.e. 404s specifically), not "high-severity issues" generically. It also
computes `total_issues` as a fresh sum (`non-ok pages + anomalies + lowCtrPages`), not a
passthrough of the old page's `attention["issue_count"]` (which only counted technical
issues, not anomalies/low-CTR too). Table below reflects the corrected mapping.

| New field | Old source | Reshape needed |
|---|---|---|
| `kpis.low_ctr` | `attention["low_ctr_count"]` (`len(low_ctr_pages)`) | rename key |
| `kpis.anomalies` | `attention["anomaly_count"]` (`len(anomalies)`) | rename key |
| `kpis.critical` | **new**: unlimited count of `TechnicalIssue` rows where `issue_type == "not_found_404"` | **not** `_get_technical_issues()` — that helper caps at `limit=15` (a display limit for the old page's table), which would silently undercount on any site with more than 15 issues. Needs a fresh, unlimited `COUNT(*) ... WHERE issue_type = 'not_found_404'` query. |
| `kpis.total_issues` | **new**: `technical_issue_count + len(anomalies) + len(low_ctr_pages)` | fresh sum; `technical_issue_count` is the same unlimited count query as above, without the type filter — again, not `_get_technical_issues()`'s capped-at-15 list length |
| `lowCtrPages[]` | `_get_low_ctr_pages()` | drop `url_short`; keep `url/impressions/clicks/ctr`; rename `avg_position`→`avg_pos` |
| `countries[]` | `_get_seo_by_dimension()["by_country"]` | already has `country/clicks/ctr` (plus harmless extra `impressions`/`position` — leave them, JSON consumers ignore unknown keys) |
| `anomalies[]` | `_get_recent_anomalies()` (raw `Anomaly` rows) | shape to `{id, metric, severity, deviation, date, detail}` — `id`=`str(row.id)`, `detail`=`row.description` (real column, already exists — confirmed via `pipeline/db/schema.py`'s `Anomaly.description`, no synthesis needed), `deviation`=existing formatted string (already `"+38%"`/`"-38%"` style) |
| `quickWinKws` | new one-liner: count of `KeywordRanking` rows where `position` 4–10 and `clicks > 0` | same rule already used by `_get_keyword_intelligence`'s quick_wins filter (`apps/dashboard/services/decision_engine`-adjacent logic in `views.py`) — a simple count query, not the full list |

`_get_recent_anomalies()` currently filters `is_acknowledged == 0` (unacknowledged only) —
keep that filter; the SEO page's anomalies list is meant to be "what needs attention now",
same as today.

## Architecture (same pattern as Phase A)

- New file `apps/dashboard/services/seo_service.py`:
  - Raw calculators (DB queries only, try/except-wrapped with safe fallbacks — apply the
    lesson from Phase A's Task 5 finding, don't drop error handling this time):
    `query_low_ctr_pages_raw`, `query_seo_by_country_raw`, `query_seo_anomalies_raw`,
    `count_quick_win_keywords`, `count_technical_issues(site_id, issue_type=None)` (unlimited
    `COUNT(*)`, optionally filtered by type — powers both `kpis.critical` and
    `kpis.total_issues`, not the capped-at-15 `_get_technical_issues()`).
  - Old-template formatters: reuse of what's already in `views.py` if any exists, or a thin
    formatter kept there — Task granularity to be decided in the implementation plan
    (this task is smaller than Overview's extraction was, since `seo()`'s helpers are less
    entangled with presentation formatting than `_get_kpi_stats` was).
  - New API-shaped builder: `build_seo_response(site_id) -> dict` returning the exact
    top-level shape above, calling the raw calculators.
- `apps/api/views.py`: new `ProjectSEOView(APIView)`, route `projects/<slug:seo>/seo`
  (no trailing slash, same auth pattern as Overview — `login_not_required` + default
  `IsAuthenticated`).
- No `range` query param — `HANDOFF_SPEC.md`'s endpoint table lists `seo` with no `range`
  column, unlike `overview`/`positions`/`offsite`/`ads`.

## Verification

- `manage.py test` full suite green, including new tests against a real seeded temp DB
  (same `_SessionFactory` reset pattern as Phase A).
- Old SEO page (`/seo/`) renders unchanged — no behavior change, same as Task 5's "pinning"
  discipline in Phase A.
- `GET /api/projects/<slug>/seo` returns real data matching what `/seo/` shows for the same
  site.

## Explicitly out of scope

Keywords, Position Tracking, Alerts (B2–B4, each their own cycle). No new anomaly-detection
logic — reuses whatever thresholds/logic already populates the `anomalies` table today.

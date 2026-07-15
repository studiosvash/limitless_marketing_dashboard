# Phase C2 — Site Audit Page Design Spec

> Status: draft, self-authored (continuing autonomously per user's standing "continue B3, B4,
> and next... without any permission" instruction). Second of four Phase C sub-projects (C1
> Backlinks done, C2 Site Audit, C3 Off-site SEO, C4 Ads). Branched from `phase-c1-backlinks`.

## Why this phase is scoped differently from C1 — and even more conservatively

Site Audit is the largest, most structurally new page in the whole SPA. Per `HANDOFF_SPEC.md`
§2.4, the full target shape is `score`, `crawl{}`, `domainChecks[]`, `breakdown{}`, `catScore{}`,
`cwv{}`, `checks[]` (28 distinct rule IDs across 6 categories, each with `severity`/`category`/
`title`/`howToFix`/`pages[]`/`count`), `totals{}`, `crawledPages[]`, `structure[]`, `snapshots[]`
(historical, weekly).

Unlike Backlinks — where a `Backlink` table + connector already existed and only 7 fields needed
`state:"setup"` — **no rules catalog, crawl-run table, or historical-snapshot table exists
anywhere in this codebase.** `dataforseo_onpage.py` (the one connector that touches this domain)
is real but only ever extracts a flat per-page boolean `checks{}` map into `TechnicalIssue` rows
(4 known `issue_type` values), and DataForSEO credentials remain balance-blocked — so even that
connector currently produces 0 rows, same as Backlinks.

**Decision:** build ONLY what's an honest reshape of tables that are already real, already
populated (from working, non-blocked connectors — PageSpeed via Google PSI, IndexingStatus via
GSC, TechnicalIssue from whatever partial data exists), with zero invented severities, zero
invented check results, and zero fabricated historical trend. Everything requiring the 28-rule
catalog, a crawl-run concept, or history reports `state:"setup"`. This is a **narrower** real
slice than C1's, because the underlying pipeline genuinely has less to reshape here — that's a
fact about the data, not a scoping shortcut.

## Mapping — what's real vs. `state:"setup"`

| Field | Source | Status |
|---|---|---|
| `score` | Would require scoring across the full 28-check catalog, which doesn't exist | `state:"setup"` |
| `crawl.*` (status/pagesCrawled/maxPages/startedAt/duration/userAgent) | No crawl-run table exists; `dataforseo_onpage` doesn't record run metadata | `state:"setup"` |
| `domainChecks[]` (ssl/sitemap/robots/http2/www) | No existing connector/table computes any of these; would require new domain-probe logic | `state:"setup"` |
| `breakdown.healthy/withIssues/broken/redirected/blocked` | Real — derivable from `IndexingStatus.verdict`/`coverage_state` (existing GSC data, real reshape, not invented) | Real |
| `catScore.*` (6 categories) | Requires the 28-check catalog to attribute scores per category | `state:"setup"` |
| `cwv.lcp/cls` (p75 + good/mid/poor buckets) | Real — derivable from `PageSpeed.lcp_ms`/`PageSpeed.cls` (mobile strategy, real Lighthouse data) | Real |
| `cwv.tbt` | `PageSpeed` table has no `tbt_ms` column (has `inp_ms` instead — a different metric, not a substitute) | `state:"setup"` |
| `checks[]` | Only 4 of 28 catalog IDs have any real mapping (`TechnicalIssue.issue_type`: `not_found_404`, `crawled_not_indexed`, `page_with_redirect`, `long_url`), and today that table is empty (DataForSEO OnPage blocked) — inventing results for the other 24 is exactly the fabrication the project forbids | `state:"setup"` (empty array; see note below) |
| `totals.errors/warnings/notices` | Depends on `checks[]` | `{errors:0, warnings:0, notices:0}` (honest zero, not fabricated) |
| `crawledPages[]` | Would require crawl-specific fields (`depth`, `inLinks`, `internalLinks`, `externalLinks`, `failed[]`, per-page `score`) that no table captures | `state:"setup"` (empty array) |
| `structure[]` | Per `HANDOFF_SPEC.md`, this is a client-side rollup computed FROM `crawledPages` — with `crawledPages` empty/setup, this is naturally empty too, not a separate gap | `state:"setup"` (empty array) |
| `snapshots[]` | No historical audit-run tracking table exists | `state:"setup"` (empty array) |

**Note on `checks[]` being fully `state:"setup"` rather than partially populated:** the 4
`TechnicalIssue.issue_type` values map to catalog IDs `broken_pages` (from `not_found_404`),
`crawled_not_indexed`, `redirect_chains`-ish (from `page_with_redirect`), and `long_urls` (from
`long_url`) — but `TechnicalIssue` is fed exclusively by the balance-blocked `dataforseo_onpage`
connector and currently holds 0 rows for the real site. Emitting a `checks[]` array with 4
possibly-empty entries and 24 silently-missing ones risks being read by the SPA/user as "audit
found only 4 possible issues" — a misleading signal, not a neutral gap. The whole `checks[]`
(and dependent `totals`) reports `state:"setup"` until the OnPage connector has real data to
reshape, at which point `checks[]` can honestly cover its true (still partial: 4/28) real
subset — that reshape is real, scoped, follow-up work once credentials unblock, not for this
task to guess at.

## Architecture

- New file `apps/dashboard/services/site_audit_service.py`:
  - `query_indexing_breakdown_raw(site_id)` — reshape of existing `_get_indexing_issues`/
    `IndexingStatus` query pattern into `{healthy, withIssues, broken, redirected, blocked}`
    counts (mapped from `verdict`/`coverage_state`, not invented).
  - `query_cwv_raw(site_id)` — reshape of existing `_get_page_speed_issues`/`PageSpeed` query
    pattern (mobile strategy) into p75 LCP/CLS + good/mid/poor bucket counts, using the
    thresholds already implied by Google's own CWV standard (LCP good ≤2.5s/poor >4s, CLS good
    ≤0.1/poor >0.25 — these are Google's published, not invented, thresholds).
  - `build_site_audit_response(site_id) -> dict` — assembles real `breakdown`/`cwv.lcp`/
    `cwv.cls` plus `state:"setup"` placeholders for everything else per the mapping table.
- `apps/api/views.py`: `ProjectSiteAuditView` on `GET /api/projects/<slug>/audit` — no `range`
  param (matches `HANDOFF_SPEC.md`'s endpoint table: `audit | — | ...`). Same
  `resolve_project_or_404` + `login_not_required` pattern as every prior endpoint.
- `POST /api/projects/<slug>/audit/toggle-check` is explicitly OUT of scope for this task: it
  mutates a per-project hidden-checks list that only makes sense once `checks[]` has real data
  to hide. Building the mutation endpoint against an always-empty `checks[]` would be dead code.

## Verification

- Full suite green.
- No existing page in `apps/dashboard/views.py` is touched (this is new-shape work, not an
  extraction from an existing view — there is no existing "site audit" page in the MVP to keep
  pixel-identical; the closest analogue, `pages()`/`_get_page_health`, has a different flat
  shape and is left completely alone).
- `GET /api/projects/<slug>/audit` returns real `breakdown`/`cwv.lcp`/`cwv.cls` (currently
  possibly-zero since PageSpeed/IndexingStatus rows depend on real syncs having run) and
  `state:"setup"` for every other field — never fabricated scores, checks, or history.

## Explicitly out of scope

- The 28-rule `checks[]` catalog and its category-scoring (`catScore`) — real design + connector
  work for once `dataforseo_onpage` is unblocked and returns real per-page check data.
- `domainChecks[]` (SSL/sitemap/robots/HTTP2/WWW) — a genuinely new, small, independent probe
  each; deliberately not bundled into this task to avoid scope creep beyond "reshape what's
  real today."
- Crawl-run metadata and historical `snapshots[]` — needs new schema (a `CrawlRun`-style table)
  that doesn't exist; a real schema-design decision for a future phase, not this one.
- `POST /audit/toggle-check` mutation endpoint — see Architecture note above.
- C3 (Off-site SEO), C4 (Ads).

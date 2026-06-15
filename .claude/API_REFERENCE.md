# FuseHealth — API & Connector Reference

> Auto-loaded by CLAUDE.md when touching `pipeline/connectors/` or `/sync/` views.
> Last updated: 2026-06-11

## Status Legend

| Status | Meaning |
|--------|---------|
| WORKING | Credentials present, live auth verified |
| BALANCE_NEGATIVE | Auth works but DataForSEO balance is negative — top up before using |
| CREDENTIALS_MISSING | Env vars unset / not yet obtained |
| NO_CREDS_NEEDED | No API credentials required |

---

## BaseConnector

**Module:** `pipeline.connectors.base`
**Class:** `BaseConnector`

All connectors extend `BaseConnector`. Subclasses must define `name` (str) and implement `fetch(site_id, **kwargs) -> list[dict]`. Subclasses should override `_write_records` to call the appropriate `pipeline.db.writer` function.

**`sync(site_id=None, **kwargs) -> dict`** — the public entry point. Calls `fetch` then `_write_records` inside a DB session. Writes status rows to Django's `SyncLog` model (in `django_internal.db`) so the HTMX progress bar can track state. Returns:

```python
{
    "status": "success" | "error",
    "site_id": str,
    "records_written": int,
    "duration_seconds": float,
    "error": str | None,
}
```

`SyncLog.status` transitions: `"running"` → `"success"` or `"error"`. The `_update_django_sync_log` helper is a silent no-op when Django is not available (standalone scripts, tests).

---

## PAGE_CONNECTORS Mapping

Which connectors feed each dashboard page (from `sync_engine.py`):

| Page | Connectors |
|------|-----------|
| overview | `gsc`, `ga4` |
| seo | `gsc`, `ga4` |
| ads | *(blocked — no ad credentials)* |
| keywords | `gsc_keywords` |
| pages | `gsc_pages`, `url_inspection`, `pagespeed` |
| backlinks | *(blocked — balance negative)* |
| insights | *(manual)* |
| alerts | `gsc`, `ga4` |
| settings | *(none)* |
| positioning | `gsc_keywords` |

---

## Connectors

### `gsc` — Google Search Console (Site Performance)

| Field | Value |
|-------|-------|
| Class | `GSCConnector` |
| Module | `pipeline.connectors.gsc` |
| Status | **WORKING** |
| Credentials | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` |
| Site config | `GSC_SITE_URL` (.env fallback) or `Site.gsc_property` (DB) |
| API | Google Search Console API v1 — `searchanalytics.query` |
| Rate limit | 50,000 page-keyword pairs/day; 25,000 rows per paginated call |
| Tables written | `seo_daily` |
| Pages that use it | `overview`, `seo`, `alerts` |
| Notes | 3-day data delay — always fetches D-3 as the end date. Incremental: checks `max(seo_daily.date)` and only fetches new dates. Dimensions: `date`, `country`, `device`, `page`. |

---

### `ga4` — Google Analytics 4

| Field | Value |
|-------|-------|
| Class | `GA4Connector` |
| Module | `pipeline.connectors.ga4` |
| Status | **WORKING** |
| Credentials | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` |
| Site config | `GA4_PROPERTY_ID` (.env fallback) or `Site.ga4_property_id` (DB) |
| API | Google Analytics Data API v1 beta — `BetaAnalyticsDataClient.run_report` |
| Rate limit | 14,000 tokens/hour; single batched call per sync |
| Tables written | `seo_daily` (upserts GA4-specific columns only, preserving GSC data) |
| Pages that use it | `overview`, `seo`, `alerts` |
| Notes | Fetches `sessions`, `screenPageViews`, `conversions`, `bounceRate`, `totalUsers`, `newUsers`, `engagementRate`. Writes in batches of 60 to stay under SQLite's ~999 variable limit. Conflict key: `(date, site_id, country, device, landing_page)`. |

---

### `gsc_keywords` — GSC Query-Level Keyword Rankings

| Field | Value |
|-------|-------|
| Class | `GSCKeywordsConnector` |
| Module | `pipeline.connectors.gsc_keywords` |
| Status | **WORKING** |
| Credentials | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` |
| Site config | `GSC_SITE_URL` (.env fallback) or `Site.gsc_property` (DB) |
| API | Google Search Console API v1 — `searchanalytics.query` |
| Rate limit | 50,000 page-keyword pairs/day; 25,000 rows per paginated call |
| Tables written | `keyword_rankings` |
| Pages that use it | `keywords`, `positioning` |
| Notes | Dimensions: `date`, `query`, `page`. Provides real clicks/impressions/CTR/position. Does NOT provide search volume, KD, or CPC — those require DataForSEO. Groups by `(date, query)`, keeps the page with the most clicks. Incremental fetch via `max(keyword_rankings.date)`. Writes in batches of 80. Conflict key: `(date, site_id, keyword)`. |

---

### `gsc_pages` — GSC Page-Level Performance

| Field | Value |
|-------|-------|
| Class | `GSCPagesConnector` |
| Module | `pipeline.connectors.gsc_pages` |
| Status | **WORKING** |
| Credentials | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` |
| Site config | `GSC_SITE_URL` (.env fallback) or `Site.gsc_property` (DB) |
| API | Google Search Console API v1 — `searchanalytics.query` |
| Rate limit | 25,000 rows per paginated call |
| Tables written | `pages` |
| Pages that use it | `pages` |
| Notes | Dimension: `page` (aggregated over date range). Derives `cms_type` heuristically from URL path (`/blog/` → `blog`, `/services/` → `service`, else `page`). Derives `title` from URL path slug. `sessions` is left 0 (filled by GA4). Calls `upsert_pages`. Must run before `url_inspection` and `pagespeed`. |

---

### `url_inspection` — GSC URL Inspection

| Field | Value |
|-------|-------|
| Class | `URLInspectionConnector` |
| Module | `pipeline.connectors.url_inspection` |
| Status | **WORKING** |
| Credentials | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` |
| Site config | `GSC_SITE_URL` (.env fallback) or `Site.gsc_property` (DB) |
| API | Google Search Console URL Inspection API v1 — `urlInspection.index.inspect` |
| Rate limit | 2,000 requests/day, 600/minute; enforced in code at 0.2s/request (300 req/min) |
| Tables written | `indexing_status` |
| Pages that use it | `pages` |
| Notes | Inspects top 100 pages by clicks + up to 50 zero-click pages with impressions. Capped at 200 URLs total. Reads from `pages` table — requires `gsc_pages` to have run first. Fields: `verdict`, `coverage_state`, `indexing_state`, `last_crawl_time`, `crawl_status`, `robots_txt_state`, `mobile_usability`, `rich_results_status`. Gracefully stops on quota exceeded (429). Conflict key: `(site_id, url)`. |

---

### `pagespeed` — Google PageSpeed Insights

| Field | Value |
|-------|-------|
| Class | `PageSpeedConnector` |
| Module | `pipeline.connectors.pagespeed` |
| Status | **WORKING** |
| Credentials | `GOOGLE_API_KEY` |
| API | PageSpeed Insights API v5 — `https://www.googleapis.com/pagespeedonline/v5/runPagespeed` |
| Rate limit | ~400 requests/day (free tier); 2.5s sleep between requests |
| Tables written | `pagespeed` |
| Pages that use it | `pages` |
| Notes | Scans top 50 pages by clicks (mobile strategy only — mobile-first indexing). Reads from `pages` table — requires `gsc_pages` first. Scores: `performance`, `seo`, `accessibility`, `best-practices` (0–100). CWV metrics: `lcp_ms`, `cls`, `inp_ms`, `fcp_ms`, `ttfb_ms`, `si_ms`. Conflict key: `(site_id, url, strategy)`. |

---

### `sitemap` — Framer Sitemap Parser

| Field | Value |
|-------|-------|
| Class | `SitemapConnector` |
| Module | `pipeline.connectors.sitemap` |
| Status | **NO_CREDS_NEEDED** |
| Credentials | None — but requires `FRAMER_SITEMAP_URL` in .env (not a secret) |
| API | HTTP GET to the sitemap XML URL |
| Rate limit | None |
| Tables written | `pages`, `technical_issues` (robots.txt blocked URLs) |
| Pages that use it | `pages` |
| Notes | Parses `sitemap.xml` (namespace `http://www.sitemaps.org/schemas/sitemap/0.9`). Sets `cms_type = "framer"`. Cross-references `robots.txt` — blocked pages are written to `technical_issues` with `issue_type = "robots_txt_blocked"`. `title` is not available in sitemap (left null). `FRAMER_SITEMAP_URL` is unset in current .env — connector will raise on instantiation until set. |

---

### `dataforseo_keywords` — DataForSEO Keyword Metadata

| Field | Value |
|-------|-------|
| Class | `DataForSEOKeywordsConnector` |
| Module | `pipeline.connectors.dataforseo_keywords` |
| Status | **BALANCE_NEGATIVE** |
| Credentials | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` |
| API | DataForSEO v3 — `keywords_data/google_ads/search_volume/live` + `dataforseo_labs/google/bulk_keyword_difficulty/live` |
| Rate limit | 12 req/min (Google Ads live endpoint); 5s sleep between keyword batches |
| Tables written | `keyword_rankings` (enriches: `search_volume`, `cpc`, `keyword_difficulty`) |
| Pages that use it | `keywords`, `positioning` |
| Notes | Reads tracked keywords from `keywords.txt` via `pipeline.utils.keywords.load_tracked_keywords`. Batches up to 1,000 keywords per API call. KD comes from a separate Labs endpoint — failures degrade gracefully (KD stays `None`). Does NOT set `position` or `url` — those come from `dataforseo_serp` or `gsc_keywords`. Conflict key: `(date, site_id, keyword)`. |

---

### `dataforseo_serp` — DataForSEO SERP Rank Tracking

| Field | Value |
|-------|-------|
| Class | `DataForSEOSERPConnector` |
| Module | `pipeline.connectors.dataforseo_serp` |
| Status | **BALANCE_NEGATIVE** |
| Credentials | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` |
| Site config | `DATAFORSEO_TARGET_DOMAIN` (.env fallback) or `Site.dataforseo_target_domain` (DB) |
| API | DataForSEO v3 — `serp/google/organic/task_post` + `serp/google/organic/task_get/{task_id}` |
| Rate limit | Standard Queue (async); cost $0.0006/query — never use Live mode for batch jobs |
| Tables written | `keyword_rankings` (`position`, `url` per keyword per day) |
| Pages that use it | `keywords`, `positioning` |
| Notes | Submit-then-poll pattern. Batches 100 keywords per POST request. Polls every 15s, up to 20 polls (5 min max). Optimizations: `stop_crawl_on_match=True`, `depth=30`. Records domain-not-found as `position=None`. Tagged with `fusehealth_{yesterday_date}`. Keywords loaded from `keywords.txt`. Search volume/KD/CPC left null (enriched by `dataforseo_keywords`). |

---

### `dataforseo_backlinks` — DataForSEO Backlinks

| Field | Value |
|-------|-------|
| Class | `DataForSEOBacklinksConnector` |
| Module | `pipeline.connectors.dataforseo_backlinks` |
| Status | **BALANCE_NEGATIVE** |
| Credentials | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` |
| Site config | `DATAFORSEO_TARGET_DOMAIN` (.env fallback), then `GSC_SITE_URL` |
| API | DataForSEO v3 — `backlinks/backlinks/live` |
| Rate limit | Live endpoint; single call per sync |
| Tables written | `backlinks` |
| Pages that use it | `backlinks` *(page currently blocked)* |
| Notes | Fetches up to 1,000 dofollow backlinks ordered by `rank` descending. Fields: `referring_domain`, `target_url`, `anchor`, `status`, `dofollow`, `domain_rank`, `first_seen`, `last_seen`. |

---

### `dataforseo_labs_competitors` — DataForSEO Labs Competitor Discovery

| Field | Value |
|-------|-------|
| Class | `DataForSEOLabsCompetitorsConnector` |
| Module | `pipeline.connectors.dataforseo_labs_competitors` |
| Status | **BALANCE_NEGATIVE** |
| Credentials | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` |
| Site config | `DATAFORSEO_TARGET_DOMAIN` (.env fallback) or `Site.dataforseo_target_domain` (DB) |
| API | DataForSEO v3 — `dataforseo_labs/google/competitors_domain/live` |
| Rate limit | ~$0.01/call; single call per sync; recommended weekly cadence |
| Tables written | `competitor_domains` |
| Pages that use it | `positioning` |
| Notes | Returns up to 25 competitor domains ranked by `intersections` (shared keywords), filtered to `intersections > 1`. Estimates `avg_position` from position-band counts (pos_1, pos_2_3, … pos_51_100) using weighted midpoints. Fields: `competitor_domain`, `intersections`, `full_domain_metrics_organic_count`, `avg_position`, `etv`. Must run before `dataforseo_opportunities`. |

---

### `dataforseo_onpage` — DataForSEO On-Page Technical Audit

| Field | Value |
|-------|-------|
| Class | `DataForSEOOnPageConnector` |
| Module | `pipeline.connectors.dataforseo_onpage` |
| Status | **BALANCE_NEGATIVE** |
| Credentials | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` |
| Site config | `DATAFORSEO_TARGET_DOMAIN` (.env) — not site-row aware yet |
| API | DataForSEO v3 — `on_page/task_post`, `on_page/summary/{task_id}`, `on_page/pages` |
| Rate limit | Async crawl; polls every 30s, up to 600s total |
| Tables written | `technical_issues` |
| Pages that use it | `seo` |
| Notes | Crawls up to 200 pages (`max_crawl_pages=200`, `load_resources=False`, `store_raw_html=False`, `enable_browser_rendering=False`). Extracts technical issues from `checks` dict per page. Severity: `"high"` if `"error"` in issue_type key, else `"medium"`. |

---

### `dataforseo_opportunities` — DataForSEO Keyword Opportunities

| Field | Value |
|-------|-------|
| Class | `DataForSEOOpportunitiesConnector` |
| Module | `pipeline.connectors.dataforseo_opportunities` |
| Status | **BALANCE_NEGATIVE** |
| Credentials | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` |
| Site config | `DATAFORSEO_TARGET_DOMAIN` (.env fallback) or `Site.dataforseo_target_domain` (DB) |
| API | DataForSEO v3 — `dataforseo_labs/google/ranked_keywords/live` |
| Rate limit | Live endpoint; one call per competitor |
| Tables written | `keyword_rankings` |
| Pages that use it | `keywords` |
| Notes | Reads the top 3 competitors from `competitor_domains` table (by `intersections`). Requires `dataforseo_labs_competitors` to have run first. Fetches top 30 ranked keywords per competitor. Deduplicates across competitors. Fields written: `search_volume`, `keyword_difficulty`, `cpc`, `intent` (from `search_intent_info.main_intent`). |

---

### `google_ads` — Google Ads Campaigns

| Field | Value |
|-------|-------|
| Class | `GoogleAdsConnector` |
| Module | `pipeline.connectors.google_ads` |
| Status | **CREDENTIALS_MISSING** |
| Credentials | `GOOGLE_ADS_CUSTOMER_ID`, `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` |
| Optional | `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (MCC manager account) |
| API | Google Ads API — `GoogleAdsService.search` (GAQL) |
| Rate limit | 2 QPS (enforced by SDK); Basic Access: 15,000 ops/day; Standard: unlimited |
| Tables written | `ad_metrics_daily` (`platform='google'`) |
| Pages that use it | `ads` *(page currently blocked)* |
| Notes | Requires Standard Access application at https://developers.google.com/google-ads/api/docs/access-levels. Fetches `campaign.id`, `campaign.name`, `cost_micros` (÷1,000,000 for USD), `clicks`, `impressions`, `conversions` per day for ENABLED campaigns. `roas` is left `None` until conversion value tracking is added. |

---

### `meta` — Meta (Facebook/Instagram) Ads

| Field | Value |
|-------|-------|
| Class | `MetaConnector` |
| Module | `pipeline.connectors.meta` |
| Status | **CREDENTIALS_MISSING** |
| Credentials | `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` (format: `act_XXXXXXXXXX`) |
| API | Meta Graph API v18.0 — `/{ad_account_id}/insights` |
| Rate limit | Standard tier required (100K pts/hr); Dev tier (300 pts/hr) is unusable for production |
| Tables written | `ad_metrics_daily` (`platform='meta'`) |
| Pages that use it | `ads` *(page currently blocked)* |
| Notes | Must use a System User token (never expires) — not a personal token. `time_increment=1` gives daily breakdown. Conversions extracted from `actions` array filtering for `purchase`, `omni_purchase`, `offsite_conversion.fb_pixel_purchase`. Paginated (limit 500). `roas` left `None`. |

---

### `linkedin` — LinkedIn Ads

| Field | Value |
|-------|-------|
| Class | `LinkedInConnector` |
| Module | `pipeline.connectors.linkedin` |
| Status | **CREDENTIALS_MISSING** |
| Credentials | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_ACCOUNT_ID` |
| Optional | `LINKEDIN_REFRESH_TOKEN`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` (for auto-refresh) |
| API | LinkedIn Marketing API v2 — `adCampaignsV2`, `adAnalyticsV2` |
| Rate limit | Not published by LinkedIn; 0.5s sleep between calls; max 5 retries with exponential backoff |
| Tables written | `ad_metrics_daily` (`platform='linkedin'`) |
| Pages that use it | `ads` *(page currently blocked)* |
| Notes | Access token expires every 60 days. Auto-refresh implemented but requires `LINKEDIN_REFRESH_TOKEN` + `LINKEDIN_CLIENT_ID` + `LINKEDIN_CLIENT_SECRET`. After refresh, the new token is only in memory — `.env` must be updated manually. Fetches one campaign at a time (LinkedIn API requirement). `roas` left `None`. |

---

### `webflow` — Webflow CMS Page Inventory

| Field | Value |
|-------|-------|
| Class | `WebflowConnector` |
| Module | `pipeline.connectors.webflow` |
| Status | **CREDENTIALS_MISSING** |
| Credentials | `WEBFLOW_API_KEY`, `WEBFLOW_SITE_ID` |
| Optional | `WEBFLOW_COLLECTION_IDS` (comma-separated, not yet consumed in code) |
| API | Webflow API v2 — `GET /v2/sites/{site_id}/pages` |
| Rate limit | 60 req/min, 1,000 req/hr; 1s sleep between paginated requests |
| Tables written | `pages` (`cms_type='webflow'`) |
| Pages that use it | `pages` |
| Notes | Paginated at 100 per request. `sessions`, `clicks`, `impressions` are all 0 on insert — enriched by GSC/GA4 connectors later. `last_modified` is left null (not available from this endpoint). |

---

### `wordpress` — WordPress REST API Page Inventory

| Field | Value |
|-------|-------|
| Class | `WordPressConnector` |
| Module | `pipeline.connectors.wordpress` |
| Status | **CREDENTIALS_MISSING** |
| Credentials | `WP_SITE_URL` (required); `WP_USERNAME`, `WP_APP_PASSWORD` (optional — only needed for private/draft content) |
| API | WordPress REST API v2 — `/wp-json/wp/v2/posts` + `/wp-json/wp/v2/pages` |
| Rate limit | None specified; retry with 3 attempts |
| Tables written | `pages` (`cms_type='wordpress'`) |
| Pages that use it | `pages` |
| Notes | Fetches only `status=publish` content. 100 items per page; stops when WordPress returns 400 (page exceeds total). `title` from `title.rendered`. `last_modified` from `modified_gmt[:10]`. `sessions`, `clicks`, `impressions` are 0 on insert — enriched by GSC/GA4 later. |

---

## Dependency Order

When running a full sync, connectors must be called in this order due to data dependencies:

1. `gsc_pages` — populates `pages` table (required by `url_inspection`, `pagespeed`)
2. `gsc` — populates `seo_daily` with GSC metrics
3. `ga4` — enriches `seo_daily` with GA4 metrics
4. `gsc_keywords` — populates `keyword_rankings` with real position + engagement data
5. `url_inspection` — reads `pages` table; writes `indexing_status`
6. `pagespeed` — reads `pages` table; writes `pagespeed`
7. `dataforseo_labs_competitors` — writes `competitor_domains` (required by `dataforseo_opportunities`)
8. `dataforseo_keywords` — enriches `keyword_rankings` with volume/KD/CPC
9. `dataforseo_serp` — enriches `keyword_rankings` with SERP positions
10. `dataforseo_opportunities` — reads `competitor_domains`; writes `keyword_rankings`
11. `dataforseo_backlinks` — independent; writes `backlinks`
12. `dataforseo_onpage` — independent; writes `technical_issues`

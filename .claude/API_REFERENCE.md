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

## Official API Documentation & Capabilities Summary

This section summarizes the core platform APIs integrated into FuseHealth, detailing their flexibility, data capabilities, limitations, and official reference links.

### 1. Google Search Console (GSC) API
* **Official Reference Docs:** [Google Search Console API Home](https://developers.google.com/webmaster-tools/v1/searchanalytics) | [Search Analytics Query Docs](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) | [URL Inspection API Docs](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect)
* **What They Provide:**
  * Organic search performance metrics: Clicks, Impressions, Click-Through Rate (CTR), and Average Position.
  * Indexing & Crawl diagnostics: Coverage state, indexing state, robots.txt status, last crawl time, mobile usability, and rich results status.
* **Flexibility & Capabilities:**
  * **Granular Filtering & Grouping:** Supports multi-dimensional grouping and filtering across `query`, `page`, `country`, `device`, `date`, and `searchAppearance`.
  * **Regex & Exact Matching:** Allows custom regex or exact matching filters on query strings and URL paths to isolate brand vs. non-brand traffic or specific subdirectories.
  * **Pagination & Volume:** Generous rate limits allowing up to 25,000 rows per paginated call and 50,000 page-keyword pairs per day.
* **Limitations & Trade-offs:**
  * **Data Latency:** 2-to-3 day reporting delay (hence why pipeline ingestion defaults to `D-3`).
  * **Missing SEO Metadata:** Does *not* provide keyword search volume, CPC, or Keyword Difficulty (KD). Those metrics must be enriched via DataForSEO.
  * **URL Inspection Quotas:** Strict quota of 2,000 requests/day and 600 requests/minute per property.

---

### 2. Google Analytics 4 (GA4) Data API
* **Official Reference Docs:** [GA4 Data API v1 Reference](https://developers.google.com/analytics/devguides/reporting/data/v1) | [API Dimensions & Metrics Explorer](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema)
* **What They Provide:**
  * User acquisition and engagement metrics: Sessions, Screen/Page Views, Total/New Users, Bounce Rate, Engagement Rate, and Event Conversions.
  * Attribution and traffic source data grouped by channel, medium, campaign, and landing page.
* **Flexibility & Capabilities:**
  * **Custom Report Construction:** High flexibility via `runReport` (historical) and `runRealtimeReport` (live activity), allowing up to 9 dimensions and 10 metrics per query.
  * **Advanced Analytics:** Supports cohort exploration, conversion funnels, and custom event parameter extraction.
* **Limitations & Trade-offs:**
  * **Data Thresholding:** Google applies privacy thresholding on low-volume data slices, which can hide metrics for low-traffic landing pages.
  * **Token Quotas:** Limited to 14,000 core tokens per hour per property.
  * **SQLite Variable Limits:** Ingested batches must be chunked (e.g., 60 rows per batch) to respect SQLite parameter limits during local development.

---

### 3. DataForSEO API (v3)
* **Official Reference Docs:** [DataForSEO API v3 Documentation](https://docs.dataforseo.com/v3/) | [SERP API](https://docs.dataforseo.com/v3/serp/google/organic/overview) | [Keywords Data API](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/overview) | [DataForSEO Labs API](https://docs.dataforseo.com/v3/dataforseo_labs/overview) | [Backlinks API](https://docs.dataforseo.com/v3/backlinks/overview) | [On-Page API](https://docs.dataforseo.com/v3/on_page/overview)
* **What They Provide:**
  * **Keyword Intelligence:** Live search volume, keyword difficulty (KD), Cost-Per-Click (CPC), competition density, and search intent classification.
  * **Rank Tracking & SERP Features:** Accurate position tracking across any geographic location or device, including SERP feature detection (Featured Snippets, People Also Ask, Local Pack).
  * **Competitor & Market Discovery:** Domain intersection analysis, competitor discovery, and keyword gap identification.
  * **Technical SEO & Backlinks:** Comprehensive dofollow/nofollow backlink profiles, referring domains, domain authority ranking, and full site technical health crawling (HTML structure, broken links, resource load times).
* **Flexibility & Capabilities:**
  * **Unmatched SEO Breadth:** Bridges the gaps left by GSC and GA4 by providing commercial keyword metrics, competitor intelligence, and SERP scraping without IP blocking risks.
  * **Dual Execution Modes:**
    * *Live Endpoints:* Synchronous, real-time results (best for ad-hoc UI exploration like Keyword Explorer).
    * *Standard Queue (Task-Based):* Submit-then-poll asynchronous processing at significantly lower cost (up to 80% cheaper, ideal for daily batch cron jobs).
  * **Geo & Language Precision:** Supports targeting down to specific countries, states, cities, GPS coordinates, or languages.
* **Limitations & Trade-offs:**
  * **Pay-As-You-Go Cost:** Every API call consumes account balance (e.g., ~$0.0006/query for queue SERP, ~$0.01 for Labs competitor discovery). Negative balance blocks all sync pipelines.

---

### 4. Google PageSpeed Insights API
* **Official Reference Docs:** [PageSpeed Insights API v5 Docs](https://developers.google.com/speed/docs/insights/v5/get-started) | [Lighthouse Scoring Guide](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/)
* **What They Provide:**
  * **Lab Data (Lighthouse):** Simulated scores (0–100) for Performance, SEO, Accessibility, and Best Practices.
  * **Field Data (CrUX):** Real-world Chrome User Experience Report metrics for Core Web Vitals (LCP, CLS, INP, FCP, TTFB, and Speed Index).
* **Flexibility & Capabilities:**
  * Separate evaluations for mobile and desktop rendering strategies (supporting mobile-first indexing priorities).
  * Returns detailed diagnostic audits and resource bottlenecks for individual URLs.
* **Limitations & Trade-offs:**
  * **Rate Limits:** Free tier is capped at ~400 requests/day (~1 request per second), requiring deliberate sleep intervals between URL scans.
  * **Execution Latency:** Each test takes ~2 to 5 seconds to run on Google's servers.

---

### 5. Advertising & Social Marketing APIs (Google Ads, Meta Ads, LinkedIn Ads)
* **Official Reference Docs:** [Google Ads API Guide](https://developers.google.com/google-ads/api/docs/start) | [Meta Marketing API Guide](https://developers.facebook.com/docs/marketing-apis) | [LinkedIn Marketing API Guide](https://learn.microsoft.com/en-us/linkedin/marketing/)
* **What They Provide:**
  * Cross-platform ad spend, cost per click, impressions, ad clicks, conversion events, and campaign metadata.
* **Flexibility & Capabilities:**
  * **Google Ads GAQL:** SQL-like query language allowing flexible joins between ad campaigns, keywords, and conversion metrics.
  * **Meta Graph Insights:** Granular breakdown by demographic, placement (Facebook Feed, Instagram Reels), and custom conversion actions (e.g., Pixel purchases).
  * **LinkedIn Analytics:** Professional B2B demographic reporting (by job title, industry, company size) and lead generation analytics.
* **Limitations & Trade-offs:**
  * **Strict Auth & Approval Tiers:** Google Ads requires Developer Token approval (Standard vs. Basic access). Meta requires System User token generation. LinkedIn tokens expire every 60 days requiring manual OAuth refresh flow.

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
| Official Docs | [GSC searchanalytics.query Reference](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) |
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
| Official Docs | [GA4 Data API v1 Reference](https://developers.google.com/analytics/devguides/reporting/data/v1) |
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
| Official Docs | [GSC searchanalytics.query Reference](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) |
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
| Official Docs | [GSC searchanalytics.query Reference](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) |
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
| Official Docs | [GSC URL Inspection API Reference](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect) |
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
| Official Docs | [PageSpeed Insights API v5 Reference](https://developers.google.com/speed/docs/insights/v5/get-started) |
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
| Official Docs | [Sitemaps XML Protocol Specification](https://www.sitemaps.org/protocol.html) |
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
| Official Docs | [Search Volume API Reference](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/overview) \| [Keyword Difficulty API Reference](https://docs.dataforseo.com/v3/dataforseo_labs/google/bulk_keyword_difficulty/overview) |
| Rate limit | 12 req/min (Google Ads live endpoint); 5s sleep between keyword batches |
| Tables written | `keyword_rankings` (enriches: `search_volume`, `cpc`, `keyword_difficulty`) |
| Pages that use it | `keywords`, `positioning` |
| Notes | Reads tracked keywords from `keywords.txt` via `pipeline.utils.keywords.load_tracked_keywords`. Batches up to 1,000 keywords per API call. KD comes from a separate Labs endpoint — failures degrade gracefully (KD stays `None`). Does NOT set `position` or `url` — those come from `dataforseo_serp` or `gsc_keywords`. Conflict key: `(date, site_id, keyword)`. |
| Ad-hoc lookup | `lookup_keywords(keywords, location_name="United States") -> dict` — **read-only** method for the Keyword Explorer (Keywords page). One call to Labs `dataforseo_labs/google/keyword_overview/live` (≤700 kw/call) returns volume, KD, CPC, competition, intent, and SERP features at once. Does **not** write the DB or read `keywords.txt` — fully separate from the tracking `fetch()`/`sync()` path. Triggered by the user-action `keywords/explore/` endpoint (not page render). Returns `{status, rows, no_data, location, error}`. |

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
| Official Docs | [DataForSEO Google Organic SERP API Reference](https://docs.dataforseo.com/v3/serp/google/organic/overview) |
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
| Official Docs | [DataForSEO Backlinks API Reference](https://docs.dataforseo.com/v3/backlinks/backlinks/overview) |
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
| Official Docs | [DataForSEO Labs Competitors Domain API Reference](https://docs.dataforseo.com/v3/dataforseo_labs/google/competitors_domain/overview) |
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
| Official Docs | [DataForSEO On-Page API Reference](https://docs.dataforseo.com/v3/on_page/overview) |
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
| Official Docs | [DataForSEO Labs Ranked Keywords API Reference](https://docs.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/overview) |
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
| Official Docs | [Google Ads API Reference](https://developers.google.com/google-ads/api/docs/start) |
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
| Official Docs | [Meta Marketing API Insights Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-account/insights) |
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
| Official Docs | [LinkedIn Ads Reporting & Analytics API Reference](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting) |
| Rate limit | Not published by LinkedIn; 0.5s sleep between calls; max 5 retries with exponential backoff |
| Tables written | `ad_metrics_daily` (`platform='linkedin'`) |
| Pages that use it | `ads` *(page currently blocked)* |
| Notes | Access token expires every 60 days. Auto-refresh implemented but requires `LINKEDIN_REFRESH_TOKEN` + `LINKEDIN_CLIENT_ID` + `LINKEDIN_CLIENT_SECRET`. After refresh, the new token is only in memory — `.env` must be updated manually. Fetches one campaign at a time (LinkedIn API requirement). `roas` left `None`. |

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

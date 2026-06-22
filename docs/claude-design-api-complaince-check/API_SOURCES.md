# FuseHealth — API Sources & Official Documentation

> **Who this is for:** Anyone building on or redesigning FuseHealth.
> Every API the dashboard connects to is listed here with its official docs URL,
> auth type, key limits, and current project status.

---

## Status Key

| Status | Meaning |
|--------|---------|
| WORKING | Credentials present, live auth verified |
| BALANCE_NEGATIVE | Auth works but DataForSEO account balance is zero — top up before use |
| CREDENTIALS_MISSING | API keys not yet obtained — see "How to get credentials" column |
| NO_CREDS_NEEDED | Public endpoint, no API key required |

---

## Google APIs (shared OAuth credentials)

All three Google APIs below share the same OAuth2 credentials:
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`

How to obtain: [Google Cloud Console](https://console.cloud.google.com/) → OAuth 2.0 → enable each API.

| Connector | API Name | Official Docs | Rate Limit | Status |
|-----------|----------|---------------|------------|--------|
| `gsc` | Google Search Console API v1 | https://developers.google.com/webmaster-tools/v1/searchanalytics/query | 50,000 page-keyword pairs/day; 25,000 rows/call | WORKING |
| `gsc_keywords` | Google Search Console API v1 | https://developers.google.com/webmaster-tools/v1/searchanalytics/query | Same as above | WORKING |
| `gsc_pages` | Google Search Console API v1 | https://developers.google.com/webmaster-tools/v1/searchanalytics/query | 25,000 rows/call | WORKING |
| `url_inspection` | GSC URL Inspection API v1 | https://developers.google.com/webmaster-tools/v1/urlInspectionResult | 2,000 req/day, 600/min | WORKING |
| `ga4` | Google Analytics Data API v1 beta | https://developers.google.com/analytics/devguides/reporting/data/v1 | 14,000 tokens/hour | WORKING |
| `pagespeed` | PageSpeed Insights API v5 | https://developers.google.com/speed/docs/insights/v5/get-started | ~400 req/day (free tier) | WORKING |

> **Google Ads** uses the same OAuth credentials but is listed under **Paid Advertising APIs** below (credentials not yet obtained).

---

## DataForSEO APIs

Shared credentials: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`

How to obtain: [DataForSEO dashboard](https://app.dataforseo.com/) → API access.
All endpoints below are currently blocked due to a negative account balance.

| Connector | API Endpoint | Official Docs | Approx. Cost | Status |
|-----------|-------------|---------------|--------------|--------|
| `dataforseo_keywords` | `keywords_data/google_ads/search_volume/live` + `dataforseo_labs/google/bulk_keyword_difficulty/live` | https://docs.dataforseo.com/v3/keywords_data/ | ~$0.001/keyword | BALANCE_NEGATIVE |
| `dataforseo_serp` | `serp/google/organic/task_post` + `task_get` (async queue) | https://docs.dataforseo.com/v3/serp/ | $0.0006/query | BALANCE_NEGATIVE |
| `dataforseo_backlinks` | `backlinks/backlinks/live` | https://docs.dataforseo.com/v3/backlinks/ | Live endpoint | BALANCE_NEGATIVE |
| `dataforseo_onpage` | `on_page/task_post` + `on_page/summary` + `on_page/pages` | https://docs.dataforseo.com/v3/on_page/ | Async crawl | BALANCE_NEGATIVE |
| `dataforseo_labs_competitors` | `dataforseo_labs/google/competitors_domain/live` | https://docs.dataforseo.com/v3/dataforseo_labs/ | ~$0.01/call | BALANCE_NEGATIVE |
| `dataforseo_opportunities` | `dataforseo_labs/google/ranked_keywords/live` | https://docs.dataforseo.com/v3/dataforseo_labs/ | Live endpoint | BALANCE_NEGATIVE |
| `dataforseo_serp_competitors` | `serp/google/organic/task_post` (competitor variant) | https://docs.dataforseo.com/v3/serp/ | $0.0006/query | BALANCE_NEGATIVE |
| `dataforseo_ai_keywords` | DataForSEO AI Optimization endpoint | https://docs.dataforseo.com/v3/ | Per-call | BALANCE_NEGATIVE |

> **Full DataForSEO v3 reference:** https://docs.dataforseo.com/v3/

---

## Paid Advertising APIs

| Connector | API Name | Official Docs | Credentials Needed | Status |
|-----------|----------|---------------|--------------------|--------|
| `google_ads` | Google Ads API | https://developers.google.com/google-ads/api/docs/start | `GOOGLE_ADS_CUSTOMER_ID`, `GOOGLE_ADS_DEVELOPER_TOKEN` | CREDENTIALS_MISSING |
| `meta` | Meta Marketing API (Graph API v18.0) | https://developers.facebook.com/docs/marketing-apis/ | `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` | CREDENTIALS_MISSING |
| `linkedin` | LinkedIn Marketing API v2 | https://learn.microsoft.com/en-us/linkedin/marketing/ | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_ACCOUNT_ID` | CREDENTIALS_MISSING |

> **Meta note:** Must use a System User token (never-expiring) — not a personal access token.
> See: https://developers.facebook.com/docs/marketing-api/system-users
>
> **LinkedIn note:** Access token expires every 60 days. Auto-refresh requires
> `LINKEDIN_REFRESH_TOKEN` + `LINKEDIN_CLIENT_ID` + `LINKEDIN_CLIENT_SECRET`.

---

## CMS / Content APIs

| Connector | API Name | Official Docs | Credentials Needed | Status |
|-----------|----------|---------------|--------------------|--------|
| `webflow` | Webflow API v2 | https://developers.webflow.com/ | `WEBFLOW_API_KEY`, `WEBFLOW_SITE_ID` | CREDENTIALS_MISSING |
| `wordpress` | WordPress REST API v2 | https://developer.wordpress.org/rest-api/ | `WP_SITE_URL` (required); username/app password (optional) | CREDENTIALS_MISSING |
| `sitemap` | Sitemap XML (no auth) | https://www.sitemaps.org/protocol.html | `FRAMER_SITEMAP_URL` in `.env` (not a secret) | NO_CREDS_NEEDED |

---

## Supporting Documentation

| Topic | Official Docs |
|-------|--------------|
| Google OAuth2 (shared by all Google APIs) | https://developers.google.com/identity/protocols/oauth2 |
| Google Cloud Console (create & manage credentials) | https://console.cloud.google.com/ |
| Google Search Console property setup | https://support.google.com/webmasters/answer/34592 |
| GA4 property & measurement ID setup | https://support.google.com/analytics/answer/9304153 |
| DataForSEO account & billing | https://app.dataforseo.com/ |
| Meta Business Suite (ad account setup) | https://business.facebook.com/ |
| LinkedIn Campaign Manager (ad account) | https://www.linkedin.com/campaignmanager/ |
| Google Ads account access levels | https://developers.google.com/google-ads/api/docs/access-levels |

# FuseHealth — AI Technical Guide for Design Verification

> **Who this is for:** Claude (AI) — this document tells you how to verify FuseHealth UI designs
> against the actual API capabilities of the connected data sources.
>
> **How to use:** A designer will paste this guide along with a component description into
> a Claude conversation. Follow the verification process below exactly.

---

## Your Role

You are a technical reviewer checking whether a proposed UI design for the FuseHealth dashboard
is buildable given the real-world constraints of its connected APIs.

You do NOT invent capabilities. If a field or behavior is not documented in the official API
reference sections below, you say it is unavailable. You do not suggest workarounds that would
require calling an API on page load.

---

## The Core Constraint (read before every review)

FuseHealth is **database-first**. This means:

1. Pages read from a local database — they never call an external API when rendering
2. Data is only fetched when a user clicks a Refresh button
3. Any design that requires a live API call on page load is **architecturally invalid**
4. Any design that implies real-time or automatic data refresh (without a user action) is **invalid**

Flag any design element that violates this contract as a **HARD BLOCK**.

---

## How to Run a Design Verification

When a designer gives you a component to review, follow these steps:

### Step 1 — Parse the component

Identify:
- Every data field the component displays
- The data source (connector name) it pulls from
- The interaction pattern (static display, filter, sort, drill-down, etc.)
- Whether any part of it implies a live API call

### Step 2 — Check each field against the API

For each data field:
1. Find the connector that supplies it (use the Field-to-Connector map below)
2. Check whether that connector's API actually returns that field
3. Check the connector's current status (WORKING / BALANCE_NEGATIVE / CREDENTIALS_MISSING)
4. Note any data delays, null conditions, or rate limits that affect the field

### Step 3 — Check the interaction pattern

Ask:
- Does this interaction require fetching new data? → It must use the HTMX Refresh pattern, not a live API call
- Does this filter/sort operate on data already in the database? → Valid
- Does this require real-time streaming data? → Invalid (no WebSockets in the stack)
- Does the component need to handle null/empty values gracefully? → Yes, always

### Step 4 — Write the verdict

For each component, produce a verdict table:

| Field | Connector | API Returns It? | Status | Notes |
|-------|-----------|----------------|--------|-------|
| [field name] | [connector] | YES / NO / PARTIAL | WORKING / BLOCKED / UNAVAILABLE | [any constraint] |

Then write one of:
- **APPROVED** — all fields available, no architectural violations
- **APPROVED WITH CONDITIONS** — available but requires handling nulls / blocked states / data delays
- **NEEDS REVISION** — one or more fields unavailable or interaction pattern is invalid; list what must change
- **HARD BLOCK** — design requires a live API call on page load or violates the database-first contract

---

## Field-to-Connector Map

Use this to identify which connector supplies each type of data.

### SEO & Organic Traffic
| Data field | Connector | Table | Notes |
|-----------|-----------|-------|-------|
| clicks, impressions, CTR, avg_position | `gsc` | `seo_daily` | 3-day data delay |
| by country breakdown | `gsc` | `seo_daily` | dimension: country |
| by device breakdown | `gsc` | `seo_daily` | dimension: device |
| sessions, pageviews, bounce_rate, conversions | `ga4` | `seo_daily` | upserted alongside GSC |
| new_users, engagement_rate | `ga4` | `seo_daily` | |
| keyword, position, clicks per keyword | `gsc_keywords` | `keyword_rankings` | |
| search_volume, cpc | `dataforseo_keywords` | `keyword_rankings` | BALANCE_NEGATIVE |
| keyword_difficulty (KD) | `dataforseo_keywords` | `keyword_rankings` | BALANCE_NEGATIVE |
| SERP rank per keyword per day | `dataforseo_serp` | `keyword_rankings` | BALANCE_NEGATIVE |
| AI search volume, MoM trend | `dataforseo_ai_keywords` | `ai_keyword_data` | BALANCE_NEGATIVE |

### Pages & Technical Health
| Data field | Connector | Table | Notes |
|-----------|-----------|-------|-------|
| page URL, clicks, impressions per page | `gsc_pages` | `pages` | aggregated, no date dimension |
| cms_type (blog/service/page/framer/webflow/wordpress) | `gsc_pages` / `sitemap` / `webflow` / `wordpress` | `pages` | heuristic from URL path |
| indexing verdict, crawl status, last_crawl_time | `url_inspection` | `indexing_status` | 2,000 req/day limit; top 200 URLs only |
| mobile_usability, rich_results_status | `url_inspection` | `indexing_status` | |
| performance_score, seo_score, accessibility_score | `pagespeed` | `pagespeed` | 0–100; free tier ~400 req/day |
| lcp_ms, cls, inp_ms, fcp_ms, ttfb_ms (Core Web Vitals) | `pagespeed` | `pagespeed` | mobile strategy only |
| technical_issues (crawl errors, missing tags) | `dataforseo_onpage` | `technical_issues` | BALANCE_NEGATIVE |
| robots.txt blocked URLs | `sitemap` | `technical_issues` | NO_CREDS_NEEDED |

### Competitors & Positioning
| Data field | Connector | Table | Notes |
|-----------|-----------|-------|-------|
| competitor_domain, intersections, avg_position, etv | `dataforseo_labs_competitors` | `competitor_domains` | BALANCE_NEGATIVE |
| your rank vs competitor rank per keyword | `dataforseo_serp_competitors` | `competitor_keyword_rankings` | BALANCE_NEGATIVE |
| keyword opportunities from competitor keywords | `dataforseo_opportunities` | `keyword_rankings` | BALANCE_NEGATIVE; requires competitors first |

### Backlinks
| Data field | Connector | Table | Notes |
|-----------|-----------|-------|-------|
| referring_domain, anchor, dofollow, domain_rank | `dataforseo_backlinks` | `backlinks` | BALANCE_NEGATIVE |
| first_seen, last_seen per backlink | `dataforseo_backlinks` | `backlinks` | BALANCE_NEGATIVE |

### Paid Advertising
| Data field | Connector | Table | Notes |
|-----------|-----------|-------|-------|
| google ads: cost, clicks, impressions, conversions | `google_ads` | `ad_metrics_daily` | CREDENTIALS_MISSING |
| meta ads: spend, impressions, clicks, conversions | `meta` | `ad_metrics_daily` | CREDENTIALS_MISSING |
| linkedin ads: spend, impressions, clicks, conversions | `linkedin` | `ad_metrics_daily` | CREDENTIALS_MISSING |
| ROAS (return on ad spend) | *none* | — | **NOT AVAILABLE** — no connected API returns revenue value |
| campaign name, campaign id | `google_ads` | `ad_metrics_daily` | CREDENTIALS_MISSING |

### Fields That Do Not Exist (common design assumptions to reject)

These fields are **never available** from any connected API:

| Requested field | Why it doesn't exist |
|----------------|---------------------|
| Real-time keyword position | No live SERP API connected; DataForSEO is async |
| Competitor ad spend | Not exposed by any ad platform API |
| Page revenue / conversion value | No revenue tracking connected |
| ROAS | Requires conversion value — not tracked |
| Social media engagement (likes, shares) | No social API connected |
| Email campaign metrics | No email platform connected |
| Heatmap / scroll depth | No behavioral analytics connected |
| Keyword search trend over time (Google Trends style) | Not in DataForSEO response |

---

## Official API Documentation (paste the relevant section when verifying)

> **Designer instruction:** For each component you're verifying, copy the relevant section
> from `API_SOURCES.md` and paste it here so Claude can check against the real documentation.

**Paste the official API docs section here:**

```
[PASTE RELEVANT OFFICIAL API DOCUMENTATION SECTION HERE]

Example: paste the DataForSEO keywords_data endpoint response schema, 
or the GSC searchanalytics.query response format, etc.
```

---

## Component Verification Prompt Template

Copy this entire block, fill in the `[BRACKETS]`, and paste into Claude:

---

```
I am designing a component for the FuseHealth dashboard and need you to verify it is
buildable given the real API constraints.

Read AI_TECHNICAL_GUIDE.md first to understand your role as a technical reviewer.

## Component I am designing

Page: [e.g. Keywords page]
Component name: [e.g. Keyword Rankings Table]
Description: [describe what it looks like and what it shows]

## Fields this component displays

[List every data field, e.g.:]
- Keyword text
- Current position (rank)
- Search volume
- Keyword difficulty score
- CPC (cost per click)
- Position change (vs last week)
- Intent (informational / transactional / commercial)

## Interaction patterns

[Describe any filtering, sorting, or dynamic behavior, e.g.:]
- User can filter by intent type
- Table sorts by search volume descending by default
- Clicking a keyword opens a detail panel

## Connectors I believe feed this component

[List from DESIGN_BRIEF.md, e.g.:]
- gsc_keywords (position, clicks, impressions)
- dataforseo_keywords (search_volume, KD, CPC, intent)

## Official API documentation for these endpoints

[Paste the relevant section from the official API docs here — 
find the URLs in API_SOURCES.md]

---

Please run a full design verification following the process in AI_TECHNICAL_GUIDE.md.
Produce a verdict table and a final APPROVED / APPROVED WITH CONDITIONS / NEEDS REVISION / HARD BLOCK verdict.
```

---

## Example Verified Component

**Component:** Keyword Rankings Table (Keywords page)

| Field | Connector | API Returns It? | Status | Notes |
|-------|-----------|----------------|--------|-------|
| keyword | gsc_keywords | YES | WORKING | from GSC `query` dimension |
| position | gsc_keywords | YES | WORKING | from GSC `position` metric |
| clicks | gsc_keywords | YES | WORKING | from GSC `clicks` metric |
| impressions | gsc_keywords | YES | WORKING | from GSC `impressions` metric |
| search_volume | dataforseo_keywords | YES | BALANCE_NEGATIVE | will show `—` until topped up |
| keyword_difficulty | dataforseo_keywords | YES | BALANCE_NEGATIVE | will show `—` until topped up |
| cpc | dataforseo_keywords | YES | BALANCE_NEGATIVE | will show `—` until topped up |
| intent | dataforseo_keywords | YES | BALANCE_NEGATIVE | will show `—` until topped up |
| position_change vs last week | gsc_keywords | PARTIAL | WORKING | requires 2+ days of data in DB; show `—` on first sync |

**Verdict: APPROVED WITH CONDITIONS**

Conditions:
1. Search volume, KD, CPC, and intent columns must show `—` (not zero, not blank) with a tooltip: "Requires DataForSEO balance — contact admin."
2. Position change column must handle the case where only one day of data exists (show `—` instead of crashing).
3. Filter by intent is valid — operates on data already in the DB, no live API call.

---

## Glossary of Connector Statuses

| Status | What it means for design |
|--------|--------------------------|
| WORKING | Data is available. Design the component normally. |
| BALANCE_NEGATIVE | Data is missing. Design a graceful `—` or locked state. |
| CREDENTIALS_MISSING | API not yet connected. Design a full "connect this account" empty state. |
| NO_CREDS_NEEDED | Data available but requires a config value (`FRAMER_SITEMAP_URL`). |

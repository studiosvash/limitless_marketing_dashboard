# Limitless Marketing Dashboard — Backend Handoff Spec v2

**This document supersedes `API_CONTRACT.md` (v1).** It is the authoritative,
self-contained spec for implementing the Django backend. It was regenerated
against the actual frontend source (`Limitless Marketing Dashboard v2.dc.html`,
`app/api.js`, `app/fixtures.js`) on 2026-07-07 and covers every route, shape,
and behavior the frontend exercises — including the AI Optimization layer and
extended Settings that v1 did not document.

---

## 0. Architecture — how the frontend talks to you

- The entire dashboard is one page. **All data access goes through
  `window.FuseAPI`** (`app/api.js`): `FuseAPI.get(path, params)`,
  `FuseAPI.post(path, body)`, `FuseAPI.put(path, body)`.
- Until a backend exists, FuseAPI serves deterministic fixtures
  (`app/fixtures.js`) with simulated latency, and persists user mutations in
  `localStorage['fuse.mutations.v1']` (see §7).
- **To go live, set two values — nothing else in the frontend changes:**

```js
FuseAPI.config.baseUrl   = 'https://api.yourhost.com'; // or the DC's `apiBaseUrl` prop
FuseAPI.config.authToken = '<token>';                  // sent as `Authorization: Bearer <token>`
```

- All endpoints are JSON under base path **`/api`**. Errors: any non-2xx makes
  the frontend show its error panel (GET) or a "Could not…" toast (mutations).
  No error-body contract is required — status code is enough.

### 0.1 Auth — decision required

The transport sends `credentials: 'include'` **and** (if configured)
`Authorization: Bearer <token>`. It does **not** send `X-CSRFToken`.
Recommended: **token auth** (DRF TokenAuthentication or JWT) — one header, no
CSRF dance. If you insist on Django session auth instead, you must CSRF-exempt
`/api/*` (or extend `http()` in `app/api.js` to read the `csrftoken` cookie —
a 3-line change, but decide before building).

CORS: the dashboard is served from a different origin than the API. Allow the
dashboard origin with `Access-Control-Allow-Credentials: true` and the
`Authorization` + `Content-Type` headers.

### 0.2 Naming note

`FuseAPI` / `fuse.mutations.v1` are legacy internal names from the FuseHealth
pilot project — the product is **Limitless Marketing**. Keep route names as
specced here; do not derive backend naming from "Fuse".

---

## 1. Endpoint reference (complete)

### Projects
| Method | Path | Body / Query | Returns |
|---|---|---|---|
| GET | `/api/projects` | — | `[{id, domain, name, vertical, location}]` |
| POST | `/api/projects` | `{domain, name?, vertical?, location?}` | `{id, domain, name, vertical, location}` — creates a project; frontend switches to it immediately |

### Per-project views — `GET /api/projects/:id/...`
`range` is `7d | 30d | 90d` (default `30d`). The frontend sends `range` for
**overview, positions, offsite, ads** and caches responses per
`(project, view, range)`; a manual sync invalidates the cache.

| Path | Query | Top-level keys returned |
|---|---|---|
| `overview` | `range` | `kpis[4]`, `pillars[5]`, `modules[7]`, `priority[≤6]`, `signals[≤3]`, `trend[]`, `summary{wins[],critical[],watch[]}`, `topPages[≤6]` |
| `seo` | — | `kpis{low_ctr, anomalies, critical, total_issues}`, `lowCtrPages[]`, `countries[]`, `anomalies[]`, `quickWinKws` |
| `keywords` | — | `kpis{total, avg_pos, total_volume, total_clicks}`, `intents{informational,commercial,transactional,navigational}`, `difficulty{easy,medium,hard}`, `segments{quick_wins[],striking[],declining[],low_ctr[]}` (keyword ids), `keywords[]` |
| `positions` | `range` | `kpis{tracked, avg_pos, est_traffic, impressions}`, `distribution{top3,p4_10,p11_20,p21_100}`, `movement{improved,declined,added,lost}`, `competitors{domains[], rows[]}`, `movers[≤8]` |
| `backlinks` | — | `kpis{total,live,lost,referring_domains,avg_rank}`, `links[]`, `summary{...}`, `months[24]`, `types[]`, `asBuckets[]`, `refDomains[]`, `anchors[]`, `competitors[≤4]`, `gapDomains[]` — see §2.3 |
| `audit` | — | `score`, `crawl{}`, `domainChecks[]`, `breakdown{}`, `catScore{}`, `cwv{}`, `checks[]`, `totals{errors,warnings,notices}`, `crawledPages[]`, `structure[]`, `snapshots[]` — see §2.4 |
| `ai` | — | full AI Optimization payload — see §2.5 |
| `offsite` | `range` | `totals{}`, `prev{}`, `trend[]`, `channels[]`, `referrers[]`, `social[]`, `landingPages[]`, `connectors{}`, `syncMeta{}` — see §2.6 |
| `ads` | `range` | `totals{}`, `prev{}`, `trend[]`, `pacing{}`, `campaigns[]`, `searchTerms[]`, `attribution[]`, `window{from,to,days}`, `landingPages[]`, `negatives[]`, `syncMeta{}` — see §2.7 |
| `alerts` | — | `feed[{id, ts, kind, severity, title, detail, acknowledged}]` |
| `settings` | — | **15 groups** — see §2.8. v1 documented only 6 of these. |

### Mutations
| Method | Path | Body | Effect / Returns |
|---|---|---|---|
| POST | `/api/projects/:id/keywords` | `{kw, volume?, kd?, cpc?, intent?}` | Track keyword (source `manual`). `{ok, keyword}` |
| POST | `/api/projects/:id/sync` | `{scope: all\|positions\|backlinks\|audit\|keywords\|ads\|ai}` | Enqueue sync. `{task_id, est_cost, steps[]}` |
| GET | `/api/tasks/:task_id` | — | `{task_id, progress: 0..1, step, done, est_cost}`. **Frontend polls every 500 ms** until `done`; unknown ids should return `{done: true}`. |
| POST | `/api/projects/:id/ads/status` | `{campaignId, status: enabled\|paused}` | Google Ads `CampaignService.mutate`. `{ok, status}` |
| POST | `/api/projects/:id/ads/budget` | `{campaignId, budgetDaily}` | `CampaignBudgetService.mutate`. `{ok, budgetDaily}` (integer ≥ 1) |
| POST | `/api/projects/:id/ads/negatives` | `{term, matchType, campaignId?}` | Add negative (campaign-level; shared set if no campaignId). `{ok, negatives[]}` |
| POST | `/api/projects/:id/ads/promote` | `{term}` | Track term as organic keyword (source `ads_term`) + mark term `tracked`. `{ok, keyword}` |
| POST | `/api/projects/:id/audit/toggle-check` | `{checkId}` | Hide/restore an audit check, persisted per project. `{hidden[]}` |
| POST | `/api/alerts/:alert_id/ack` | — | Acknowledge. `{ok}`. The UI also has **"Acknowledge all"** — it issues one ack POST per unacknowledged alert (parallel); a bulk endpoint is optional. |
| PUT | `/api/projects/:id/settings` | partial — see §2.8 key list | `{ok}` |
| POST | `/api/research` | `{project, keywords[], location}` | Keyword Explorer expansion — see §2.9. |
| POST | `/api/prompt-research` | `{project, seeds[]}` | Prompt Explorer — see §2.10. |
| POST | `/api/projects/:id/ai/:action` | see §2.5b | AI Optimization mutations (8 actions). |

---

## 2. Object shapes (canonical — matched to what the UI renders)

### 2.1 Core objects (unchanged from v1)

```jsonc
// keyword
{ "id": "fusehealth-kw-3", "kw": "hydration iv therapy", "intent": "commercial",
  "pos": 3, "prevPos": 5, "volume": 2400, "kd": 24, "cpc": 4.20,
  "clicks": 842, "impressions": 9100, "ctr": 9.2, "url": "/services/iv-therapy",
  "monthly": [ /* 12 ints */ ], "source": "sync|manual|ads_term",
  "serpFeatures": ["local_pack", "people_also_ask"] }

// backlink (links[] on the backlinks view)
{ "id": "fusehealth-bl-7", "domain": "healthline.com", "anchor": "iv hydration benefits",
  "type": "dofollow|nofollow", "status": "live|lost", "rank": 88,
  "firstSeen": "2026-01-14", "lostAt": null, "target": "/services/iv-therapy" }

// alert
{ "id": "fusehealth-al-2", "ts": "2026-06-28",
  "kind": "anomaly|ranking|backlink|technical|ads|ai|system",
  "severity": "high|medium|info", "title": "...", "detail": "...", "acknowledged": false }

// kpi (overview)   { "label": "Total clicks", "value": 18204, "delta": 8.2, "unit": "%|pos" }
// trend point      { "date": "2026-07-01", "clicks": 610, "impressions": 12400 }
```

### 2.2 Overview rollups

```jsonc
// pillar (5 cards; `target` is a dashboard tab key the card deep-links to)
{ "label": "Site health", "target": "pages", "valueKind": "num|pos|score|roas|pct",
  "value": 82, "delta": 3, "deltaUnit": "%|pos|pts", "sub": "5 errors to fix",
  "state": "ok|setup" }        // "setup" when AI Optimization isn't configured

// module card (7; tone drives the status dot)
{ "label": "Backlinks", "target": "backlinks", "stat": "128 live",
  "sub": "+8 new · −2 lost (7d)", "tone": "ok|warn|bad|setup" }

// priority item (unacknowledged alerts, severity-sorted, tagged with owning module)
{ "id": "fusehealth-al-2", "severity": "high", "kind": "ads", "title": "...",
  "detail": "...", "ts": "2026-06-28", "module": { "label": "Ads", "target": "ads" } }
// kind→module map: anomaly→seo, ranking→positioning, backlink→backlinks,
//                  technical→pages, ads→ads, ai→ai, system→alerts
```

`summary` (wins/critical/watch string arrays) is the cached AI-generated weekly
summary. The UI has a **Copy** button that pastes it as plain text — keep each
item a complete sentence.

### 2.3 Backlink Analytics (NEW in v2 — the whole analytics suite)

Maps to DataForSEO Backlinks API: `summary`→ backlinks/summary, `months`→
backlinks/history (24 mo), `types`→ referring_links_types, `asBuckets`→
referring_domains grouped by rank band, `refDomains`→ backlinks/referring_domains,
`anchors`→ backlinks/anchors, `gapDomains`→ backlinks/domain_intersection.

```jsonc
"summary":   { "authorityScore": 47, "asDelta": 2, "refDomains": 1450, "backlinks": 12400,
               "dofollowPct": 71, "broken": 64, "spamScore": 6, "newRdMonth": 38,
               "lastUpdated": "Jun 30, 2026" },
"months":    [{ "label": "Jul '24", "nw": 42, "lost": 18 }],           // 24 entries
"types":     [{ "key": "text", "label": "Text", "color": "#4f46e5", "pct": 62 }],
"asBuckets": [{ "label": "81-100", "color": "#059669", "count": 96 }],
"refDomains":[{ "domain": "healthline.com", "flag": "🌐", "rank": 88, "backlinks": 140,
               "linksToUs": 6, "follow": true, "category": "Health",
               "firstSeen": "Mar 2023", "isNew": false, "spam": 4 }],
"anchors":   [{ "anchor": "fusehealth", "type": "Branded|URL|Keyword|Generic|Empty",
               "backlinks": 620, "refDomains": 121, "dofollowPct": 74 }],
"competitors": ["driphydration.com", ...],                              // ≤ 4
"gapDomains":[{ "domain": "forbes.com", "flag": "🌐", "rank": 94,
               "you": false, "comp": [true, true, false, true] }]       // aligned to competitors[]
```

UI notes: referring-domain names and backlink source URLs are rendered as
live `https://` links; `rank` is DataForSEO domain rank (0–100).

### 2.4 Site Audit (unchanged from v1 — shapes confirmed)

```jsonc
"crawl":     { "status": "done", "pagesCrawled": 148, "maxPages": 500,
               "startedAt": "...", "duration": "4m 12s", "userAgent": "..." },
"domainChecks": [{ "id": "ssl", "label": "SSL certificate", "ok": true, "detail": "..." }],
"breakdown": { "healthy": 92, "withIssues": 41, "broken": 6, "redirected": 7, "blocked": 2 },
"catScore":  { "Crawlability": 88, "HTTPS": 100, "Internal Linking": 74,
               "Markup": 81, "Performance": 69, "Content": 77 },
"cwv":       { "lcp": { "p75": 2.1, "unit": "s", "good": 2.5, "poor": 4,
                        "buckets": { "good": 61, "mid": 25, "poor": 14 } }, "tbt": {...}, "cls": {...} },
"checks":    [{ "id": "missing_description", "severity": "error|warning|notice",
               "category": "Content", "title": "...", "howToFix": "...",
               "pages": ["/a", "/b"], "count": 2, "hidden": false }],
"crawledPages": [{ "id": "...", "url": "/services/iv-therapy", "statusCode": 200,
               "kind": "ok|gone|redirect|noindex", "depth": 2, "score": 84,
               "errors": 0, "warnings": 2, "notices": 1, "inLinks": 22,
               "internalLinks": 31, "externalLinks": 4, "loadTimeMs": 1240,
               "wordCount": 1430, "failed": ["missing_description"],
               "cwv": { "lcp": 2.1, "tbt": 180, "cls": 0.06 } }],
"structure": [{ "folder": "/services/", "pages": 24, "avgScore": 81,
               "errors": 3, "warnings": 9, "notices": 4 }],
"snapshots": [{ "id": "crawl-6", "date": "2026-06-28", "score": 76, "pagesCrawled": 148,
               "errors": 16, "warnings": 42, "notices": 30, "byCheck": { "<checkId>": 7 } }]
```

`totals` must be computed over **non-hidden** checks only (per-project hidden
list from `audit/toggle-check`). The legacy page shape from v1
(`pages[]` with clicks/ctr/indexed/verdict) is still used by the **seo** and
**overview** views.

### 2.5 AI Optimization (NEW in v2 — entirely undocumented in v1)

`GET /api/projects/:id/ai` returns:

```jsonc
{
  "setupDone": true,                       // false → UI shows the first-run wizard
  "targets": { "brand": "FuseHealth", "aliases": ["FuseHealth"], "competitors": ["driphydration.com"] },
  "budget":  { "cap": 25, "spent": 4.31, "weekly_est": 1.29 },
  "costs":   { "model": 0.006, "inspect": 0.01 },      // $ per model-run / per inspection
  "next_run": "2026-07-13",
  "mentionPlatforms": [{ "id": "ai_overview", "name": "AI Overviews", "color": "#4f46e5" },
                       { "id": "chat_gpt", "name": "ChatGPT", "color": "#0d9488" }],
  "llmPlatforms":     [ /* chat_gpt, claude, gemini, perplexity — same shape */ ],
  "sov": { "you": 34.2, "delta": 2.2,
           "rows": [{ "domain": "fusehealth.com", "isYou": true, "mentions": 142,
                      "sov": 34.2, "prevSov": 32.0, "aiVolume": 4900,
                      "byPlatform": [88, 54] }] },      // aligned to mentionPlatforms
  "kpis": { "mentions": 142, "impressions": 18400, "cited_pages": 6,
            "prompt_coverage": { "cited": 4, "total": 9 } },
  "trend": [{ "date": "2026-04-20", "ai_overview": 12, "chat_gpt": 9 }],   // 12 weekly pts
  "topPages":   [{ "url": "/services/iv-therapy", "mentions": 31, "impressions": 4200,
                   "platforms": ["AI Overviews", "ChatGPT"] }],
  "topDomains": [{ "domain": "healthline.com", "isYou": false, "isComp": false,
                   "mentions": 210, "share": 18.4 }],
  "lists":   [{ "id": "pl1", "name": "Core prompts" }],
  "prompts": [{ "id": "...", "text": "What is the best mobile IV therapy?",
                "listId": "pl1",
                "cfg": { "models": ["chat_gpt","claude","gemini","perplexity"],
                         "webSearch": true, "country": "United States", "city": "",
                         "cadence": "daily|weekly|manual" },
                "addedAt": "2026-06-02", "runs": 4, "lastRun": "2026-07-01",
                "results": { "chat_gpt": { "mentioned": true, "cited": true,
                                           "position": 2, "snippet": "..." } } }],
  "suggestions": [{ "id": "...", "text": "...", "kw": "iv therapy",
                    "category": "recommendation|comparison|cost|question|local",
                    "aiVolume": 320 }],                 // exclude already-tracked texts
  "aiKeywords": [{ "kw": "iv therapy", "aiVolume": 480, "gVolume": 2400, "ratio": 20,
                   "trend": [ /* 12 ints */ ], "intent": "commercial",
                   "mentions": 6, "gap": false }],      // gap = aiVolume≥200 && mentions==0
  "history": [ /* inspection entries, newest first, capped at 50 — shape below */ ]
}
```

#### 2.5b AI mutations — `POST /api/projects/:id/ai/:action`

| Action | Body | Effect / Returns |
|---|---|---|
| `setup` | `{brand, aliases[], competitors[≤9], prompts?[], listId?}` | Configure targets, add starter prompts, set `setupDone`. `{ok}` |
| `targets` | `{brand, aliases[], competitors[≤9]}` | Update tracked entities. `{ok}` |
| `prompts` | `{texts[], listId}` | Add prompts (dedupe by text, trim, ≤500 chars). `{ok, added}` |
| `prompts-remove` | `{id}` | `{ok}` |
| `prompts-config` | `{id, cfg{models,webSearch,country,city,cadence}, listId?}` | `{ok}` |
| `lists` | `{op: create\|rename\|delete, id?, name?}` | Deleting the last list recreates a default; orphaned prompts move to the first list. create → `{ok, id}` |
| `run` | `{promptId?}` or `{listId?}` or `{}` (= all) | Run prompt(s) across their configured models now. Charges `models.length × costs.model` per prompt. `{ok, ran, cost}` |
| `inspect` | `{question, promptId?}` | Live ChatGPT-with-search scrape ("Answer Inspector"). Charges `costs.inspect`. Returns and persists a history entry: |

```jsonc
// inspection history entry
{ "id": "insp...", "question": "...", "promptId": null, "ts": "2026-07-07",
  "verdict": "cited|mentioned|absent", "position": 2, "cost": 0.01,
  "scrape": {
    "model": "ChatGPT · gpt-4o with search", "location": "United States",
    "results": { "chat_gpt": { "mentioned": true, "cited": true, "position": 2, "snippet": "..." } },
    "paragraphs": [{ "text": "... [1]", "hit": false },
                   { "text": "FuseHealth (fusehealth.com) is frequently recommended ... [2]", "hit": true }],
    "citations": [{ "n": 1, "title": "Guide: ...", "domain": "healthline.com", "isYou": false },
                  { "n": 2, "title": "FuseHealth — official site", "domain": "fusehealth.com", "isYou": true }]
  } }
```

**Data source:** DataForSEO AI Optimization APIs — LLM **Mentions** API covers
AI Overviews + ChatGPT (feeds `sov`, `trend`, `topPages`, `topDomains`,
`aiKeywords.aiVolume`); LLM **Responses** API runs tracked prompts across the 4
models (feeds `prompts[].results`); the **inspect** action is a ChatGPT
Scraper call. Budget: enforce `budget.cap` as a soft cap on manual runs, never
on the weekly cron (same rule as DataForSEO budget, §5).

### 2.6 Off-site SEO (v1 shape confirmed, plus `connectors`)

`totals{sessions, engagedSessions, engagementRate, keyEvents, revenue,
referringDomains}`, `prev{...}`, `trend[{date, sessions, engagedSessions,
keyEvents, revenue}]`, `channels[]`, `referrers[]`, `social[]`,
`landingPages[]`, `connectors{linkedin, reddit, youtube, x, facebook,
instagram}` (booleans), `syncMeta{cadence, last_pull, next_pull,
ga4_tokens_used, ga4_tokens_limit}`.

```jsonc
// referrer (GA4 sessionSource where medium=referral)
{ "domain": "healthline.com", "rank": 88, "source": "healthline.com", "channel": "Referral",
  "sessions": 512, "engagedSessions": 331, "engagedRate": 0.65, "keyEvents": 14.2,
  "revenue": 1840.50, "newUserRate": 0.62, "avgEngagementSec": 128, "tracked": true }

// social/video platform — impressions come from the platform's OWN connector,
// NOT GA4; null until that connector is linked (connected:false)
{ "platform": "LinkedIn", "source": "linkedin.com", "channel": "Organic Social",
  "sessions": 468, "engagedSessions": 300, "engagedRate": 0.64, "keyEvents": 12.1,
  "revenue": 1520.00, "impressions": 18400, "connected": true }

// landing page
{ "url": "/services/iv-therapy", "sessions": 940, "engagedSessions": 620,
  "engagedRate": 0.66, "keyEvents": 22.4, "revenue": 2100.00, "topSource": "healthline.com" }
```

### 2.7 Ads (v1 shape confirmed, plus `window`)

Everything from v1 §1/§2 stands (campaign, search term, pacing, attribution,
syncMeta shapes). Additions/confirmations:

- Response includes `window: { from: "2026-06-08", to: "2026-07-07", days: 30 }`
  — the exact date window the aggregates cover.
- `searchTerms[].status` is derived **server-side**:
  `negative` (in negatives list) > `tracked` (promoted) > `converting`
  (conversions > 0) > `wasted`.
- Aggregates are re-computed over the requested `range` (GAQL
  `WHERE segments.date BETWEEN …`), not scaled from a fixed window — the
  fixture's scaling hack is fixture-only.
- `budget_daily` edits round to integers ≥ 1.

```jsonc
// campaign (metrics aggregated over `range`)
{ "id": "fusehealth-cmp-0", "name": "Brand — Search", "platform": "Google Ads|Meta",
  "type": "Search|Performance Max|Retargeting|Prospecting", "status": "enabled|paused",
  "budget_daily": 38, "spend": 1180.2, "impressions": 24800, "clicks": 1140,
  "ctr": 4.6, "cpc": 1.04, "conversions": 64.2, "cpa": 18.4,
  "conv_value": 5120.5, "roas": 4.34, "ga4_key_events": 48.9, "ga4_revenue": 3890.1,
  "lost_is_budget": 19, "lost_is_rank": 8,            // 0 when paused
  "prev": { "spend": 1050.0, "conversions": 58.1 },   // previous equal-length period
  "adGroups": [{ "id": "...", "name": "...", "spend": 402.1, "clicks": 380, "conversions": 22.4, "cpa": 17.9 }],
  "daily": [{ "date": "2026-07-01", "spend": 39.2, "impressions": 820, "clicks": 38,
              "conversions": 2.1, "conv_value": 168.0, "ga4_key_events": 1.6, "ga4_revenue": 120.4 }] }

// pacing (calendar month, computed server-side)
{ "monthly_budget": 4200, "mtd_spend": 1180, "projected": 3900, "pct": 28,
  "day_of_month": 7, "days_in_month": 31,
  "channels": [{ "platform": "Google Ads", "budget": 3000, "mtd": 890, "pct": 30 }] }

// search term
{ "id": "...", "term": "iv therapy near me", "matchedKeyword": "iv therapy",
  "matchType": "exact|phrase|broad", "campaignId": "...", "campaign": "Non-Brand — Search",
  "impressions": 1900, "clicks": 82, "cost": 148.6, "conversions": 4.1, "cpa": 36.2,
  "status": "converting|wasted|negative|tracked" }

// attribution row (only campaigns with spend > 0)
{ "id": "...", "name": "...", "platform": "Google Ads",
  "ads_conversions": 64.2, "ga4_key_events": 48.9,
  "ads_value": 5120.5, "ga4_revenue": 3890.1, "gap_pct": -24 }
```

### 2.8 Settings (v1 documented 6 groups; the real payload has 15)

`GET /api/projects/:id/settings` returns ALL of:

```jsonc
{
  "project":     { "id", "domain", "name", "vertical", "location", "competitors": [] },
  "credentials": { "gsc_property": "sc-domain:fusehealth.com", "ga4_property_id": "512345678" },
  "connectors":  [{ "name": "Search Console", "status": "ok", "last_sync": "...", "records": 18204 }],
  "prefs":       { "email_alerts": true, "weekly_digest": true },
  "crawl":       { "maxPages": 500, "frequency": "weekly|biweekly|monthly", "jsRendering": false,
                   "respectRobots": true, "excludedPaths": "/admin\n/cart" },
  "alertRules":  [{ "id": "pos_drop", "label": "Keyword position drops by",
                    "threshold": 3, "unit": "positions", "on": true }],   // 4 built-in rules
  "sync":        { "cadence": "...", "last_run": "...", "next_run": "..." },
  "usage":       { "budget": 75, "currency": "USD", "month_to_date": 4.31, "est_monthly": 7.90,
                   "items": [{ "module": "...", "cadence": "Weekly|Monthly|On demand", "est": 1.92, "note": "..." }] },
  "workspace":   { "name", "plan", "seats_used", "seats_total", "billing_cycle", "renews",
                   "mrr", "currency", "timezone", "week_start", "owner_email" },
  "team":        [{ "id", "name", "email", "role": "Owner|Admin|Analyst|Viewer",
                    "status": "active|invited", "last_active", "initials" }],
  "syncConfig":  { "positions": "weekly", "backlinks": "weekly", "audit": "monthly",
                   "keywords": "monthly", "ads": "12h", "ai": "weekly" },
  "budget":      { "cap": 75, "enforce": true, "mtd": 4.31,
                   "quotas": { "ga4_tokens_used", "ga4_tokens_limit",
                               "ads_ops_used", "ads_ops_limit",
                               "gsc_queries_used", "gsc_queries_limit" } },
  "platformConnectors": { "linkedin": true, "reddit": false, "youtube": false,
                          "x": false, "facebook": false, "instagram": false, "meta_ads": false },
  "notifications": { "email_enabled", "weekly_digest", "digest_day", "recipients",
                     "slack_enabled", "slack_webhook", "quiet_start", "quiet_end",
                     "route_high": "email|digest|none", "route_medium", "route_info" },
  "aiConfig":    { "provider", "model", "tone", "cadence", "monthly_cap", "brand_voice" },
  "security":    { "twofa", "sso", "session_timeout",
                   "sessions": [{ "id", "device", "ip", "location", "current", "last" }],
                   "tokens":   [{ "id", "name", "prefix", "created", "last_used" }] },
  "dataPrefs":   { "export_format", "retention", "report_timezone", "number_format" }
}
```

`PUT /api/projects/:id/settings` accepts a **partial body** with any of these
keys — persist each independently and return `{ok}`:
`credentials, prefs, crawl, alertRules, syncConfig, platformConnectors`
(per-project) and `workspace, team, notifications, aiConfig, security,
dataPrefs, budgetCap, budgetEnforce` (workspace-level).

Scoping: workspace-level groups are shared across projects. `usage.budget` /
`budget.cap` is the DataForSEO soft cap (§5); `aiConfig.monthly_cap` is the AI
summary cap; the AI Optimization cap lives in the `ai` view's `budget.cap`.

### 2.9 Keyword Explorer — `POST /api/research`

**v1 documented this wrong.** The actual request/response:

```jsonc
// request
{ "project": "fusehealth", "keywords": ["iv therapy", "mobile iv"], "location": "United States" }
// response
{ "rows": [                                             // ≤ 200 in fixture; cap ~1000 live
    { "kw": "best iv therapy near me", "volume": 1900,
      "match": "exact|phrase|broad|questions|related",  // which expansion produced it
      "monthly": [ /* 12 ints */ ], "serpFeatures": ["local_pack"],
      "kd": 32, "cpc": 3.40, "intent": "commercial", "tracked": false } ],
  "cost": 0.036, "location": "United States" }
```

One call returns the union of ALL expansion algorithms, each row tagged with
`match`; the frontend's match-type tabs, filters, grouping, and sorting all run
client-side on this cached set — **filter changes never re-hit the API**.
Endpoint mapping per match type (all DataForSEO Labs **Live** calls, cache per
`(seeds, location)` for 7 days):

| `match` | Endpoint | Algorithm |
|---|---|---|
| `broad` | `dataforseo_labs/google/keyword_ideas/live` | same-category relevance search; results may not contain the seed |
| `phrase` | `dataforseo_labs/google/keyword_suggestions/live` | full-text: seed contained with extra words |
| `questions` | `keyword_suggestions` + server regex filter `^(how\|what\|why\|when\|where\|is\|are\|can\|does\|do\|will\|which\|who)\b` | question long-tail |
| `related` | `dataforseo_labs/google/related_keywords/live` (depth 2) | semantic neighbors; may drop the seed |
| `exact` | `keywords_data/google_ads/search_volume` | literal seed metrics |

KD from `bulk_keyword_difficulty` (≤1000/req) on the cached set; intent from
`search_intent`. Pricing: $0.012/task + $0.00012/row → 1,000 rows ≈ $0.13.
Sort union by volume desc, dedupe on keyword string.

### 2.10 Prompt Explorer — `POST /api/prompt-research` (NEW)

```jsonc
// request:  { "project": "fusehealth", "seeds": ["mobile iv therapy"] }
// response: { "rows": [{ "text": "What is the best mobile iv therapy and who do you recommend?",
//                        "category": "recommendation|comparison|cost|question|local",
//                        "aiVolume": 320, "tracked": false }],   // ≤ 40, aiVolume desc
//             "cost": 0.01, "location": "United States" }
```

Mirrors Keyword Explorer for AI prompts. v1: template expansion over seeds +
LLM Mentions volume lookup is sufficient; `tracked` = text already in the
project's prompt list.

---

## 3. Data-source mapping (what feeds what)

| Module | Source | Cadence |
|---|---|---|
| Overview KPIs / trend / countries / topPages | **Google Search Console API** (free) | daily rows, pulled weekly+ |
| Position Tracking | DataForSEO `serp/google/organic/task_post`+`task_get` (Standard queue), 1 task/keyword; competitor positions parsed from the same SERP | weekly (Mon 06:00) |
| Keywords volume/KD/intent | `keywords_data/google_ads/search_volume` (bulk) + `dataforseo_labs` bulk_keyword_difficulty + search_intent | monthly |
| Keyword Explorer | §2.9 Labs live calls | on demand |
| Backlinks (all sub-tabs) | `backlinks/summary` + `history` + `backlinks` (`mode=new_lost`) + `referring_domains` + `anchors` + `domain_intersection` | summary weekly; full dump monthly |
| Site Audit | `on_page/task_post` (≤500 pages, JS off) → summary, pages, lighthouse, redirect_chains, non_indexable, duplicate_tags, links | monthly (configurable via `crawl.frequency`) |
| Off-site SEO | **GA4 Data API `runReport`** — dims `sessionDefaultChannelGroup`, `sessionSource`, `landingPage`; metrics sessions, engagedSessions, engagementRate, keyEvents, totalRevenue; filter Referral + Organic Social/Video. Per-platform impressions from each platform's own connector. | every 12h |
| Ads | **Google Ads API** GAQL on `campaign`, `ad_group`, `search_term_view`, `campaign_budget` + **GA4** join on `sessionCampaignName` | every 12h (06:00/18:00) |
| AI Optimization | DataForSEO **LLM Mentions** (AI Overviews + ChatGPT) + **LLM Responses** (4 models) + ChatGPT **Scraper** (inspect) | weekly per prompt cfg; on-demand runs/inspect |
| Alerts | generated server-side after each sync using `alertRules` thresholds (position drops, lost backlinks rank≥40, new 404s, GSC ±% vs 28-day mean, audit errors) + ads alerts (lost-IS ≥15%, CPA +30%, disapproved, silent conversions >48h) + AI alerts (SOV drop, unmentioned prompt) | after each sync |
| AI weekly summary | OpenAI/Claude call on cron after weekly sync (provider/model/tone from `aiConfig`); cache the result | weekly |

## 4. Sync tasks

`POST /sync {scope}` enqueues (Celery or equivalent) and returns
`{task_id, est_cost, steps[]}` where `steps` are human-readable stage labels
(the UI shows them verbatim during polling). Scopes and their step lists live
in `app/api.js` (`SCOPE_STEPS`) — reuse the same wording. On completion the
frontend re-fetches the active tab and alerts; your task should therefore
finish only after all derived data (alerts, rollups) is recomputed.

## 5. Cost model & budget enforcement

Unchanged from v1 (≈$5–8/mo at current scale; see v1 §4 table) **plus** AI
Optimization: `runs = prompts × models × $0.006`, inspections $0.01 — the
`ai.budget.weekly_est` shown in the UI is
`Σ enabled prompts (models.length × 0.006 × runs/week)`.
Record actual charges per call and expose them in `usage`. Enforce
`budget.cap` (when `budget.enforce`) as a **soft cap: refuse manual/on-demand
work when `month_to_date ≥ cap`, never block scheduled crons.**

## 6. Fixture artifacts — do NOT ship these

Values the fixture hardcodes or fakes that the backend must genuinely compute:

- `positions.movement.lost` — fixture returns literal `2`; compute keywords that ranked last week and rank nowhere now.
- `ads/offsite syncMeta` op/token counters (26, 310, 214…) — report real quota usage.
- `seo.anomalies` — fixture regex-parses alert titles; compute from the GSC daily series (±30% vs 28-day mean, or the `alertRules` threshold).
- The entire Backlink Analytics dataset (§2.3) is a deterministic per-domain generator — replace wholesale with DataForSEO.
- `genPromptResults` / `genScrape` — deterministic AI results; replace with LLM Responses/Scraper.
- Ads search-term range scaling (§2.7 note) — re-aggregate server-side.

## 7. Fixture-mode localStorage → your database

Every user mutation the fixture persists in `localStorage['fuse.mutations.v1']`
maps to an endpoint above; once `baseUrl` is set, localStorage is bypassed
entirely. Complete key map (all keyed per project id unless noted):

| localStorage key | Endpoint that replaces it |
|---|---|
| `ack.<alertId>` | POST `/alerts/:id/ack` |
| `added.<pid>` | POST `/projects/:id/keywords` |
| `adsStatus.<pid>`, `adsBudget.<pid>`, `adsNegatives.<pid>`, `adsPromoted.<pid>` | POST `ads/status`, `ads/budget`, `ads/negatives`, `ads/promote` |
| `auditHidden.<pid>` | POST `audit/toggle-check` |
| `creds/prefs/crawlCfg/alertRules/syncConfig/platformConn.<pid>` | PUT `settings` (per-project keys) |
| `workspace, team, notifications, aiConfig, security, dataPrefs, budgetCap, budgetEnforce` | PUT `settings` (workspace keys) |
| `lastSync.<pid>`, `usageExtra.<pid>` | server-side sync bookkeeping + `usage` |
| `aiSetup/aiTargets/aiLists/aiPrompts/aiHistory/aiSpend/aiCap.<pid>` | POST `ai/:action` + `ai` view |

**Frontend-only (stays client-side, no endpoint needed for v1):**
`localStorage['fh_keyword_lists']` — the Keyword Explorer's saved keyword
lists. Optional later: a `/keyword-lists` CRUD if lists should sync across devices.

## 8. Frontend behaviors to honor

- **Caching:** responses cached per `(project, view, range)` until the user
  syncs, mutates, or hits Refresh — GETs must be side-effect-free.
- **Task polling:** 500 ms interval on `/api/tasks/:id`; return monotonic
  `progress` and a current `step` string.
- **Mutation → refetch:** after ads mutations the frontend invalidates all ads
  caches for the project and refetches; after `promote` it also invalidates
  keywords/positions. Mutations must be immediately visible in subsequent GETs.
- **Write-back semantics:** campaign pause/budget/negative mutations are
  applied to Google Ads on the next 12h sync — the UI copy says so
  ("written back on next sync"); your API just records intent + returns `{ok}`.
- **Date format:** ISO `YYYY-MM-DD` everywhere; timestamps ISO 8601.
- **Ack-all:** parallel per-alert POSTs (no bulk endpoint required).
- The UI links page paths as `https://{project.domain}{url}` — return `url`
  as a root-relative path (`/services/iv-therapy`), never absolute.

## 9. Milestones deliberately NOT in v1 backend

1. Rule-builder **engine** — the Settings UI already edits 4 threshold rules
   (`alertRules`); v1 backend only needs to apply those thresholds when
   generating alerts. Arbitrary user-defined rules = later.
2. Brand monitoring (Content Analysis API: mentions, sentiment).
3. Platform impression connectors beyond LinkedIn (Reddit/YouTube/X/FB/IG
   toggles exist in Settings; return `connected:false` until built).
4. Team invites / SSO / 2FA as real auth flows — the Settings UI mutates these
   via PUT `settings`; persisting the JSON is enough for v1.
5. Dark mode.

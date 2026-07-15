# FuseHealth / Limitless Marketing Dashboard — API Contract v1

> **⚠ SUPERSEDED — see [`HANDOFF_SPEC.md`](HANDOFF_SPEC.md) (v2).**
> This v1 contract predates the AI Optimization layer, Prompt Explorer,
> extended Settings, Backlink Analytics, and the auth decision. It is kept
> for history only; implement against HANDOFF_SPEC.md.

The frontend (`FuseHealth App v2.dc.html`) talks to data **only** through `window.FuseAPI`
(`app/api.js`). Until the Django backend exists, FuseAPI serves fixtures shaped exactly
like this contract. To go live, implement these endpoints and set:

```js
FuseAPI.config.baseUrl = 'https://yourhost.com';   // or the app's `apiBaseUrl` tweak/prop
```

All endpoints are JSON, session-authenticated (Django auth + CSRF exempt for the API or
token auth — your call). Base path: `/api`.

---

## 1. Endpoints

### Projects
| Method | Path | Params | Returns |
|---|---|---|---|
| GET | `/api/projects` | — | `[{id, domain, name, vertical, location}]` |

### Per-project views (all `GET /api/projects/:id/...`)
| Path | Query | Returns (top-level keys) |
|---|---|---|
| `overview` | `range=7d\|30d\|90d` | `kpis[]`, `pillars[]`, `modules[]`, `priority[]`, `signals[]`, `trend[]`, `summary{wins,critical,watch}`, `topPages[]` |
| `seo` | — | `kpis{low_ctr,anomalies,critical,total_issues}`, `lowCtrPages[]`, `countries[]`, `anomalies[]`, `quickWinKws` |
| `keywords` | — | `kpis{total,avg_pos,total_volume,total_clicks}`, `intents{}`, `difficulty{easy,medium,hard}`, `segments{quick_wins[],striking[],declining[],low_ctr[]}` (arrays of keyword ids), `keywords[]` |
| `positions` | `range` | `kpis{tracked,avg_pos,est_traffic,impressions}`, `distribution{top3,p4_10,p11_20,p21_100}`, `movement{improved,declined,added,lost}`, `competitors{domains[],rows[]}`, `movers[]` |
| `backlinks` | — | `kpis{total,live,lost,referring_domains,avg_rank}`, `links[]` |
| `offsite` | `range=7d\|30d\|90d` | `totals{sessions,engagedSessions,engagementRate,keyEvents,revenue,referringDomains}`, `prev{sessions,engagedSessions,keyEvents,revenue}`, `trend[{date,sessions,engagedSessions,keyEvents,revenue}]`, `channels[{channel,sessions,keyEvents,revenue,engagedRate,offsite}]`, `referrers[]`, `social[]`, `landingPages[{url,sessions,engagedSessions,engagedRate,keyEvents,revenue,topSource}]`, `connectors{linkedin,reddit,youtube,x,facebook,instagram}`, `syncMeta{cadence,last_pull,next_pull,ga4_tokens_used,ga4_tokens_limit}` |
| `audit` | — | `score`, `crawl{status,pagesCrawled,maxPages,startedAt,duration,userAgent}`, `domainChecks[{id,label,ok,detail}]`, `breakdown{healthy,withIssues,broken,redirected,blocked}`, `catScore{Crawlability,HTTPS,Internal Linking,Markup,Performance,Content}`, `cwv{lcp,tbt,cls: {p75,unit,good,poor,buckets{good,mid,poor}}}`, `checks[{id,severity:error\|warning\|notice,category,title,howToFix,pages[],count,hidden}]`, `totals{errors,warnings,notices}`, `crawledPages[]`, `structure[{folder,pages,avgScore,errors,warnings,notices}]`, `snapshots[{id,date,score,pagesCrawled,errors,warnings,notices,byCheck{}}]` |
| `ads` | `range` | `totals{spend,impressions,clicks,conversions,conv_value,ga4_key_events,ga4_revenue,cpa,cpc,roas}`, `prev{spend,conversions}`, `trend[{date,spend,conversions,ga4_key_events}]`, `pacing{monthly_budget,mtd_spend,projected,pct,day_of_month,days_in_month,channels[{platform,budget,mtd,pct}]}`, `campaigns[]`, `searchTerms[]`, `attribution[{id,name,platform,ads_conversions,ga4_key_events,ads_value,ga4_revenue,gap_pct}]`, `landingPages[{url,campaign,sessions,engagedRate,keyEvents,revenue}]`, `negatives[]`, `syncMeta{cadence,last_pull,next_pull,ops_used,ops_limit,ga4_tokens_used,ga4_tokens_limit,monthly_cost}` |
| `alerts` | — | `feed[{id,ts,kind,severity,title,detail,acknowledged}]` |
| `settings` | — | `project{}`, `credentials{}`, `connectors[]`, `prefs{}`, `sync{}`, `usage{}` |

### Mutations
| Method | Path | Body | Effect |
|---|---|---|---|
| POST | `/api/projects/:id/keywords` | `{kw, volume?, kd?, cpc?, intent?}` | Add keyword to tracking (source `manual`). Returns `{ok, keyword}` |
| POST | `/api/projects/:id/sync` | `{scope: all\|positions\|backlinks\|audit\|keywords}` | Enqueue sync. Returns `{task_id, est_cost, steps[]}` |
| POST | `/api/projects/:id/ads/status` | `{campaignId, status: enabled\|paused}` | Pause/enable campaign (backend: Google Ads `CampaignService.mutate`). `{ok, status}` |
| POST | `/api/projects/:id/ads/budget` | `{campaignId, budgetDaily}` | Update daily budget (`CampaignBudgetService.mutate`). `{ok, budgetDaily}` |
| POST | `/api/projects/:id/ads/negatives` | `{term, matchType, campaignId?}` | Add negative keyword (campaign-level; shared set if no campaignId). `{ok, negatives[]}` |
| POST | `/api/projects/:id/ads/promote` | `{term}` | Track a search term as an organic keyword (same effect as POST /keywords, source `ads_term`) and mark the term. `{ok, keyword}` |
| POST | `/api/projects/:id/audit/toggle-check` | `{checkId}` | Hide/restore an audit check (persisted per project). Returns `{hidden[]}` |
| GET | `/api/tasks/:task_id` | — | `{task_id, progress: 0..1, step, done, est_cost}` — frontend polls every 500 ms |
| POST | `/api/alerts/:alert_id/ack` | — | Acknowledge alert. `{ok}` |
| PUT | `/api/projects/:id/settings` | `{credentials?, prefs?}` | Partial update. `{ok}` |
| POST | `/api/research` | `{project, seed, matchType: broad\|phrase\|related\|questions\|exact\|all, filters?, limit?, offset?, location}` | Keyword Explorer expansion (see §3c). Returns `{rows[{kw,volume,kd,cpc,intent,serpFeatures,monthly,tracked}], total_count, cost, location, cached}` |

## 2. Object shapes (canonical)

```jsonc
// keyword
{ "id": "fusehealth-kw-3", "kw": "hydration iv therapy", "intent": "commercial",
  "pos": 3, "prevPos": 5, "volume": 2400, "kd": 24, "cpc": 4.20,
  "clicks": 842, "impressions": 9100, "ctr": 9.2, "url": "/services/iv-therapy",
  "monthly": [1900, ...12 ints...], "source": "sync|manual",
  "serpFeatures": ["local_pack", "people_also_ask"] }

// backlink
{ "id": "fusehealth-bl-7", "domain": "healthline.com", "anchor": "iv hydration benefits",
  "type": "dofollow|nofollow", "status": "live|lost", "rank": 88,
  "firstSeen": "2026-01-14", "lostAt": null, "target": "/services/iv-therapy" }

// offsite referring domain (GA4 sessionSource where medium=referral)
{ "domain": "healthline.com", "rank": 88, "source": "healthline.com", "channel": "Referral",
  "sessions": 512, "engagedSessions": 331, "engagedRate": 0.65, "keyEvents": 14.2,
  "revenue": 1840.50, "newUserRate": 0.62, "avgEngagementSec": 128, "tracked": true }

// offsite social/video platform (GA4 sessionSource by Organic Social/Video channel)
// impressions/CTR come from the platform's OWN connector (LinkedIn API etc), NOT GA4 —
// impressions is null until that platform's connector is linked (connected:false).
{ "platform": "LinkedIn", "source": "linkedin.com", "channel": "Organic Social",
  "sessions": 468, "engagedSessions": 300, "engagedRate": 0.64, "keyEvents": 12.1,
  "revenue": 1520.00, "impressions": 18400, "connected": true }

// audit crawled page (OnPage-shaped)
{ "id": "fusehealth-cp-0", "url": "/services/iv-therapy", "statusCode": 200,
  "kind": "ok", "depth": 2, "score": 84, "errors": 0, "warnings": 2, "notices": 1,
  "inLinks": 22, "internalLinks": 31, "externalLinks": 4, "loadTimeMs": 1240,
  "wordCount": 1430, "failed": ["missing_description", "missing_alt_tags"],
  "cwv": { "lcp": 2.1, "tbt": 180, "cls": 0.06 } }

// legacy audit page (still used by SEO/overview views)
{ "id": "fusehealth-pg-0", "url": "/services/iv-therapy", "clicks": 1204,
  "impressions": 28400, "ctr": 4.2, "speed": 92, "indexed": true,
  "kind": "ok|gone|redirect|noindex", "verdict": "Indexed",
  "title_length": 54, "word_count": 1400 }

// ads campaign (Google Ads API + GA4 join; metrics aggregated over `range`)
{ "id": "fusehealth-cmp-0", "name": "Brand — Search", "platform": "Google Ads|Meta",
  "type": "Search|Performance Max|Retargeting|Prospecting", "status": "enabled|paused",
  "budget_daily": 38, "spend": 1180.2, "impressions": 24800, "clicks": 1140,
  "ctr": 4.6, "cpc": 1.04, "conversions": 64.2, "cpa": 18.4, "conv_value": 5120.5, "roas": 4.34,
  "ga4_key_events": 48.9, "ga4_revenue": 3890.1,
  "lost_is_budget": 19, "lost_is_rank": 8,          // impression share lost, %
  "prev": { "spend": 1050.0, "conversions": 58.1 },   // previous equal-length period
  "adGroups": [{ "id": "...", "name": "Exact — core services", "spend": 402.1, "clicks": 380, "conversions": 22.4, "cpa": 17.9 }],
  "daily": [{ "date": "2026-07-01", "spend": 39.2, "impressions": 820, "clicks": 38, "conversions": 2.1, "conv_value": 168.0, "ga4_key_events": 1.6, "ga4_revenue": 120.4 }] }

// ads search term (Google Ads search_term_view)
{ "id": "fusehealth-st-0", "term": "iv therapy near me", "matchedKeyword": "iv therapy",
  "matchType": "exact|phrase|broad", "campaignId": "fusehealth-cmp-1", "campaign": "Non-Brand — Search",
  "impressions": 1900, "clicks": 82, "cost": 148.6, "conversions": 4.1, "cpa": 36.2,
  "status": "converting|wasted|negative|tracked" }   // derived server-side

// alert
{ "id": "fusehealth-al-2", "ts": "2026-06-28", "kind": "anomaly|ranking|backlink|technical|system",
  "severity": "high|medium|info", "title": "...", "detail": "...", "acknowledged": false }

// kpi (overview)
{ "label": "Total clicks", "value": 18204, "delta": 8.2, "unit": "%|pos" }

// overview pillar (one headline metric per product surface; card deep-links via `target`)
{ "label": "Site health", "target": "pages",          // target = a dashboard tab key
  "valueKind": "num|pos|score|roas|pct", "value": 82, "delta": 3, "deltaUnit": "%|pos|pts",
  "sub": "5 errors to fix", "state": "ok|setup" }       // state:"setup" when AI Optimization isn't configured

// overview module-status card (current state of each tool; `tone` drives the status dot)
{ "label": "Backlinks", "target": "backlinks", "stat": "128 live",
  "sub": "+8 new · −2 lost (7d)", "tone": "ok|warn|bad|setup" }

// overview priority item (an unacknowledged alert tagged with its owning module)
{ "id": "fusehealth-al-2", "severity": "high|medium|info", "kind": "anomaly|ranking|backlink|technical|ads|system",
  "title": "...", "detail": "...", "ts": "2026-06-28",
  "module": { "label": "Positions", "target": "positioning" } }   // kind→module mapping, screen-level deep link

// trend point
{ "date": "2026-07-01", "clicks": 610, "impressions": 12400 }

// usage
{ "budget": 75, "currency": "USD", "month_to_date": 4.31, "est_monthly": 7.90,
  "items": [{ "module": "...", "cadence": "Weekly|Monthly|On demand", "est": 1.92, "note": "..." }] }
```

---

## 3. DataForSEO mapping (what feeds what)

| Dashboard module | DataForSEO endpoint(s) | Notes |
|---|---|---|
| Position Tracking | `serp/google/organic/task_post` + `task_get` (Standard queue) | 1 task per tracked keyword. Store weekly snapshots → `pos`/`prevPos`/`movement`. Competitor positions parsed from the same SERP result. |
| Keywords (volume/KD/CPC/intent) | `keywords_data/google_ads/search_volume` (bulk, ≤1000 kw/req) + `dataforseo_labs/google/bulk_keyword_difficulty` + `dataforseo_labs/google/search_intent` | Monthly refresh is enough — volumes barely move weekly. |
| Keyword Explorer | `dataforseo_labs/google/keyword_ideas` / `keyword_suggestions` / `related_keywords` (Live) — per match type, see §3c | On-demand; returns volume/KD/CPC/intent/SERP info in one call. Expansion cached server-side per (seed, matchType, location). |
| Backlinks | `backlinks/summary` (weekly) + `backlinks/history` + `backlinks/backlinks` with `mode=new_lost` filters | Summary is cheap; full link dump monthly. `rank` = DataForSEO domain rank. |
| Site Audit | `on_page/task_post` (crawl ≤500 pages, JS off) → `on_page/summary` (score, domain checks, totals), `on_page/pages` (per-page checks + OnPage score), `on_page/lighthouse` (LCP/TBT/CLS), `on_page/redirect_chains`, `on_page/non_indexable`, `on_page/duplicate_tags`, `on_page/links` (in-links, depth) | Monthly crawl. Checks catalog maps 1:1 to OnPage `checks{}` booleans; snapshots = stored past summaries for Compare/Progress. | (or `on_page/lighthouse`). |
| Overview KPIs / trend | **Google Search Console API** (clicks/impressions/CTR/position by day) — not DataForSEO | GSC is free; DataForSEO fills rankings/backlinks/audit. |
| Off-site SEO | **GA4 Data API `runReport`** — dims `sessionDefaultChannelGroup`, `sessionSource`, `landingPage`; metrics `sessions`, `engagedSessions`, `engagementRate`, `keyEvents`, `totalRevenue`. Filter to Referral + Organic Social/Video for off-site organic. Per-platform **impressions/CTR** come from each channel's own connector (LinkedIn Marketing API, Reddit, YouTube Data API…), joined by source — GA4 has no impression data. | Same 12h GA4 pull as Ads. $0 (GA4 free); platform impression connectors optional. |
| Ads (all sub-tabs) | **Google Ads API + GA4 Data API** — see §3b | Not DataForSEO. Both APIs are free. |
| Alerts feed | Generated server-side after each sync: position drops ≥3, lost backlinks (rank ≥40), new 404s, GSC anomalies (±30% vs. 28-day mean) | Rule-builder is a **later** milestone. |
| AI summary | OpenAI/Claude call on cron after weekly sync; cache result | |

## 3c. Keyword Explorer match types (DataForSEO Labs)

Each match tab is a different expansion algorithm over the same seed. All are **Live** calls
(no task queue). Pricing: **$0.012/task + $0.00012/row** → 1,000 rows ≈ $0.13.

| Match tab | Endpoint | Algorithm | Notes |
|---|---|---|---|
| **Broad Match** (default) | `dataforseo_labs/google/keyword_ideas/live` | Relevance search over DataForSEO's keyword DB segmented by Google Ads product categories — returns terms in the same category that may NOT contain the seed | Widest net. Accepts up to 200 seed phrases (`keywords[]`). |
| **Phrase Match** | `dataforseo_labs/google/keyword_suggestions/live` | Full-text search: every result contains the seed with extra words before/after/within (any word order) | The long-tail workhorse. Returns volume, 12-mo trend, CPC, competition per row. |
| **Related** | `dataforseo_labs/google/related_keywords/live` | Walks Google's "searches related to" SERP graph outward from the seed (`depth` 1–4) | Semantic neighbors; terms need not contain the seed. |
| **Questions** | `keyword_suggestions` + server filter | Suggestions filtered to `^(how\|what\|why\|when\|where\|is\|are\|can\|does\|do\|will\|which\|who)\b` | One filtered call — Labs supports up to 8 stacked `filters` per request. |
| **Exact Match** | `keywords_data/google_ads/search_volume` | Metrics for the literal seed phrase only | Cheapest; also used for the Overview drawer refresh. |
| **All** | union of `keyword_ideas` + `keyword_suggestions` | Deduped union, cached | Two tasks; dedupe on keyword string server-side. |

**Request payload examples:**

```jsonc
// Broad Match
POST /v3/dataforseo_labs/google/keyword_ideas/live
[{ "keywords": ["semaglutide"], "location_code": 2840, "language_code": "en",
   "include_serp_info": true, "include_clickstream_data": false,
   "limit": 1000, "order_by": ["keyword_info.search_volume,desc"],
   "filters": [["keyword_info.search_volume", ">", 10]] }]

// Phrase Match (long-tail)
POST /v3/dataforseo_labs/google/keyword_suggestions/live
[{ "keyword": "semaglutide", "location_code": 2840, "language_code": "en",
   "include_serp_info": true, "include_seed_keyword": true,
   "limit": 1000, "order_by": ["keyword_info.search_volume,desc"] }]

// Related (semantic)
POST /v3/dataforseo_labs/google/related_keywords/live
[{ "keyword": "semaglutide", "location_code": 2840, "language_code": "en",
   "depth": 2, "include_serp_info": true, "limit": 1000 }]
```

**Caps & caching:** cap initial pulls at **1,000 rows sorted by volume desc** (~$0.13); the
backend caches the expanded set per `(seed, matchType, location)` for 7 days and serves all
filtering/sorting/grouping/pagination from the cache — filter changes never re-hit DataForSEO.
Deeper pulls (`offset`) only on explicit "Load more". KD comes from
`bulk_keyword_difficulty` (batched ≤1000/req) on the cached set; intent from `search_intent`
(same four values as the I/N/C/T badges). Filter state is serialized into the page URL
(`?f=` base64 of the filter JSON) so filtered views are shareable — pure frontend, no API cost.

**Cost note:** DataForSEO's `keyword_difficulty` is its own model — tune KD band cutoffs to
our data; keep the band labels/colors (Very easy 0–14 … Very hard 85–100).

## 3b. Ads mapping (Google Ads API + GA4 Data API)

| Dashboard module | Source | Notes |
|---|---|---|
| Campaign metrics, ad groups | Google Ads API `GoogleAdsService.searchStream` — GAQL on `campaign`, `ad_group` (metrics: cost_micros, impressions, clicks, conversions, conversions_value, search_budget_lost_impression_share, search_rank_lost_impression_share) | 1 op per report. Segment by `segments.date`, store daily rows. |
| Search terms | GAQL on `search_term_view` | Weekly review workflow; negatives written back via `CampaignCriterionService` (or shared set). |
| Budget pacing | `campaign_budget` amount_micros × days-in-month vs. stored daily spend | Computed server-side. |
| Pause/enable, budget edits | `CampaignService.mutate`, `CampaignBudgetService.mutate` | Mutations count 1 op each — negligible. |
| GA4 outcomes & post-click | GA4 Data API `runReport` — dims `sessionCampaignName`, `landingPage`; metrics `sessions`, `engagementRate`, `keyEvents`, `totalRevenue` | Attribution differs from Google Ads by design; show both, never reconcile silently. |
| Meta campaigns | Meta Marketing API (existing connector) | Same daily-row shape. |

**Sync cadence: every 12 hours (06:00 & 18:00 cron).** Per pull: ~6 GAQL reports + ~4 GA4 runReports ≈ 25 ops/day total — 0.2% of the Basic-access 15,000 ops/day quota; GA4 property token quotas are similarly untouched. **API cost: $0** (both APIs are free; developer token required for Google Ads, Basic access is sufficient for a reporting tool — stay reporting-only to avoid RMF). Ads alerts (budget-limited ≥15% lost IS, CPA +30% vs. prior period, disapproved ads, conversion tracking silent >48h) are regenerated after each pull into the `alerts` feed with `kind: "ads"`.

## 4. Sync & cost model (budget: $50–100/mo)

**Default schedule (backend cron):**
- **Every 12h (06:00 / 18:00):** Google Ads GAQL reports + GA4 runReports → upsert daily ads rows, recompute pacing + ads alerts. ($0)
- **Weekly (Mon 06:00):** SERP positions for all tracked keywords + backlinks summary/deltas → regenerate alerts + AI summary.
- **Monthly (1st):** OnPage crawl (≤200 pages/project) + keyword volume/KD refresh.
- **On demand:** Keyword Explorer searches, manual per-module refresh (`POST /sync {scope}`).

**Estimated cost at current scale (~70 keywords, ~50 pages, 3 projects):**
| Item | Unit cost (approx) | Monthly |
|---|---|---|
| SERP Standard, 70 kw × 4.3 wk | ~$0.0015/query | ~$0.45 |
| Backlinks summary weekly ×3 projects | ~$0.02–0.06/call | ~$0.60 |
| OnPage crawl 150 pages/mo | ~$1.25/1000 pages | ~$0.30 |
| Volume/KD refresh monthly | ~$0.05–0.12/batch | ~$0.35 |
| Explorer expansions (~30/mo, ≤1,000 rows) | ~$0.13/search | ~$3.90 |
| **Total** | | **≈ $5–8/mo** |

Even at 10× keyword scale this stays under ~$25/mo — well inside budget. The Settings
page shows a live usage meter (`usage` object); the backend should record actual
DataForSEO charges per call and expose them there. Enforce `budget` as a soft cap:
refuse manual syncs when `month_to_date >= budget`, never block the weekly cron.

## 5. Frontend state the backend replaces

Fixture mode persists user mutations in `localStorage['fuse.mutations.v1']`:
acknowledged alerts, manually added keywords, edited credentials/prefs, last-sync
timestamps, on-demand usage. Each maps 1:1 to a mutation endpoint above — once
`baseUrl` is set, localStorage is no longer used for these.

## 6. Later milestones (agreed, not in v1)
1. Rule-driven alert builder (user-defined thresholds → alert rules engine).
2. AI Visibility page (AI Optimization API: LLM mentions across ChatGPT/Claude/Gemini/Perplexity).
3. Brand monitoring (Content Analysis API: mentions, sentiment, phrase trends).
4. Dark mode.

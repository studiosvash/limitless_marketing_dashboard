# FuseHealth — Design Brief

> **Who this is for:** The designer/engineer redesigning the FuseHealth UI.
> Read this before touching any screen. It defines what the product does, what data
> is actually available per page, and the hard constraints every design must respect.

---

## What This Product Is

An **internal marketing intelligence dashboard** for 2–3 people on the FuseHealth team.
It replaces SEMRush, Google Analytics, Google Search Console, and ad platform dashboards
by pulling all data into one place.

It is **not** a SaaS product. There are no external customers, no sign-up flow, no billing.

**Three user roles:**

| Role | Access |
|------|--------|
| `founder` | Every page |
| `seo` | SEO · Keywords · Pages · Backlinks · Positioning · Insights · Alerts |
| `ads` | Ads · Overview · Alerts |

---

## The One Rule That Governs Every Design Decision

**The dashboard is database-first.** Data is fetched on demand and stored in a local database.
Pages always read from the database — never from live APIs.

What this means in practice:

| Situation | Correct behavior | Forbidden behavior |
|-----------|------------------|--------------------|
| User opens any page | Reads from database, renders instantly | Calls a live API, shows a loading spinner |
| User wants fresh data | Clicks the Refresh button for that page | Automatic background polling or auto-refresh |
| API is rate-limited / slow | Last saved data is shown | Page hangs or errors |
| Sync is running | Progress bar shows per-connector status | Page blocks until sync finishes |

**Why:** The APIs are rate-limited and a full sync takes minutes. Calling them on page load
would make the dashboard slow, burn API quota, and show different data mid-session.
The database is the single source of truth.

---

## Required UI Elements on Every Data Page

Every page that shows data **must** include:

1. **A per-page Refresh button** — triggers sync for only that page's connectors
2. **A global Refresh All button** (in the top bar or sidebar) — syncs every connector
3. **A live progress bar** — appears during any active sync, shows per-connector status
4. **A "last synced" timestamp** — tells the user how fresh the current data is
5. **A graceful empty state** — shown before the first sync has run (no crashes, no blank areas)

---

## Technology Stack (what the design must be compatible with)

| Layer | Technology |
|-------|-----------|
| Frontend rendering | Django templates (server-rendered HTML) |
| Interactivity | HTMX — partial HTML swaps, no full-page reloads |
| CSS | Tailwind CSS (CDN, no build step) |
| Charts | Plotly (rendered client-side from JSON) |
| No JavaScript frameworks | React, Vue, Angular, Svelte are not in the stack |

**Implication for design:** Every interactive element (filter, date range picker, refresh button,
tab switch) must work as an HTMX partial swap or a standard form POST. Complex SPA-style
interactions that require client-side state are not available.

---

## The 10 Dashboard Pages

### 1 · Overview
**Status:** Live  
**Data sources:** GSC (seo_daily) + GA4 (seo_daily) + keyword_rankings + ad_metrics_daily  
**What it shows:**
- KPI cards with period-over-period deltas: clicks, impressions, CTR, avg position, sessions, conversions
- 30-day trend chart (clicks + sessions over time)
- AI-generated summary of the week's performance
- Top pages by clicks
- Top keywords by clicks
- Ads summary (spend, impressions, conversions) — **blocked until ad credentials added**
- Competitor positioning snapshot

**Design constraints:** KPI cards must show both current value and delta vs previous period.
Multi-site selector (dropdown) is session-persisted — changing it reloads the page for the selected site.

---

### 2 · SEO
**Status:** Live  
**Data sources:** GSC (seo_daily) + GA4 (seo_daily) + technical_issues (DataForSEO OnPage)  
**What it shows:**
- Metrics broken down by country and by device
- Recent anomalies (automated detection of unusual drops/spikes)
- Technical issues list (crawl errors, missing tags, etc.) — **partial: DataForSEO balance negative**

**Design constraints:** Country/device filter must use HTMX partial swap (not full-page reload).
Technical issues section must show a graceful "DataForSEO balance required" state when blocked.

---

### 3 · Keywords
**Status:** Live  
**Data sources:** GSC keywords (keyword_rankings) + DataForSEO enrichment (search volume, KD, CPC)  
**What it shows:**
- All tracked keywords with: current position, clicks, impressions, CTR, search volume, keyword difficulty, CPC, intent
- Quick Wins filter (position 4–20, high volume)
- Striking Distance filter (position 2–10)
- Keyword Health Score

**Design constraints:** Search volume, KD, and CPC columns show `—` when DataForSEO balance is
negative (data is missing, not zero). The table must handle null values gracefully.
Keywords come from `keywords.txt` — there is no in-app keyword management UI yet.

---

### 4 · Positioning
**Status:** Live  
**Data sources:** GSC keywords + DataForSEO competitors  
**What it shows:**
- Your rank vs each tracked competitor per keyword
- Date-over-date rank change
- Competitor domain list (discovered automatically, editable in Settings)
- Shared keywords count, avg position, estimated traffic value per competitor

**Design constraints:** Competitor rankings grid is the primary feature; the domain-level
competitor map sits below it. Competitor list is editable in Settings, not here.

---

### 5 · Ads
**Status:** BLOCKED — no ad platform credentials  
**Data sources:** ad_metrics_daily (Google Ads + Meta + LinkedIn)  
**What it shows (when unblocked):**
- Daily spend, impressions, clicks, conversions, ROAS per platform
- Platform comparison (Google vs Meta vs LinkedIn)
- Campaign-level breakdown

**Design constraints:** Page must currently show a clear "Ads credentials not yet connected"
state. Design should anticipate a platform toggle (Google / Meta / LinkedIn) tab pattern.

---

### 6 · Alerts
**Status:** Live  
**Data sources:** GSC (seo_daily) + GA4 + PageSpeed (pagespeed) + indexing_status  
**What it shows:**
- Automated anomaly alerts (drops/spikes in clicks, sessions, CTR)
- PageSpeed scores: performance, SEO, accessibility, best-practices (0–100)
- Core Web Vitals: LCP, CLS, INP, FCP, TTFB, SI
- Indexing status per URL (indexed, not indexed, coverage state)
- Technical issues

**Design constraints:** Alerts must be color-coded by severity (high/medium/low).
PageSpeed scores below 50 = red, 50–89 = amber, 90+ = green.

---

### 7 · Pages
**Status:** Live (partial — sitemap connector needs `FRAMER_SITEMAP_URL`)  
**Data sources:** gsc_pages + GA4 (sessions) + url_inspection + pagespeed + sitemap/webflow/wordpress  
**What it shows:**
- All indexed pages with: clicks, impressions, CTR, avg position, sessions, CMS type
- Indexing status per page
- PageSpeed score per page
- Technical issues per page (robots.txt blocks, crawl errors)

**Design constraints:** CMS type column values: `blog`, `service`, `page`, `framer`, `webflow`, `wordpress`.
Pages are discovered from GSC — not necessarily all pages on the site.

---

### 8 · Backlinks
**Status:** BLOCKED — DataForSEO balance negative  
**Data sources:** backlinks (DataForSEO)  
**What it shows (when unblocked):**
- Referring domain, target URL, anchor text, dofollow/nofollow, domain rank, first/last seen

**Design constraints:** Must show a "DataForSEO balance required" empty state for now.

---

### 9 · Insights
**Status:** Live (manual entry)  
**Data sources:** Insight Django model (team notes, not API data)  
**What it shows:**
- Team-authored insights: date, impact level, description, site URL, author
- No API sync — data entered manually by the team

**Design constraints:** Insight cards are the primary UI; no refresh button needed here.

---

### 10 · Settings
**Status:** Live  
**Data sources:** Site model + SyncLog + connector status  
**What it shows:**
- Site selector (switch between tracked websites)
- Connector status panel (working / errored / never run / last synced)
- Tracked Competitors editor (textarea + discovered-domain chips → saves to DB)
- Per-page refresh buttons

**Design constraints:** This is a configuration page, not a data page.
The connector status panel must show real-time state from the database.

---

## Data Freshness & Rate Limit Facts (design must accommodate these)

| API | Data delay | How fresh is the data shown? |
|-----|-----------|------------------------------|
| Google Search Console | 3-day delay | Shows data up to D-3 |
| Google Analytics 4 | Same-day (approx) | Yesterday's sessions |
| DataForSEO SERP | On-demand | Reflects last sync run |
| PageSpeed | On-demand | Reflects last sync run |
| LinkedIn token | Expires every 60 days | Manual re-auth required |

**Implication:** The "last synced" timestamp is important — the user needs to know how old their
data is at a glance on every page.

---

## What Is Already Built (do not redesign these as new features)

| Built | What it is |
|-------|-----------|
| Base template + sidebar + topbar | Django `base.html` with Tailwind design tokens |
| All 10 pages | Working views, URL routing, data queries |
| Role-based auth | Login page, role matrix, middleware |
| Sync engine | `POST /sync/all/`, `POST /sync/page/<page>/`, `GET /sync/status/` |
| HTMX progress bar | Polls `/sync/status/` every 2s during a refresh |
| Multi-site selector | Dropdown in topbar, session-persisted |

The redesign is **visual and structural** — it is not adding new features. Every component
you design has a working backend behind it. The goal is a better UI over the same data.

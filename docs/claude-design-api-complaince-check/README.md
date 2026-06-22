# FuseHealth — Designer Onboarding README

> **Who this is for:** The designer/engineer redesigning FuseHealth UI using Claude.
> Read this first. Then use `AI_TECHNICAL_GUIDE.md` to verify specific design decisions.

---

## Start Here: What You're Redesigning

FuseHealth is a working internal marketing dashboard. All 10 pages have live backends —
SEO data, keyword rankings, Google Analytics, PageSpeed scores, and more are all connected
and pulling real data.

Your job is to **redesign the UI** — not rebuild the logic. Better layouts, clearer data
presentation, stronger visual hierarchy. The data layer does not change.

**Before designing anything, read these two files (in order):**

1. `docs/handoff/DESIGN_BRIEF.md` — what every page shows, what's blocked, and the hard rules
2. `docs/handoff/API_SOURCES.md` — official docs for every API the dashboard connects to

---

## The One Rule You Cannot Break

**The dashboard is database-first.** Pages always read from a local database — they never
call a live API. Fresh data is only fetched when the user clicks a Refresh button.

This means:
- Every data page needs a visible Refresh button
- No design should imply real-time data (no "live" indicators that suggest instant updates)
- Loading states are only for when a sync is actively running — not for page loads
- Empty states must be designed (before the first sync, there is no data)

If you design a component that would require a live API call on page load, it will not work.
Use the AI verification process below to catch these before implementation.

---

## How to Use Claude to Verify a Design

Use this process whenever you're unsure whether a component can be built given the actual APIs.

### Step 1 — Identify the data the component needs

For each component you're designing, write down:
- What data fields it displays (e.g. "keyword, position, search volume, trend sparkline")
- Where that data comes from (check `DESIGN_BRIEF.md` → the page's "Data sources" section)
- How fresh the data needs to be (check the "Data Freshness" table in `DESIGN_BRIEF.md`)

### Step 2 — Open `AI_TECHNICAL_GUIDE.md`

Copy the **Component Verification Prompt** from that file.

### Step 3 — Fill in the template

Replace every `[PLACEHOLDER]` in the template with:
- Your component description
- The data fields it needs
- The connector(s) that feed it (from `DESIGN_BRIEF.md`)
- The relevant section of the official API docs (from `API_SOURCES.md`)

### Step 4 — Paste into Claude

Start a new Claude conversation. Paste the filled-in template and send it.

### Step 5 — Read the verdict

Claude will tell you:
- Which fields are **available** from the API as-is
- Which fields are **unavailable** (not in the API response — would need a different source)
- Which fields are **blocked** (API works but credentials/balance are missing)
- Any **constraints** the design must respect (rate limits, data delays, null values)

### Step 6 — Adjust the design

If a field is unavailable, either remove it or swap in an available alternative.
If a field is blocked, design a graceful "not yet connected" empty state for it.

---

## Common Design Pitfalls (what Claude will flag)

| Design idea | Why it fails | What to do instead |
|-------------|-------------|-------------------|
| "Show real-time keyword position" | GSC has a 3-day delay; no live ranking API | Show "Position as of [last sync date]" |
| "Show ROAS for ads" | ROAS is not returned by any connected ad API | Show spend, clicks, conversions separately; note ROAS is not yet tracked |
| "Show search volume for every keyword automatically" | Requires DataForSEO (balance negative) | Show `—` with a "DataForSEO required" tooltip |
| "Auto-refresh every 60 seconds" | Violates the database-first contract; would burn API quota | Use a manual Refresh button only |
| "Show competitor ad spend" | Not available from any connected API | Remove from design |
| "Show LinkedIn impressions in real time" | LinkedIn token expires every 60 days; credentials not yet connected | Design a "reconnect" empty state |
| "Trend sparkline for every metric" | Only available if multiple days of data exist in the DB | Design a graceful single-value fallback |

---

## Pages That Are Currently Blocked

These pages exist in the codebase but show empty states because credentials are missing:

| Page | Blocked by | What the design must include |
|------|-----------|------------------------------|
| Ads | No Google Ads / Meta / LinkedIn credentials | "Connect your ad accounts" empty state with instructions |
| Backlinks | DataForSEO balance negative | "Top up DataForSEO balance to unlock" empty state |

Design these pages fully — they will be unblocked when credentials are added.
But every blocked field or section needs a designed empty/locked state, not a blank space.

---

## What's Already Built (don't propose replacing these)

The following are working, tested, and not changing:

- Django backend, URL routing, all views
- Role-based login (founder / seo / ads)
- HTMX sync engine (Refresh buttons, progress bar, `/sync/status/` polling)
- Multi-site selector (top bar dropdown)
- All 10 page data queries

Your redesign works **on top of** this. You're changing how the data looks — not how it's fetched.

---

## Questions to Ask Claude During Design Review

These prompts work well when pasted into Claude with your design spec:

- *"Given the API constraints in `API_SOURCES.md`, can this component be built as designed?"*
- *"What empty states does this page need before the first sync runs?"*
- *"Which fields on this table will be null when DataForSEO balance is negative?"*
- *"Does any part of this design require a live API call on page load?"*
- *"What does the HTMX partial swap boundary need to be for this filter interaction?"*

---

## File Map for This Handoff Package

| File | Purpose |
|------|---------|
| `DESIGN_BRIEF.md` | Product overview, page-by-page data map, hard constraints |
| `API_SOURCES.md` | Official docs URLs for all 12 APIs, credentials needed, status |
| `BOSS_README.md` | This file — how to use the package |
| `AI_TECHNICAL_GUIDE.md` | Claude prompt templates for design verification |

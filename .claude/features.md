# Features — The Product Manual

> Everything the dashboard does today, page by page. Written from the code, not from intent.
> Where a screen is built but its data source does not exist yet, that is stated plainly so
> nobody demos a placeholder as a finished feature.

---

## 1. What this product is

An internal SEO, content and paid-media intelligence dashboard for a small team (2–3 users). It
pulls marketing data from Google Search Console, Google Analytics 4, PageSpeed Insights,
DataForSEO and (optionally) Google Ads into a local database, and presents it as decision-shaped
pages: what changed, what is broken, what to do next.

**The one contract that governs the whole product:**

1. Pages read **only** from the database. Opening a page never waits on an external API.
2. **Refresh** is the only path that calls external APIs. It writes to the database; the page
   then re-reads it.
3. Every page that has its own data source also has its **own** refresh button.
4. Every refresh shows a **live progress bar** with the connector currently running and an ETA.
5. Between refreshes the user sees the **last saved data**. Stale-but-instant beats
   fresh-but-frozen.

Three features deliberately break rule 1 because they are explicit user lookups rather than page
renders: the **Keyword Explorer**, **Domain Overview**, and the **live SERP drawer**. Each calls
its API only when the user presses a button.

---

## 2. Getting in

### Login (`/login/`)

A single server-rendered page (the only one left). Fields: **Email or Username**, **Password**.
Either identifier works — `EmailOrUsernameModelBackend` tries username first, then email,
case-insensitively.

- **Success** → redirected to `/` (the SPA), or to `?next=` if present.
- **Failure** → an inline rose-tinted banner: *"The username or password is incorrect."*
- Already logged in → bounced straight to the dashboard.
- Any unauthenticated URL redirects here, because `LoginRequiredMiddleware` protects everything.

Accounts are created three ways: `python manage.py seed_users` (founder/seo/ads), the Settings →
Team tab (direct creation or email invite), or the Django admin at `/admin/`.

### Accept invitation (`/#/accept-invite?token=…`)

A full-screen modal that intercepts the SPA before anything else renders. It validates the token
against `GET /api/auth/invite-status`, then asks for a **username** and **password**.

- Shows who invited you and the role you will get.
- **Invalid / expired / already-used token** → a red "Invalid Invitation" panel with a
  *Return to Dashboard* link.
- Password must be ≥ 8 characters; username must be free.
- **Success** → a green "Account Activated!" panel, then a redirect after 2 seconds.

This modal is the normal entry point. *Invite a teammate* creates a `UserInvitation` row and
emails a `/#/accept-invite?token=` link — it does **not** create the `User`, and it never sends a
password. The account is created here, by the invitee, with a password only they have chosen.

*(Until 2026-07 this flow emailed a generated temporary password in plaintext and a plain login
link, created the User immediately, and wrote no invitation record — so invitees never appeared
in the pending list and could not be revoked. Do not reintroduce that shape.)*

### Change password

The padlock icon at the bottom of the sidebar opens a modal: **Current Password**, **New
Password** (≥ 8 chars), **Confirm New Password**. Validation is client-side first (all fields
present, ≥ 8 chars, both new fields matching), then server-side. Errors render in a red box,
success in a green box, and the modal closes itself after 2 seconds. The session survives the
change.

### Logout

The exit icon beside it clears `localStorage` and `sessionStorage`, then navigates to `/logout/`.

---

## 3. The shell

Every screen shares the same three-part chrome.

### Sidebar (240 px, fixed)

**Brand block** — the project's display name and an indigo mark.

**Back / forward buttons** — an *in-app* history, independent of the browser's. It records a
snapshot of `{tab, projectId, research, kwSeg, blFilter, alFilter, auSub, aiSub}`, so stepping
back restores not just the page but the filter you were on. Arrows grey out at the ends.

**Navigation tree**

```
Overview
SEO                      ▾  (expandable group)
  ├ Domain Overview
  ├ Keywords
  ├ Position Tracking
  ├ Backlinks
  ├ Off-site SEO
  ├ Site Audit
  └ AI Optimization
Ads                      ▾  (expandable group)
  ├ Campaigns
  ├ Search Terms
  └ Attribution
Alerts                      (red badge = unacknowledged count)
Settings                    (hidden from Analysts)
```

Groups auto-expand when you navigate into one of their children. The Alerts badge counts
unacknowledged items of severity `high` or `medium` only — `info` never nags.

**Footer** — a Data Freshness pill (`Weekly · Mon`, flipping to `Just now` after a sync), the
current user's initials, username and role, plus the change-password and logout icons.

### Topbar (64 px)

- **Title + subtitle**, per page, suffixed with the active domain.
- **Site selector** — a globe-icon `<select>` of every active project. Switching sites resets
  page-level filters, refetches the current tab and the alerts badge, and remembers the choice
  in `localStorage` across reloads.
- **Add a site (+)** — a popover with *Domain* (required) and *Display name* (optional).
  Validates the domain shape client-side and rejects duplicates before calling the API. On
  success it switches to the new site, shows a toast, and **auto-starts the initial full sync**
  using the `sync_task_id` the backend returned — so the progress bar appears without a second
  click. If Search Console does not recognise the domain the toast says so and points at
  Settings. `Enter` submits, `Escape` closes.
- **Range switch** — `7d` / `30d` / `90d`. Only refetches on pages that are range-aware
  (Overview, Position Tracking, Off-site, and the four Ads pages).
- **Page refresh button** (green, "Fetch …") — appears only on pages that map to a sync scope.
  Spins and disables while that scope is running.
- **Refresh all button** (indigo) — runs all 14 connectors.

### Global overlays

- **Sync banner** — appears above the page content during any refresh: scope, current step,
  percentage, ETA and an animated progress bar. The ETA is measured from real elapsed progress
  after the first few seconds (before that it assumes 5 minutes for `audit`/`all`, 1 minute
  otherwise).
- **Error state** — *"Couldn't load this view"* with the message and a **Retry** button that
  forces a refetch.
- **Loading skeleton** — four pulsing KPI blocks plus two content blocks, shown on first load of
  a tab.
- **Toast** — a dark pill at the bottom centre, auto-dismissed after 2.6 s. Used for every
  confirmation.
- **Keyword lists modal** — the saved keyword lists (see §5).
- **Page detail drawer** — the Site Audit page inspector (see §9).

### Keyboard & accessibility

- `Enter` / `Space` activate any element carrying `role="button"` or `role="switch"`.
- `Escape` closes the add-site popover, the negative-keyword menu, and the send/export menus.
- A `MutationObserver` re-sweeps the DOM after every render, promoting leaf clickable elements
  (cursor: pointer, no interactive descendant) to `role="button"` with `tabindex="0"`.
- A `:focus-visible` outline is forced on for keyboard users only.
- `prefers-reduced-motion` collapses every animation and transition to ~0 ms.

---

## 4. Overview

**Purpose.** The morning page. One screen that answers: is traffic up or down, what is broken,
and what should I look at first.

**Business value.** Replaces a manual sweep of five tools with a single ranked list of what
changed and who owns it.

**Navigation.** Sidebar → Overview. Also the landing page after login and the fallback when an
Analyst tries to open Settings.

**Data source.** `GET /api/projects/<slug>/overview?range=` — range-aware.

### Sections

| Section | What it shows | Interaction |
|---|---|---|
| **Pillar cards** (5) | Organic clicks, Avg. position, Site health, Paid ROAS, AI visibility. Each has a value, a delta chip and a one-line subtitle. | Clicking a card navigates to the owning page. |
| **Priority feed** (≤ 6) | Unacknowledged alerts, most severe first, each tagged with its module (SEO, Positions, Backlinks, Site Audit, Ads, System) in that module's colour. | Clicking a row jumps to that module. Empty state when nothing is outstanding. |
| **Module cards** (7) | SEO Performance, Keywords, Position Tracking, Backlinks, Site Audit, AI Optimization, Paid Media — each with a headline stat, a sub-stat and a status dot. | Clicking navigates. |
| **Traffic trend** | Dual-axis clicks + impressions line chart over the selected range, with hover tooltips, y-tick labels on both axes and ten x-axis date ticks. | Hovering a vertical zone shows exact values for that day. |
| **Weekly summary** | Three coloured boxes — **Wins**, **Critical**, **Watch** — populated from the AI-generated summary. Boxes with no items are omitted entirely. | *Copy summary* copies a plain-text version formatted for email or Slack. |
| **Top pages** | Up to 6 landing pages by clicks, with impressions and CTR. | *Export CSV*. |

### Edge cases

- **Paid ROAS and AI visibility always read "Set up"** — they are hard-coded to the setup state
  because neither has a wired data source.
- **Site health shows "Set up"** until the Site Audit page has data; once it does, the pillar and
  the Site Audit module both show the same 0–100 score (a test enforces that they never diverge).
- **The Weekly summary is absent** when `OPENAI_API_KEY` is unset or no summary has been
  generated — the section simply does not render.
- The newest day of data is excluded from the current period by design, so a same-day refresh
  will not move the KPI numbers.

**Permissions.** All roles.
**Related pages.** Every module and pillar links onward; the priority feed links to Alerts.

---

## 5. Keywords

**Purpose.** Two jobs in one screen: understand the keyword portfolio you already rank for, and
research new keywords to add to tracking.

**Business value.** The Explorer is the control point for API spend — only keywords you
explicitly *Track* are ever sent to the paid per-keyword DataForSEO endpoints.

**Navigation.** Sidebar → SEO → Keywords.
**Data source.** `GET /api/projects/<slug>/keywords` (always a 30-day window, not range-aware),
plus `POST /api/research` on demand.

### 5a. Keyword Explorer (top of page)

**Form:** a seed-keyword input (comma-separated) and a location `<select>`. `Enter` or the
**Search** button runs the research; the button label becomes *"Searching…"* while in flight.

**Match-type tabs:** All · Broad Match · Phrase Match · Exact Match · Questions · Related.
Each tab states which DataForSEO Labs algorithm produced it and an estimated pull cost — filters
run over the already-fetched set and cost nothing.

**Filter chips** (each opens a small popover):

| Chip | Options |
|---|---|
| Volume | Any · 101+ · 1,001+ · 10,001+ |
| KD | Any · Very easy–Easy (0–29) · Possible (30–49) · Difficult (50–69) · Hard+ (70–100) |
| Intent | Informational · Navigational · Commercial · Transactional (multi-select) |
| Include | comma-separated terms, all of which must appear |
| Exclude | comma-separated terms, none of which may appear |

A **Reset** control appears whenever any filter is active.

**Grouping sidebar.** Tokenises the visible keywords, drops seed words and stop-words, and lists
the words appearing in ≥ 2 keywords — sortable **By number** or **By volume**. Clicking a group
filters the table to it.

**Results table.** Checkbox · Keyword · Volume · KD (coloured bar) · CPC · Intent badge ·
12-month sparkline (green if trending up) · SERP-feature count · *Tracked* badge.
Clicking a row opens the **keyword drawer**: volume, KD with a plain-English label
(Very easy → Very hard), CPC, intent, a large sparkline, SERP features, a link to the live Google
SERP, and a **Track in Position Tracking** button.

**Bulk actions** (enabled once rows are selected):

- **Select all** toggles every visible row.
- **Copy** — keywords to clipboard, one per line.
- **Send keywords ▾** →
  - *Position Tracking* → pick any project; the keywords are saved to that project's tracked list
    and the Keywords/Positioning/Overview caches are invalidated so the numbers update
    immediately.
  - *Keyword list* → add to an existing local list, or create a new one by name.
- **Export ▾** — CSV or Excel-readable `.xls`. Exports the selection, or all visible rows when
  nothing is selected. The button label tells you which: `(3)` vs `(all 87)`.

**Keyword lists** are stored in the browser's `localStorage` (`fh_keyword_lists`), not on the
server. The lists modal (opened from the toolbar) lets you rename-free browse, remove individual
keywords, **Send to tracking**, or delete a list. A default list *"Priority targets"* is created
on first load.

### 5b. Portfolio view (below the Explorer)

**KPI row:** Total keywords · Avg. position · Total volume · Total clicks.

**Two distribution cards:** Search Intent (Informational / Commercial / Transactional /
Navigational) and Keyword Difficulty (Easy 0–29 / Medium 30–59 / Hard 60+), each as a labelled
bar with counts.

**Segment tabs**, each with a live count and an explanatory hint + recommended action:

| Tab | Rule | Suggested action |
|---|---|---|
| All | everything tracked | — |
| ⚡ Quick Wins | position 4–10 **and** already earning clicks | improve meta titles, add internal links, expand depth |
| 🎯 Striking Distance | position 11–20 | refresh content, link from top pages |
| 📉 Declining | dropped ≥ 2 positions since the last sync | check SERP changes and competitors |
| 👀 High Imp, Low CTR | ≥ 100 impressions, < 2 % CTR | rewrite titles and meta descriptions |

**Keyword table.** Keyword (with its ranking URL, or *"not ranking yet"*) · Intent · Position
badge (colour-banded: top-3 green, 4–10 blue, 11–20 amber, beyond grey) · Change (`▲ n` / `▼ n` /
`new`) · Volume · sparkline · KD bar · Clicks. Sortable by position, volume, KD or clicks.

### Edge cases

- **Empty state** — when nothing is tracked yet, the portfolio collapses to a setup panel; the
  Explorer stays usable so you can populate it.
- Rows added manually show a *manual* marker and have no position until the next positions sync.
- Sparklines are always flat/empty — no monthly-volume history is stored for tracked keywords.
- If DataForSEO is unreachable the Explorer returns **zero rows with an error message**, never
  invented data.

**Permissions.** All roles.
**Related pages.** Position Tracking (tracking destination), Domain Overview, Overview.

---

## 6. Domain Overview

**Purpose.** Competitive reconnaissance — look up any domain or individual URL and see what it
ranks for.

**Business value.** Answers "what is this competitor winning on?" without leaving the dashboard.

**Navigation.** Sidebar → SEO → Domain Overview. Also reached automatically from the Position
Tracking SERP drawer's *Analyze* action, which pre-fills the URL and runs the lookup.

**Data source.** `POST /api/domain-overview` → DataForSEO Labs `ranked_keywords`. Results are
cached server-side for 24 hours per (target, location).

**Sections.** A search input (`Enter` or button), three metric cards — **Organic traffic**
(estimated), **Traffic value**, **Ranked keywords** — and a **Top Organic Keywords** table:
Keyword · Intent badge · Position badge · Volume · CPC · Estimated traffic · Ranking URL.

**Edge cases.** A path in the input (`example.com/blog`) filters results to that page. Empty
input does nothing. Failures render an inline error message and the previous results are cleared.

**Permissions.** All roles. **Related pages.** Keywords, Position Tracking.

---

## 7. Position Tracking

**Purpose.** Track where you rank week to week, and how that compares to competitors.

**Business value.** The retained-client reporting surface — movement, distribution and
head-to-head position by keyword.

**Navigation.** Sidebar → SEO → Position Tracking.
**Data source.** `GET /api/projects/<slug>/positions?range=` — range-aware. Also
`POST /api/live-serp` on demand.

This page has **two views**.

### 7a. Project list (default)

A search box, an "All projects" filter, and a row per project: name/domain, location, device,
tracked-keyword count, visibility bar (derived from average position), improved/declined counts,
and last-updated. Clicking a row opens that project's workspace.

**+ New project** opens the **Create SEO Project wizard** — four steps with a progress rail:

1. **Site** — domain (required) and display name.
2. **Tracking area** — search engine (Google / Bing), language, location (searchable, backed by
   a ~1 MB US-cities dataset), device (Desktop / Mobile).
3. **Keywords** — paste a list, or pick one of your saved keyword lists.
4. **Competitors** — up to 5 domains, added with `Enter` or a button, removable as chips.

**Finish** creates the project, saves the tracking-area choices and competitors, sends the
keywords to tracking, and drops you into the new workspace. Adding a domain that already exists
is caught with a toast instead of an error.

Search engine, device and language are **stored on the `sites` row** (`search_engine`, `device`,
`language`) and read back by the workspace header and the Edit modal. They used to be collected
and silently discarded. They remain a **recorded preference, not a sync parameter**: the SERP
connectors still query Google, United States, English, desktop as literals.

The Keyword Explorer's *"create a new project and send these keywords"* path enters the same
wizard with step 3 pre-filled.

### 7b. Project workspace

Header: project name, then domain · search engine · device · language · location — all read from
the stored row — plus **Edit**, **Delete** and **Refresh**.

**Edit Project Settings** modal — display name, engine, device, language, location, competitor
chips, and a full-text keyword list (one per line). The three selects are seeded from the stored
row and saved back to it. Saving replaces the tracked keyword list wholesale, saves competitors,
location and the tracking-area choices, then automatically starts a `positions` sync.

Three workspace tabs:

**Landscape**
- KPI row: Tracked keywords · Avg. position · Est. traffic · Impressions.
- **Rankings Distribution** — a stacked bar of Top 3 / 4–10 / 11–20 / 21–100 with a legend.
- **Movement** counters: Improved · Declined · Added · Lost.
- **Biggest Movers** — up to 8 keywords with was → now, a coloured change chip and volume.
- **Keyword Opportunities** — the top 25 keywords to target next: keyword, your position, an
  opportunity-type chip (Quick Win 4–10 · Rising, improved ≥2 · Striking Distance 11–20 ·
  Content Gap), search volume, KD, Est. gain and a 0–100 score. Hovering a row shows the
  `rationale` — the arithmetic that produced the score, in words. Written to
  `keyword_opportunities`, which nothing had ever filled. **Est. gain is "—" for every row**, and
  the card says why: there is no real position→CTR curve to convert a rank change into clicks.
  Keywords already in the top 3, and keywords with neither a position nor a volume, are not
  scored at all.
- **All Tracked Keywords** — keyword, position badge, delta (`▲ +n`, `▼ −n`, `NEW`), volume,
  clicks, KD bar, CPC, intent badge, ranking URL.

**Overview**
- **Competitor Map** — the domain-level aggregate of the same captured SERP rows the grid
  renders: a scatter placing you and each competitor by how much of your captured keyword set
  they appear on (x) against their average position (y), bubble size = top-10 count, over a
  table of keywords / coverage / avg position / top 10 / ahead-of-you / visibility. Head-to-head
  is counted only where both domains have a real captured position. With no captured rows it
  renders an empty state with a capture button — **nothing is estimated to fill it**.
- Per-domain **visibility score cards** (you + each competitor), each with a colour swatch and a
  checkbox that toggles the domain in and out of the chart.
- A multi-series visibility line chart over six months.
- A **competitor grid**: one row per keyword, one column per domain, each cell a position badge
  with a day-over-day diff arrow. Clicking a cell opens a URL popover with a copy button.
  Clicking the SERP icon opens the **live SERP drawer** — a real-time top-15 organic result list
  for that keyword and location, with your own domain highlighted and an *Analyze* action that
  hands the URL to Domain Overview.

**Pages**
- Keywords rolled up by ranking URL: URL, keyword count, an intent mix bar, estimated traffic,
  average position, total volume. Expanding a row lists its keywords.

### Edge cases

- **Empty state** when nothing is tracked, with a fetch prompt.
- **Competitor positions are never estimated.** The grid used to synthesise a position from each
  competitor's average plus a deterministic hash offset whenever no SERP capture existed; that
  was removed. A pair with no captured row renders `—`, and the Competitor Map renders an empty
  state rather than a picture. Do not reintroduce it in any form.
- The Overview tab's visibility trend, deltas and the Pages tab's traffic/change figures are
  **derived approximations**, not stored history.
- This page performs a **live DataForSEO lookup** to backfill missing volume/KD, so it can be
  slower than other pages on first load after adding keywords.
- **Delete project** works (fixed 2026-07 — it previously called `FuseAPI.delete`, which does not
  exist; the transport exposes `del`). Failures now surface via `.catch()` instead of throwing
  silently. Note the endpoint hard-deletes the `Site` row but leaves analytics rows keyed on the
  old `site_id` string in place.

**Permissions.** All roles. **Related pages.** Keywords, Domain Overview, Backlinks.

---

## 8. Backlinks

**Purpose.** Understand who links to you, how authoritative they are, and where competitors have
links you do not.

**Navigation.** Sidebar → SEO → Backlinks. **Data source.** `GET /api/projects/<slug>/backlinks`.

**Five sub-tabs:**

1. **Overview** — Authority Score gauge with a delta, referring domains, total backlinks,
   dofollow %, broken links, spam score; a new/lost bar chart by month; a link-type donut
   (Text / Image / Redirect); an authority-distribution histogram (0–20 … 81–100); and the top
   anchors by share.
2. **Backlinks** — the link table: source page title, source URL, anchor, target URL, domain
   rank chip, spam score, dofollow/nofollow, first-seen, and NEW/LOST/BROKEN badges. Two filter
   rows: status (All · New · Lost · Broken) and follow type (All links · Dofollow · Nofollow).
   Capped at 60 rows.
3. **Referring Domains** — domain, authority chip, backlink count, links-to-us, follow type,
   first-seen, category.
4. **Anchors** — anchor text, classified type (Branded / URL / Keyword / Generic / Empty),
   backlinks, referring domains, dofollow %.
5. **Link Gap** — a matrix of you vs each tracked competitor per domain, with an opportunity
   rating (High / Medium / Low / Have it). A toggle restricts the view to gaps only (domains you
   lack that ≥ 2 competitors have).

**Edge cases.** Empty state when no backlinks are stored. ⚠️ **The Backlinks table rows are
generated deterministically from the referring-domain list** — page titles, source paths, anchors
and NEW/LOST/BROKEN flags are synthesised, not real link records. `firstSeen`, `spam`, `isNew`
and `category` on referring domains are fixed placeholder values. Treat the Overview and
Referring Domains tabs as directional and the Backlinks tab as illustrative until a richer
backlink feed is wired in.

**Permissions.** All roles. **Related pages.** Off-site SEO (referrers), Position Tracking.

---

## 9. Site Audit

**Purpose.** The technical health of the site: what is broken, why it matters, and how to fix it.

**Business value.** Turns raw Lighthouse and Search Console output into a prioritised,
assignable work list with fix instructions.

**Navigation.** Sidebar → SEO → Site Audit. **Data source.**
`GET /api/projects/<slug>/audit` + `POST /api/projects/<slug>/audit/toggle-check`.

**Six sub-tabs:**

### Overview
- A conic-gradient **health gauge** (0–100) with a verdict word: Good ≥ 80, Needs work ≥ 60,
  else Poor. The score is `60 % average mobile Lighthouse performance + 40 % share of pages
  indexed`.
- A page-status bar and breakdown: Healthy · With issues · Broken (4xx/5xx) · Redirected ·
  Blocked. Each row jumps to Crawled Pages.
- **Severity totals** — Errors / Warnings / Notices as three clickable cards that deep-link into
  the Issues tab pre-filtered.
- **Thematic Reports** — a score card per category (Performance, SEO, Accessibility, Best
  Practices, Indexing, Crawlability, Content, HTTPS, Internal Linking, URL structure) with a
  count of failing checks. Clicking filters Issues to that category.
- **Core Web Vitals** — LCP, TBT and CLS, each with its p75 value, a Good/Needs work/Poor verdict
  against Google's published thresholds, and a good/mid/poor distribution bar. ⚠️ **TBT reads
  "—"** — it is no longer estimated from unrelated paint timings, and the connector does not yet
  persist a real Total Blocking Time. LCP and CLS are real.
- **Domain Checks** — six checks run **during sync**, not at request time: SSL certificate (with
  days to expiry), sitemap.xml, robots.txt (with rule count), HTTP/2, www-redirect consolidation,
  and llms.txt. The page reads the stored result, so opening Site Audit never waits on the
  network. Before the first sync the card shows an empty state with a *Run a Crawl Now* action.
- **Top Issues** — the six highest-impact failing checks.

### Issues
Severity filter (All / Errors / Warnings / Notices / Hidden), a category chip row, and a search
box. Each issue row expands to show up to 8 affected pages (URL, page score chip, status), a
**How to fix** paragraph written for that issue type, an **Export** action for the full page
list, and a **Hide this check / Restore check** toggle. Hidden checks are excluded from the
totals and from Overview's error count, and persist per project.

### Crawled Pages
Two views. **Table**: URL, score chip, HTTP status chip, an `nE · nW · nN` issue summary, crawl
depth, in-links and load time, filterable by URL and sortable on five columns, capped at 40 rows
with a clear note when more exist. **Tree**: a folder rollup with page counts, average score and
issue counts.

Clicking a row opens the **page detail drawer**: score, status, six stats (crawl depth, in-links,
load time, internal links, external links, word count), Core Web Vitals, and the list of failed
checks — each of which jumps back into the Issues tab focused on that check.

### Statistics
Two averages (page score, load time) plus three distribution charts: HTTP status codes, crawl
depth and load time bands.

*"Avg. internal links", "Avg. word count" and the "Content length" chart were **removed**, not
blanked — they were computed from `performance_score × 0.4` and `fcp_ms × 1.5`, i.e. a Lighthouse
score and a paint timing relabelled as a link count and a word count. The `inLinks` column is
gone from the Crawled Pages table for the same reason. They return when the OnPage connector
persists the real `internal_links_count` / `plain_text_word_count` it already receives.*

⚠️ The two surviving KPIs are currently skewed: only ~15 of 154 pages have a `PageSpeed` row, and
the rest are counted as `score: 0` / `loadTimeMs: 0` rather than excluded — see plan item 5.4i.

### Compare Crawls & Progress
Compare two crawl snapshots side by side, and chart five metrics over time. Both read real
history from the `audit_snapshots` table — one row is written per completed sync, so the tabs
fill in as the project accumulates crawls. Each shows its empty state until **two** snapshots
exist, because a comparison and a trend both need at least two points; that is a genuine
"not enough history yet", not a missing data source.

### Edge cases

- Empty state when no crawl data exists, with a fetch prompt.
- `in-links` is always `0`; internal-link count, word count and TBT are **derived from PageSpeed
  timings**, not measured directly.
- Checks whose id starts with `lh:` are dynamic Lighthouse audits; their fix text comes straight
  from Lighthouse.

**Permissions.** All roles. **Related pages.** Overview (Site health pillar), Alerts, SEO.

---

## 10. Off-site SEO

**Purpose.** Measure the traffic your links, PR and social presence actually earn.

**Navigation.** Sidebar → SEO → Off-site SEO. **Data source.**
`GET /api/projects/<slug>/offsite?range=` — range-aware.

**Sections**

- A source banner explaining the definition: off-site = Referral + Organic Social/Video sessions.
- **Five KPIs** — off-site sessions, engagement rate, key events, attributed revenue, referring
  domains — each with a period-over-period chip.
- **Trend chart** — sessions vs engaged sessions over the range, with an area fill.
- **Channel mix** — every GA4 default channel group as a labelled bar, with off-site channels
  emphasised, plus two rollups: the off-site share of all sessions and off-site key events.
- **LinkedIn spotlight** — impressions, click-throughs, CTR and key events. When the LinkedIn
  connector toggle is off, impressions read "—" and the badge links to Settings → Connections.
- **Social & video platforms** table — LinkedIn, Reddit, YouTube, X/Twitter: impressions,
  sessions, engagement, key events, revenue. Unconnected platforms show a *"connector needed"*
  link instead of a number. Exportable to CSV.
- **Top referring domains** — domain, DR, sessions, engagement, key events, revenue and an
  open-in-new-tab link. Sortable on sessions, key events and revenue. Exportable.
- **Where off-site traffic lands** — landing page, top source, sessions, engagement, key events.

**Edge cases.** Empty state with a *"Fetch Off-site Data Now"* button when nothing is synced.
Revenue and platform impressions are no longer fabricated (fixed 2026-07 — revenue used to be
imputed at a flat **$45 per conversion** with GA4 revenue never fetched, and platform impressions
were session-count multiples rather than platform-API figures). Where the number is not measured,
the surface is empty rather than filled. The *Track* action on a referring domain, and its
companion *"Tracked link"* badge, were **removed** (2026-07-27): the action only toasted
`"… added to backlink tracking on next sync"` and persisted nothing, and the badge read a
`tracked` field the endpoint has never returned. It was deleted rather than implemented because
there is no honest target for it — `dataforseo_backlinks` syncs the target's entire profile in
one call and takes no per-domain input, so every listed domain is already tracked, and
`tracked_competitors` is the Positioning SERP-competitor grid, which a referring site is not.

**Permissions.** All roles. **Related pages.** Backlinks, Settings → Connections.

---

## 11. AI Optimization

**Purpose.** Track how visible the brand is inside AI answer engines (ChatGPT, Claude, Gemini,
Perplexity) and manage the prompts you want to monitor.

**Navigation.** Sidebar → SEO → AI Optimization. **Data source.**
`GET /api/projects/<slug>/ai` + `POST /api/projects/<slug>/ai/<action>` +
`POST /api/prompt-research`.

**Header:** an AI spend/cap chip, the next scheduled run, and a **Run all now** button.

**Five sub-tabs:**

1. **AI Visibility** — share-of-voice percentage with a week-over-week delta and a ranked
   competitor bar list; four KPIs (brand mentions, AI impressions, cited pages, prompt coverage);
   per-platform toggle chips (real data now, see below) that are meant to drive a multi-series
   mentions trend chart — the chart itself has no series to plot yet, see Edge cases; your
   most-cited pages; and the domains dominating AI answers, tagged *You* / *Competitor*.
2. **Prompts** — a **Prompt Explorer** (seed terms → template-expanded prompt ideas, selectable
   and addable to a list), list-filter chips, a list manager (create / rename / delete), a
   **composer** for adding prompts in bulk with suggestion shortcuts, and the main
   **Tracked Prompts × LLMs** grid — one row per prompt, one column per model, expandable to per-
   model snippets. A checkbox per row plus a header "select all" drive a bulk toolbar
   (**Remove selected**) once ≥1 row is checked, in addition to each row's own Run now,
   Inspect, Settings and Remove actions.
   The **Prompt settings** modal edits the prompt's question text itself (blank/whitespace-only
   edits are ignored, never saved) alongside which models to check, web-search on/off, country,
   city, cadence and which list the prompt belongs to — all persist and round-trip
   (`apps/dashboard/services/ai_service.py`'s `PROMPT_CFG_KEY`/`get_prompt_cfg`/
   `set_prompt_cfg` back `cadence`/`country`/`city`/`webSearch`, since `AIPrompt` has no columns
   for them; `models`, `listId` and `text` are real `AIPrompt` columns). Every path that creates a
   prompt — the composer, the AI Keywords bulk-add, `_handle_setup`'s wizard seeding — sets
   `tracked_models` to `connectable_platforms()`, so a newly added prompt is runnable
   immediately rather than showing "0 models" and being silently skipped by `run_prompt_checks`.
3. **AI Keywords** — how people ask AI about your topics: keyword, AI volume, Google volume, an
   AI-share ratio, a 12-month sparkline, intent, and your mention count. Segment chips
   (All / AI-heavy / Gaps / Mentioned), a search box, multi-select with bulk *add as prompts to a
   list*, and CSV export.
4. **Answer Inspector** — ask any question and see the answer with your brand's mentions
   highlighted plus the citation list.
5. **History** — previous inspections with verdict, position and cost.

### Setup wizard

A three-step wizard (Your brand → Competitors → Starter prompts) that captures brand name,
aliases, up to 9 competitor domains, and a selection of suggested + custom prompts, then persists
them. It appears when the project genuinely has not been set up — `setupDone` is now real
(`bool(target and target.setup_done)`), where it used to be hard-coded `true` so the wizard was
unreachable.

### Edge cases — read this before demoing

**What is real:** the tracked brand/aliases/competitors, prompt lists, the prompts themselves,
their model selections and now their cadence/country/city/web-search settings, and AI keyword
data when `AIKeywordData` rows exist (self-provisioning via `ensure_tables` — a database
predating that table no longer silently reports zero keywords). **Run now** and **Inspect now**
are real, billed calls through `pipeline/services/ai_visibility_service` — the frontend surfaces
a failure via `.catch()` rather than swallowing it. Suggestions (the wizard's step 3 and the
composer's quick-add shortcuts) are real too, generated from the tracked brand + aliases via the
same deterministic template expansion `/api/prompt-research` uses — empty only when no brand has
been saved yet, which is the normal state the very first time a brand-new project's wizard opens.

As of the 2026-07-31 LLM Mentions feature, **share-of-voice, the brand-mentions/AI-impressions/
cited-pages KPIs, your most-cited pages, and the domains-dominating-AI-answers list are real
too** — read back weekly from DataForSEO's LLM Mentions API by the `dataforseo_llm_mentions`
connector (`llm_mention_metrics` / `llm_cited_pages` tables) and assembled by
`apps/dashboard/services/llm_mentions_service.build_visibility_block`. A project with no captured
week reports `visibilityState: "setup"`; one with a brand but no tracked competitors reports
`"no_competitors"` (DataForSEO's cross-aggregation endpoint needs ≥2 targets to produce a
share, so the page shows an "add competitors" prompt rather than a false 100%) and falls back to
reporting the brand's own mentions/impressions only; a project with both reports `"ok"` and a
real ranked competitor list. This replaces the honest-empty-state described in the previous
revision of this document — do not describe AI share-of-voice as unbuilt.

**What is still not real:**
- **The 12-week mentions trend chart has no data to plot.** Weekly LLM Mentions snapshots are
  now being collected (see above), but `kpis`/`sov`/`topPages`/`topDomains` only ever read the
  latest one or two stored weeks — the response's `trend` field is still always `[]`, and the
  chart the platform-toggle chips are meant to drive stays empty until it is wired to read the
  accumulating weekly history. Nothing is fabricated to fill it.
- **Claude, Gemini and Perplexity mention tracking does not exist, at any price.** DataForSEO's
  LLM Mentions API covers exactly two platforms — Google AI Overviews and ChatGPT
  (`mentionPlatforms`, 2 entries) — full stop; there is no paid tier or alternate endpoint that
  adds the other three. The Prompts tab's separate four-engine list (`llmPlatforms`: ChatGPT,
  Claude, Gemini, Perplexity) is unrelated — it comes from this deployment's own LLM API keys via
  `run`/`inspect`, not from DataForSEO, and the two lists must not be confused (see
  `api-reference.md`'s `/ai` section and `SKILLS.md` §9).
- AI Keywords' `mentions`/`gap` columns are honestly `0`/`false` for every row: nothing in the
  schema links an `AIKeywordData` row to a specific `AIPrompt`, so there is no reliable way to say
  "this keyword's prompt got mentioned" without guessing — an earlier revision derived them from
  search volume instead and that was reverted for inventing a signal.
- Budget/cost/next-run are real-or-`None` (never a fabricated placeholder): cost is computed from
  actual recorded spend, and there is no scheduler, so `next_run` is honestly `None`.

**Permissions.** All roles. **Related pages.** Keywords, Settings → AI Summaries.

---

## 12. Ads (four pages)

All four share one payload: `GET /api/projects/<slug>/ads?range=` — range-aware.
All four show a setup panel when Google Ads is not connected and no spend exists.

### 12a. Paid Overview

Six KPIs (Spend, Conversions, CPA, ROAS, Avg CPC, GA4 key events) with period-over-period chips;
a **Spend & conversions** chart plotting spend against both Google-Ads and GA4 conversions;
a **Budget pacing** panel (monthly budget, month-to-date, projected, day-of-month, an On/Over/
Under-pace verdict and a progress bar, split by channel); and a **Needs attention** list derived
from the data — budget-limited campaigns, CPA spikes above 30 %, and wasted search-term spend —
each with a jump-to-page action.

⚠️ The monthly budget is a fixed $3,500 whenever any spend exists; conversion value is imputed at
$65/conversion and GA4 revenue at $45/key-event.

### 12b. Campaigns

A filterable, sortable campaign table with a totals row. Columns: status toggle, campaign
(name + platform chip + type), daily budget, spend, clicks, CTR, CPC, conversions, CPA, ROAS,
and lost impression share to budget. Filters: All / Google Ads / Meta / Paused, plus a name
search. Sortable on seven columns. CSV export.

**Inline actions:**
- **Status toggle** — flips enabled/paused. Records the intent; it is written back on the next
  sync, not immediately.
- **Budget** — click the value to edit inline; `Enter` saves, `Escape` cancels, blur saves.
  Values are rounded and floored at 1.
- **Expand** — reveals ad groups and a *View search terms for this campaign* link.

⚠️ Ad groups are always empty (`adGroups: []`), so expanded rows show nothing.

### 12c. Search Terms

Four KPIs (term spend, wasted spend, converting terms, negatives added); status filters
(All / Converting / Wasted spend / Managed); a text search; a match-type `<select>`; pagination
(10/25/50 per page); a totals row; and multi-select bulk actions — **Add as phrase negatives**
and **Track as organic keywords**.

Per row: a negative-keyword menu offering phrase / exact / broad match with an explanation of
each, and a **+ Track** action that promotes the query to an organic tracked keyword.
A campaign scope chip appears when you arrive from a specific campaign.

The `ad_search_terms` table and the `google_ads_search_terms` connector now exist and are wired
into the `ads` sync scope, so this page fills the moment Google grants **Standard Access** to the
Ads API. Until that approval lands the sync succeeds and writes zero rows — the token
authenticates, the query runs, and the report comes back empty — so the page shows its empty
state. The negative and promote endpoints work correctly.

### 12d. Attribution

A Google Ads vs GA4 comparison per campaign — dual bars, a gap percentage flagged beyond ±25 %,
conversion value and GA4 revenue — plus a post-click quality table by landing page (sessions,
engaged-rate bar, key events, revenue).

The campaign comparison joins `ad_metrics_daily` against the new `ga4_campaign_daily` table
(written by the `ga4` connector). Like Search Terms it stays empty until Google Ads Standard
Access is granted, since the Ads half of the join has no rows without it. The landing-page table
is populated from GA4 data and works today.

**Permissions.** All roles (the legacy `ads` role is not enforced by the SPA).
**Related pages.** Overview (Paid ROAS pillar), Keywords (promoted terms).

---

## 13. Alerts

**Purpose.** One inbox for everything that changed and needs a decision.

**Navigation.** Sidebar → Alerts (with an unacknowledged badge).
**Data source.** `GET /api/projects/<slug>/alerts` + `POST /api/alerts/<id>/ack` +
`POST /api/alerts/<id>/unack`.
This tab is **prefetched on boot and after every sync**, because the sidebar badge depends on it.

**Sections.** A filter row — All · High · Medium · Acknowledged, each with a count — an
**Acknowledge all** button, and the feed itself. Each row shows a severity chip, a kind label
(Anomaly / Ranking / Backlink / Technical / System / AI Visibility / Ads), the title, the detail
and the date, with an **Acknowledge** action. Acknowledged rows dim to 55 % opacity, lose that
button and gain an **Undo** one: acknowledging is reversible per row, including after
"Acknowledge all". Undo restores the row to the unacknowledged list and to the sidebar and bell
badges, which both count the same `acknowledged` flag.

**What produces alerts**

| Kind | Trigger |
|---|---|
| Anomaly | A metric deviating from its 12-week baseline (detected automatically after every GSC/GA4 sync) |
| Technical | `TechnicalIssue` rows, grouped by type — e.g. *"404 — Not found (12 pages affected)"* |
| System | The site's most recent refresh finished with connector errors; names the failing connectors and points at Settings → Connections |

**Edge cases.** Acknowledgements survive a re-sync: technical alerts are keyed on a content hash
of (url, issue_type) rather than a database id, because issue rows are rebuilt wholesale after
every sync. *Acknowledge all* fires one request per item in parallel, so the endpoint is
idempotent by design. `info`-severity items never count toward the sidebar badge and have no
Acknowledge button.

**Permissions.** All roles. **Related pages.** Every module the feed links to.

---

## 14. Settings

**Purpose.** Everything configurable: the project, credentials, people, connectors, schedules,
budget, alert rules and data policy.

**Navigation.** Sidebar → Settings. **Hidden entirely from Analysts** — the nav item does not
render, direct navigation shows a toast, and the page redirects to Overview.

**Data source.** `GET` / `PUT /api/projects/<slug>/settings`, plus the team and invitation
endpoints. All writes require Owner or Admin (403 otherwise); invitations require Owner.

**Eight sub-tabs:**

### General
Active project (domain, vertical, project id, competitor chips); Workspace (name, owner email,
timezone, week start) with a Save button that confirms with a ✓; Site credentials — GSC property
and GA4 property id — with its own save; and a **Danger zone** (clear all synced analytics data,
behind a confirm dialog). The clear-data button works (fixed 2026-07 — it used to read
`this.props.ctx.route.params.id`, which does not exist in this runtime, so the handler threw
before reaching the API; it now reads `this.state.projectId`).

### Team & Access
- **Add a teammate**, in two modes:
  - *Email invite* (Owner only) — email + role. Creates the account, emails a temporary password
    and a login link.
  - *Direct create* — email, username, password, role. Creates the user immediately.
- **Pending invitations** — email, role, invited-by, expiry, with **Resend** (extends 48 h) and
  **Revoke**.
- **Members & roles** — avatar, name, email, a role `<select>` and a delete action. The Owner row
  is locked: the role cannot be changed and the account cannot be deleted. Roles normalise
  themselves on read — the first user is always Owner, and stray Owner/Viewer values become
  Admin.

### Connections
Google Authorization status; the **data pipeline** connector grid — one card per connector with
its real status colour (green = success, red = error, grey = never/running), last sync time,
record count and error text; and **Social & platform connectors** — LinkedIn, Reddit, YouTube,
X, Facebook, Instagram, Meta Ads — each a Connect/Disconnect toggle. ⚠️ These toggles are
preference flags only; they gate whether the Off-site page shows an impressions column. They do
not authenticate anything.

### Automation
A **sync schedule** row per module (Position tracking, Backlinks, Site audit crawl, Keyword
volumes, Ads, AI visibility) with a cadence `<select>` and a **Run now** button that starts that
scope's sync immediately. Plus **Site audit crawl** settings: max pages, frequency, JS rendering,
respect robots.txt, excluded paths.

Cadences are **acted on** by `python manage.py run_scheduled_syncs`, which the operator drives
hourly from the OS scheduler (Task Scheduler / cron). It reads each module's configured cadence,
compares it against real run history, and starts only the scopes that are actually due. The
header's next-run date comes from `apps.sync.scheduling.schedule_summary()` — the same logic the
command itself uses, so the promise and the behaviour cannot drift apart. The **Run now**
buttons still trigger an immediate sync of that one scope.

⚠️ The hourly OS task is an **operator install step**, not something the app can do for itself.
Until it is registered, cadences are stored and the panel is accurate about what *would* run,
but nothing fires.

### Usage & Budget
Month-to-date spend against budget, projected monthly, a DataForSEO budget cap with a soft-cap
enforcement toggle, free-API quota bars (GA4 tokens, Ads ops, GSC queries), and a cost-by-module
table with per-row **Run now**.

**This panel shows real measured money.** 11 DataForSEO call sites append a `connector_costs` row
carrying the charge the API itself reported (`tasks[].cost`), and Settings reads it back: a
90-day total with a per-connector breakdown (runs, units, cost per unit), a 3-month trend, and
month-to-date. The cap you set is genuinely persisted.

Module rows map to connectors through the same `PAGE_CONNECTORS` / `SCOPE_ALIASES` registry that
`start_sync_run()` uses — so a row's **Run now** button and its attributed cost are, by
construction, about the same connectors. Spend from connectors no module owns (Domain overview,
Live SERP, AI visibility) is reported separately, so the rows reconcile against the total instead
of appearing to disagree with it.

Three honesty rules the panel follows:
- **Never measured ≠ measured zero.** Told apart by run counts, never totals. No billed run ever
  → a §10 empty state, not `$0.00`. History but nothing this month → a real measured `$0.00`.
- **The monthly figure is labelled as a projection.** It carries a `PROJECTED` chip and states its
  basis ("the spend recorded over the first 27 days of July 2026 (9 billed runs), extended at that
  same daily rate…"). With no billed run this month there is no rate to extrapolate, so it shows
  an em dash rather than a confident `$0.00`.
- **Sub-cent spend reads "under $0.01"**, and unit rates keep 6 decimal places so DataForSEO's
  real `$0.00125`/page survives instead of rounding away.

### Alerts & Rules
Four alert rules — keyword position drop, backlink lost from a high-DR domain, click deviation
from the 28-day mean, new crawl errors — each with an on/off switch and an editable threshold
(debounced auto-save). Plus notification settings: email on/off, weekly digest + day, recipients,
Slack webhook, quiet hours, and per-severity routing (Don't notify / Email immediately / Weekly
digest / Slack).

**Two of the four rules now drive real detectors** (`alerts_service.load_alert_rules`, read on
every `GET /alerts`, which is also what feeds the Overview priority list and the sidebar badge):

| Rule | Drives | Meaning of `threshold` |
|---|---|---|
| `traffic_anomaly` | `query_alert_anomalies_raw` (kind `anomaly`) | minimum \|deviation_pct\| an anomaly must show to reach the feed |
| `audit_errors` | `query_alert_technical_issues_raw` (kind `technical`) | minimum affected pages in an issue group |
| `pos_drop` | — **nothing** | no per-keyword ranking detector exists |
| `lost_backlink` | — **nothing** | no lost-backlink detector exists |

Switching a wired rule off suppresses that kind at source (the detector does not run), not
after the fact. Missing, `null` or malformed `alertRules` falls back to the pre-rules
behaviour — every detector on, unfiltered — never to an empty feed.

Caveats, all deliberate:
- `traffic_anomaly` is labelled "Clicks deviate from 28-day mean by", but it governs the whole
  anomaly detector: every `metric_type` `anomaly_service` writes (SEO **and** ads), measured
  against a **12-week** rolling baseline. It is the only rule mapped there, so scoping it to
  clicks alone would leave the other metrics with no control at all. The label should be
  reworded in `settings_service.DEFAULT_SETTINGS_BLOB`.
- `anomaly_service` only *writes* rows above its own `ANOMALY_THRESHOLD_PCT` (35), so a
  `traffic_anomaly` threshold below 35 cannot surface anything extra.
- `audit_errors` is labelled "Crawl finds **new** errors" — "new" is not implemented (nothing
  snapshots a previous crawl to diff), so the threshold applies to the group's total affected
  pages.
- ⚠️ `pos_drop` and `lost_backlink` are controls that change nothing. They should be removed
  from the defaults or given detectors.
- The kind `system` sync-failure alert is intentionally **not** suppressible by any rule — it
  is the alert that says the data is stale.

⚠️ Notification preferences are still persisted with **nothing consuming them** — no
notification is ever sent.

### AI Summaries
Provider (OpenAI / Anthropic), model, tone (Concise / Detailed / Executive), cadence, monthly
cap, brand voice. ⚠️ Persisted but not consumed — the summary generator hard-codes `gpt-4o-mini`
against OpenAI and runs after every qualifying sync.

### Security & Data
Two-factor and SSO toggles, a **Change Password** form, active sessions with revoke, API tokens
with create/revoke, data preferences (export format, retention, report timezone, number format),
a full-export request and a GDPR delete request.

The `security` group is **per-field**. `session_timeout` saves like any other preference. 2FA,
SSO, session revocation and token management are **refused** with a 400 naming the refused
fields, because no TOTP or SAML implementation exists here and a stored `twofa: true` would
assert a guarantee that is not real.

The UI tells the truth about it now: `putSettings` takes a `revert` callback, shows the error and
rolls the control back. Previously all five controls animated to "on" while the frontend's
`.catch(() => {})` swallowed the 400 — the UI claimed 2FA was enabled when nothing implemented
it. Data preferences and the change-password form are real.

**Permissions.** Owner and Admin only. Owner additionally required for all invitation actions.
**Related pages.** Alerts (rules), Off-site SEO (platform connectors), every page (refresh
scopes).

---

## 15. Cross-cutting flows

### Refreshing data

1. Click **Refresh all** (topbar), a page's **Fetch …** button, or a **Run now** in Settings.
2. The SPA posts to `/api/projects/<slug>/sync` with a scope. If Search Console or GA4 is not
   configured for the site, the request is rejected with a message pointing at Settings.
3. The server creates a run record and starts a background thread; the response carries the task
   id and the list of connectors it will run.
4. The banner appears; the SPA polls every 500 ms for progress, current step and ETA.
5. On completion the entire cache for that project is discarded, the current tab and the alerts
   badge refetch, the freshness pill flips to *"Just now"*, and a scope-specific toast confirms.
6. If any connector failed, the run is marked errored and a **System alert** appears in Alerts
   naming the failures.

Adding a site runs this flow automatically for scope `all`.

### Adding a keyword to tracking

Keyword Explorer → select rows → **Send keywords → Position Tracking → project**, or the
drawer's **Track** button, or Search Terms' **+ Track**, or the Position Tracking wizard/edit
modal. All paths write to the same tracked-keyword list, which is what the paid per-keyword
DataForSEO connectors read — so this is the lever that controls API spend.

### Caching

Responses are cached client-side per `projectId : tab [: range]`. Switching tabs or projects
reuses the cache; a sync or a mutation invalidates the relevant keys and forces a refetch. There
is no server-side HTTP cache; the only server caches are the 24-hour Domain Overview / live-SERP
caches and the 6-hour domain-checks cache.

---

## 16. Permissions summary

| Capability | Owner | Admin | Analyst |
|---|:--:|:--:|:--:|
| View every dashboard page | ✅ | ✅ | ✅ |
| Refresh data | ✅ | ✅ | ✅ |
| Track keywords, acknowledge alerts, hide audit checks, ads write-backs | ✅ | ✅ | ✅ |
| Open Settings | ✅ | ✅ | ❌ (hidden + redirected) |
| Save any settings group | ✅ | ✅ | ❌ (403) |
| Create / delete users | ✅ | ✅ | ❌ (403) |
| Send / resend / revoke email invitations | ✅ | ❌ (403) | ❌ (403) |
| Delete the Owner account | ❌ | ❌ | ❌ |

The first user (id 1) and any user named `founder`/`owner` are always treated as Owner.
Role checks are UI-level guards, not a security boundary: they return *allow* for an
unauthenticated caller.

---

## 17. Known gaps

Documented so nobody mistakes a built screen for a working feature.

**Blocked on external access, not on code**
- Ads → Search Terms and Attribution. The `ad_search_terms` and `ga4_campaign_daily` tables,
  the `google_ads_search_terms` connector and the `ads` sync scope all exist and are wired.
  Data flows the moment Google grants **Standard Access** to the Ads API — a developer-token
  approval outside this codebase. Until then the pages show an honest empty state.
- Overview → Paid ROAS pillar — same dependency.

**Saved but not consumed**
- Alert rules `pos_drop` and `lost_backlink` only. The other two (`traffic_anomaly`,
  `audit_errors`) are now read by `alerts_service.load_alert_rules` and really do gate their
  detectors — see "Alerts & Rules" above. These two remain inert because the detectors they
  would drive (per-keyword ranking drops, lost backlinks) do not exist anywhere.
- AI-summary provider/model/tone/cadence — `pipeline/services/ai_summary_service.py` hard-codes
  `gpt-4o-mini` and ignores `aiConfig`.
- Platform connector toggles (presentation flags only, not connections).
- Position Tracking's search engine / device / language. They are now really stored on the
  `sites` row and really shown in the workspace header and Edit modal, instead of being
  discarded as they were before — but `dataforseo_serp` and `dataforseo_serp_competitors` still
  post `location_name="United States"`, `language_name="English"`, `device="desktop"` as
  literals and read none of them. Choosing Bing/Mobile/Spanish changes what the page reports
  back to you, not what gets fetched. Closing this means threading the row into both connectors'
  payloads (and DataForSEO has no Bing SERP on the same endpoint).
*(Per-run connector spend and alert-rule thresholds were both on this list and are now consumed —
Settings → Usage & Budget shows measured spend, and `alerts_service._RULE_DETECTORS` reads the
stored thresholds. See §14 and the Alerts & Rules section.)*

**Partly supported by design, and honest about it**
- Settings → Security. `session_timeout` persists like any other preference. `twofa`, `sso`,
  `sessions` and `tokens` are **refused** with a disclosing message, because no TOTP or SAML
  implementation exists and a stored `true` would assert a security guarantee that is not real.
  The UI now surfaces the refusal and reverts the control instead of animating success.

**Derived rather than measured** — remaining clearly-flagged approximations in Backlinks (link
rows, first-seen, spam) and Ads (monthly budget, conversion value). Each is labelled in the UI
as derived; none is presented as a measurement.

**Not offered by the data source, not a code gap**
- AI Optimization's per-platform mention tracking covers **Google AI Overviews and ChatGPT
  only** (`mentionPlatforms`). DataForSEO's LLM Mentions API — the only vendor wired for this —
  does not offer Claude, Gemini or Perplexity mention data at any price; there is no fallback
  connector to add them. The Prompts tab's four-engine list (`llmPlatforms`) is a different
  feature (this deployment's own LLM keys via `run`/`inspect`) and is unaffected.

**Saved but not consumed**, continued
- AI Optimization's 12-week mentions trend chart. Weekly LLM Mentions snapshots have started
  accumulating in `llm_mention_metrics`/`llm_cited_pages` (one row per site/week/subject/platform
  since the 2026-07-31 feature), but `build_ai_response`'s `trend` field is still hard-coded to
  `[]` — the chart is not wired to read the accumulating history in this release. Wiring it needs
  no new API calls, only a query over the weeks already being stored.

Removed during the 2026-07 honesty pass, listed so nobody reintroduces them: Position Tracking
competitor cells (an MD5-derived offset on the competitor's site-wide average, which produced a
*stable* fake number and so read as real — an absent cell is now the answer), Off-site revenue
and platform impressions, and the Off-site *Track* action on a referring domain (see §10 — a
toast with no write behind it, and no honest write available, since the backlink profile is
synced wholesale and needs no per-domain opt-in).

*(AI Optimization share of voice / mention KPIs / top-pages / top-domains were on this
"removed placeholder" list — they are real now, as of the 2026-07-31 LLM Mentions feature; see
§11. Only the trend chart and the Claude/Gemini/Perplexity gap above remain.)*

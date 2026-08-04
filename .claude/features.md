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

Fields: **Email or Username**, **Password**. Either identifier works —
`EmailOrUsernameModelBackend` tries username first, then email, case-insensitively.

- **Success** → redirected to `/` (the SPA), or to `?next=` if present.
- **Failure** → an inline rose-tinted banner: *"The username or password is incorrect."*
- Already logged in → bounced straight to the dashboard.
- Any unauthenticated URL redirects here, because `LoginRequiredMiddleware` protects everything.
- **Forgot password?** next to the password label → `/password-reset/`.

Accounts are created three ways: `python manage.py seed_users` (founder/seo/ads), the Settings →
Team tab (direct creation or email invite), or the Django admin at `/admin/`.

The server-rendered pages are login, accept-invite and the four password-reset steps; all six
extend `templates/registration/auth_base.html` so they stay one visual system. Everything else
is the SPA.

### Accept invitation (`/accept-invite/?token=…`)

The page the invitation email links to. Public — the invitee has no account yet — and rendered
by Django, not the SPA.

- Shows the role they were invited as, and the invited email **read-only**: that address is
  their username. Nothing else to choose.
- Fields: **Choose a password**, **Confirm password**. Rejected if they don't match, or if
  Django's `AUTH_PASSWORD_VALIDATORS` reject the password (too short, too common, all numeric,
  too close to the email).
- **Invalid / expired / already-used token** → the form is replaced by an explanation and a
  *Go to sign in* button (404 for unknown, 400 otherwise).
- **Success** → the account is created with the invited role, the invite is marked accepted,
  the user is signed in and lands on the dashboard.

*Invite a teammate* creates a `UserInvitation` row and emails this link — it does **not** create
the `User`, and it never sends a password.

The acceptance rules live in `apps/accounts/services.py` and are shared with
`POST /api/auth/accept-invite` (the SPA's older modal path), so the two cannot drift.

*(Fixed 2026-08. The email used to link to `/#/accept-invite?token=…`, a route inside the SPA —
which is served from `/` behind `LoginRequiredMiddleware`, so invitees were redirected to a
sign-in form they had no account for and the flow was unusable. Until 2026-07 it was worse: a
generated temporary password mailed in plaintext, the User created immediately, and no
invitation record. Do not reintroduce either shape.)*

### Forgot password (`/password-reset/`)

Django's standard four-step flow, branded: enter your email → *Check your email* (worded so it
never confirms whether an address is registered) → the emailed one-time link → set a new
password → *Password updated*. Reached from the login page; needs SMTP configured
(`EMAIL_HOST_USER` etc.), and falls back to printing the email to the console in dev without it.

Both this email's link and the invitation link are built from the **host the request came in
on** — `http://localhost:8000/...` in dev, `https://limitless.vashstudios.cloud/...` on the
deployed site — so neither needs per-environment configuration.

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
- **Refresh all button** (indigo) — runs every connector in `ALL_CONNECTORS`.
- **Stop** — the sync banner carries a Stop control while any refresh is running. It takes
  effect within a couple of seconds, keeps everything already written, and skips every
  connector that had not started; the one in flight may already be billed. No confirmation —
  recovery is clicking Fetch again.
- **Already fetched recently** — pressing a refresh button for a scope whose connectors all
  synced successfully within the last 24 hours does not start a run. A prompt says when it was
  last fetched and offers *Refetch anyway* or *Cancel*. A connector whose last run failed is
  never treated as fresh, so a refresh right after fixing a credential always runs. Scheduled
  syncs are unaffected — their cadences in Settings → Automation are their own freshness logic.

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
in Position Tracking is **allowed** — it registers a second, independent project against the
same domain (its own tracking-area settings, keyword list and competitors), sent to
`POST /api/projects` with `allow_duplicate: true`. This is the one project-creation path that
allows it: the topbar "+" add-site popover and Settings still reject a domain that is already
registered (`add_site()` defaults `allow_duplicate` to `False` there). Because Position
Tracking's own data (`saved_keywords`, `keyword_rankings`) is keyed by the raw domain string, not
by project id, duplicate projects for the same domain share the same tracked-keyword pool and
ranking history — they differ in name and tracking-area settings, not in underlying SEO data.

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
  clicks, KD bar, CPC, intent badge, ranking URL. Only keywords with a measured position in the
  current window (`pos != null`) appear here, so no row ever shows a blank Pos/Δ cell — this
  catches both a brand-new tracked keyword and a keyword `dataforseo_keywords` has priced but no
  rank connector has ever captured. The "All (N)" tab count reflects this table's own row count,
  not the portfolio-wide `Tracked keywords` KPI above it.
- **Newly Added Keywords — Not Tracked Yet** — a separate, tinted card shown only when non-empty,
  for every tracked keyword with no measured position yet (`pos == null`): keyword, volume, KD,
  CPC, intent — no Pos/Δ/clicks columns, since there is genuinely no measurement to show. This is
  what a "Send keywords → Position Tracking" from the Keyword Explorer lands in first. Its own
  "Track These New Keywords" button runs the `positions_new` sync scope (`h.refreshNewKeywords`,
  §11/`app.js`), which `sync_engine.sync_page` narrows to exactly `keywords_needing_backfill`'s
  list via `connector.only_keywords` — it does not re-query the rest of the tracked set. The
  "All Tracked Keywords" card's own "Refresh Tracked Keywords" button is the full `positions`
  scope (every tracked keyword against every competitor) and carries a tooltip pointing at the
  narrower button, since it's the one that used to get clicked by mistake right after adding a
  few keywords. Once a keyword is measured it drops out of this card and appears in the main
  table and in Rankings Overview on its own — nothing else needs to move it.

**Overview**
- **Competitor Map** — the domain-level aggregate of the same captured SERP rows the grid
  renders: a scatter placing you and each competitor by how much of your captured keyword set
  they appear on (x) against their average position (y), bubble size = top-10 count, over a
  table of keywords / coverage / avg position / top 10 / ahead-of-you / visibility. Head-to-head
  is counted only where both domains have a real captured position. With no captured rows it
  renders an empty state with a capture button — **nothing is estimated to fill it**.
- Per-domain **visibility index cards** (you + each competitor), sorted **strongest first** — the
  question the tab answers is which competitor is ranking best, so that must be the reading order,
  and your own domain is deliberately *not* pinned to the front because its rank among the rivals
  is the answer. Each card carries a colour swatch, the index, a sub-line (`n/N keywords · avg
  #p`), and a legend checkbox.
  **The index is 0–100 where 100 = #1 on every tracked keyword.** Position → credit follows an
  organic CTR curve (#1 = 31.7, #2 = 24.7, #5 = 9.5, #10 = 1.8, ~0 past #20); the earned points
  are divided by a perfect board (`keywords × 31.7`). A keyword the domain does not rank on scores
  0 but stays in the denominator, so coverage counts alongside position and the denominator is
  identical for every domain — which is the only reason the cards are comparable.
  **Every keyword is weighted equally, and that is deliberate.** Two earlier formulas were wrong
  and must not come back: (1) `(100 − pos)/100` per domain paid 55% credit for sitting at #45, so
  five domains totalled 264% under a caption reading "share"; (2) the CTR curve **weighted by
  search volume** inverted the ranking outright on real data — four keywords carry 81% of the
  Premier Staff project's volume, which scored atneventstaffing.com (avg position 7.7, the
  strongest board) at 2.21 while eventstaff.com (avg 18.7) scored 12.09. Every tracked keyword is
  one the user chose to track, so the index measures **ranking strength, not traffic potential**.
  The sub-line exists because the index alone cannot separate "ranks everywhere, mid-table" from
  "ranks on three keywords, all #1" — both can land on the same number.
  Unticking a legend entry only greys its card and hides its (future) chart series; it never
  changes anyone's number.
- A multi-series visibility line chart — **dormant**: `/api/positions` returns no per-date series,
  so `hasHistory` is hard-`false` and an empty state renders instead. The SVG is kept as the target
  shape; populate it only from real positions, never a generator.
  It *is* buildable without a new table: `competitor_keyword_rankings` stores a row per
  (keyword, domain, **date**), so the index can be recomputed for each capture date. The trap is
  that capture sets differ between dates — the Premier Staff project has 6 keywords captured on
  2026-07-23 and 15 on 2026-07-26 — so an index computed over "whatever was captured that day"
  moves when the keyword set moves, not when the rankings do. Any implementation must fix the
  denominator across dates (or plot the keyword count alongside) or the line will report sync
  coverage as if it were performance.
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
- The Overview visibility cards are **per-domain indices, not a share**. Each is independently
  0–100 against the same perfect board, so they do not sum to 100 and are not meant to. Do not
  "fix" that by normalising the set to total 100%: it was tried, and it makes a domain's number
  move whenever an unrelated competitor is added or removed, which is worse than the gap.
  Verified against the real Premier Staff payload: #1 on every keyword = exactly 100.0, ranking
  nowhere = exactly 0.0, and the highest live card is 9.4.
- **Low index values are usually true, not a scaling bug.** On the Premier Staff project the best
  domain scores 9.4 because it ranks on 7 of 24 keywords at an average of #8. The pre-2026-08
  formula printed 80.41% for an average position of *38* — that number was the bug, not this one.
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
   anchors by share. These five cards/charts come from the `BacklinksSnapshot` blob, not the
   `Backlink` table — they render empty until `manage.py refresh_backlinks <slug>` has been run
   at least once for that site (the page's own Refresh action calls the same path).
2. **Backlinks** — the link table: the referring domain (linked to the exact page that carries
   the backlink — `url_from` — falling back to the domain's homepage when a row predates that
   column), anchor, target URL, domain-authority chip (0-100, scaled from DataForSEO's raw
   0-1000 `domain_from_rank`), per-link spam score, dofollow/nofollow, first-seen, and NEW/LOST
   badges. Two filter rows: status (All · New · Lost) and follow type (All links · Dofollow ·
   Nofollow). Capped at 60 rows. ("Broken" is not tracked — no HTTP-status column exists yet.)
3. **Referring Domains** — domain (linked to its homepage), authority chip, per-domain spam
   score (averaged across that domain's stored links), backlink count, links-to-us, follow type,
   first-seen. `category` stays empty — no column/connector backs it.
4. **Anchors** — anchor text, classified type (Branded / URL / Keyword / Generic / Empty),
   backlinks, referring domains, dofollow %. Sourced from the snapshot; empty until
   `refresh_backlinks` has run.
5. **Link Gap** — needs each tracked competitor's own referring-domain list, which nothing syncs
   yet, so `gapDomains` is always empty and the tab shows its empty state.

**Edge cases.** Empty state when no backlinks are stored. Every value on this page is a real
column or a real DataForSEO aggregate — nothing is fabricated to fill a shape. `domain_rank` /
`page_rank` (per link) and `rank` (per referring domain) are DataForSEO's raw 0-1000 scale in
the API response; the SPA scales to 0-100 for display. A `Backlink` row synced before the
`url_from`/`page_from_rank`/`spam_score` columns existed reads those as unknown (empty/null),
not zero — re-running the connector backfills them.

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
  network.

  This card **refreshes on its own**, via the `domain_checks` scope — *Run Domain Checks* in the
  empty state, *Re-run* in the header once checks exist. That scope is one credential-free
  connector making six plain HTTPS requests to the site: a few seconds, nothing metered. It used
  to be wired to the full `audit` scope, so filling in this one card cost a 20-30 minute crawl
  and a billable DataForSEO OnPage job. A full Site Audit crawl still refreshes these checks
  (`domain_checks` runs first in the `audit` scope), so nothing was traded away for the speed.
- **Top Issues** — the six highest-impact failing checks.

### Issues
Severity filter (All / Errors / Warnings / Notices / Hidden / Resolved), a category chip row,
and a search box. A checkbox at the left of each issue row marks/unmarks that check
**resolved** (`POST audit/toggle-resolved`) without expanding the row. Each row also expands to
show a preview of 8 affected pages (URL, page score chip, status, and a per-row **Resolve /
Undo** action at the right end that acknowledges just that one page via `POST
audit/toggle-page-resolved`) with a **Show all N affected pages** toggle that reveals the rest
in a scrollable box (capped at 500 rendered rows, with an "export for the full list" note beyond
that), a **How to fix** paragraph written for that issue type, an **Export** action for the full
page list, a **Mark as resolved / Unresolve** text action mirroring the checkbox, and a **Hide
this check / Restore check** toggle.

Hidden and resolved checks are both excluded from the totals and from Overview's error count,
and both persist per project. They differ in intent: hiding is "ignore this, don't count it,"
while resolving is "this is fixed." A check counts as resolved once every one of its CURRENT
affected pages has been individually acknowledged — a **subset** rule, not equality — so
clicking the whole-check control acknowledges every current page in one shot, and the per-row
Resolve action does the same one page at a time; either path can complete the other. A resolved
check **auto-unresolves**, not when its affected-page set changes at all, but specifically the
moment an unacknowledged page shows up under it (a crawl finds a genuinely new/unacked page,
same check) — a page that was fixed and drops out of the current set does not by itself flip the
check back to active. This keeps a real regression from staying silently buried in the Resolved
tab while not punishing partial progress.

### Crawled Pages
Two views. **Table**: URL, score chip, HTTP status chip, an `nE · nW · nN` issue summary, crawl
depth, in-links and load time, filterable by URL, sortable on five columns, and **paginated at
40 rows a page** (`‹ Prev`, a 7-wide window of page numbers with first/last always reachable,
`Next ›`). The footer reads "Showing 1–40 of 1 139 pages · N of 1 139 Lighthouse-scored across
the whole list" — the coverage count spans the entire filtered list, not the visible page, so
clicking through does not make coverage look like it is changing. Filtering or re-sorting
returns to page 1, and a stale page index is clamped rather than rendering an empty table.
Before 2026-08-02 the table rendered `rows.slice(0, 40)` and told the reader to export a CSV for
the rest, which on the largest site made 96% of an already-downloaded payload unreachable.
**Tree**: a folder rollup with page counts, average score and issue counts.

**Sorting puts unmeasured rows last, in both directions** (`App.sortRows`, tested in
`static/spa/tests/sort_rows.test.js`). Only a sampled subset of crawled pages is ever
Lighthouse-scored, so `score` and `loadTimeMs` are `null` on the rest; `inLinks` is `null` on
every page the OnPage crawl did not reach. The comparator used to substitute `-1` for `null`,
which is below every real metric, so the default score-ascending sort ranked all unmeasured
pages as worse than the worst measured one and the 40-row cap hid every real score below the
fold — the table read as an empty column of dashes on a site that had a full set of
measurements. A real `0` is still a result (an orphan page has 0 in-links) and sorts as `0`.

Clicking a row opens the **page detail drawer**: score, status, six stats (crawl depth, in-links,
load time, internal links, external links, word count), Core Web Vitals, and the list of failed
checks — each of which jumps back into the Issues tab focused on that check.

### Statistics
Two averages (page score, load time) plus three distribution charts: HTTP status codes, crawl
depth and load time bands.

*"Avg. internal links", "Avg. word count" and the "Content length" chart were once removed for
being computed from `performance_score × 0.4` and `fcp_ms × 1.5` — a Lighthouse score and a paint
timing relabelled as a link count and a word count. They are back as real measurements now that
`dataforseo_onpage` persists `internal_links_count` / `inbound_links_count` /
`plain_text_word_count` to `page_crawl_meta` (`upsert_page_crawl_meta`).*

Every KPI and chart here is computed over **measured pages only** and prints how many that was
("across N pages measured by Lighthouse"). Unmeasured pages are excluded rather than counted as
a perfect `score: 0` / `loadTimeMs: 0`, which used to drag the averages down and stack every
distribution's fastest bucket.

**How many pages get a score.** `pagespeed` scans every page in the `pages` table, mobile only,
**stalest first** (never measured → oldest measured → most clicks), bounded by a 30-minute wall
clock rather than a page quota. A site bigger than one run is therefore covered across
consecutive runs and then rotates, so no page is permanently unscored: fusehealth's 55 pages
finish in one run (~8 min), premierstaff's 1 139 take several. Before 2026-08-02 it scanned 15
pages of a 55-page site — a `WHERE clicks > 0` pool meant a page had to already have Google
traffic to be eligible for a speed audit at all, which excluded exactly the new pages worth
fixing.

The `pages` table itself still comes from GSC (`gsc_pages`), so a page Search Console has never
reported is not in the inventory and cannot be audited by any of these connectors; that is the
remaining coverage limit. The `sitemap` connector exists and would close it, but is not in any
scope.

### Compare Crawls & Progress
Compare two crawl snapshots side by side, and chart five metrics over time. Both read real
history from the `audit_snapshots` table — one row is written per completed sync, so the tabs
fill in as the project accumulates crawls. Each shows its empty state until **two** snapshots
exist, because a comparison and a trend both need at least two points; that is a genuine
"not enough history yet", not a missing data source.

### Edge cases

- Empty state when no crawl data exists, with a fetch prompt.
- `in-links`, internal links and word count come from `page_crawl_meta`, written only by
  `dataforseo_onpage`. On a site where that connector has never run, the table has no
  `page_crawl_meta` rows at all and **every** in-links cell is a dash — that is "we did not
  look", not "no inbound links" (a real `0` is an orphan page and renders amber). Check
  `SyncLog` for a `dataforseo_onpage` row before treating an all-dash column as a bug;
  **Re-crawl now** runs it (billable OnPage crawl, ~$0.00125/page).
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
- **LinkedIn spotlight** — impressions, click-throughs, CTR and key events. No LinkedIn
  connector is wired, so impressions and CTR read "—", the badge reads *"No connector"* (grey,
  not styled as a link — it still opens Settings → Connections, where the explanation lives,
  but nothing there can be pressed), and the subtitle says sessions come from GA4 while
  impressions & CTR need the LinkedIn API. Sessions, key events and revenue are real GA4 numbers.
- **Social & video platforms** table — LinkedIn, Reddit, YouTube, X/Twitter: impressions,
  sessions, engagement, key events, revenue. Impressions read *"connector needed"* (grey text,
  not a link) for every platform — no platform connector exists, so that is the permanent state
  until one is built. Exportable to CSV.
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
X, Facebook, Instagram, Meta Ads — each an **inert row reading "Connector not built yet"**, with
a footnote explaining that Off-site SEO already shows the GA4 sessions from these platforms and
what is missing is on-platform impressions & CTR.

**Ads platforms** (Google Ads / Meta Ads) is a real credential-entry form as of
2026-08-03 — not a display: each platform has its own fields (Google Ads: Developer
Token, Customer ID, optional Manager/MCC Customer ID; Meta Ads: Access Token, Ad Account
ID), a **Test connection** button that makes one real, cheap API call against whatever is
currently in the form (or the already-saved value if nothing was edited), and a **Save**
button. Credentials are encrypted at rest in `ProjectSettings.data["adsCredentials"]`
(never round-tripped back to the browser — only a last-4-characters mask) and are what
`GoogleAdsConnector`/`MetaConnector` actually use during a sync, falling back to the
server's `.env` values for any site with nothing saved. See
`docs/superpowers/specs/2026-08-03-ads-credentials-design.md`.

These were Connect/Disconnect buttons until 2026-08-02. They authenticated nothing: the click
flipped a `platformConnectors` boolean in `ProjectSettings.data`, the row instantly read
"Connected", and the only downstream effect was a `connected: true` flag on the Off-site page —
whose `impressions` are `null` for every platform regardless. Two connectors exist as code
(`pipeline/connectors/linkedin.py`, `meta.py`) but neither is in `PAGE_CONNECTORS` /
`ALL_CONNECTORS`, so no refresh runs them, and LinkedIn's writes `ad_metrics` rather than
off-site impressions; Reddit, YouTube and X have no connector module. A control that looks like
a connection but only sets a display flag is the "never fabricate data to fill a shape" rule
broken with a widget instead of a number. Replace the row with a real credential flow when a
connector is genuinely wired — not with the boolean.

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

**Derived rather than measured** — remaining clearly-flagged approximations in Ads (monthly
budget, conversion value). Each is labelled in the UI as derived; none is presented as a
measurement.
*(Backlinks link rows, first-seen and spam score were on this list — as of 2026-08-01 the
`dataforseo_backlinks` connector captures `url_from`, `domain_from_rank`, `page_from_rank` and
`backlink_spam_score` for real, so those rows are now measured, not derived. See §8.)*

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

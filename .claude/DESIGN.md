# Design System

> Extracted from the shipped templates and view-model builders. There is no CSS framework, no
> class system and no theme file in the application — every value below is a literal that appears
> in `static/spa/src/`. This document is the de-facto token list; keep it in sync when you add a
> new value, and prefer reusing an existing one.

---

## 1. Architecture decisions

**Inline styles, not classes.** Every element carries `style="…"` (in templates) or a JS style
object (from `renderVals()`). There is no stylesheet for the app. This came from the design-tool
export the UI was built from: keeping styles inline means the served markup stays comparable to
the authored design, and there is no cascade to reason about. The cost is that a token change is
a find-and-replace, which is exactly why this document exists.

**One global CSS block.** The only real stylesheet lives in `index.html`'s `<helmet>`: the Inter
web-font import, `body { margin: 0 }`, scrollbar styling, two keyframe animations
(`fusePulse`, `fuseSpin`), the `:focus-visible` ring, and a `prefers-reduced-motion` override.
Nothing else.

**Styling is a render-time computation.** Conditional appearance is expressed as a function
returning a style object — `posBadge(p)`, `kdColor(kd)`, `sevChip(sev)`, `scoreChip(v)`,
`intentView(intent)`, `toggle(on)` — never as a conditional class name. Add new visual states by
extending these helpers, not by branching in the template.

**Composition by text inclusion.** Templates are assembled server-side by `resolve_includes()`.
There is no component framework: a "component" is an HTML fragment plus the slice of
`renderVals()` that feeds it.

---

## 2. Folder structure

```
static/spa/
├── vendor/support.js        # dc-runtime (generated; never edit)
├── app/api.js               # FuseAPI transport (+ legacy fixture backend)
├── app/fixtures.js          # demo data (dead in production)
├── us_cities.json           # location picker dataset
├── assets/{fuse-logo.svg, logo.png}
└── src/                     # ← THE application
    ├── index.html           # document shell + layout + #include directives
    ├── components/
    │   ├── sidebar.html
    │   ├── topbar.html
    │   ├── password_modal.html
    │   └── accept_invite_modal.html
    ├── pages/               # one fragment per screen
    │   ├── overview.html   seo.html   domain_overview.html   keywords.html
    │   ├── positioning.html   backlinks.html
    │   ├── pages.html          → Site Audit
    │   ├── site_audit.html     → AI Optimization
    │   ├── ads.html   alerts.html   settings.html
    └── js/
        ├── app.js           # state, router, actions, formatters, renderVals() head
        └── pages/*.js       # per-page view-model builders, spliced into renderVals()
```

⚠️ **Two filenames are misleading and must not be "fixed" casually:** `pages/pages.html` contains
the **Site Audit** screen and `pages/site_audit.html` contains the **AI Optimization** screen.
`index.html`'s include comments label them correctly. The internal tab key for Site Audit is
`pages`, which is where the confusion originated.

Also note: **Off-site SEO, Campaigns, Search Terms and Attribution have no separate page file** —
their markup is inline in `index.html`.

---

## 3. Layout

```
┌───────────┬───────────────────────────────────────────────┐
│           │  header 64px  title · site · range · refresh   │
│  sidebar  ├───────────────────────────────────────────────┤
│  240px    │                                               │
│  fixed    │  main  flex:1  overflow-y:auto  padding:24px   │
│           │    ├ sync banner        (conditional)          │
│           │    ├ error state        (conditional)          │
│           │    ├ loading skeleton   (conditional)          │
│           │    └ one <sc-if> per screen                    │
└───────────┴───────────────────────────────────────────────┘
```

Root: `height: 100vh; display: flex`, `background: #f8fafc`, `color: #0f172a`,
`font-family: 'Inter', system-ui, sans-serif`, `-webkit-font-smoothing: antialiased`.

- **Sidebar** — `width: 240px; flex-shrink: 0; background: white; border-right: 1px solid
  #e2e8f0`; itself a column of brand block (64 px) / scrollable nav / footer.
- **Main column** — `flex: 1; min-width: 0`. The `min-width: 0` is load-bearing: without it a
  wide table forces the whole layout past the viewport.
- **Header** — `height: 64px`, `rgba(255,255,255,0.85)` with `backdrop-filter: blur(20px)`,
  bottom border, `z-index: 5`.
- **Content** — the only scroll container. Screens are `display: flex; flex-direction: column;
  gap: 20px`.

**Screen switching** is one `<sc-if value="{{ showX }}">` per screen, all present in the single
document. Only one `showX` is ever true, so exactly one screen mounts.

**Content grids in use:** `repeat(4, 1fr)` for KPI rows · `repeat(5, 1fr)` for Off-site KPIs and
Overview pillars · `1.15fr 0.85fr` for a wide+narrow pair · `minmax(180px, 1.4fr) repeat(N, 1fr)`
for the competitor grid. Gaps: 14–16 px inside a grid, 20 px between sections.

---

## 4. Color system

### Neutrals (slate)

| Role | Hex | Where |
|---|---|---|
| App background | `#f8fafc` | body, table headers, expanded rows |
| Surface | `#ffffff` | every card, table, modal |
| Card border | `#e2e8f0` | all card and input borders |
| Divider | `#f1f5f9` | header/row separators, bar tracks |
| Faint divider | `#f8fafc` | table row borders inside a card |
| Text primary | `#0f172a` | headings, metric values |
| Text strong | `#334155` | table cell text, labels |
| Text body | `#475569` | secondary numeric cells |
| Text secondary | `#64748b` | descriptions, inactive nav |
| Text muted | `#94a3b8` | captions, column headers, placeholders |
| Text disabled | `#cbd5e1` | empty values, disabled arrows, "—" |

### Brand (indigo)

| Token | Hex | Use |
|---|---|---|
| Brand 600 | `#4f46e5` | primary buttons, active dots, chart series 1, focus ring |
| Brand 700 | `#4338ca` | active nav text, button hover, "you" emphasis |
| Brand 800 | `#3730a3` | bulk-selection bar text |
| Brand 500 | `#6366f1` | setup-state values, quota bar |
| Brand 400 | `#818cf8` | disabled/in-progress primary button |
| Brand 200 | `#c7d2fe` | active borders, selected-row borders |
| Brand 100 | `#e0e7ff` | avatar backgrounds |
| Brand 50 | `#eef2ff` | active nav background, selected chips, highlight rows |
| Selected row | `#f5f7ff` | checked table rows |

### Semantic

| Meaning | Strong | Mid | Text-on-tint | Tint background | Tint border |
|---|---|---|---|---|---|
| Success / positive | `#059669` | `#10b981` | `#047857`, `#15803d` | `#ecfdf5`, `#d1fae5`, `#dcfce7`, `#f0fdf4` | `#a7f3d0`, `#bbf7d0` |
| Warning / needs work | `#d97706` | `#f59e0b` | `#b45309`, `#a16207` | `#fffbeb`, `#fef3c7`, `#fef9c3` | — |
| Danger / negative | `#dc2626` | `#ef4444`, `#e11d48` | `#b91c1c`, `#991b1b` | `#fef2f2`, `#fee2e2`, `#fff1f2` | `#fecaca`, `#fca5a5` |
| Info | `#2563eb` | `#3b82f6` | `#1d4ed8` | `#eff6ff`, `#dbeafe` | `#bfdbfe` |
| Neutral / setup | `#64748b` | `#94a3b8` | `#64748b` | `#f1f5f9` | `#e2e8f0` |

### Accents

Purple `#a855f7` / `#7c3aed` / `#7e22ce` on `#f3e8ff` — navigational intent, setup dots,
redirects. Cyan `#0891b2` / `#06b6d4` on `#ecfeff` — Positions module, keyword-list icons.
Orange `#f97316` / `#ea580c` / `#c2410c` on `#ffedd5` — transactional intent.

### Fixed brand colors (do not re-map)

**Modules:** SEO `#4f46e5` · Positions `#0891b2` · Backlinks `#7c3aed` · Site Audit `#dc2626` ·
Ads `#059669` · System/General `#64748b`.

**Platforms:** LinkedIn `#0a66c2` · Reddit `#ff4500` · YouTube `#dc2626` · X `#0f172a` ·
Facebook `#1877f2` · Instagram `#c13584`.

**LLMs:** ChatGPT `#10a37f` · Claude `#d97757` · Gemini `#4285f4` · Perplexity `#20808d`.

### Color as a scale

Four functions turn a number into a colour. Use them; do not invent new bands.

```js
posBadge(p)   // ≤3 green · ≤10 blue · ≤20 amber · else grey · null → transparent
kdColor(kd)   // <30 #10b981 · <60 #f59e0b · else #ef4444
scoreColor(v) // ≥80 #059669 · ≥60 #d97706 · else #dc2626       (audit scores)
asColorOf(as) // ≥60 #059669 · ≥40 #0891b2 · ≥20 #d97706 · else #94a3b8  (authority)
```

---

## 5. Typography

**Inter**, loaded from Google Fonts at weights 400/500/600/700, falling back to
`system-ui, sans-serif`. `monospace` appears only for URLs in the audit drawer and for
API-identifier callouts.

| Size | Weight | Role |
|---|---|---|
| 34 px | 800 | Audit health-gauge number |
| 30 px | 800 | Core Web Vitals value |
| 24 px | 600–700 | KPI value, category score |
| 22 px | 700 | Spotlight metric |
| 18 px | 600–700 | Module stat, modal title |
| 17 px | 600 | Page title (topbar) |
| 16 px | 700 | Modal heading |
| 15 px | 600 | Card heading (`<h2>`) |
| 14 px | 400–600 | Body, table cells, buttons, nav |
| 13.5 px | 400 | Dense table cells (Ads) |
| 13 px | 400–600 | Sub-nav, form labels, secondary body |
| 12.5 px | 500 | Compact buttons, chips |
| 12 px | 400–600 | Captions, subtitles, filter labels |
| 11 px | 500–700 | Uppercase eyebrow labels, column headers, badges |
| 10–10.5 px | 600–700 | Micro badges (intent, module tags) |

Two recurring treatments:

```
Eyebrow:  font-size 11px; text-transform uppercase; letter-spacing .05–.06em;
          font-weight 500–600; color #94a3b8
Th:       font-size 11px; text-transform uppercase; letter-spacing .06em;
          font-weight 500; color #94a3b8; left-aligned (right for numerics)
```

`letter-spacing: -0.01em` is applied to the page title and brand name only.

---

## 6. Spacing & shape

**Spacing scale (px):** 2 · 3 · 4 · 6 · 7 · 8 · 10 · 12 · 14 · 16 · 18 · 20 · 22 · 24 · 28 · 32 · 56.

Conventions: main content padding `24px` · section gap `20px` · card padding `16–18px 18–20px` ·
card header `14–18px 20px` · table cell `10–14px` with first/last columns padded to `20px` on the
outside · empty-state panels `44–56px 20–32px`.

**Radii:** `4px` micro badges · `6px` small controls and menu items · `7px` chips and compact
buttons · `8px` inputs, buttons, nav items · `10px` panels and popovers · `12px` cards ·
`14px` modals · `16px` large modals · `9999px` pills, toggles, progress bars, avatars.

**Borders:** `1px solid #e2e8f0` default · `1.5px` on checkboxes · `2px` on active tab
underlines · `1px dashed #cbd5e1` on editable inline values · `1px dotted #cbd5e1` on
tooltip-bearing text.

**Shadows:**

```
card       0 1px 2px rgba(0,0,0,0.05)
button     0 1px 2px rgba(0,0,0,0.05)   (hover: 0 3px 8px rgba(79,70,229,0.3))
popover    0 12px 32px rgba(15,23,42,0.16)
add-site   0 16px 40px rgba(15,23,42,0.18)
modal      0 24px 60px rgba(15,23,42,0.28)
drawer    -20px 0 50px rgba(15,23,42,0.2)
toast      0 12px 32px rgba(15,23,42,0.28)
```

**Overlay scrims:** `rgba(15,23,42,0.3)` drawer · `0.35` modal · `0.4` password modal (with
`backdrop-filter: blur(2px)`) · `0.75` accept-invite (with `blur(8px)`).

**Z-index ladder:** header `5` · add-site popover `30` · negative-keyword menu `60` ·
page drawer `80` · lists modal `85` · toast `90` · password modal `100` · accept-invite `9999`.

---

## 7. Components

### Card

```
border-radius: 12px; background: white; border: 1px solid #e2e8f0;
box-shadow: 0 1px 2px rgba(0,0,0,0.05);
```

With a header: `padding: 16px 20px; border-bottom: 1px solid #f1f5f9`, containing an `<h2>`
(15 px/600) and a `<p>` subtitle (12 px, `#94a3b8`). Body padding `18px 20px`, or `padding: 0`
when the body is a table.

### KPI card

Card + eyebrow label + a baseline-aligned row of a 24 px/600 value and an optional delta chip,
plus a 12 px muted note.

```
delta chip: font-size 11px; font-weight 600; padding 2px 6px; border-radius 4px
            positive → color #059669, background #ecfdf5
            negative → color #e11d48, background #fff1f2
```

### Clickable card (pillar / module)

Card + `cursor: pointer` + `transition: all .16s` + a `›` arrow in `#cbd5e1`. The whole card is
the hit target. Setup-state cards drop the value to 16 px/600 in `#6366f1` and read "Set up".

### Table

```html
<table style="width:100%; border-collapse:collapse; font-size:14px">
  <thead><tr style="text-align:left; color:#94a3b8; font-size:11px;
                    text-transform:uppercase; letter-spacing:.06em;
                    background:#f8fafc; border-bottom:1px solid #f1f5f9">
  <tbody><tr style="border-bottom:1px solid #f8fafc" style-hover="background:#fcfcfd">
```

Numeric columns right-align. Sortable headers are `cursor: pointer` and append an arrow
(` ↓` / ` ↑`) from `arrow(sort, key)`. A totals row uses `background: #f8fafc; font-weight: 600`
with a `1px solid #e2e8f0` top border. Dense tables (Ads) drop to 13.5 px.

### Chips & badges

| Component | Spec |
|---|---|
| Position badge | `min-width 28px; height 24px; radius 4px; 12px/600`, colour-banded |
| Intent badge | `10px/600 uppercase; padding 2px 6px; radius 4px` in the intent's tint pair |
| Severity chip | `11px/600 uppercase; letter-spacing .04em; padding 3px 8px; radius 4px` |
| Score chip | `min-width 34px; height 22px; radius 4px; 12px/700`, banded by `scoreColor` |
| Authority chip | `min-width 26px; padding 2px 6px; radius 5px; 12px/600`, banded by `asColorOf` |
| Status pill | `11px/600; padding 2px 9px; radius 9999px` |
| Filter chip | `12px/500; padding 5px 11px; radius 999px; 1px border`; active → brand border + `#eef2ff` |
| Segmented button | `4px/500` inside a `#f1f5f9` 4 px-padded track; active → white + card shadow |

### Buttons

There are no `<button>` elements in the app except in the password modal — everything else is a
`<div>`/`<span>` with `role="button"` and `cursor: pointer`.

```
Primary   background #4f46e5; color white; 13–14px/500–600; padding 8–12px 16–20px;
          radius 8px; hover #4338ca or box-shadow 0 3px 8px rgba(79,70,229,0.3)
Success   background #10b981 (page refresh, empty-state fetch); hover #059669
Ghost     border 1px #cbd5e1; background white; color #334155; radius 8px
Danger    color #dc2626; border 1px #fecaca; background #fff5f5
Link      color #4f46e5; 12px/500; hover opacity .7
Disabled  opacity .5; cursor default    (never a separate colour)
Busy      lighter tint (#818cf8 / #6ee7b7) + a spinning icon
```

### Toggle switch

```
track  36–40 × 20–22px; radius 9999px; background on:#4f46e5 off:#cbd5e1;
       transition background .15s
knob   16–18px white circle; position absolute; top 2px; left on:18–20px off:2px;
       transition left .15s
```

Always `role="switch"` with an `aria-label`.

### Checkbox

`15 × 15px; radius 4px; border 1.5px`. Checked is a `#4f46e5` fill with a white SVG tick;
unchecked is white with a `#cbd5e1` border. Always `role="checkbox"` with `aria-checked`.

### Inputs

```
font-size 13–14px; padding 7–10px 12px; border 1px solid #e2e8f0 (or #cbd5e1 on forms);
border-radius 7–8px; outline none
focus → border-color #a5b4fc   (or #4f46e5 + 0 0 0 3px rgba(79,70,229,.1) in modals)
```

Labels are 11–13 px/600 in `#334155` or `#64748b`, 4–6 px above the field. `<select>` uses the
same box with `cursor: pointer`; the topbar site selector sets `appearance: none` and overlays a
positioned SVG.

**Inline edit** (campaign budget): a dashed-underline value that becomes a 62 px input with an
`#a5b4fc` border and `autoFocus`; `Enter` saves, `Escape` cancels, blur saves.

### Progress bar

```
track  height 5–10px; background #f1f5f9; border-radius 9999px; overflow hidden
fill   height 100%; background <semantic>; border-radius 9999px;
       transition width .3–.4s ease
```

### Sub-tab bar

```
inactive  padding 10px 16px; 13px/600; color #64748b;
          border-bottom 2px solid transparent; margin-bottom -1px
active    color #4f46e5; border-bottom 2px solid #4f46e5
```

The `margin-bottom: -1px` overlaps the container's own bottom border so the underline sits flush.

Settings uses a wider variant — `9px 4px; margin-right 20px; 13.5px` — with an optional count
badge (`10.5px/700; padding 1px 7px; radius 9999px`) that turns red when it reads `!`.

---

## 8. Overlays

| Overlay | Position | Size | Dismissal |
|---|---|---|---|
| **Popover** (add site, negative menu, send/export, filters) | `absolute` under the trigger | 268–280 px | trigger click, `Escape` |
| **Modal** (keyword lists, AI targets/composer/config, PT wizard/edit) | fixed, flex-centred | 400–560 px, `max-width: 92vw`, `max-height: 82vh` | scrim click, ✕ |
| **Drawer** (audit page detail, keyword detail, SERP) | fixed right, full height | 440 px, `max-width: 92vw` | scrim click, ✕ |
| **Toast** | fixed, bottom centre, `translateX(-50%)` | auto | 2.6 s timeout |

Modals are a column of header (`18px 22px` + bottom border), scrollable body, and — where
present — an action footer. Drawers follow the same structure.

---

## 9. Charts

Every chart is hand-written inline SVG. No charting library is loaded. (`plotly` is in
`requirements.txt` and `overview_service.build_traffic_chart()` emits a Plotly spec, but nothing
renders it.)

**Line / area** — `viewBox="0 0 600 220"` with `preserveAspectRatio="none"`; points from
`linePts(arr, key, w, h)`. Series are
`<polyline fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">`; the
area is a `<path>` filled with a `<linearGradient>` running `stop-opacity .16 → 0`. Overview adds
invisible per-day `hoverZones` rects that set `chartHoverIndex`, drawing a vertical rule and a
tooltip that flips side past the midpoint.

**Sparkline** — `spark(arr, 46, 16)` inside a table cell; stroke `#22c55e` when the last value ≥
the first, else `#ef4444`.

**Bars** — `<div>` tracks with percentage-width fills, not SVG.

**Stacked distribution** — a flex row whose children carry `flex: <count>` and a segment colour.

**Donut** — an SVG circle with `stroke-dasharray: "<pct> <100-pct>"` and a running
`stroke-dashoffset`.

**Gauge** — a CSS `conic-gradient(<color> <score×3.6>deg, #f1f5f9 0deg)` on a 128 px circle.

**Palettes** — categorical `['#4f46e5','#a855f7','#f59e0b','#ef4444','#10b981','#06b6d4']` ·
sequential `['#4f46e5','#818cf8','#c7d2fe','#e0e7ff']` ·
good/warn/poor `['#059669','#d97706','#dc2626']`.

---

## 10. State patterns

Every data screen implements the same five states. Reuse the exact markup.

**Loading** — four 92 px pulsing blocks plus a 260 px and a 220 px block, all
`background: #e9eef5; border-radius: 12px` with
`animation: fusePulse 1.3s ease-in-out infinite` and staggered delays (0 / .1 / .2 / .3 s).

**Error** — a `#fef2f2` panel with a `#fecaca` border: bold `#991b1b` headline
*"Couldn't load this view"*, the message in `#b91c1c`, and a white **Retry** button.

**Empty (no data yet)** — a white card, `padding: 56px 32px`, centred: a 15 px/600 headline
naming what is missing, a 13 px `#64748b` explanation capped at 420 px, and a green
**⚡ Fetch … Now** button that starts that page's sync.

**Empty (filtered to nothing)** — inline inside the table: `padding: 40–44px 20px`, centred,
*"Nothing here"* + *"No … match this filter."* No fetch button — the data exists, the filter is
too narrow.

**Setup (feature not configured)** — the value is replaced by the word "Set up" in `#6366f1`,
the status dot turns purple `#a855f7`, and the tone key is `setup`.

**Acknowledged / inactive** — `opacity: 0.55` on the row and the action removed.

---

## 11. Interaction patterns

- **Optimistic-then-refetch.** A mutation posts, shows a toast, invalidates the affected cache
  keys, and refetches. The UI is never updated from the response body alone — the one exception
  is alert acknowledgement, which patches the cached feed directly for instant feedback.
- **Every mutation confirms with a toast**, phrased as an outcome and often naming the next step:
  *"…added as a phrase-match negative — written back to Google Ads on next sync"*.
- **Debounced auto-save** for slider-like inputs — alert-rule thresholds 600 ms, budget cap
  500 ms. Explicit forms use a Save button that flips to `Saved ✓` for 1.8 s.
- **Destructive actions use `window.confirm`** — delete user, delete project, clear data.
- **Filter state is navigation state.** `pushNav()` records the active filter alongside the tab,
  so the in-app back button restores the view you were actually looking at.
- **Deep links carry context** — an Overview module lands on the right page; an audit severity
  card lands on Issues pre-filtered; a campaign name in Search Terms opens Campaigns with that
  row expanded.
- **Hover** is expressed with the runtime's `style-hover="…"` attribute
  (`background:#f8fafc`, `border-color:#cbd5e1`, `opacity:0.7`, `color:#4f46e5`), never CSS.
- **Bulk selection** shows a sticky action bar in `#eef2ff` with a `#c7d2fe` bottom border, a
  bold `#3730a3` count, the actions, and a *Clear selection* link.

---

## 12. Icons

Inline SVG only — no icon font, no icon library. House style:

```html
<svg width="14|15|16" height="…" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
```

Sizes: 10–11 px inside chips, 13–16 px in buttons and nav, 20 px for a modal close.
`stroke="currentColor"` is the default so an icon inherits its container's colour.

Emoji are used sparingly and deliberately as *content*, not decoration: segment tabs
(⚡ 🎯 📉 👀), the fetch button (⚡), AI-summary section markers (🔴 🟢 ℹ️), and 🌐 as a
placeholder domain flag.

---

## 13. Responsive behaviour

**The app targets desktop.** The design preview is declared at 1440 × 900. There are **no media
queries** in the application, the sidebar has no collapsed state, and grid column counts are
fixed rather than `auto-fit`.

What does adapt: `flex-wrap: wrap` on every toolbar and meta row, `max-width: 92vw` on modals and
drawers, `min-width: 0` on the main column, and `flex: 1; min-width: 220px` on toolbar segments.
Wide tables extend their container rather than scrolling within it.

If mobile support is ever required, that is a real project, not a tweak.

---

## 14. Dark mode

**Not implemented.** `static/spa/css/global.css` — a leftover from the removed template UI —
declares `:root { color-scheme: light }`, and every colour in the app is a hard-coded
light-theme literal. There is no theme toggle, no CSS custom property, and no
`prefers-color-scheme` query. Adding dark mode would require replacing the inline-style approach
with tokens first.

---

## 15. Accessibility

Implemented in `app.js::installA11y` / `a11ySweep`:

- **Keyboard activation** — `Enter`/`Space` on any `role="button"` or `role="switch"`, with
  native controls left alone.
- **Escape** closes transient popovers and menus.
- **Automatic role promotion** — a `MutationObserver` re-scans after every render and gives leaf
  clickable elements (computed `cursor: pointer`, no interactive descendant) `role="button"` and
  `tabindex="0"`. Table structural tags are excluded, because `role="button"` is invalid on
  `<tr>`/`<td>`.
- **Focus ring** — `:focus-visible { outline: 2px solid #4f46e5; outline-offset: 2px }` forced
  over the inline `outline: none`, and suppressed for mouse users via
  `:focus:not(:focus-visible)`.
- **Reduced motion** — all animations and transitions collapse to 0.001 ms.
- **Labels** — `aria-label` on icon-only controls, `aria-checked` on custom checkboxes,
  `aria-expanded` / `aria-haspopup` on menu triggers, `title` on abbreviated metrics.
- **Semantics** — one `<h1>` per page in the topbar, `<h2>` per card, real
  `<table>`/`<thead>`/`<th>` markup, real `<label>` + `<input>` pairs.

**Known gaps:** no skip-link; no focus trap in modals or drawers; no live region for toasts; no
`aria-sort` on sortable headers; colour is sometimes the only signal (position bands, KD bars);
and several small greys fall below WCAG AA on white (`#94a3b8` ≈ 2.8:1, `#cbd5e1` ≈ 1.7:1).

---

## 16. Component → data relationships

```
index.html
├── accept_invite_modal ← vals.acceptInvite
├── password_modal      ← vals.cpw*
├── sidebar             ← vals.navStyle / dotStyle / h.nav* / hasUnacked / userName / freshness
├── topbar              ← vals.title / subtitle / projects / rangeStyle / refresh*
└── main
    ├── sync banner     ← vals.syncing / syncStep / syncPct / syncEtaText
    ├── error / loading ← vals.hasError, vals.errorText · vals.loading
    └── screens         ← vals.showX  +  one namespace each:

        overview             ov
        seo                  seo
        domain_overview      do
        keywords             kw  (+ res*, rf, rg, rd)
        positioning          pt, ptWs, ptOv, ptPages, ptWiz, ptSerp
        backlinks            bl
        offsite              off
        pages (Site Audit)   au  (+ pd drawer)
        ai (AI Optimization) aiv
        ads / campaigns /
        terms / attribution  ads, cmp, trm, att, adsSync
        alerts               al
        settings             st
```

Each namespace is produced by exactly one file in `js/pages/`. A page fragment must never read
outside its own namespace plus the documented shell values (`h`, `projectDomain`, `projects`,
`toast`, sort helpers) — that boundary is what keeps the includes independent.

---

## 17. Adding UI — the checklist

1. Reuse a token from §4–§6. If you genuinely need a new one, add it to this file in the same
   commit.
2. Build the fragment in `pages/<name>.html` and its view model in `js/pages/<name>.js`; wire
   both with `#include` directives.
3. Compute every conditional style in `renderVals()` and expose it as a single value
   (`r.statusStyle`), so the template stays declarative.
4. Implement all five states from §10 — loading, error, empty-no-data, empty-filtered, setup.
5. Give every clickable element a `role`, an `aria-label` where the text is not self-describing,
   and a `title` where a metric needs explanation.
6. Confirm every mutation with a toast and invalidate the caches it affects.
7. If the screen introduces a filter a user would expect to survive back-navigation, add it to
   `navSnapshot()` / `sameNav()` / `applyNav()`.

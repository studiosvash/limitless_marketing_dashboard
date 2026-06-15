# FuseHealth — Design System

*Read before building or changing any template/CSS. Approved direction: **light, clean & airy**
with an **indigo/violet** brand accent, **Inter** typeface. Every page inherits `base.html` and
must use these tokens — do not introduce ad-hoc colors, fonts, or spacing.*

## Foundations

- **Framework:** Tailwind CSS via **CDN** (no Node build). Brand tokens are registered in the
  `tailwind.config` inside `base.html` so classes like `bg-brand-600` work everywhere.
- **Font:** Inter (Google Fonts), weights 400/500/600/700. Fallback `system-ui, sans-serif`.
- **Feel:** generous whitespace, soft borders, subtle shadows. Calm, premium, low-noise.

## Color tokens

| Role | Tailwind | Hex |
|---|---|---|
| App background | `bg-slate-50` | `#f8fafc` |
| Surface / card | `bg-white` | `#ffffff` |
| Card border | `border-slate-200` | `#e2e8f0` |
| Divider | `border-slate-100` | `#f1f5f9` |
| Text primary | `text-slate-900` | `#0f172a` |
| Text secondary | `text-slate-500` | `#64748b` |
| Text muted / labels | `text-slate-400` | `#94a3b8` |
| **Brand 50** (tints, active nav bg) | `brand-50` | `#eef2ff` |
| **Brand 100** (progress track) | `brand-100` | `#e0e7ff` |
| **Brand 200** (rings/borders) | `brand-200` | `#c7d2fe` |
| **Brand 600** (primary: buttons, active, chart) | `brand-600` | `#4f46e5` |
| **Brand 700** (hover) | `brand-700` | `#4338ca` |
| Success / positive delta | emerald | text `#059669` · bg `#ecfdf5` |
| Warning | amber | text `#d97706` · bg `#fffbeb` |
| Danger / negative delta | rose | text `#e11d48` · bg `#fff1f2` |

Full brand ramp registered in Tailwind config:
`50 #eef2ff · 100 #e0e7ff · 200 #c7d2fe · 300 #a5b4fc · 500 #6366f1 · 600 #4f46e5 · 700 #4338ca · 900 #312e81`

## Typography scale

| Use | Classes |
|---|---|
| Page title (topbar h1) | `text-[17px] font-semibold tracking-tight` |
| Section / card title | `text-[15px] font-semibold tracking-tight` |
| Stat number | `text-2xl font-semibold tracking-tight` |
| Body | `text-sm` (14px) `text-slate-600/900` |
| Small / meta | `text-xs text-slate-400` |
| Eyebrow label | `text-[11px] font-semibold uppercase tracking-wider text-slate-400` |

## Spacing, radius, shadow

- **Card:** `rounded-xl border border-slate-200 bg-white p-5 shadow-sm`
- **Content padding:** `p-6` · **vertical rhythm between blocks:** `space-y-6`
- **Grid gaps:** `gap-4` (cards) · `gap-6` (sections)
- **Radius:** cards/inputs `rounded-xl` (12px); buttons/pills `rounded-lg`
- **Shadow:** `shadow-sm` only. No heavy drop shadows.

## Layout shell (base.html)

- **Sidebar:** `w-60` (240px), `bg-white border-r border-slate-200`, fixed full height. Logo block
  (h-16) + nav + user footer.
- **Topbar:** `h-16 bg-white/80 backdrop-blur border-b border-slate-200`. Holds page title +
  subtitle (left) and date-range + Refresh (right).
- **Content:** scrollable, `p-6 space-y-6`.

## Components (in templates/components/)

- **Nav item** — inactive: `text-slate-600 hover:bg-slate-50`; active: `bg-brand-50 text-brand-700
  font-medium` + a `w-1` `bg-brand-600` left bar.
- **Stat card** — label (`text-sm text-slate-500`), value (`text-2xl`), delta pill.
- **Delta pill** — up: `text-emerald-600 bg-emerald-50` with `▲`; down: `text-rose-600 bg-rose-50`
  with `▼`. Class `px-1.5 py-0.5 rounded text-xs font-medium`.
- **Primary button** — `bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2
  rounded-lg shadow-sm`.
- **Secondary button** — `border border-slate-200 bg-white text-slate-600 hover:text-slate-800`.
- **Refresh button** — primary button + rotating arrows icon; drives the sync flow.
- **Sync progress** — `rounded-xl border border-brand-200 bg-brand-50 p-4`; label + percent;
  track `bg-brand-100`, fill `bg-brand-600`. Updated by HTMX polling (Phase 4).
- **Table** — header row `text-slate-400 text-xs uppercase tracking-wider`; rows
  `divide-y divide-slate-100 hover:bg-slate-50`; numbers right-aligned.
- **Badge** — `text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-400` (e.g. "no data").

## Plotly chart theme (apply to every chart)

```python
layout = dict(
    font=dict(family="Inter", size=12, color="#64748b"),
    paper_bgcolor="white", plot_bgcolor="white",
    margin=dict(l=40, r=40, t=10, b=30),
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor="#f1f5f9", zeroline=False),
    legend=dict(orientation="h", y=1.15, x=0),
    hovermode="x unified",
)
config = dict(displayModeBar=False, responsive=True)
```

- Primary series: `#4f46e5`, width 3, `shape="spline"`, soft fill `rgba(79,70,229,0.08)`.
- Secondary series: `#94a3b8`, width 2, `dash="dot"`.
- Categorical palette (multi-series): `#4f46e5 · #0d9488 · #f59e0b · #f43f5e · #8b5cf6 · #0ea5e9 · #10b981`.

## Rules

1. Inherit `base.html`; never hand-roll a page shell.
2. Use only the tokens above — no off-palette hex, no other fonts.
3. HTMX-swappable regions are small **partials** (a card, a table, the progress bar), never a
   whole page.
4. Charts always use the Plotly theme above so they feel consistent.
5. Keep it airy: when in doubt, add whitespace, not borders.

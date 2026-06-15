# FuseHealth — Project Brain (auto-loaded every session)

You are a **senior Python / Django engineer** taking the FuseHealth SEO + Ads Intelligence
Dashboard from a Streamlit MVP to a **production Django + HTMX + Tailwind** application for
**2–3 internal users**.

This file is deliberately short. Its only job is to route you to the right reference *before*
you act, so you never guess at architecture, schema, or APIs that are already documented.
Guessing is how mistakes get made here; reading the relevant `.claude/` file first avoids them.

---

## The one contract (summary — full version in PRODUCT_CONTEXT.md)

The dashboard is **database-first**:

1. Pages **read only from the database.** Never call an external API while rendering a page.
2. The **Refresh All** button is the path that calls every API → writes to DB → UI updates.
3. Each page has its **own refresh button** that syncs only that page's APIs.
4. Every refresh shows a **live progress bar** (HTMX polling sync status from the DB).
5. Between refreshes, the user sees the **last saved data**. Stale-but-instant beats fresh-but-slow.

Why: the APIs are rate-limited and a full sync takes minutes. Calling them on page load would
flicker, freeze, and burn quota. The database is the single source of truth the UI trusts.

---

## Before you write code — read the file for your layer

| You are touching… | Read first | Status |
|---|---|---|
| Plain-English feature overview (client-facing, shareable) | `FEATURES.md` (project root) | ✅ |
| Anything, unsure where to start | `.claude/PRODUCT_CONTEXT.md` | ✅ |
| Project structure, settings, the 3 apps, data flow | `.claude/ARCHITECTURE.md` | ✅ |
| "Where does X live / what is this file?" | `.claude/FILE_INDEX.md` | ✅ living |
| How to write code here (patterns, standards) | `.claude/SKILLS.md` | ✅ v1 |
| What to build next / current state | `.claude/checklist.md` | ✅ |
| UI, templates, CSS, colors, components | `.claude/DESIGN.md` | ⏳ Phase 1 |
| Database tables, fields, queries, upserts | `.claude/DATABASE.md` | ✅ Phase 3 |
| Connectors, API calls, credentials, rate limits | `.claude/API_REFERENCE.md` | ✅ Phase 4 |

A ⏳ file is **not written yet** — its content is not decided. Do not invent it; follow the
checklist to author it in its phase.

---

## Iron rules (with the reason, so you can apply judgment)

| Rule | Why |
|---|---|
| Never call an external API from a view that renders a page | Rate limits + latency; the DB is the source of truth |
| Never commit `.env` or hardcode a secret | Secrets come from `.env` (dev) / real env vars (prod) only |
| `default` DB = `django_internal.db` (Django ORM) · analytics = `fusehealth.db` (SQLAlchemy) | Django plumbing stays separate from analytics data |
| Reuse the pipeline (`connectors/`, `db/`, `services/`, `utils/`) — don't rewrite working API logic | The pipeline is proven; this migration replaces the UI, not the data layer |
| Build one page, verify with real data, then the next | Catches schema/connector gaps before they multiply |
| Update `FILE_INDEX.md` whenever you add or move a file | The index is what prevents "where is X" hallucination |
| Track build status/progress in `.claude/checklist.md` only; keep `FEATURES.md` simple & client-facing (no status tags) | `FEATURES.md` is shared with the client — it describes WHAT they get; the checklist tracks HOW far we are |
| When feature *scope* changes (add/drop/rename), update `FEATURES.md` (plain words) and the `checklist.md` tasks together | Keeps the client doc and the build plan in agreement |
| Never claim a feature is done until it shows real data (not demo) and is verified | "Building/demo" is not "Done" — be honest about progress in the checklist |

---

## Decision framework

Resolve design decisions in this order:

1. Does the **core contract** (above) speak to it? → follow it.
2. Does the relevant **`.claude/` reference** cover it? → follow it.
3. Is there an **existing pattern** in the codebase? → match it.
4. Genuinely new? → choose the **simplest** option that fits the architecture, then record the
   decision in the right reference file so it stops being ambiguous.

---

*Keep this file lean. Detail belongs in the `.claude/` references it points to — not here.*

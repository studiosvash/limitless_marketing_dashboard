# FuseHealth — Project Brain (auto-loaded every session)

You are a **senior Python / Django engineer** working on the FuseHealth (Limitless) SEO + Ads
Intelligence Dashboard: a **Django 6 + DRF backend serving a single-page frontend** for
**2–3 internal users**.

This file is deliberately short. Its only job is to route you to the right reference *before*
you act, so you never guess at architecture, schema, or APIs that are already documented.
Guessing is how mistakes get made here; reading the relevant `.claude/` file first avoids them.

---

## The one contract

The dashboard is **database-first**:

1. Pages **read only from the database.** Never call an external API while rendering a page.
2. The **Refresh all** button is the path that calls every API → writes to DB → UI updates.
3. Each page has its **own refresh button** that syncs only that page's APIs.
4. Every refresh shows a **live progress bar** (the SPA polls `GET /api/tasks/<id>` every 500 ms).
5. Between refreshes, the user sees the **last saved data**. Stale-but-instant beats fresh-but-slow.

Why: the APIs are rate-limited and a full sync takes minutes. Calling them on page load would
flicker, freeze, and burn quota. The database is the single source of truth the UI trusts.

The only sanctioned exceptions are three explicit user lookups — `/api/research`,
`/api/domain-overview`, `/api/live-serp` — which call an API because the user pressed a button.

---

## Before you write code — read the file for your layer

| You are touching… | Read first |
|---|---|
| **Anything. Start here.** How to work in this codebase, patterns, traps, checklists | `.claude/skills.md` |
| Endpoints, request/response shapes, external API integrations | `.claude/api-reference.md` |
| What each page does, user flows, permissions, known gaps | `.claude/features.md` |
| UI tokens, components, layout, states, accessibility | `.claude/design.md` |
| Frameworks, databases, dependencies, env vars, deployment | `.claude/tech-stack.md` |

These five files were reverse-engineered from the current code and are the authoritative
description of it. `FEATURES.md` (project root), `docs/superpowers/`, `Design_features/` and
`scratch/` are historical or throwaway material — **do not treat them as specifications.**

---

## Iron rules (with the reason, so you can apply judgment)

| Rule | Why |
|---|---|
| Never call an external API from a page-data endpoint | Rate limits + latency; the DB is the source of truth |
| Every API view needs `@method_decorator(login_not_required, name="dispatch")` | `LoginRequiredMiddleware` runs before DRF; without it, token requests are 302'd to the login page |
| Never fabricate data to fill a shape — return empty, `null`, or `state: "setup"` | An invented number that looks real is worse than a visible gap |
| Never commit `.env` or hardcode a secret | Secrets come from `.env` (dev) / real env vars (prod) only |
| `default` DB = `django_internal.db` (Django ORM) · analytics = `data/fusehealth.db` (SQLAlchemy) | Django plumbing stays separate from analytics data; the join key is the `site_url` string |
| Analytics writes always go through a `pipeline/db/writer.py` upsert | Re-syncs must update, never duplicate |
| Reuse the pipeline (`connectors/`, `db/`, `services/`, `utils/`) — don't rewrite working API logic | The pipeline is proven |
| Views resolve and delegate; services compute; connectors fetch; writers persist | One concern per file |
| Never claim a feature is done until it shows real data (not a placeholder) and is verified | Several screens are fully built over data sources that don't exist — see `features.md` §17 |
| Update the relevant `.claude/` file in the same change as the behaviour it describes | A stale doc is worse than none |

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

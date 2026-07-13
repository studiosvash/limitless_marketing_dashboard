# Phase E — Settings Design Spec

> Status: approved, self-authored (continuing autonomously per user's standing "continue
> according to plan, finish ASAP" instruction). Branched from `phase-d-ai-optimization`.

## Why this phase needs an unusually disciplined scope cut

Settings is the largest single tab in the SPA (528 template lines, 8 sub-tabs: General, Team &
Access, Connections, Automation, Usage & Budget, Alerts & Rules, AI Summaries, Security & Data)
and it is fed by **one endpoint pair** — `GET`/`PUT /api/projects/<slug>/settings` — that the SPA
reads/writes as ~15 flat top-level keys, **all dereferenced unguarded** (confirmed by direct
research against `static/spa/index.html:3557-3576`, not the design doc). An honest response
missing or nulling even one key crashes the whole tab, not one widget — so this phase's GET must
return a fully-shaped object for every key from day one.

**Applying the Phase D lesson explicitly**: every mutation contract below was verified against
the actual SPA call sites (`aiPost`/`putSettings`/`FuseAPI.put` invocations in
`static/spa/index.html`), not against `HANDOFF_SPEC.md`'s documented shape — the two diverge in
at least one place already known (HANDOFF_SPEC's own §9.4 concedes the Team/SSO/2FA "real auth
flows" don't exist and "persisting the JSON is enough for v1").

**Why several sub-tabs are scoped out entirely, not just partially:** research found the
original fixture **fabricates** several settings as if they were real: `workspace.plan:
"Growth"`/`mrr: 149`/`seats_used: 3` (no billing system exists anywhere in this codebase),
`security.twofa: true` (no 2FA implementation — no OTP model, nothing), `platformConnectors.
linkedin: true` (no LinkedIn connector, same credential-blocked status as every other social
platform since C3), and `createToken()` generates a **fake secret client-side**
(`'lm_live_' + Math.random()...`, never touching a server, never authenticating anything). These
aren't "not yet built" gaps like C1-C4's DataForSEO connectors — they're places where shipping
the fixture's shape as a real default would be a **direct, active fabrication** (claiming 2FA is
on, claiming a real API token was minted, claiming a connector is live) rather than an honest
absence. The responsible choice for these is not "return honest zeros" but "don't build the
mutation at all yet" — a fake-but-plausible security control (2FA toggle that does nothing, a
token that authenticates nothing) is worse than an honestly-missing one.

## What's real vs. net-new vs. explicitly out of scope

| Group | Backing | Status |
|---|---|---|
| `project` (id/domain/name/vertical/location/competitors) | Real — `Site` model + `pipeline.services.competitor_service` (already used by the legacy `dashboard/settings.html` view) | **Real, buildable** |
| `credentials` (gsc_property/ga4_property_id/dataforseo_target_domain) | Real — `pipeline.services.site_service.update_site`, exact same fields the legacy `update_site_credentials` view already writes | **Real, buildable, incl. mutation** |
| `connectors` (name/status/last_sync/records) | Real — `apps.sync.models.SyncLog`, one row per (connector, site_url), already used by the legacy Settings view | **Real reshape** |
| `team` | Real — the app's actual 3 Django users (`founder`/`seo`/`ads`, `apps.accounts.models`) with their real roles and real `last_login` | **Real, READ-ONLY** — no invite/add/remove-user mutation (the real system has no such concept; building a fake one would repeat the exact "Team & Access" fabrication this design explicitly rejects above) |
| `workspace`, `notifications`, `aiConfig`, `dataPrefs`, `syncConfig`, `platformConnectors`, `budget.cap`/`.enforce`, `alertRules`, `crawl` | No dedicated relational need — HANDOFF_SPEC's own §9 explicitly says "persisting the JSON is enough for v1" for the security/team equivalents, and the same reasoning applies here: nothing downstream reads these values yet (no cron sends digests, no code enforces a budget cap, no crawl-config field gates the real DataForSEO crawl params) | **Real, GENUINE persistence** via one new `ProjectSettings.data` JSONField blob — saves survive reload (not fake), but explicitly disclosed as not-yet-wired to any downstream system. Honest static defaults synthesized on first read if never saved. |
| `budget.quotas` (ga4_tokens_used/limit, ads_ops_used/limit, gsc_queries_used/limit) | No quota-tracking counter exists anywhere in `apps/`/`pipeline/` | Honest `0`/reasonable static limits, not fabricated usage numbers |
| `security` (2FA, SSO, sessions, tokens), `sync` cadence *enforcement*, Danger Zone (transfer/delete workspace), Download-all/GDPR-delete | No real backing AND shipping a working-looking mutation would be an active fabrication of a security/compliance control (see rationale above) | **Explicitly out of scope** — GET still returns an honest, non-crashing shape (real single-session note, real single per-user DRF token if one exists, `twofa`/`sso` honestly `false`), but no new mutation is built for any of these this phase |
| Alert rule *thresholds actually gating alert generation* (vs. just persisting the 4 threshold values) | `apps/dashboard/services/alerts_service.py`/`decision_engine.py` exist and generate real alerts today with hardcoded thresholds | Persisting `alertRules` config is this phase's job (honest, real, survives reload); **wiring the persisted thresholds into `alerts_service.py`'s actual generation logic is explicitly out of scope** — real, valuable, separate work for a future phase, not a guess to make now |

## Mutation contract (verified against the SPA's actual call sites)

The SPA's `putSettings(body, msg, flag)` (`index.html:4028`) always calls `PUT
/api/projects/<pid>/settings` with a **partial** body containing only the top-level key(s)
being changed (e.g. `{workspace: {...}}`, `{budgetCap: 50}`, `{platformConnectors: {...}}`), then
re-fetches GET — same "ack + reload is the source of truth" pattern established in Phase D.

| Key(s) in PUT body | Effect |
|---|---|
| `credentials` | Real — `update_site(site_pk, gsc_property=..., ga4_property_id=..., dataforseo_target_domain=...)` |
| `project.competitors` (sent as part of a workspace/project save — verify exact call site at implementation; if not actually wired in the SPA's current handlers, do not invent a route for it) | Real — `competitor_service.set_tracked_competitors` |
| `workspace`, `notifications`, `aiConfig`, `dataPrefs`, `syncConfig`, `platformConnectors`, `budgetCap`, `budgetEnforce`, `alertRules`, `crawl` | Merge into `ProjectSettings.data[<key>]` (or `data['budget']['cap']`/`['enforce']` for the two flat budget keys) — genuine persistence, real 200, honestly disclosed as not-yet-wired downstream where applicable |
| `team`, `security` | **Reject with a clear 400** ("not yet available") rather than a silent no-op 200 — per the Phase D lesson, a fake-success response for a security/team-membership change would be actively misleading, worse than an honest error |

## Architecture

- New Django ORM model `ProjectSettings` (`apps/dashboard/models.py`): `site_url` (unique),
  `data` (`JSONField`, default `{}`) — one flexible blob for every "no dedicated relational
  need" group above, same `site_url`-string-keyed pattern as `Insight`/`AITarget`.
- New file `apps/dashboard/services/settings_service.py`:
  - `query_connectors_raw(site_id)` — real reshape of `SyncLog` rows into the SPA's
    `connectors[]` shape (name/status/last_sync/records).
  - `query_team_raw()` — real reshape of the 3 real Django users (id/username/role/
    `last_login`) — no email field exists on these seeded users (confirmed by research), so
    `email` is honestly blank, not invented.
  - `DEFAULT_SETTINGS_BLOB` — the honest static defaults for every blob-backed group (real
    reasonable system defaults, e.g. `syncConfig` cadences matching each connector's actual
    intended sync frequency — not the fixture's fabricated workspace/billing numbers, which
    become honest blanks/zeros instead).
  - `build_settings_response(site_id) -> dict` — assembles everything.
- `apps/api/views.py`: `ProjectSettingsView` (`GET`/`PUT`, no range param — Settings has no
  period concept, matching Backlinks/SiteAudit/Alerts/AI).
- **SPA fidelity check** (mandatory per the by-now-standard practice, and especially important
  here given the unguarded-flat-read finding): after Tasks 1-3 ship the real response shape,
  independently re-trace the ENTIRE Settings computed-values block (`index.html:6311-6495`)
  against the actual shape `build_settings_response` returns — not against this design doc's
  table — field by field, the same way Phase D's final review caught two bugs task-level
  reviews missed. Additionally: fix the hardcoded "All healthy" Connections header
  (`index.html:2896`) to reflect real `SyncLog` error/never-run states, since shipping it
  unguarded is a hardcoded-honesty violation the same class as C3's LinkedIn badge.

## Verification

- Full suite green.
- No existing page/view touched — 100% new-shape work (the legacy `update_site_credentials`
  Django view stays as-is; its underlying `update_site`/`competitor_service` functions are
  reused, not modified).
- `GET /api/projects/<slug>/settings` returns real `project`/`credentials`/`connectors`/`team`
  plus a fully-shaped, honestly-defaulted blob for everything else — never the fixture's
  fabricated billing/2FA/connector-status numbers.
- `PUT` persists real changes for `credentials` and every blob-backed key; `team`/`security`
  mutations return a clean 400, never a false-success 200.
- SPA renders every Settings sub-tab without crashing (the unguarded-15-key-read finding is
  resolved by returning a real, fully-shaped object for all 15 keys, not by adding a guard).

## Explicitly out of scope

- Team invite/role-change/remove-member mutations (the real system has exactly 3 fixed
  users with no invite concept — building a fake multi-seat flow would repeat the exact
  fabrication this design rejects).
- 2FA/SSO enable, session revocation, API token creation/revocation (fake-security-control
  risk — see rationale above; real multi-token-per-user support would need new auth
  infrastructure beyond DRF's one-token-per-user default, a separate, real feature).
- Wiring persisted `alertRules` thresholds into `alerts_service.py`'s actual generation logic
  (persisting the config is this phase's job; consuming it is real, separate future work).
- Real quota/usage-counter tracking (`budget.quotas`), real notification-sending (email/Slack),
  real crawl-config enforcement, Danger Zone (transfer/delete workspace), Download-all/GDPR
  export — no infrastructure exists for any of these; persisting the config values is honest
  and in scope, actually *doing* any of them is not.
- Phase F (production hardening + deploy).

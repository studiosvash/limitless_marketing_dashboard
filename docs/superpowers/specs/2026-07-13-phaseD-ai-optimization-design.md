# Phase D — AI Optimization Design Spec

> Status: approved, self-authored (continuing autonomously per user's standing "continue
> according to plan, finish ASAP" instruction). First genuinely NET-NEW feature phase — no old
> MVP page exists for this at all, unlike every Phase B/C page. Branched from `phase-c4-ads`.

## Why this phase is architecturally different from every prior phase

Phases B/C all ported or honestly-reshaped **existing** query logic against **existing** tables.
AI Optimization has almost no existing backend at all — and, uniquely, requires **real
first-party mutation endpoints** (not just GET+cache), because the wizard and every "Add
prompts"/"Edit targets"/"New list" action in the approved SPA persist user input (brand name,
tracked competitors, prompt text, prompt lists) that must survive a page reload. Unlike C4's Ads
mutations (deferred because they write to an *external* Google Ads API against data that doesn't
exist), these mutations write to *our own* database and are needed for the page to function at
all — there's no honest way to ship a GET-only AI Optimization tab.

**Two genuinely different meanings of "AI" already coexist in this codebase — do not conflate
them:**
1. `overview_service.get_ai_summary_text`/`parse_ai_summary` — an LLM (OpenAI) used **internally**
   to *summarize our own SEO data* for the Overview page. Unrelated to this phase.
2. **AI Optimization** (this phase) — monitoring how **external AI answer engines** (ChatGPT,
   Claude, Gemini, Perplexity) mention the client's brand in response to tracked prompts. This
   needs an "LLM Mentions API" / "LLM Responses API" / a scraper — **none of which exist in this
   codebase in any form** (confirmed: no connector, no table, zero references anywhere in
   `pipeline/`).

## What's real vs. 100% net-new (no backend exists at all)

| Feature slice | Backing | Status |
|---|---|---|
| `targets` (brand/aliases/competitors), `lists`, `prompts` (text + per-prompt config) | Plain first-party persistence — new Django models, no external API needed | **Real, buildable now** |
| `setupDone` | Derived from whether a target row with a non-empty brand exists | **Real, buildable now** |
| `aiKeywords[]` ("How People Ask AI") | Real — `pipeline/connectors/dataforseo_ai_keywords.py` + `AIKeywordData` table already exist (same credential-blocked status as every other DataForSEO connector — 0 rows today, but the code path and schema are real) | **Real reshape** (honest empty today) |
| `sov{}`, `kpis.mentions/impressions/cited_pages`, `trend[]`, `topPages[]`, `topDomains[]`, `prompts[].results`, `suggestions[]`, `history[]` | Would require an LLM Mentions API + LLM Responses API + an "inspect" scraper — **zero connector code, zero backing table, anywhere** | Honest `[]` / zero-object |
| `budget{}`, `costs{}`, `next_run` | No cost-tracking/scheduling infrastructure exists for this feature | Honest `0`/`None` |
| `mentionPlatforms[]`, `llmPlatforms[]` | Static, real capability list (which platforms this feature is *designed* to eventually check — same category as C3's `connectors{linkedin,...}` boolean map: real information about system capability, not user data) | Real (static) |
| `run` (trigger an LLM Responses check), `inspect` (trigger a scraper "ask the AI live" check) | Both call external LLM/scraper APIs that don't exist | **Explicitly out of scope** — see below |
| Keyword Explorer (`POST /api/research`), Prompt Explorer (`POST /api/prompt-research`) | 4 of 5 DataForSEO Labs algorithms (`keyword_ideas`/`keyword_suggestions`×2/`related_keywords`) have no connector at all; prompt template-expansion engine is 100% net-new | **Explicitly out of scope** — same "real, unvalidated integration work for a future phase" pattern as C1's 5 missing Backlinks sub-endpoints |

## Mutation contract (verified against the approved SPA's own call sites — `static/spa/index.html:4206-4285`)

The SPA always re-fetches `GET /api/projects/<slug>/ai` after any mutation (`aiReload()`) — every
mutation endpoint only needs to persist the change and return a minimal ack; the full truth is
always re-derived by the next GET, exactly like this project's existing pattern of "the DB is the
source of truth, never trust a mutation's own echo."

| Endpoint | Body | Response (only fields the SPA actually reads) | Effect |
|---|---|---|---|
| `POST /ai/setup` | `{brand, aliases[], competitors[], prompts[]}` | `{}` (ack only) | Upserts `AITarget` (marks `setup_done=True`), bulk-creates `AIPrompt` rows (no list) |
| `POST /ai/targets` | `{brand, aliases[], competitors[]}` | `{}` | Updates existing `AITarget` row |
| `POST /ai/prompts` | `{texts[], listId}` | `{"added": <int>}` | Bulk-creates `AIPrompt` rows, optionally scoped to a list |
| `POST /ai/prompts-remove` | `{id}` | `{}` | Deletes one `AIPrompt` row |
| `POST /ai/prompts-config` | `{id, models[]}` | `{}` | Updates `AIPrompt.tracked_models` (which LLMs this prompt *would* check once `run` exists — honest persisted preference, not a live check) |
| `POST /ai/lists` | `{op: "create"\|"rename"\|"delete", id, name}` | `{"id": <int>}` on create (SPA immediately uses this to add prompts to the new list) | CRUD on `AIPromptList` |

**`run`/`inspect` are explicitly out of scope** — they call external LLM Responses/scraper APIs
this codebase has no connector for. Returning a 4xx/clear "not yet available" response from these
two routes (added but not fully implemented) is preferable to leaving them 404 and silently
breaking the "Run now"/"Inspect" buttons with a generic network error — but building them for
real is future, credential/API-design work, not this phase's job.

## Architecture

- New Django ORM models in `apps/dashboard/models.py` (this is genuinely first-party app state,
  not analytics data — same `site_url`-string-keyed pattern as the existing `Insight` model,
  joined to the SQLAlchemy `Site` the same way every `apps.api` view already does via
  `resolve_project_or_404(slug).site_url`):
  - `AITarget(site_url unique, brand, aliases JSONField, competitors JSONField, setup_done bool, created_at, updated_at)`
  - `AIPromptList(site_url, name, created_at)`
  - `AIPrompt(site_url, list FK nullable, text, tracked_models JSONField default=[], created_at)`
- New file `apps/dashboard/services/ai_service.py`:
  - `query_ai_keywords_raw(site_id) -> list[dict]` — real reshape of `AIKeywordData` rows into
    the SPA's `aiKeywords[]` row shape (`kw`, `aiVolume`, `gVolume`, `ratio`, `intent`, `trend[12]`,
    `mentions`, `gap`) — `mentions`/`gap` are honestly always `0`/`false` (no LLM Mentions data
    exists to compute them from; NOT derived from `AIKeywordData` at all).
  - `build_ai_response(site_id) -> dict` — assembles real `targets`/`lists`/`prompts`/
    `setupDone`/`aiKeywords`/`mentionPlatforms`/`llmPlatforms` plus honest empty/zero for
    everything requiring the LLM Mentions/Responses/scraper infrastructure that doesn't exist.
- `apps/api/views.py`: `ProjectAIView` (`GET`) + a `ProjectAIActionView` (`POST
  /api/projects/<slug>/ai/<action>`) dispatching to the 6 real mutation handlers above by
  `action` path segment, `login_not_required`, same auth pattern as every other view.
- **SPA fidelity fix, two parts** (same discipline as every Phase C page, now standard practice
  per the Phase C retrospective):
  1. **Crash risk**: `if (tab === 'ai')`'s main-dashboard branch does `d.trend[0].date` /
     `d.trend[d.trend.length-1].date` (`static/spa/index.html:5627`ish, verify exact line at
     implementation) with no length guard — `trend` is honestly `[]` (no LLM Mentions data), so
     `d.trend[0]` is `undefined` → `.date` throws. Also verify `d.targets.brand`/`.aliases`/
     `.competitors` are dereferenced before `setupDone` is even checked (`~5491-5493`) — since
     `build_ai_response` always returns a real (if empty-valued) `targets` object, this itself
     is safe, but confirm no other unguarded chain exists in the wizard-prefill path.
  2. **Hardcoded-honesty**: the Keyword Explorer's "Live" badge (`static/spa/index.html:455`) is
     hardcoded markup with **zero data binding at all** — a flat false claim once served against
     a real (non-fixture) backend, since Keyword Explorer's own endpoint is explicitly out of
     scope this phase. Remove or replace with an honest "Coming soon"-style label — this is not
     a "gate on real data" fix like C3/C4's, since there's no real endpoint at all to gate on;
     the honest fix is removing the false claim, not conditionally hiding it.

## Verification

- Full suite green.
- No existing page/view is touched — this is 100% new-shape work.
- `GET /api/projects/<slug>/ai` returns real `targets`/`lists`/`prompts`/`setupDone`/
  `aiKeywords` (currently empty since `AIKeywordData` has 0 rows) and honest `[]`/`0`/`None` for
  every field requiring infrastructure that doesn't exist — never fabricated mentions, SOV, or
  trend data.
- Mutations persist correctly and are reflected on the next `GET` (matches the SPA's own
  reload-after-mutate pattern — no mutation response needs to carry authoritative state).
- SPA renders the AI Optimization tab (wizard AND dashboard states) without crashing, and the
  Keyword Explorer no longer falsely claims to be "Live."

## Explicitly out of scope

- `run`/`inspect` actions (real external LLM Responses API / scraper integration).
- Keyword Explorer (`POST /api/research`) and Prompt Explorer (`POST /api/prompt-research`) —
  4 of 5 DataForSEO Labs algorithms + a 100%-net-new prompt template-expansion engine.
- `sov`/`trend`/`topPages`/`topDomains`/`prompts[].results`/`suggestions`/`history` real data —
  needs the LLM Mentions/Responses APIs this codebase has no connector for.
- Phase E (Settings expansion), Phase F (deploy).

"""AI Optimization page — assembles the response from things that really exist.

Four real sources, and nothing else:

1. **First-party ORM data** — `AITarget` / `AIPromptList` / `AIPrompt` (targets, lists, prompts,
   `setupDone`).
2. **`AIKeywordData`** (analytics DB) — reshaped into `aiKeywords`.
3. **Stored answer-engine checks** — what `pipeline/services/ai_visibility_service.check_prompt`
   actually observed, written by the `run`/`inspect` actions in `apps/api/views.py` and read back
   here as `prompts[].results`, `prompts[].lastRun`, `history`, and `kpis.prompt_coverage`. Their
   real USD cost is read back out of the `connector_costs` table.
4. **Stored DataForSEO LLM Mentions snapshots** — assembled by
   `apps.dashboard.services.llm_mentions_service.build_visibility_block` from the
   `llm_mention_metrics` / `llm_cited_pages` tables and merged in here as `sov`, `mentionPlatforms`,
   `topPages`, `topDomains`, `visibilityState`, and `kpis.mentions`/`.impressions`/`.cited_pages`.

Everything with no source is `0` / `None` / `[]` and stays that way. `trend` and `suggestions`
are the honest empties: a trend line needs a stable weekly series to chart against, and while
LLM Mentions snapshots are now being collected weekly, the chart itself is not wired yet in this
release; a real prompt-suggestion engine does not exist. A plausible-looking number in either of
those slots is worse than a visible gap.
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from apps.dashboard.models import AITarget, AIPromptList, AIPrompt, ProjectSettings
from apps.dashboard.services.llm_mentions_service import build_visibility_block
from apps.dashboard.services.mutation_state import get_state, set_state
from pipeline.db.schema import AIKeywordData, ConnectorCost
from pipeline.db.writer import ensure_tables, insert_connector_cost
from pipeline.services.ai_visibility_service import (
    check_prompt, connected_platforms, is_platform_connected, not_connected_result,
    not_connected_reason, platform_name,
)
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import resolve_site_ids

logger = logging.getLogger(__name__)

# The SPA reads pl2.name (not .label) off both mentionPlatforms and llmPlatforms, and treats
# llmPlatforms as the SAME {id,name,color} object shape as mentionPlatforms (pl2.id/.name/.color
# are all dereferenced against it) -- not a bare id string.
MENTION_PLATFORMS = [
    {"id": "chatgpt", "name": "ChatGPT", "color": "#10a37f"},
    {"id": "claude", "name": "Claude", "color": "#d97757"},
    {"id": "gemini", "name": "Gemini", "color": "#4285f4"},
    {"id": "perplexity", "name": "Perplexity", "color": "#20808d"},
]

# ── Where a run is stored ────────────────────────────────────────────────────────────────────
# The ProjectSettings JSON blob, via mutation_state.get_state/set_state — the same mechanism
# alert acks, hidden audit checks and ads overrides already use. Chosen because a new Django
# model + migration would have to land in apps/dashboard/models.py, which this change does not
# own; these keys are distinct from every group name settings_service routes, so a Settings PUT
# cannot clobber them.
#
# The limits of a JSON blob are real and are accepted deliberately, not overlooked:
#   * the whole blob is read and rewritten on every access — no partial update, no index, so
#     history is capped at MAX_HISTORY entries and only the LATEST result per (prompt, platform)
#     is kept. Older runs are dropped, not archived;
#   * two concurrent runs are last-write-wins (acceptable at 2-3 internal users, not beyond);
#   * you cannot query it — "every check where a competitor outranked us" needs a table scan in
#     Python, so trend/share-of-voice over time stay out of scope until a real table exists.
# The follow-up is a proper `AIRunResult` model (site_url, prompt_id, platform, checked_at,
# verdict, position, cost, answer) in apps/dashboard/models.py; see the report.
RESULTS_KEY = "aiPromptResults"   # {"<prompt_id>": {"results": {...}, "lastRun": iso}}
HISTORY_KEY = "aiRunHistory"      # [entry, ...] newest first
MAX_HISTORY = 50

# Per-prompt cadence/country/city/webSearch. AIPrompt has no columns for these -- adding them
# would need a migration this change does not own -- so they live in the same JSON blob as
# RESULTS_KEY/HISTORY_KEY, keyed by prompt id like RESULTS_KEY is. Before this existed,
# `prompts-config` accepted the fields and silently discarded them: the modal showed a Save
# button for values that were never actually persisted.
PROMPT_CFG_KEY = "aiPromptCfg"    # {"<prompt_id>": {"cadence": "weekly", "country": "", ...}}
DEFAULT_PROMPT_CFG = {"cadence": "weekly", "country": "", "city": "", "webSearch": False}

# connector_costs.connector values this page writes and reads back.
COST_CONNECTOR_RUN = "ai_visibility_run"
COST_CONNECTOR_INSPECT = "ai_visibility_inspect"
AI_COST_CONNECTORS = (COST_CONNECTOR_RUN, COST_CONNECTOR_INSPECT)


def _resolve_site_ids(site_id: str) -> list[str]:
    """Every spelling this site's analytics rows may be keyed under. Delegates to the one
    matcher in `pipeline/utils/site_ids.py`.

    This used to expand only the `sc-domain:` prefix, which is why this page rendered empty for
    a project registered as `premierstaff.com` whose `ai_keyword_data` rows had been written
    under `https://premierstaff.com/`."""
    return resolve_site_ids(site_id)


def query_ai_keywords_raw(site_id: str) -> list[dict]:
    """Real reshape of AIKeywordData for the latest captured snapshot date.

    AIKeywordData rows are captured as one full snapshot per sync date, so "latest date" is the
    correct notion of current state, not a per-keyword max-date dedup.

    `mentions`/`gap` are ALWAYS 0/False: they describe answer-engine mentions of a *keyword*,
    which nothing in this codebase measures (the visibility checker measures mentions of a
    *brand* in a *prompt's* answer — a different thing). Deriving them from search volume, as
    an earlier revision did, invented a signal.
    """
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            # _cost_rows already self-provisions its table this way; this query didn't, so a
            # database created before ai_keyword_data existed raised here, was caught below, and
            # silently reported zero AI keywords with only a log line -- indistinguishable from
            # "this project genuinely has none."
            ensure_tables(session, AIKeywordData)
            latest = session.execute(
                select(func.max(AIKeywordData.date)).where(AIKeywordData.site_id.in_(site_ids))
            ).scalar()
            if latest is None:
                return []
            rows = session.execute(
                select(AIKeywordData)
                .where(AIKeywordData.site_id.in_(site_ids), AIKeywordData.date == latest)
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_ai_keywords_raw error: {e}", exc_info=True)
        return []

    out = []
    for r in rows:
        ai_vol = r.ai_search_volume or 0
        g_vol = r.search_volume or 0
        try:
            monthly = json.loads(r.trend) if r.trend else []
        except (ValueError, TypeError):
            monthly = []
        # trend is stored as a list of {year, month, ai_search_volume} objects (see
        # pipeline/connectors/dataforseo_ai_keywords.py::_normalize), not a flat list of
        # numbers -- flatten + sort chronologically before handing it to the SPA's sparkline,
        # which expects trend[11] to be the most recent month.
        ordered = sorted(monthly, key=lambda m: (m.get("year") or 0, m.get("month") or 0))
        trend = [int(m["ai_search_volume"]) if m.get("ai_search_volume") is not None else 0 for m in ordered]
        if len(trend) < 12:
            # Pad at the START with zeros so the most-recent real month stays last (index 11).
            trend = [0] * (12 - len(trend)) + trend
        out.append({
            "kw": r.keyword,
            "aiVolume": ai_vol,
            "gVolume": g_vol,
            # None (not a fabricated 0%) when there's no Google-volume denominator to compare
            # against -- g_vol == 0 means "no signal," not "0% AI share." A flat 0% would
            # misleadingly read as "no AI interest."
            "ratio": round(ai_vol / g_vol * 100) if g_vol else None,
            "intent": r.intent or "",
            "trend": trend[-12:],
            "mentions": 0,   # honest -- nothing measures per-keyword answer-engine mentions
            "gap": False,    # honest -- same
        })
    return out


def _target_dict(t: "AITarget | None") -> dict:
    if t is None:
        return {"brand": "", "aliases": [], "competitors": []}
    return {"brand": t.brand, "aliases": t.aliases, "competitors": t.competitors}


# ─────────────────────────────────────────────
# Stored checks (written by the run/inspect actions)
# ─────────────────────────────────────────────

def get_prompt_results(site_id: str) -> dict:
    """`{"<prompt_id>": {"results": {platform: result}, "lastRun": iso}}` — only checks that
    really happened. `{}` before the first run."""
    stored = get_state(site_id, RESULTS_KEY, {})
    return stored if isinstance(stored, dict) else {}


def get_run_history(site_id: str) -> list:
    """Inspector/history entries, newest first. `[]` before the first run."""
    stored = get_state(site_id, HISTORY_KEY, [])
    return stored if isinstance(stored, list) else []


def get_prompt_cfg(site_id: str, prompt_id) -> dict:
    """cadence/country/city/webSearch for one prompt, defaulted when never configured."""
    stored = get_state(site_id, PROMPT_CFG_KEY, {})
    if not isinstance(stored, dict):
        return dict(DEFAULT_PROMPT_CFG)
    saved = stored.get(str(prompt_id))
    return {**DEFAULT_PROMPT_CFG, **saved} if isinstance(saved, dict) else dict(DEFAULT_PROMPT_CFG)


def set_prompt_cfg(site_id: str, prompt_id, cadence=None, country=None, city=None, web_search=None) -> None:
    """Persist whichever of the four extra fields the caller actually sent, leaving the rest of
    this prompt's stored config untouched -- the same "only touch what was sent" rule that fixed
    the credentials save silently blanking dataforseo_target_domain (see settings_service)."""
    stored = get_state(site_id, PROMPT_CFG_KEY, {})
    if not isinstance(stored, dict):
        stored = {}
    key = str(prompt_id)
    current = {**DEFAULT_PROMPT_CFG, **stored.get(key, {})}
    if cadence is not None:
        current["cadence"] = cadence
    if country is not None:
        current["country"] = country
    if city is not None:
        current["city"] = city
    if web_search is not None:
        current["webSearch"] = bool(web_search)
    stored[key] = current
    set_state(site_id, PROMPT_CFG_KEY, stored)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cell(result: dict) -> dict:
    """The part of a check the Prompts table needs, stored per (prompt, platform).

    The answer text and its paragraph split are deliberately NOT kept here — they are large and
    they live once, in the history entry, which is what the Answer Inspector opens.
    """
    return {
        "state": result.get("state"),
        "platform": result.get("platform"),
        "platformName": result.get("platformName"),
        "model": result.get("model"),
        "verdict": result.get("verdict"),
        "mentioned": bool(result.get("mentioned")),
        "cited": bool(result.get("cited")),
        "position": result.get("position"),
        "snippet": result.get("snippet") or "",
        "competitors": result.get("competitors") or [],
        "cost": result.get("cost"),
        "error": result.get("error"),
        "checkedAt": result.get("checkedAt"),
    }


def _history_entry(result: dict, question: str, prompt_id) -> dict:
    """One archived answer, in the shape the Answer Inspector and History tab read
    (`e.ts/.question/.verdict/.position/.cost` and `e.scrape.{model,location,paragraphs,
    citations}`)."""
    return {
        "id": f"{result.get('platform')}-{result.get('checkedAt') or _now_iso()}-{prompt_id or 'adhoc'}",
        "ts": result.get("checkedAt") or _now_iso(),
        "question": question,
        "promptId": prompt_id,
        "platform": result.get("platform"),
        "platformName": result.get("platformName"),
        "verdict": result.get("verdict"),
        "position": result.get("position"),
        "mentioned": bool(result.get("mentioned")),
        "cited": bool(result.get("cited")),
        "snippet": result.get("snippet") or "",
        "competitors": result.get("competitors") or [],
        "cost": result.get("cost"),
        "scrape": {
            "model": result.get("model"),
            # Real: no geo-targeting is applied to the request, so there is no location to name.
            "location": "No location targeting",
            "paragraphs": result.get("paragraphs") or [],
            # Provider-verified sources from a web-search-enabled DataForSEO check; [] when the
            # prompt ran without web search. Never URLs scraped out of the answer prose.
            "citations": result.get("citations") or [],
        },
    }


def _record_spend(site_id: str, connector: str, cost: float, units: int, notes: str) -> None:
    """Append the real USD this action spent to `connector_costs`. Never raises: losing a cost
    row must not lose the results the user already paid for."""
    if not units:
        return
    try:
        with get_session() as session:
            insert_connector_cost(session, site_id, connector, cost, units=units, notes=notes)
    except Exception as exc:
        logger.warning(f"ai_service: could not record {connector} spend: {exc}")


def _target_for_run(site_id: str):
    target = AITarget.objects.filter(site_url=site_id).first()
    brand = (target.brand or "").strip() if target else ""
    aliases = (target.aliases or []) if target else []
    competitors = (target.competitors or []) if target else []
    return brand, aliases, competitors


def run_prompt_checks(site_id: str, prompts: list) -> dict:
    """Ask every tracked answer engine each of `prompts`, for real, and persist what came back.

    Spends money — only ever reached from the explicit "Run now" user action, never from a GET.
    Returns `{"ran", "checked", "cost", "skipped", "notConnected", "detail"}`; `ran`/`cost` are
    the two keys the SPA's notification reads.
    """
    brand, aliases, competitors = _target_for_run(site_id)
    if not brand:
        return {"ran": 0, "checked": 0, "cost": 0.0, "skipped": len(prompts),
                "notConnected": [], "detail": "Set your brand under Targets before running checks."}

    stored = get_prompt_results(site_id)
    history = get_run_history(site_id)

    checked = 0
    total_cost = 0.0
    cost_unknown = 0
    skipped = 0
    not_connected: set[str] = set()
    new_entries: list[dict] = []

    for prompt in prompts:
        platforms = list(prompt.tracked_models or [])
        if not platforms:
            skipped += 1
            continue
        entry = stored.get(str(prompt.id))
        if not isinstance(entry, dict):
            entry = {"results": {}, "lastRun": None}
        results = entry.get("results")
        if not isinstance(results, dict):
            results = {}

        # The modal's webSearch toggle used to be stored and never consumed; it now really
        # switches the DataForSEO check to a web-search-enabled answer (with citations), and
        # `country` geo-scopes those web results. `city` is still stored and NOT sent: the LLM
        # Responses endpoint has no city parameter, and inventing one would be a setting that
        # pretends to work.
        prompt_cfg = get_prompt_cfg(site_id, prompt.id)
        web_search = bool(prompt_cfg.get("webSearch"))
        country = prompt_cfg.get("country")

        ran_any = False
        for platform in platforms:
            if not is_platform_connected(platform):
                # Recorded as an explicit not_connected cell, never as a verdict. Nothing is
                # called and nothing is charged.
                results[platform] = _cell(not_connected_result(platform))
                not_connected.add(platform)
                continue
            result = check_prompt(prompt.text, brand, aliases, competitors, platform=platform,
                                  web_search=web_search, country=country)
            results[platform] = _cell(result)
            if not result.get("ok"):
                continue
            ran_any = True
            checked += 1
            if result.get("cost") is None:
                cost_unknown += 1
            else:
                total_cost += float(result["cost"])
            new_entries.append(_history_entry(result, prompt.text, prompt.id))

        entry["results"] = results
        if ran_any:
            entry["lastRun"] = _now_iso()
        stored[str(prompt.id)] = entry

    set_state(site_id, RESULTS_KEY, stored)
    if new_entries:
        set_state(site_id, HISTORY_KEY, (new_entries[::-1] + history)[:MAX_HISTORY])

    notes = f"{checked} check(s) across {len(prompts)} prompt(s)"
    if cost_unknown:
        notes += f"; {cost_unknown} with no usage block (cost unknown)"
    _record_spend(site_id, COST_CONNECTOR_RUN, round(total_cost, 6), checked, notes)

    detail = None
    if not checked:
        if not_connected:
            detail = "; ".join(sorted(not_connected_reason(p) for p in not_connected))
        elif skipped:
            detail = "No answer engines are selected on these prompts."
    return {
        "ran": len(prompts),
        "checked": checked,
        "cost": round(total_cost, 6),
        "skipped": skipped,
        "notConnected": sorted(not_connected),
        "detail": detail,
    }


def inspect_question(site_id: str, question: str, prompt_id=None) -> dict:
    """One ad-hoc answer-engine check for the Answer Inspector.

    Returns `{"ok": True, "entry": <history entry>}` on a real check, or
    `{"ok": False, "reason": ...}` when it could not honestly be performed. Spends money — only
    reached from the explicit "Inspect now" user action.
    """
    question = (question or "").strip()
    if not question:
        return {"ok": False, "reason": "Enter a question to inspect."}

    brand, aliases, competitors = _target_for_run(site_id)
    if not brand:
        return {"ok": False, "reason": "Set your brand under Targets before inspecting an answer."}

    available = connected_platforms()
    if not available:
        # Exactly the ai_summary_service degradation: no key, no call, and say so.
        return {"ok": False, "reason": not_connected_reason("chatgpt"), "notConnected": True}

    platform = available[0]
    result = check_prompt(question, brand, aliases, competitors, platform=platform)
    if not result.get("ok"):
        return {"ok": False, "reason": result.get("error") or f"{platform_name(platform)} check failed."}

    entry = _history_entry(result, question, prompt_id)
    history = get_run_history(site_id)
    set_state(site_id, HISTORY_KEY, ([entry] + history)[:MAX_HISTORY])

    if prompt_id is not None:
        # An inspection of a tracked prompt's own text is a real observation of that prompt —
        # reflect it in the Prompts table too, rather than throwing the result away.
        stored = get_prompt_results(site_id)
        pentry = stored.get(str(prompt_id))
        if not isinstance(pentry, dict):
            pentry = {"results": {}, "lastRun": None}
        results = pentry.get("results")
        if not isinstance(results, dict):
            results = {}
        results[platform] = _cell(result)
        pentry["results"] = results
        pentry["lastRun"] = _now_iso()
        stored[str(prompt_id)] = pentry
        set_state(site_id, RESULTS_KEY, stored)

    cost = result.get("cost")
    _record_spend(site_id, COST_CONNECTOR_INSPECT, float(cost or 0.0), 1,
                  f"answer inspector · {result.get('model')}"
                  + ("" if cost is not None else " · no usage block (cost unknown)"))
    return {"ok": True, "entry": entry}


# ─────────────────────────────────────────────
# Real spend (connector_costs)
# ─────────────────────────────────────────────

def _cost_rows(site_id: str) -> list:
    """(connector, run_at, cost, units) for this page's own spend events. [] on any failure —
    a cost read must never take the page down, and [] renders as an honest zero."""
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            # Self-provision: a database created before connector_costs existed must not raise
            # "no such table" on first read. Same pattern as cost_service.
            ensure_tables(session, ConnectorCost)
            return list(session.execute(
                select(ConnectorCost.connector, ConnectorCost.run_at,
                       ConnectorCost.cost, ConnectorCost.units)
                .where(ConnectorCost.site_id.in_(site_ids))
                .where(ConnectorCost.connector.in_(AI_COST_CONNECTORS))
            ).all())
    except Exception as exc:
        logger.error(f"ai_service: could not read connector_costs: {exc}", exc_info=True)
        return []


def _as_naive_utc(value):
    """connector_costs.run_at is a plain DateTime column: SQLite hands back naive values and
    Postgres would compare an aware bound parameter against a naive column. One code path for
    both — filtering happens in Python here, so this only normalises what came back."""
    if value is None:
        return None
    if getattr(value, "tzinfo", None) is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _spend(site_id: str) -> dict:
    """Real recorded spend on answer-engine checks, and the real mean cost of one check.

    Every figure comes from `connector_costs` rows this page's own actions inserted. No rows
    means every figure is 0 / None — never an estimate of what a check "should" cost.
    """
    rows = _cost_rows(site_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    spent_month = 0.0
    spent_week = 0.0
    totals = {c: {"cost": 0.0, "units": 0} for c in AI_COST_CONNECTORS}
    for connector, run_at, cost, units in rows:
        cost = float(cost or 0.0)
        run_at = _as_naive_utc(run_at)
        if connector in totals:
            totals[connector]["cost"] += cost
            totals[connector]["units"] += int(units or 0)
        if run_at is not None and run_at >= month_start:
            spent_month += cost
        if run_at is not None and run_at >= week_start:
            spent_week += cost

    def per_unit(connector):
        agg = totals[connector]
        if not agg["units"]:
            return None  # unknown, not zero and not a guess
        return round(agg["cost"] / agg["units"], 6)

    return {
        "spent_month": round(spent_month, 6),
        "spent_week": round(spent_week, 6),
        "per_run_check": per_unit(COST_CONNECTOR_RUN),
        "per_inspect": per_unit(COST_CONNECTOR_INSPECT),
    }


def _budget_cap(site_id: str) -> float:
    """The user's own configured cap from Settings → Usage & Budget. 0 when never configured —
    that is the real stored default, not a stand-in for a plan allowance we don't know."""
    obj = ProjectSettings.objects.filter(site_url=site_id).first()
    if obj is None:
        return 0
    try:
        return (obj.data.get("budget") or {}).get("cap", 0) or 0
    except AttributeError:
        return 0


# ─────────────────────────────────────────────
# Response
# ─────────────────────────────────────────────

def build_ai_response(site_id: str) -> dict:
    """API-shaped AI Optimization response.

    Never calls an answer engine: a check costs money, so it only ever happens on the explicit
    `run`/`inspect` user action. This function reads back what those actions stored.
    """
    target = AITarget.objects.filter(site_url=site_id).first()
    lists = list(AIPromptList.objects.filter(site_url=site_id).values("id", "name"))
    prompts_qs = AIPrompt.objects.filter(site_url=site_id)

    stored = get_prompt_results(site_id)
    prompts = []
    for p in prompts_qs:
        entry = stored.get(str(p.id)) or {}
        results = entry.get("results") or {}
        prompt_cfg = get_prompt_cfg(site_id, p.id)
        prompts.append({
            "id": p.id,
            "text": p.text,
            "listId": p.list_id,
            # The SPA reads pr.cfg.models/.cadence/.country/.city (a nested object), not a flat
            # pr.models -- without this, pr.cfg.models.length crashes once any prompt exists.
            # cadence/country/city/webSearch now round-trip through PROMPT_CFG_KEY (see
            # get_prompt_cfg/set_prompt_cfg) -- the modal used to accept and silently discard
            # them, so "Save" looked like it worked while nothing but `models`/`listId` landed.
            "cfg": {
                "models": p.tracked_models,
                "cadence": prompt_cfg["cadence"],
                "country": prompt_cfg["country"],
                "city": prompt_cfg["city"],
                "webSearch": prompt_cfg["webSearch"],
            },
            # Real observed results keyed by platform id -- {} until this prompt is actually run.
            "results": results if isinstance(results, dict) else {},
            "lastRun": entry.get("lastRun"),
        })

    history = get_run_history(site_id)
    spend = _spend(site_id)

    # prompt_coverage still comes off real stored answer-engine checks, nothing else.
    cited_prompts = 0
    for pr in prompts:
        hit_cited = False
        for res in pr["results"].values():
            if not isinstance(res, dict):
                continue
            if res.get("cited"):
                hit_cited = True
        if hit_cited:
            cited_prompts += 1

    # Real AI-answer visibility, read back from stored LLM Mentions snapshots. Everything it
    # returns used to be a hardcoded 0/[] under a label claiming an API that was not wired.
    vis = build_visibility_block(site_id)

    return {
        "setupDone": bool(target and target.setup_done),
        "targets": _target_dict(target),
        "budget": {
            # cap: the user's own configured cap. spent: real recorded answer-engine spend this
            # calendar month. weekly_est: real recorded spend over the trailing 7 days (an
            # observed figure, not a projection).
            "cap": _budget_cap(site_id),
            "spent": spend["spent_month"],
            "weekly_est": spend["spent_week"],
        },
        # Real mean USD cost of one check, computed from recorded spend / recorded checks.
        # None until at least one real check has been paid for -- the price of a call is not
        # something to guess at in the UI.
        "costs": {"model": spend["per_run_check"], "inspect": spend["per_inspect"]},
        # No scheduler runs these prompts (they are manual-only), so there is no next run.
        "next_run": None,
        "mentionPlatforms": vis["mentionPlatforms"],
        # llmPlatforms stays the four answer engines the Prompts tab checks with this
        # deployment's own API keys. DataForSEO's LLM Mentions covers only two platforms, so
        # these two lists are NOT interchangeable -- they were the same constant, which is why
        # the visibility toggles offered Claude/Gemini/Perplexity that could never have data.
        "llmPlatforms": MENTION_PLATFORMS,
        "sov": vis["sov"],
        "kpis": {
            "mentions": vis["mentions"],
            "impressions": vis["impressions"],
            "cited_pages": vis["cited_pages"],
            # Still from real prompt runs -- a different measurement, deliberately unchanged.
            "prompt_coverage": {"cited": cited_prompts, "total": len(prompts)},
        },
        "trend": [],   # Lean v1: weekly rows are being collected; the chart is not wired yet.
        "topPages": vis["topPages"],
        "topDomains": vis["topDomains"],
        "visibilityState": vis["state"],
        "lists": lists,
        "prompts": prompts,
        "suggestions": _suggestions_for(site_id, target),
        "aiKeywords": query_ai_keywords_raw(site_id),
        "history": history,
    }


def _suggestions_for(site_id: str, target) -> list:
    """Starter-prompt suggestions for the setup wizard's step 3 and the composer's quick-add
    shortcuts. Reuses run_prompt_research's deterministic template expansion (no external API,
    already used by the Prompt Explorer via POST /api/prompt-research) -- seeded from the
    tracked brand + aliases, which is real, owned data rather than a fabricated placeholder.

    Empty for a target that hasn't been saved yet, which is the normal state the FIRST time a
    brand-new project's setup wizard opens (its step 1/2 fields are only a client-side draft
    until "Finish setup" submits them). Once a brand is tracked, re-opening the composer to add
    more prompts gets real suggestions immediately.
    """
    if target is None or not (target.brand or "").strip():
        return []
    seeds = [target.brand] + list(target.aliases or [])
    try:
        from apps.dashboard.services.keyword_research_service import run_prompt_research
        rows = run_prompt_research(site_id, seeds).get("rows", [])
    except Exception:
        logger.error("[ai_service] suggestion generation failed for %r", site_id, exc_info=True)
        return []
    # run_prompt_research's rows have no `id` -- the wizard/composer select by id
    # (aiWizSel.includes(x.id)), so a stable index-based one is assigned here at the edge.
    return [{**row, "id": f"sug-{i}"} for i, row in enumerate(rows)]

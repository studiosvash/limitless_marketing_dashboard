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
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings
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

# ── Where a RUN IN FLIGHT is tracked ─────────────────────────────────────────────────────────
# One task per site, in the same JSON blob. It exists because a run is not a request: a full
# grid is (prompts x engines) sequential DataForSEO calls at up to REQUEST_TIMEOUT=120s each,
# i.e. 8-15 minutes for a modest project. That used to run INLINE in `POST /ai/run`, which
# failed three ways at once:
#
#   * nginx/gunicorn/Cloudflare killed the request. The SPA's local `aiRunning` flag was only
#     ever cleared in .then/.catch, so a killed request left every Run button permanently
#     disabled and relabelled "Running…" for the rest of the session.
#   * results were written ONCE after the whole loop, so a worker killed at check 41 of 60
#     threw away 40 checks DataForSEO had already billed.
#   * a run that DID finish server-side looked like nothing had happened.
#
# The fix is the pattern this codebase already uses for its 20-30 minute syncs
# (`sync_api_service.start_sync_run` -> `manage.py run_sync` in its own `subprocess.Popen`):
# the request plans, records this task, spawns `manage.py run_ai_checks` and returns. The
# worker persists after EVERY PROMPT and writes its progress here; the SPA reads the task off
# the ordinary AI GET, so "is a run in flight?" survives a reload, a tab switch, and the death
# of the worker itself (see `_reap_task_if_dead`).
RUN_TASK_KEY = "aiRunTask"

# Same liveness reasoning as sync_api_service._reap_if_dead: a pid is written a moment AFTER
# the task row, so a just-started run legitimately has no live pid yet.
RUN_DEAD_MESSAGE = (
    "The run process (pid {pid}) is no longer running but never reported a result. It was most "
    "likely killed by a server restart or deploy. Press Run again to continue — checks that "
    "already completed are saved and will not be re-billed."
)

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


# ─────────────────────────────────────────────
# Runs — planning, the task, and the worker
# ─────────────────────────────────────────────

def plan_run(site_id: str, prompts: list, force: bool = False) -> dict:
    """Which (prompt, platform) CELLS this run should actually pay for.

    The unit of work is a cell, not a prompt: an engine that already answered a prompt has
    nothing left to observe, and re-asking it is a second charge for the same fact.
    """
    cells = []
    skipped_no_models = 0
    for prompt in prompts:
        platforms = list(prompt.tracked_models or [])
        if not platforms:
            skipped_no_models += 1
            continue
        for platform in platforms:
            cells.append({"promptId": prompt.id, "platform": platform,
                          "text": prompt.text})
    return {"cells": cells, "skippedNoModels": skipped_no_models}


def _idle_task() -> dict:
    return {"state": "idle", "taskId": None, "total": 0, "completed": 0, "current": None,
            "checked": 0, "cost": 0.0, "costUnknown": 0, "notConnected": [], "planned": 0,
            "error": None, "detail": None, "startedAt": None, "finishedAt": None}


def _parse_iso(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _reap_task_if_dead(site_id: str, task: dict) -> dict:
    """Resolve a task whose OS process is gone.

    Without this, a worker killed by a deploy leaves the task at `running` forever and every
    Run button in the SPA stays disabled — the exact failure the old in-request run had, just
    moved. Biased towards "still alive" on any uncertainty, like `scheduling._process_alive`:
    wrongly declaring a live paid run dead is worse than showing a spinner a little too long.
    """
    if task.get("state") != "running":
        return task
    pid = task.get("pid")
    started = _parse_iso(task.get("startedAt"))
    if not pid or started is None:
        return task
    from apps.sync.scheduling import PID_GRACE, _process_alive
    if datetime.now(timezone.utc) - started < PID_GRACE:
        return task
    try:
        if _process_alive(pid):
            return task
    except Exception:
        logger.warning("[ai_service] liveness check failed for run task %s", task.get("taskId"),
                       exc_info=True)
        return task
    task = {**task, "state": "error", "finishedAt": _now_iso(), "current": None,
            "error": RUN_DEAD_MESSAGE.format(pid=pid)}
    set_state(site_id, RUN_TASK_KEY, task)
    logger.warning("[ai_service] run task %s reaped — pid %s is gone", task.get("taskId"), pid)
    return task


def get_run_task(site_id: str) -> dict:
    """The run task as the UI should see it — reaped if its worker died."""
    task = get_state(site_id, RUN_TASK_KEY, None)
    if not isinstance(task, dict) or not task.get("taskId"):
        return _idle_task()
    return _reap_task_if_dead(site_id, {**_idle_task(), **task})


def _save_task(site_id: str, task: dict) -> None:
    set_state(site_id, RUN_TASK_KEY, task)


def _spawn_run_process(site_id: str, task_id: str) -> int | None:
    """Launch `manage.py run_ai_checks` as a detached child. Returns its pid.

    A near-copy of `sync_api_service._spawn_sync_process`, and deliberately so: same detach
    flags (so a signal aimed at the web worker cannot reach it), same "write to a file, never a
    pipe" rule (a pipe whose reader is the web worker fills its OS buffer and BLOCKS the run
    partway through).
    """
    manage_py = Path(settings.BASE_DIR) / "manage.py"
    log_dir = Path(os.getenv("FUSEHEALTH_LOG_DIR") or (Path(settings.BASE_DIR) / "logs"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        out = open(log_dir / f"ai_run_{task_id}.log", "ab", buffering=0)
    except Exception:
        logger.warning("[ai_service] could not open a log file for run %s; discarding its output",
                       task_id, exc_info=True)
        out = subprocess.DEVNULL

    kwargs: dict = {}
    if hasattr(os, "setsid"):                                     # POSIX — production
        kwargs["start_new_session"] = True
    elif hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):         # Windows — dev
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                   | getattr(subprocess, "DETACHED_PROCESS", 0))

    proc = subprocess.Popen(
        [sys.executable, str(manage_py), "run_ai_checks",
         "--site-url", site_id, "--task-id", task_id],
        cwd=str(settings.BASE_DIR),
        stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
        **kwargs,
    )
    logger.info("[ai_service] spawned AI run %s as pid %s", task_id, proc.pid)
    return proc.pid


def start_ai_run(site_id: str, prompts: list, force: bool = False) -> dict:
    """Plan a run, record it as a task, spawn the worker, and return immediately.

    Returns `{task_id, planned, skipped, estimated_cost, ...}`. `task_id` is None when nothing
    was started — an empty plan and a missing brand are both normal outcomes, not errors, and
    `detail` says which.

    A second call while a run is in flight returns the EXISTING task_id rather than forking a
    parallel run: two runs over the same grid would race on the results blob and double-spend.
    """
    existing = get_run_task(site_id)
    if existing.get("state") == "running":
        return {"task_id": existing["taskId"], "already_running": True,
                "planned": existing.get("planned") or existing.get("total") or 0,
                "skipped": 0, "estimated_cost": None,
                "detail": "A run is already in progress — showing its progress instead of "
                          "starting another."}

    brand, _aliases, _competitors = _target_for_run(site_id)
    if not brand:
        return {"task_id": None, "planned": 0, "skipped": len(prompts),
                "estimated_cost": None,
                "detail": "Set your brand under Targets before running checks."}

    plan = plan_run(site_id, prompts, force=force)
    cells = plan["cells"]
    if not cells:
        return {"task_id": None, "planned": 0, "skipped": plan["skippedNoModels"],
                "estimated_cost": None,
                "detail": ("No answer engines are selected on these prompts."
                           if plan["skippedNoModels"] else "Everything is up to date.")}

    per_check = _spend(site_id)["per_run_check"]
    task_id = uuid.uuid4().hex[:16]
    task = {
        **_idle_task(),
        "taskId": task_id, "state": "running", "pid": None,
        "startedAt": _now_iso(), "finishedAt": None,
        "total": len(cells), "planned": len(cells), "completed": 0, "current": None,
        "force": bool(force),
        "plan": [{"promptId": c["promptId"], "platform": c["platform"]} for c in cells],
    }
    _save_task(site_id, task)

    try:
        pid = _spawn_run_process(site_id, task_id)
    except Exception as exc:
        # A run we could not start must never be left claiming to be running — that would
        # disable every Run button until the pid reaper cleared it.
        logger.error("[ai_service] could not spawn the AI run worker", exc_info=True)
        _save_task(site_id, {**task, "state": "error", "finishedAt": _now_iso(),
                             "error": f"Could not start the run process: {exc}"})
        return {"task_id": None, "planned": len(cells), "skipped": plan["skippedNoModels"],
                "estimated_cost": None,
                "detail": f"Could not start the run process: {exc}"}

    task["pid"] = pid
    _save_task(site_id, task)
    return {
        "task_id": task_id,
        "planned": len(cells),
        "skipped": plan["skippedNoModels"],
        # None (not 0.0) until a real check has been billed: the price of a call is not
        # something to guess at, and "$0.00" on a paid action is the one lie a price may not tell.
        "estimated_cost": round(per_check * len(cells), 6) if per_check is not None else None,
    }


def _persist_prompt_results(site_id: str, prompt_id, cells: dict, entries: list,
                            ran_any: bool) -> None:
    """Write ONE prompt's results and history, re-reading the blob first.

    Called after every prompt rather than once after the loop. The blob is read-modify-write
    with no partial update, so re-reading here is what keeps the lost-update window to a single
    prompt instead of a whole run — and it is what makes a worker killed mid-run keep every
    check DataForSEO has already billed.
    """
    stored = get_prompt_results(site_id)
    entry = stored.get(str(prompt_id))
    if not isinstance(entry, dict):
        entry = {"results": {}, "lastRun": None}
    results = entry.get("results")
    if not isinstance(results, dict):
        results = {}
    results.update(cells)
    entry["results"] = results
    if ran_any:
        entry["lastRun"] = _now_iso()
    stored[str(prompt_id)] = entry
    set_state(site_id, RESULTS_KEY, stored)

    if entries:
        history = get_run_history(site_id)
        set_state(site_id, HISTORY_KEY, (entries[::-1] + history)[:MAX_HISTORY])


def execute_ai_run(site_id: str, task_id: str) -> dict:
    """Run the planned cells. THE WORKER BODY — `manage.py run_ai_checks` calls exactly this.

    Never called from a request: every DataForSEO check here is a real charge and the whole
    loop is minutes of wall-clock.
    """
    task = get_state(site_id, RUN_TASK_KEY, None)
    if not isinstance(task, dict) or task.get("taskId") != task_id:
        logger.info("[ai_service] run %s is not the current task for %r — nothing to do",
                    task_id, site_id)
        return {"ran": 0, "checked": 0, "cost": 0.0}
    if task.get("state") != "running":
        logger.info("[ai_service] run %s is already %s — nothing to do", task_id, task["state"])
        return {"ran": 0, "checked": 0, "cost": 0.0}

    brand, aliases, competitors = _target_for_run(site_id)
    plan = task.get("plan") or []

    # Grouped by prompt, preserving plan order: one prompt is the unit of persistence.
    order: list = []
    by_prompt: dict = {}
    for cell in plan:
        pid = cell.get("promptId")
        if pid not in by_prompt:
            by_prompt[pid] = []
            order.append(pid)
        by_prompt[pid].append(cell.get("platform"))

    prompts = {p.id: p for p in AIPrompt.objects.filter(site_url=site_id, id__in=order)}

    checked = 0
    total_cost = 0.0
    cost_unknown = 0
    completed = 0
    not_connected: set[str] = set()
    detail = None

    for prompt_id in order:
        prompt = prompts.get(prompt_id)
        platforms = by_prompt[prompt_id]
        if prompt is None:
            # Deleted between planning and here. Count the cells so progress still reaches 100%.
            completed += len(platforms)
            continue

        # Re-read: a cancel (or a second run taking over) must stop this loop, and the
        # DataForSEO budget can be crossed by ANOTHER sync while this run is in flight.
        current = get_state(site_id, RUN_TASK_KEY, None)
        if not isinstance(current, dict) or current.get("taskId") != task_id \
                or current.get("state") != "running":
            logger.info("[ai_service] run %s was superseded or cancelled — stopping", task_id)
            return {"ran": completed, "checked": checked, "cost": round(total_cost, 6)}
        task = current

        from apps.dashboard.services.budget_service import budget_status
        try:
            status = budget_status()
        except Exception:
            logger.warning("[ai_service] budget check failed; continuing", exc_info=True)
            status = {"exceeded": False}
        if status.get("exceeded"):
            # Stop gracefully and KEEP what has already been paid for. Refusing to record the
            # partial run would throw away checks that were genuinely billed.
            detail = (f"Stopped: the monthly DataForSEO budget of ${status.get('cap', 0):.2f} "
                      f"was reached mid-run. {completed} of {task['total']} checks completed.")
            break

        task = {**task, "current": prompt.text, "completed": completed}
        _save_task(site_id, task)

        prompt_cfg = get_prompt_cfg(site_id, prompt.id)
        web_search = bool(prompt_cfg.get("webSearch"))
        country = prompt_cfg.get("country")

        cells: dict = {}
        entries: list = []
        ran_any = False
        for platform in platforms:
            if not is_platform_connected(platform):
                # An explicit not_connected cell, never a verdict. Nothing called, nothing charged.
                cells[platform] = _cell(not_connected_result(platform))
                not_connected.add(platform)
                completed += 1
                continue
            result = check_prompt(prompt.text, brand, aliases, competitors, platform=platform,
                                  web_search=web_search, country=country)
            cells[platform] = _cell(result)
            completed += 1
            if not result.get("ok"):
                continue
            ran_any = True
            checked += 1
            if result.get("cost") is None:
                cost_unknown += 1
            else:
                total_cost += float(result["cost"])
            entries.append(_history_entry(result, prompt.text, prompt.id))

        _persist_prompt_results(site_id, prompt.id, cells, entries, ran_any)
        # Spend is recorded per prompt, not once at the end, for the same reason results are:
        # a killed worker must not lose the record of money that was actually spent.
        prompt_cost = sum(float(e.get("cost") or 0.0) for e in entries)
        _record_spend(site_id, COST_CONNECTOR_RUN, round(prompt_cost, 6), len(entries),
                      f"prompt #{prompt.id} · {len(entries)} check(s)")
        task = {**task, "completed": completed, "checked": checked,
                "cost": round(total_cost, 6), "costUnknown": cost_unknown,
                "notConnected": sorted(not_connected)}
        _save_task(site_id, task)

    if detail is None and not checked:
        if not_connected:
            detail = "; ".join(sorted(not_connected_reason(p) for p in not_connected))

    _save_task(site_id, {**task, "state": "done", "current": None, "finishedAt": _now_iso(),
                         "completed": completed, "checked": checked,
                         "cost": round(total_cost, 6), "costUnknown": cost_unknown,
                         "notConnected": sorted(not_connected), "detail": detail})
    return {"ran": len(order), "checked": checked, "cost": round(total_cost, 6),
            "notConnected": sorted(not_connected), "detail": detail}


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
        # The run in flight (or the last one), read straight off the task the worker updates.
        # The SPA drives its Run buttons from THIS, not from a client-side flag: a flag set in
        # a request that was later killed can never be cleared, which is how every Run button
        # in a session became a silent no-op.
        "run": get_run_task(site_id),
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

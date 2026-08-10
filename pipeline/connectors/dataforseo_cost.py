"""
pipeline/connectors/dataforseo_cost.py — the one place that reads a DataForSEO bill.

DataForSEO is metered and every response already tells you what it just charged you.
The docs shipped with this repo (Design_features/uploads/API Docs/) describe the SAME
envelope for every endpoint family we call — SERP, Keywords Data, DataForSEO Labs,
Backlinks, OnPage and AI Optimization all repeat this pair of rows verbatim:

    | `cost` | float | *total tasks cost, USD* |     <- top level of the response
    ...
    | **`tasks`** | array | *array of tasks* |
    ...
    | `cost` | float | *cost of the task, USD* |     <- per task, inside tasks[]

(Verified in SERP_API_Docs.md L123/L131 and L637/L645, OnPage_API_Docs.md L146/L154,
Keywords_Data_API_Docs.md L135/L143, DataForSEO_Labs_API_Docs.md L61/L69,
Backlinks_API_Docs.md L92/L100, AI_Optimization_API_Docs.md L109/L117.)

So the per-task figure is authoritative and the top-level figure is its sum. `extract_cost`
prefers summing `tasks[].cost` — a batched POST submits many tasks in one request and only
the per-task rows attribute the spend — and falls back to the top-level total when the
tasks array carries no cost (some task_get responses report the charge only at the top).

Nothing here ever raises. A connector's job is to bring back data; failing a sync because
the bookkeeping tripped would be strictly worse than not knowing what the sync cost.
"""

from typing import Optional

from pipeline.utils.logger import get_logger

logger = get_logger("dataforseo.cost")


def _as_float(value) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def extract_cost(payload) -> float:
    """Return the USD charge a DataForSEO JSON response reports for itself.

    Sums `tasks[].cost` (the authoritative per-task charge) and falls back to the
    top-level `cost` (documented as "total tasks cost") when the tasks carry none.
    Returns 0.0 for anything unparseable — never raises, never guesses.
    """
    if not isinstance(payload, dict):
        return 0.0

    task_total = 0.0
    tasks = payload.get("tasks")
    if isinstance(tasks, list):
        for task in tasks:
            if isinstance(task, dict):
                task_total += _as_float(task.get("cost"))

    if task_total > 0:
        return task_total
    return _as_float(payload.get("cost"))


def record_cost(connector: str, site_id: Optional[str], cost: float,
                units: Optional[int] = None, notes: Optional[str] = None) -> float:
    """Append one connector_costs row for a completed run. Returns the cost passed in
    so call sites can log it.

    Skips the write when cost is 0 — a zero row is not a spend event, and a run that
    legitimately cost nothing (cached task_get, credential failure before the first
    request) should not dilute the per-connector averages on Settings → Usage & Budget.

    Swallows everything. `insert_connector_cost` is already no-raise; this wrapper also
    covers acquiring/committing the session, which is the part that can still fail.
    """
    amount = _as_float(cost)
    if amount <= 0:
        return 0.0

    try:
        from pipeline.utils.db_connection import get_session
        from pipeline.db.writer import insert_connector_cost

        with get_session() as session:
            insert_connector_cost(
                session, site_id or "", connector, amount, units=units, notes=notes,
            )
    except Exception as exc:  # pragma: no cover - defensive; must never fail a sync
        logger.warning(f"[{connector}] cost not recorded (${amount}): {exc}")
        return amount

    # Budget notifications — "after every hit". Every DataForSEO connector's spend already
    # funnels through this one function, so this is the single choke point to watch the
    # monthly cap cross a $5/$50/90%/100% line, without a separate polling process.
    try:
        from apps.dashboard.services.budget_service import check_and_notify_budget, month_to_date_spend
        new_total = month_to_date_spend()
        check_and_notify_budget(new_total - amount, new_total)
    except Exception as exc:  # pragma: no cover - defensive; must never fail a sync
        logger.warning(f"[{connector}] budget notification check failed: {exc}")

    return amount


# ---------------------------------------------------------------------------------------
# The spend gate.
#
# check_and_notify_budget() above only NOTIFIES. Until this existed, nothing anywhere
# refused a call once the cap was crossed except start_sync_run()'s paywall -- which covers
# background syncs and nothing else. The four sanctioned live-lookup endpoints
# (/api/research, /api/domain-overview, /api/live-serp, /api/connection-check) are
# user-pressed buttons with no such guard, so a repeatedly-pressed lookup was an uncapped
# spend vector: every press billed, every press fired one more notification, and the money
# kept going out.
#
# `ensure_budget()` is the shared check. It deliberately answers with a value rather than
# raising, because a service function in this codebase does not raise (skills.md 2.6) and
# because the live-lookup endpoints already speak {"status": "error", "error": ...} at 200.
# ---------------------------------------------------------------------------------------

BUDGET_REACHED_MESSAGE = (
    "Monthly DataForSEO budget reached — raise it in Settings to continue"
)


def ensure_budget() -> Optional[dict]:
    """Return None when a metered live lookup may proceed, or a refusal dict when it may not.

    A cap of 0 or less means NO CAP IS CONFIGURED, and nothing changes for that deployment:
    the lookup runs exactly as it did before this function existed. That is the same reading
    `budget_status()` gives the value (`pct` is 0 when `cap` is 0) and it is the only way to
    opt out, since DATAFORSEO_MONTHLY_BUDGET otherwise defaults to $100.

    Never raises. If the budget cannot be read at all -- no database, a migration mid-flight
    -- the answer is "proceed": failing a lookup the user asked for because the BOOKKEEPING
    broke would be strictly worse than not knowing the balance, which is the same rule
    record_cost() above already follows.
    """
    try:
        from apps.dashboard.services.budget_service import budget_status
        status = budget_status()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(f"budget gate skipped (status unreadable): {exc}")
        return None

    try:
        cap = float(status.get("cap") or 0)
    except (TypeError, ValueError):
        return None
    if cap <= 0:
        return None
    if not status.get("exceeded"):
        return None

    return {
        "status": "error",
        "error": BUDGET_REACHED_MESSAGE,
        # A distinct flag, not just prose: the SPA needs to tell "we refused to spend" apart
        # from "DataForSEO returned an error", and only the first one is fixable in Settings.
        "budget_exceeded": True,
        "spent": status.get("spent"),
        "cap": cap,
    }

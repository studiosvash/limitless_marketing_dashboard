"""DataForSEO spend guardrails — the monthly budget cap, its $5/$50/90% notifications, and
the account balance check.

Two honest numbers drive this, both real:
  - "spend this month"  -> apps.dashboard.services.cost_service, summed over EVERY project
    (`cost_since_all_sites`), because DataForSEO bills one shared account, not one per site.
  - "balance remaining"  -> pipeline.connectors.dataforseo_probe.fetch_balance(), the same
    free `/appendix/user_data` call Settings' "Test connection" already uses.

There is no daemon in this codebase (see run_scheduled_syncs.py's docstring) and this module
does not add one. "Continuously" means: every DataForSEO call updates spend (hooked into
dataforseo_cost.record_cost, the one choke point every connector's cost already flows
through), and every sync run — manual or the hourly scheduled tick — re-checks the balance
(hooked into sync_engine.py). That is as continuous as this architecture gets without a new
background process, which nothing here has been asked to add.
"""
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MONTHLY_CAP = float(os.getenv("DATAFORSEO_MONTHLY_BUDGET", "100") or 100)
LOW_BALANCE_THRESHOLD = float(os.getenv("DATAFORSEO_LOW_BALANCE_THRESHOLD", "10") or 10)
THRESHOLD_STEP = 5.0
RED_PCT = 0.9  # 90% of the cap — the "red" warning line the user asked for


def _month_start() -> datetime:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return datetime(now.year, now.month, 1)


def month_to_date_spend() -> float:
    """Total DataForSEO spend across every project so far this calendar month."""
    from apps.dashboard.services.cost_service import cost_since_all_sites
    return cost_since_all_sites(_month_start())


def is_billable_connectors(connectors: list[str]) -> bool:
    """Does this connector list include any metered DataForSEO call? Every DataForSEO
    connector name is prefixed 'dataforseo_' (see sync_engine.ALL_CONNECTORS) — that prefix
    is the whole rule, so a new one is covered automatically."""
    return any((c or "").startswith("dataforseo") for c in (connectors or []))


def budget_status() -> dict:
    """{cap, spent, remaining, pct, red, exceeded, balance, balance_checked_at} — the one
    shape both the paywall check and the /api/budget-status endpoint read."""
    from apps.dashboard.models import BudgetState

    spent = month_to_date_spend()
    cap = MONTHLY_CAP
    pct = round(min(100.0, (spent / cap * 100.0) if cap > 0 else 0.0), 1)

    state = BudgetState.objects.filter(pk=1).first()
    return {
        "cap": cap,
        "spent": spent,
        "remaining": round(max(0.0, cap - spent), 4),
        "pct": pct,
        "red": spent >= cap * RED_PCT,
        "exceeded": spent >= cap,
        "balance": state.dataforseo_balance if state else None,
        "balance_checked_at": state.balance_checked_at.isoformat() if state and state.balance_checked_at else None,
    }


def check_and_notify_budget(prev_total: float, new_total: float) -> None:
    """Compare month-to-date spend before/after one recorded cost and notify on whichever
    threshold it just crossed, highest-priority first so one crossing fires one message:

        reached the $100 cap        -> critical (this is also what start_sync_run's paywall
                                        enforces on the NEXT sync attempt, not this one)
        crossed 90% of the cap      -> critical, the "red" line
        crossed $50                 -> warning
        crossed any other $5 mark   -> info

    Never raises — called from record_cost()'s finally-adjacent path, which must never fail
    a sync over a notification.
    """
    try:
        cap = MONTHLY_CAP
        if prev_total < cap <= new_total:
            notify_budget("critical",
                f"Monthly DataForSEO budget reached — ${new_total:.2f} of ${cap:.2f} spent",
                "Syncs that call DataForSEO are paused until next month, or until the budget is raised.")
        elif prev_total < cap * RED_PCT <= new_total:
            notify_budget("critical",
                f"DataForSEO spend at {RED_PCT * 100:.0f}% of budget — ${new_total:.2f} of ${cap:.2f}",
                "Approaching the monthly cap.")
        elif prev_total < 50.0 <= new_total:
            notify_budget("warning", f"DataForSEO spend passed $50 — ${new_total:.2f} of ${cap:.2f} this month")
        elif int(prev_total // THRESHOLD_STEP) < int(new_total // THRESHOLD_STEP):
            step = int(new_total // THRESHOLD_STEP) * THRESHOLD_STEP
            notify_budget("info", f"DataForSEO spend passed ${step:.0f} — ${new_total:.2f} of ${cap:.2f} this month")
    except Exception:
        logger.error("check_and_notify_budget failed", exc_info=True)


def notify_budget(severity: str, title: str, detail: str = "") -> None:
    from apps.dashboard.services.notifications_service import notify
    notify("budget", title, detail, severity=severity)


def balance_is_stale() -> bool:
    """Has money been spent since the balance was last read?

    The balance used to be re-probed in exactly ONE place — after a sync run — so every metered
    call made outside a sync left it untouched. A Domain Overview lookup, a Keyword Explorer
    search, a live SERP check and an AI prompt run all spend real money, and Settings could sit
    showing a figure days old ("Checked 4d ago") as though it were the account's state.

    The question is answered from the data rather than from a flag: every metered call already
    writes a `connector_costs` row stamped with `run_at`, so "is there spend newer than my last
    probe?" needs no new column and cannot drift out of sync with reality.

    Deliberately NOT hooked into `record_cost`. That is the one chokepoint every metered call
    passes through, but it also runs inside sync loops and inside the request cycle of the live
    lookups — a network round-trip there would slow the user's own request down in order to
    report on the money it had just spent. This is asked on READ instead, where the answer is
    about to be displayed anyway.

    Never raises: a balance that cannot be judged stale is simply reported as it stands.
    """
    try:
        from apps.dashboard.models import BudgetState

        state = BudgetState.objects.filter(pk=1).first()
        if state is None or state.balance_checked_at is None or state.dataforseo_balance is None:
            return True                     # never read — one probe is what makes it real

        from sqlalchemy import func, select

        from pipeline.db.schema import ConnectorCost
        from pipeline.db.writer import ensure_tables
        from pipeline.utils.db_connection import get_session

        with get_session() as session:
            ensure_tables(session, ConnectorCost)
            last_spend = session.execute(select(func.max(ConnectorCost.run_at))).scalar()
        if last_spend is None:
            return False

        checked = state.balance_checked_at
        # connector_costs.run_at is naive local; balance_checked_at is tz-aware UTC. Compare
        # like with like rather than letting a TypeError decide freshness.
        if checked.tzinfo is not None:
            checked = checked.astimezone(timezone.utc).replace(tzinfo=None)
        if last_spend.tzinfo is not None:
            last_spend = last_spend.astimezone(timezone.utc).replace(tzinfo=None)
        return last_spend > checked
    except Exception:
        logger.warning("balance_is_stale check failed; reporting the stored balance as-is",
                       exc_info=True)
        return False


def refresh_balance_and_notify() -> None:
    """Re-check the DataForSEO balance and update BudgetState. Called after every sync run
    (manual or scheduled). Fires a critical notification once when the balance drops to/below
    LOW_BALANCE_THRESHOLD, and clears that flag silently once it recovers — never spams the
    same low-balance fact on every subsequent tick.
    """
    try:
        from django.utils import timezone as dj_timezone

        from apps.dashboard.models import BudgetState
        from pipeline.connectors.dataforseo_probe import fetch_balance

        balance = fetch_balance()
        if balance is None:
            return  # credentials missing or the probe failed — nothing new to record

        state, _ = BudgetState.objects.get_or_create(pk=1)
        was_low = state.low_balance_notified
        state.dataforseo_balance = balance
        state.balance_checked_at = dj_timezone.now()

        if balance <= LOW_BALANCE_THRESHOLD and not was_low:
            state.low_balance_notified = True
            from apps.dashboard.services.notifications_service import notify
            notify("balance", f"DataForSEO balance is low — ${balance:.2f} remaining",
                   "Metered syncs will start failing once this reaches $0.", severity="critical")
        elif balance > LOW_BALANCE_THRESHOLD and was_low:
            state.low_balance_notified = False

        state.save(update_fields=["dataforseo_balance", "balance_checked_at", "low_balance_notified"])
    except Exception:
        logger.error("refresh_balance_and_notify failed", exc_info=True)

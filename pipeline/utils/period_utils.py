"""
utils/period_utils.py — Period comparison engine.

Provides:
  - get_period_dates()  : Calculate current + previous period date ranges
  - get_period_label()  : Human-readable period labels
  - compute_delta()     : % change with direction signal
  - PERIOD_OPTIONS      : Preset period definitions for the UI selector

All pages import from here for consistent period handling.
"""

from datetime import date, timedelta
from typing import Optional, Tuple


# ─────────────────────────────────────────────
# Period Mode Definitions
# ─────────────────────────────────────────────

PERIOD_MODES = ["Daily", "Weekly", "Monthly", "Custom"]

# Quick preset shortcuts shown in the sidebar
QUICK_PRESETS = {
    "Today vs Yesterday":       ("daily",   0),
    "Last 7 days vs Prior 7":   ("weekly",  0),
    "Last 30 days vs Prior 30": ("monthly", 0),
    "Last 90 days":             ("custom",  90),
}


# ─────────────────────────────────────────────
# Core Date Calculation
# ─────────────────────────────────────────────

def get_period_dates(
    mode: str,
    offset: int = 0,
    custom_start: Optional[date] = None,
    custom_end: Optional[date] = None,
    anchor: Optional[date] = None,
) -> Tuple[date, date, date, date]:
    """
    Calculate (current_start, current_end, prev_start, prev_end) for a given period mode.

    Args:
        mode:         'daily' | 'weekly' | 'monthly' | 'custom'
        offset:       How many periods back (0 = most recent, 1 = one period back, etc.)
        custom_start: Used when mode='custom'
        custom_end:   Used when mode='custom'
        anchor:       Treat this date as "today" when computing periods. Pass the
                      latest available data date so the dashboard doesn't default
                      to a window that postdates the data (which would render
                      empty pages when the data is a few days stale).

    Returns:
        Tuple of (current_start, current_end, prev_start, prev_end)
    """
    today = anchor if anchor is not None else date.today()
    yesterday = today - timedelta(days=1)

    if mode == "daily":
        # Current = today - offset days, Previous = day before that
        current_end   = today - timedelta(days=offset)
        current_start = current_end
        prev_end      = current_start - timedelta(days=1)
        prev_start    = prev_end

    elif mode == "weekly":
        # Current = last N days (7), Previous = the 7 days before that
        days_back     = (offset + 1) * 7
        current_end   = yesterday
        current_start = current_end - timedelta(days=6)
        if offset > 0:
            current_end   = today - timedelta(days=1 + offset * 7)
            current_start = current_end - timedelta(days=6)
        prev_end      = current_start - timedelta(days=1)
        prev_start    = prev_end - timedelta(days=6)

    elif mode == "monthly":
        # Current = last 30 days, Previous = 30 days before that
        current_end   = yesterday - timedelta(days=offset * 30)
        current_start = current_end - timedelta(days=29)
        prev_end      = current_start - timedelta(days=1)
        prev_start    = prev_end - timedelta(days=29)

    else:  # custom
        if custom_start and custom_end:
            current_start = custom_start
            current_end   = custom_end
            period_len    = (current_end - current_start).days + 1
            prev_end      = current_start - timedelta(days=1)
            prev_start    = prev_end - timedelta(days=period_len - 1)
        else:
            # Default to last 30 days
            current_end   = yesterday
            current_start = current_end - timedelta(days=29)
            prev_end      = current_start - timedelta(days=1)
            prev_start    = prev_end - timedelta(days=29)

    return current_start, current_end, prev_start, prev_end


def get_period_label(mode: str, start: date, end: date, prefix: str = "") -> str:
    """
    Generate human-readable period label.

    Examples:
        daily:   "May 21, 2026"
        weekly:  "May 15 – May 21, 2026"
        monthly: "Apr 22 – May 21, 2026"
        custom:  "Feb 20 – May 20, 2026"
    """
    if mode == "daily":
        return f"{prefix}{start.strftime('%b %d, %Y')}"
    elif start.year == end.year:
        if start.month == end.month:
            return f"{prefix}{start.strftime('%b %d')} – {end.strftime('%d, %Y')}"
        return f"{prefix}{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
    else:
        return f"{prefix}{start.strftime('%b %d, %Y')} – {end.strftime('%b %d, %Y')}"


def get_comparison_label(mode: str) -> str:
    """Return 'vs previous day/week/month/period' string."""
    labels = {
        "daily":   "vs previous day",
        "weekly":  "vs previous 7 days",
        "monthly": "vs previous 30 days",
        "custom":  "vs previous period",
    }
    return labels.get(mode, "vs previous period")


# ─────────────────────────────────────────────
# Delta Computation
# ─────────────────────────────────────────────

def compute_delta(current: float, previous: float) -> dict:
    """
    Compute % change between current and previous values.

    Returns dict with:
        pct_change:  float (e.g. 12.5 for +12.5%)
        direction:   'up' | 'down' | 'flat'
        arrow:       '↑' | '↓' | '→'
        formatted:   '+12.5%' | '-8.3%' | '0.0%'
        has_data:    bool (False if previous is 0 and current is 0)
    """
    has_data = not (current == 0 and previous == 0)
    if previous == 0 or previous is None:
        if current > 0:
            return {"pct_change": 100.0, "direction": "up", "arrow": "↑",
                    "formatted": "New data", "has_data": has_data}
        return {"pct_change": 0.0, "direction": "flat", "arrow": "→",
                "formatted": "–", "has_data": False}

    pct = ((current - previous) / abs(previous)) * 100
    pct = round(pct, 1)

    if pct > 0.5:
        direction, arrow = "up", "↑"
    elif pct < -0.5:
        direction, arrow = "down", "↓"
    else:
        direction, arrow = "flat", "→"

    sign = "+" if pct > 0 else ""
    return {
        "pct_change":  pct,
        "direction":   direction,
        "arrow":       arrow,
        "formatted":   f"{sign}{pct}%",
        "has_data":    has_data,
    }


def format_metric(value: float, metric_type: str) -> str:
    """Format a metric value for display based on type."""
    if metric_type in ("spend", "cpc", "cost_per_conv"):
        return f"${value:,.2f}"
    elif metric_type in ("ctr", "bounce_rate"):
        return f"{value:.2f}%"
    elif metric_type == "position":
        return f"{value:.1f}"
    elif metric_type == "roas":
        return f"{value:.2f}×"
    else:
        return f"{int(value):,}"


def build_period_comparison(current_data: dict, previous_data: dict) -> dict:
    """
    Build a full comparison dict from current/previous metric dicts.
    Returns {metric: {current, previous, delta}} structure.
    """
    result = {}
    all_keys = set(current_data.keys()) | set(previous_data.keys())
    for key in all_keys:
        curr = current_data.get(key, 0) or 0
        prev = previous_data.get(key, 0) or 0
        result[key] = {
            "current":  curr,
            "previous": prev,
            "delta":    compute_delta(float(curr), float(prev)),
        }
    return result

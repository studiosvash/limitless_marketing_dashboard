"""
utils/date_helpers.py — Date range utilities for API calls and dashboard filters.
"""
from datetime import date, timedelta
from typing import Tuple


def yesterday() -> date:
    return date.today() - timedelta(days=1)


def days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


def date_range(start: date, end: date) -> list[date]:
    delta = (end - start).days
    return [start + timedelta(days=i) for i in range(delta + 1)]


def iso(d: date) -> str:
    return d.isoformat()


def default_range(days: int = 90) -> Tuple[date, date]:
    end = yesterday()
    start = end - timedelta(days=days - 1)
    return start, end


def gsc_safe_range(days: int = 90) -> Tuple[str, str]:
    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=days - 1)
    return iso(start), iso(end)


def ga4_safe_range(days: int = 90) -> Tuple[str, str]:
    return f"{days}daysAgo", "yesterday"

"""Alerts page data — raw calculators for the new API's unified feed[]. These are NEW,
unlimited-count functions — separate from apps.dashboard.views' _get_all_anomalies/
_get_technical_issues, which stay capped for the old page's display tables and are
unmodified by this module. See
docs/superpowers/specs/2026-07-11-phaseB4-alerts-design.md for the feed field mapping."""

from sqlalchemy import select

from pipeline.db.schema import Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session


def query_alert_anomalies_raw(site_id: str) -> list[dict]:
    """All Anomaly rows for the site (not just unacknowledged, not capped) — the new
    alerts feed shows full history, filtering/paging is a frontend concern."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(Anomaly).where(Anomaly.site_id == site_id).order_by(Anomaly.date.desc())
            ).scalars().all()
            out = []
            for r in rows:
                up = r.actual_value >= r.baseline_value
                out.append({
                    "id": r.id,
                    "date": r.date,
                    "metric_type": r.metric_type,
                    "severity": r.severity,
                    "direction": "up" if up else "down",
                    "deviation_pct": r.deviation_pct,
                    "description": r.description or "",
                    "is_acknowledged": bool(r.is_acknowledged),
                })
            return out
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_alert_anomalies_raw error: {e}", exc_info=True)
        return []


def query_alert_technical_issues_raw(site_id: str) -> list[dict]:
    """All TechnicalIssue rows for the site (unlimited — the old page's _get_technical_issues
    caps at 15 for its own display table; this is a separate, unlimited function)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(TechnicalIssue).where(TechnicalIssue.site_id == site_id)
                .order_by(TechnicalIssue.detected_at.desc())
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "url": r.url,
                    "issue_type": r.issue_type,
                    "severity": r.severity or "medium",
                    "description": r.description or "",
                    "detected_at": r.detected_at,
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_alert_technical_issues_raw error: {e}", exc_info=True)
        return []

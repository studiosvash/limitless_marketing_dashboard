"""Alerts page data — raw calculators for the new API's unified feed[]. These are NEW,
unlimited-count functions — separate from apps.dashboard.views' _get_all_anomalies/
_get_technical_issues, which stay capped for the old page's display tables and are
unmodified by this module. See
docs/superpowers/specs/2026-07-11-phaseB4-alerts-design.md for the feed field mapping."""

import hashlib

from sqlalchemy import select, update

from apps.dashboard.services.mutation_state import get_state, set_state
from pipeline.db.schema import Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session


_METRIC_LABELS = {
    "seo_clicks": "Clicks", "seo_impressions": "Impressions",
    "seo_ctr": "CTR", "seo_avg_position": "Avg. position",
    "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
    "ad_impressions": "Ad impressions", "ad_conversions": "Conversions",
}
_ISSUE_LABELS = {
    "not_found_404": "404 — Not found",
    "crawled_not_indexed": "Crawled, not indexed",
    "page_with_redirect": "Redirect",
    "long_url": "Long URL",
}
_SEVERITY_RANK = {"high": 0, "medium": 1, "info": 2, "low": 3}


def _issue_feed_id(url: str, issue_type: str) -> str:
    """Stable feed id for a TechnicalIssue. Issue rows are wholesale-rebuilt after every
    sync (rebuild_technical_issues), so their autoincrement PKs change — an ack keyed on
    the PK would silently un-ack (or mis-ack) after the next refresh. A content hash of
    (url, issue_type) survives rebuilds; if the same issue is re-detected it stays acked."""
    digest = hashlib.sha1(f"{url or ''}|{issue_type or ''}".encode()).hexdigest()[:12]
    return f"issue-{digest}"


def get_acked_ids(site_id: str) -> set[str]:
    """Feed ids the user has acknowledged (persisted per project)."""
    return set(get_state(site_id, "alertAcks", []))


def ack_alert(site_id: str, alert_id: str) -> None:
    """Persist an acknowledgement. Idempotent — the SPA's 'Acknowledge all' fires one POST
    per item in parallel. anomaly-<pk> acks are mirrored onto Anomaly.is_acknowledged so
    the analytics table stays coherent with what the feed reports."""
    acked = get_state(site_id, "alertAcks", [])
    if alert_id not in acked:
        set_state(site_id, "alertAcks", acked + [alert_id])
    if alert_id.startswith("anomaly-"):
        try:
            pk = int(alert_id.removeprefix("anomaly-"))
            with get_session() as session:
                session.execute(
                    update(Anomaly).where(Anomaly.id == pk).values(is_acknowledged=1)
                )
        except Exception as e:  # ack must never 500 on mirror failure
            import logging; logging.getLogger(__name__).warning(f"ack_alert mirror failed: {e}")


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


def query_sync_failure_alert_raw(site_id: str) -> dict | None:
    """System alert when the site's LATEST refresh completed with connector errors — the
    answer to 'I clicked Refresh, nothing showed up, and nothing told me why'. Derived from
    the same RefreshRun row the progress bar polls; disappears once a newer run succeeds."""
    from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus

    run = RefreshRun.objects.filter(site_url=site_id).order_by("-started_at").first()
    if run is None or run.status != RefreshStatus.ERROR:
        return None
    # SyncLog holds the last per-connector result — authoritative for WHICH failed and WHY
    # (RefreshRun.error_message is a single '; '-joined string, unsafe to parse).
    failures = list(SyncLog.objects.filter(site_url=site_id, status=SyncStatus.ERROR))
    names = [f.connector for f in failures] or ["sync"]
    detail = (failures[0].error_message or run.error_message or "").splitlines()[0][:220] if failures else \
        (run.error_message or "").splitlines()[0][:220]
    return {
        "id": f"syncerr-{run.pk}",
        "ts": run.started_at.date().isoformat(),
        "kind": "system",
        "severity": "high",
        "title": f"Last refresh failed for {len(names)} connector(s): {', '.join(names[:4])}",
        "detail": f"{detail} — full detail in Settings → Connections.",
    }


def build_alerts_response(site_id: str) -> dict:
    """HANDOFF_SPEC.md `alerts` view shape: {feed: [{id, ts, kind, severity, title, detail,
    acknowledged}]}. See docs/superpowers/specs/2026-07-11-phaseB4-alerts-design.md."""
    anomalies = query_alert_anomalies_raw(site_id)
    issues = query_alert_technical_issues_raw(site_id)
    acked = get_acked_ids(site_id)

    feed = []
    sync_alert = query_sync_failure_alert_raw(site_id)
    if sync_alert is not None:
        feed.append({**sync_alert, "acknowledged": sync_alert["id"] in acked})
    for a in anomalies:
        metric_label = _METRIC_LABELS.get(a["metric_type"], a["metric_type"])
        pct = f"{'+' if a['direction'] == 'up' else '-'}{abs(a['deviation_pct']):.0f}%"
        feed_id = f"anomaly-{a['id']}"
        feed.append({
            "id": feed_id,
            "ts": str(a["date"]),
            "kind": "anomaly",
            "severity": a["severity"],
            "title": f"{metric_label} {'up' if a['direction'] == 'up' else 'dropped'} {pct}",
            "detail": a["description"],
            "acknowledged": a["is_acknowledged"] or feed_id in acked,
        })
    for i in issues:
        issue_label = _ISSUE_LABELS.get(i["issue_type"], i["issue_type"].replace("_", " ").title())
        short_url = (i["url"] or "").split("//")[-1][:55]
        feed_id = _issue_feed_id(i["url"], i["issue_type"])
        feed.append({
            "id": feed_id,
            "ts": str(i["detected_at"].date()) if i["detected_at"] else "",
            "kind": "technical",
            "severity": i["severity"],
            "title": f"{issue_label}: {short_url}",
            "detail": i["description"],
            "acknowledged": feed_id in acked,
        })

    feed.sort(key=lambda item: (item["ts"], -_SEVERITY_RANK.get(item["severity"], 9)), reverse=True)

    return {"feed": feed}

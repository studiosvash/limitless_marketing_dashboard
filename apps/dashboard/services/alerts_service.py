"""Alerts page data — raw calculators for the new API's unified feed[]. These are NEW,
unlimited-count functions — separate from apps.dashboard.views' _get_all_anomalies/
_get_technical_issues, which stay capped for the old page's display tables and are
unmodified by this module. See
.claude/api-reference.md for the feed field mapping."""

import hashlib
import logging

from sqlalchemy import select, update

from apps.dashboard.services.mutation_state import get_state, set_state
from pipeline.db.schema import Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


# --- Settings -> Alerts & Rules: which stored rule drives which detector -------------------
#
# Settings renders ProjectSettings.data["alertRules"] as [{id, label, threshold, unit, on}].
# Until this module read them, every one of those controls was inert: the user could set
# "Clicks deviate by 60%" and still be alerted at whatever the code hardcoded. The map below
# is the whole of the wiring, and it is deliberately small, because only two of the four
# shipped rules have anything to drive:
#
#   traffic_anomaly -> query_alert_anomalies_raw   (kind="anomaly")
#       threshold = the minimum |deviation_pct| an Anomaly row must show to reach the feed.
#       Scope note: the rule is LABELLED "Clicks deviate from 28-day mean by", but the
#       detector it governs emits anomalies for every metric_type anomaly_service writes
#       (seo_clicks/impressions/ctr/avg_position, ad_spend/clicks/impressions/conversions),
#       measured against a 12-week rolling baseline, not a 28-day mean. The rule is applied
#       to the whole detector rather than to seo_clicks alone: it is the only rule that maps
#       here, so narrowing it would leave the other metric types with no control at all --
#       in particular no way to switch them off. The honest fix is to reword the label in
#       settings_service.DEFAULT_SETTINGS_BLOB (owned elsewhere); the behaviour here is
#       deliberately the broader, controllable one.
#       Floor note: anomaly_service only WRITES rows above its own ANOMALY_THRESHOLD_PCT
#       (35), so a threshold below 35 cannot surface anything extra -- there are no such
#       rows. Raising it above 35 genuinely filters.
#
#   audit_errors -> query_alert_technical_issues_raw   (kind="technical")
#       threshold = the minimum number of affected pages in an issue group before it reaches
#       the feed. The label says "Crawl finds NEW errors >=" -- "new" is not implemented and
#       is not faked here: nothing in this codebase snapshots a previous crawl to diff
#       against (technical_issues is rebuilt wholesale each sync), so the threshold is
#       applied to the group's total affected-page count, which is the closest true reading.
#
# Rules with NO detector -- reported, not silently ignored, and not given an invented
# detector to justify the control:
#   pos_drop      "Keyword position drops by N positions" -- nothing emits a per-keyword
#                 ranking alert. alerts.js has a kindMap entry for "ranking", but no code
#                 path ever produces kind="ranking". The nearest data, a seo_avg_position
#                 Anomaly, is a site-wide average expressed as a PERCENT deviation; reading
#                 a "positions" threshold against it would be fabrication.
#   lost_backlink "Backlink lost from domain rank >= N" -- this module never touches
#                 backlinks, and no lost-backlink detection exists anywhere.
# Both should be removed from DEFAULT_SETTINGS_BLOB (or have detectors built) rather than
# left on screen as controls that change nothing.
#
# The sync-failure alert (query_sync_failure_alert_raw, kind="system") has no rule and is
# intentionally not made suppressible: it is the alert that says "your data is stale and
# here is why", and a rule that does not mention it must not be able to switch it off.
_RULE_DETECTORS = {
    "traffic_anomaly": "anomaly",
    "audit_errors": "technical",
}
# A rule state of {"on": True, "threshold": None} means "run this detector exactly as it ran
# before rules existed" -- unfiltered. That is the value every fallback path produces.
_UNFILTERED = {"on": True, "threshold": None}
_FALSE_STRINGS = {"false", "0", "no", "off", "n", ""}


def _coerce_threshold(value):
    """A stored threshold -> a positive float, or None meaning 'do not filter'.

    None is returned for anything that is not a usable positive number (missing, null,
    "", "abc", True, -5, 0). Filtering on a value we cannot read would suppress real
    alerts on the strength of garbage, and for a monitoring feature silence is the one
    failure mode that must never be inferred from bad input."""
    if isinstance(value, bool):          # bool is an int subclass -- reject before the number check
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    if isinstance(value, str):
        try:
            parsed = float(value.strip())
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None
    return None


def _coerce_enabled(entry: dict) -> bool:
    """Whether a rule is switched on. Absent/null/unreadable `on` => True.

    Only an explicit falsy value silences a detector. A hand-edited blob that dropped the
    key, or an old project saved before the key existed, keeps alerting."""
    if "on" not in entry:
        return True
    value = entry["on"]
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in _FALSE_STRINGS
    return True


def load_alert_rules(site_id: str) -> dict[str, dict]:
    """Read ProjectSettings.data["alertRules"] into {rule_id: {"on": bool, "threshold": float|None}}.

    Every failure mode -- no ProjectSettings row, no "alertRules" key, a JSONField
    hand-edited into a dict/string, an entry that is not a dict, an unknown rule id, a
    threshold that will not parse -- degrades to the unfiltered default for the rules it
    could not read, never to an empty feed. Malformed entries are isolated: one broken rule
    cannot disable another. `unit` is descriptive only and is deliberately not read; the
    detector defines what its threshold measures."""
    state = {rule_id: dict(_UNFILTERED) for rule_id in _RULE_DETECTORS}
    try:
        stored = get_state(site_id, "alertRules", None)
        if not isinstance(stored, list):
            return state
        for entry in stored:
            if not isinstance(entry, dict):
                continue
            rule_id = entry.get("id")
            if rule_id not in state:
                continue  # pos_drop / lost_backlink / anything unknown: no detector to drive
            state[rule_id] = {
                "on": _coerce_enabled(entry),
                "threshold": _coerce_threshold(entry.get("threshold")),
            }
    except Exception as e:
        logger.error(f"load_alert_rules error: {e}", exc_info=True)
        return {rule_id: dict(_UNFILTERED) for rule_id in _RULE_DETECTORS}
    return state


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
            logger.warning(f"ack_alert mirror failed: {e}")


def ack_alerts(site_id: str, alert_ids: list) -> dict:
    """Acknowledge many ids in one pass -> {"acknowledged": [...], "failed": [{id, detail}]}.

    Exists because 'Acknowledge all' used to fire one HTTP request per row (~104 POSTs from
    one click), each of which read and rewrote the whole alertAcks list. This does one read,
    one write, and one mirror UPDATE regardless of how many ids arrive.

    Per-id outcomes are reported rather than a single boolean, because a partial failure the
    user cannot see is a row they believe is acknowledged and is not. Ids that are not usable
    strings fail individually and do not stop the rest; if the persist itself fails, every id
    in the batch is reported failed, since none of them saved.

    Idempotent (re-acking an already-acked id is a no-op that still reports success), and
    ack_alert() is untouched -- alerts.js still uses it for a single row."""
    acknowledged: list[str] = []
    failed: list[dict] = []
    seen: set[str] = set()
    for raw in (alert_ids or []):
        if not isinstance(raw, str) or not raw.strip():
            failed.append({"id": raw if isinstance(raw, str) else str(raw),
                           "detail": "Not a valid alert id."})
            continue
        alert_id = raw.strip()
        if alert_id in seen:
            continue
        seen.add(alert_id)
        acknowledged.append(alert_id)

    if not acknowledged:
        return {"acknowledged": [], "failed": failed}

    try:
        stored = get_state(site_id, "alertAcks", [])
        existing = set(stored)
        additions = [a for a in acknowledged if a not in existing]
        if additions:
            set_state(site_id, "alertAcks", list(stored) + additions)
    except Exception as e:
        logger.error(f"ack_alerts persist failed: {e}", exc_info=True)
        failed.extend({"id": a, "detail": "Could not be saved."} for a in acknowledged)
        return {"acknowledged": [], "failed": failed}

    # Mirror anomaly acks onto the analytics table in one statement (same reason as
    # ack_alert's single-row mirror). A mirror failure is logged, never fatal: the
    # authoritative ack is the one already persisted above.
    pks = []
    for alert_id in acknowledged:
        if alert_id.startswith("anomaly-"):
            try:
                pks.append(int(alert_id.removeprefix("anomaly-")))
            except ValueError:
                pass  # a malformed anomaly-<pk> id still acks in alertAcks; nothing to mirror
    if pks:
        try:
            with get_session() as session:
                session.execute(
                    update(Anomaly).where(Anomaly.id.in_(pks)).values(is_acknowledged=1)
                )
        except Exception as e:
            logger.warning(f"ack_alerts mirror failed: {e}")

    return {"acknowledged": acknowledged, "failed": failed}


def query_alert_anomalies_raw(site_id: str, rule: dict | None = None) -> list[dict]:
    """All Anomaly rows for the site (not just unacknowledged, not capped) — the new
    alerts feed shows full history, filtering/paging is a frontend concern.

    `rule` is the caller's `traffic_anomaly` state from load_alert_rules(). Omit it (the
    default) and behaviour is exactly what it was before rules were wired -- which is what
    ai_summary_service and the existing tests rely on. Passing it:
      * on=False  -> returns [] WITHOUT querying. Suppression at source: a switched-off rule
                     means those alerts are never produced, not produced and then hidden.
      * threshold -> a row must deviate by at least that many percent to be returned. A row
                     whose deviation_pct is NULL is kept: it cannot be measured against the
                     threshold, and dropping the unmeasurable would be silent under-alerting."""
    if rule is not None and not rule.get("on", True):
        return []
    min_deviation = rule.get("threshold") if rule else None
    try:
        with get_session() as session:
            rows = session.execute(
                select(Anomaly).where(Anomaly.site_id == site_id).order_by(Anomaly.date.desc())
            ).scalars().all()
            out = []
            for r in rows:
                if (min_deviation is not None and r.deviation_pct is not None
                        and abs(r.deviation_pct) < min_deviation):
                    continue
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


def query_alert_technical_issues_raw(site_id: str, rule: dict | None = None) -> list[dict]:
    """All TechnicalIssue rows for the site (unlimited — the old page's _get_technical_issues
    caps at 15 for its own display table; this is a separate, unlimited function).

    `rule` is the caller's `audit_errors` state from load_alert_rules(). Omitted (the
    default) => pre-rules behaviour, which is what ai_summary_service wants: a weekly
    summary should describe every issue, not the subset that passed the alerting bar.
      * on=False  -> returns [] without querying.
      * threshold -> an issue group must affect at least that many pages to be returned.
                     The default (1) is a no-op, since a group with zero rows cannot exist."""
    if rule is not None and not rule.get("on", True):
        return []
    min_count = rule.get("threshold") if rule else None
    try:
        with get_session() as session:
            from sqlalchemy import func
            rows = session.execute(
                select(
                    TechnicalIssue.issue_type,
                    TechnicalIssue.severity,
                    TechnicalIssue.description,
                    func.max(TechnicalIssue.detected_at).label("latest_detected"),
                    func.count(TechnicalIssue.id).label("issue_count"),
                    func.max(TechnicalIssue.url).label("example_url")
                )
                .where(TechnicalIssue.site_id == site_id)
                .group_by(TechnicalIssue.issue_type, TechnicalIssue.severity, TechnicalIssue.description)
                .order_by(func.max(TechnicalIssue.detected_at).desc())
            ).all()
            return [
                {
                    "id": f"group-{r.issue_type}",
                    "url": r.example_url,
                    "issue_type": r.issue_type,
                    "severity": r.severity or "medium",
                    "description": r.description or "",
                    "detected_at": r.latest_detected,
                    "count": r.issue_count
                }
                for r in rows
                if min_count is None or (r.issue_count or 0) >= min_count
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
    acknowledged}]}. See .claude/api-reference.md.

    Shape is unchanged by rule support -- alerts.js and the sidebar badge read it. What the
    rules change is which items exist in `feed`, never the fields on an item.

    The kind="system" sync-failure alert is built unconditionally: see the note on
    _RULE_DETECTORS for why no rule may silence it."""
    rules = load_alert_rules(site_id)
    anomalies = query_alert_anomalies_raw(site_id, rules.get("traffic_anomaly"))
    issues = query_alert_technical_issues_raw(site_id, rules.get("audit_errors"))
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
        count = i["count"]
        short_url = (i["url"] or "").split("//")[-1][:55]
        feed_id = _issue_feed_id(i["url"] or i["issue_type"], i["issue_type"])
        
        if count > 1:
            title_text = f"{issue_label} ({count} pages affected)"
            detail_text = f"e.g., {short_url} - {i['description']}"
        else:
            title_text = f"{issue_label}: {short_url}"
            detail_text = i["description"]
            
        feed.append({
            "id": feed_id,
            "ts": str(i["detected_at"].date()) if i["detected_at"] else "",
            "kind": "technical",
            "severity": i["severity"],
            "title": title_text,
            "detail": detail_text,
            "acknowledged": feed_id in acked,
        })

    feed.sort(key=lambda item: (item["ts"], -_SEVERITY_RANK.get(item["severity"], 9)), reverse=True)

    return {"feed": feed}

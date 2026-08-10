"""pipeline/services/backlinks_service.py — the Backlinks page bridge.

Fetches the DataForSEO Backlinks aggregates (summary, referring domains, anchors, new/lost
history) for a domain, shapes them into the SPA's Backlinks `data` payload, and caches that
payload as a per-site snapshot (DB-first: the page reads the snapshot; a Refresh re-fetches).

DataForSEO domain `rank` is a 0-1000 scale; the SPA's gauge/AS chips are 0-100, so ranks are
scaled /10 throughout (see `_as`).
"""
import json
import os
from datetime import datetime, timezone

import requests

from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.db.writer import save_backlinks_snapshot, get_backlinks_snapshot
from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger

logger = get_logger("services.backlinks")

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"

# The connector name these aggregate calls book their spend under. Deliberately NOT
# "dataforseo_backlinks": that name belongs to the per-backlink `backlinks/backlinks/live`
# connector, which meters per returned backlink row and records real `units`. Filing the
# aggregate endpoints under the same name would sum two costs against one connector's unit
# count and print a cost-per-backlink that is not a real rate. The `dataforseo` prefix is
# load-bearing -- `budget_service.is_billable_connectors` keys on exactly that.
COST_CONNECTOR = "dataforseo_backlinks_live"

# Anchor rows per `backlinks/anchors/live` call. DataForSEO bills per returned row, so this
# is a price, not a display cap. 60 is what the Backlinks page refresh has always requested;
# the Domain Overview lookup reuses the same figure rather than inventing a second one.
ANCHORS_LIMIT = 60
_GENERIC = {"click here", "here", "read more", "learn more", "this", "link", "website", "visit"}


def _auth():
    return (os.getenv("DATAFORSEO_LOGIN"), os.getenv("DATAFORSEO_PASSWORD"))


def _clean_domain(target: str) -> str:
    return (target or "").replace("https://", "").replace("http://", "").rstrip("/").replace("sc-domain:", "")


def _as(rank) -> int:
    """DataForSEO 0-1000 domain rank -> 0-100 authority score."""
    try:
        return max(0, min(100, round(float(rank) / 10)))
    except (TypeError, ValueError):
        return 0


def _fmt_date(s: str) -> str:
    if not s:
        return ""
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except ValueError:
        return s[:10]


def _post(endpoint: str, body: dict, site_id: str = "") -> dict:
    """One billed DataForSEO Backlinks call, with its charge booked.

    Every one of these endpoints is metered, and until this recorded anything the four calls
    fetch_backlinks_payload makes were invisible to Settings -> Usage & Budget: the page's
    Refresh spent real money and the cost breakdown showed nothing for it.

    The cost is read off the envelope BEFORE the result is unwrapped, so an errored or empty
    task still books what it cost -- the request was billed by the time we could parse it.

    `units` is always None. Four endpoints under one connector name meter four different
    things (referring domains, anchors, monthly history points, nothing at all for the
    summary), so there is no single denominator; None is this codebase's way of saying the
    rate is unknown, where 0 would claim we measured one and found nothing.
    """
    resp = requests.post(f"{DATAFORSEO_BASE}/backlinks/{endpoint}", auth=_auth(), json=[body], timeout=45)
    resp.raise_for_status()
    data = resp.json()
    record_cost(COST_CONNECTOR, site_id, extract_cost(data), units=None,
                notes=f"backlinks/{endpoint} for {body.get('target') or '?'}")
    task = (data.get("tasks") or [{}])[0]
    return (task.get("result") or [{}])[0] or {}


def _classify_anchor(anchor: str, brand: str) -> str:
    a = (anchor or "").strip().lower()
    if not a:
        return "Empty"
    if brand and brand in a:
        return "Branded"
    if a.startswith("http") or a.startswith("www.") or "." in a.split()[0] and "/" in a:
        return "URL"
    if a in _GENERIC:
        return "Generic"
    return "Keyword"


def fetch_anchors(target_domain: str, limit: int = 60, site_id: str = "") -> list[dict]:
    """The anchor-text breakdown for a domain, classified Branded / URL / Generic / Keyword.

    Extracted from fetch_backlinks_payload so the Domain Overview lookup and the Backlinks
    page refresh share ONE implementation of this call and ONE classifier -- the alternative
    was a second copy of both, which is how two screens come to disagree about what "Branded"
    means.

    One billed `backlinks/anchors/live` call. `limit` is the row count DataForSEO bills for.
    """
    if not all(_auth()):
        raise ValueError("DataForSEO credentials are not configured.")
    domain = _clean_domain(target_domain)
    brand = domain.split(".")[0]
    anchors = _post("anchors/live", {"target": domain, "limit": limit,
                                     "order_by": ["backlinks,desc"]}, site_id=site_id).get("items") or []
    return _shape_anchors(anchors, brand)


def _shape_anchors(anchors: list[dict], brand: str) -> list[dict]:
    rows = []
    for a in anchors:
        a_nofollow = (a.get("referring_links_attributes") or {}).get("nofollow", 0)
        a_bl = a.get("backlinks") or 0
        rows.append({
            "anchor": a.get("anchor") or "(empty)", "type": _classify_anchor(a.get("anchor"), brand),
            "backlinks": a_bl, "refDomains": a.get("referring_domains") or 0,
            "dofollowPct": round((a_bl - a_nofollow) / a_bl * 100) if a_bl else 0,
        })
    return rows


def fetch_backlinks_payload(target_domain: str, site_id: str = "") -> dict:
    """Make the DataForSEO calls and build the SPA Backlinks `data` payload. Raises on hard
    failure (missing creds / network) so the caller can decide how to surface it.

    `site_id` attributes the four billed calls below to a project in Settings -> Usage &
    Budget. Without one they land on the unattributed "" row, which is honest but tells the
    user nothing about which site spent the money.
    """
    if not all(_auth()):
        raise ValueError("DataForSEO credentials are not configured.")
    domain = _clean_domain(target_domain)
    brand = domain.split(".")[0]

    summary = _post("summary/live", {"target": domain, "include_subdomains": True}, site_id=site_id)
    rdoms = _post("referring_domains/live", {"target": domain, "limit": 200,
                                             "order_by": ["rank,desc"], "include_subdomains": True},
                  site_id=site_id).get("items") or []
    anchors = _post("anchors/live", {"target": domain, "limit": ANCHORS_LIMIT,
                                     "order_by": ["backlinks,desc"]}, site_id=site_id).get("items") or []
    history = _post("history/live", {"target": domain}, site_id=site_id).get("items") or []

    total_bl = summary.get("backlinks") or 0
    nofollow = (summary.get("referring_links_attributes") or {}).get("nofollow", 0)
    dofollow_pct = round((total_bl - nofollow) / total_bl * 100) if total_bl else 0

    # new/lost referring-domain history -> monthly bars
    months = [{
        "label": _month_label(h.get("date")),
        "nw": int(h.get("new_referring_domains") or 0),
        "lost": int(h.get("lost_referring_domains") or 0),
    } for h in history]
    new_rd_month = months[-1]["nw"] if months else 0
    as_delta = 0
    if len(history) >= 2:
        as_delta = _as(history[-1].get("rank")) - _as(history[-2].get("rank"))

    # link types donut
    _TYPE_MAP = {"anchor": ("Text", "#6366f1"), "image": ("Image", "#22c55e"),
                 "redirect": ("Redirect", "#f59e0b")}
    lt = summary.get("referring_links_types") or {}
    lt_total = sum(lt.values()) or 1
    types, other = [], 0
    for key, cnt in lt.items():
        if key in _TYPE_MAP:
            label, color = _TYPE_MAP[key]
            types.append({"label": label, "color": color, "pct": round(cnt / lt_total * 100)})
        else:
            other += cnt
    if other:
        types.append({"label": "Frame / Form", "color": "#94a3b8", "pct": round(other / lt_total * 100)})

    # authority-score buckets from referring domains
    buckets = [("81-100", "#059669", 81, 100), ("61-80", "#0891b2", 61, 80),
               ("41-60", "#3b82f6", 41, 60), ("21-40", "#f59e0b", 21, 40), ("0-20", "#94a3b8", 0, 20)]
    as_buckets = []
    for label, color, lo, hi in buckets:
        count = sum(1 for r in rdoms if lo <= _as(r.get("rank")) <= hi)
        as_buckets.append({"label": label, "color": color, "count": count})

    ref_domains = []
    for r in rdoms:
        rd_nofollow = (r.get("referring_links_attributes") or {}).get("nofollow", 0)
        rd_bl = r.get("backlinks") or 0
        ref_domains.append({
            "domain": r.get("domain", ""), "flag": "", "rank": _as(r.get("rank")),
            "backlinks": rd_bl, "linksToUs": r.get("referring_pages") or rd_bl,
            "follow": rd_bl > rd_nofollow, "firstSeen": _fmt_date(r.get("first_seen")),
            "isNew": _is_recent(r.get("first_seen")), "category": "", "spam": r.get("backlinks_spam_score") or 0,
        })

    anchor_rows = _shape_anchors(anchors, brand)

    return {
        "summary": {
            "lastUpdated": datetime.now(timezone.utc).strftime("%b %d, %Y"),
            "authorityScore": _as(summary.get("rank")), "asDelta": as_delta,
            "refDomains": summary.get("referring_domains") or 0, "newRdMonth": new_rd_month,
            "backlinks": total_bl, "dofollowPct": dofollow_pct,
            "broken": summary.get("broken_backlinks") or 0,
            "spamScore": summary.get("backlinks_spam_score") or 0,
        },
        "months": months, "types": types, "asBuckets": as_buckets,
        "anchors": anchor_rows, "refDomains": ref_domains,
        "links": [], "competitors": [], "gapDomains": [], "project": None,
    }


def _month_label(date_str: str) -> str:
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%b '%y")
    except (ValueError, TypeError):
        return ""


def _is_recent(date_str: str, days: int = 30) -> bool:
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return (datetime.now() - d).days <= days
    except (ValueError, TypeError):
        return False


def refresh_backlinks(site_url: str, target_domain: str) -> dict:
    """Fetch fresh aggregates and store the snapshot. Returns the payload."""
    payload = fetch_backlinks_payload(target_domain, site_id=site_url)
    with get_session() as session:
        save_backlinks_snapshot(session, site_url, json.dumps(payload))
        session.commit()
    logger.info(f"[backlinks] refreshed snapshot for {site_url} ({payload['summary']['backlinks']} backlinks)")
    return payload


def load_backlinks(site_url: str):
    """Return (fetched_at, payload_dict) for the stored snapshot, or (None, None)."""
    with get_session() as session:
        snap = get_backlinks_snapshot(session, site_url)
    if not snap:
        return None, None
    fetched_at, payload_json = snap
    return fetched_at, json.loads(payload_json)


def empty_backlinks_payload() -> dict:
    """A zeroed payload so the page renders a clean empty state before the first Refresh."""
    return {
        "summary": {"lastUpdated": "never", "authorityScore": 0, "asDelta": 0, "refDomains": 0,
                    "newRdMonth": 0, "backlinks": 0, "dofollowPct": 0, "broken": 0, "spamScore": 0},
        "months": [{"label": "", "nw": 0, "lost": 0}], "types": [],
        "asBuckets": [{"label": "0-20", "color": "#94a3b8", "count": 0}],
        "anchors": [], "refDomains": [], "links": [], "competitors": [], "gapDomains": [], "project": None,
    }

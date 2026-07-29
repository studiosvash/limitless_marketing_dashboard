"""Backlinks page data.

Two honest sources, and nothing else:

1. The `backlinks` table — one row per stored link (`referring_domain`, `target_url`,
   `anchor`, `status`, `dofollow`, `domain_rank`, `first_seen`, `last_seen`). This drives
   every *listing* on the page: the backlinks table and the referring-domain rollup.
2. `backlinks_snapshot` — the whole-profile aggregates DataForSEO returns
   (`manage.py refresh_backlinks <slug>` writes it via `pipeline.services.backlinks_service`).
   This drives every *distribution*: the new/lost history, the link-type donut, the authority
   buckets and the anchor-text distribution.

The split matters. `query_backlinks_table_raw()` returns the top N links **ordered by
domain_rank**, so any percentage computed over it is biased towards high-authority links and
would misdescribe the profile. Distributions therefore come from the snapshot or not at all —
when there is no snapshot the keys are present but empty, and the UI omits those cards.
Nothing on this page is invented to fill a shape.
"""

import json
from collections import defaultdict
from datetime import date, timedelta
from sqlalchemy import func, select

from pipeline.db.schema import Backlink, BacklinksSnapshot, TrackedCompetitor
from pipeline.utils.db_connection import get_session
from pipeline.services.competitor_service import get_tracked_competitors


def _resolve_site_ids(site_id: str) -> list[str]:
    alt_id = site_id.replace("sc-domain:", "") if site_id.startswith("sc-domain:") else f"sc-domain:{site_id}"
    return [site_id, alt_id]


def _fmt_date(d) -> str:
    """Display form for a real date column. Empty string when the column is NULL — the UI
    renders an empty cell rather than a made-up date."""
    return d.strftime("%b %d, %Y") if d else ""


def _is_recent(d, days: int = 30) -> bool:
    return bool(d) and (date.today() - d).days <= days


def _load_snapshot(site_id: str):
    """(fetched_at, payload_dict) for the stored DataForSEO aggregates, or (None, {}).

    Never raises: an unreadable/absent snapshot simply means the distribution keys stay empty.
    """
    for sid in _resolve_site_ids(site_id):
        try:
            with get_session() as session:
                row = session.execute(
                    select(BacklinksSnapshot).where(BacklinksSnapshot.site_id == sid)
                ).scalars().first()
            if row and row.payload:
                return row.fetched_at, (json.loads(row.payload) or {})
        except Exception as e:
            import logging; logging.getLogger(__name__).warning(f"_load_snapshot({sid}) failed: {e}")
    return None, {}


def query_backlinks_summary_raw(site_id: str) -> dict:
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    func.count(Backlink.id).label("total"),
                    func.count(Backlink.id).filter(Backlink.status == 'live').label("live"),
                    func.count(Backlink.id).filter(Backlink.status == 'lost').label("lost"),
                    func.count(func.distinct(Backlink.referring_domain)).label("unique_domains"),
                    func.avg(Backlink.domain_rank).label("avg_dr")
                ).where(Backlink.site_id.in_(site_ids))
            ).first()
            if not rows or not rows.total:
                return {"total": 0, "live": 0, "lost": 0, "unique_domains": 0, "avg_dr": 0}
            return {
                "total": rows.total or 0,
                "live": rows.live or 0,
                "lost": rows.lost or 0,
                "unique_domains": rows.unique_domains or 0,
                "avg_dr": round(rows.avg_dr or 0, 1),
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_backlinks_summary_raw error: {e}", exc_info=True)
        return {"total": 0, "live": 0, "lost": 0, "unique_domains": 0, "avg_dr": 0}


def query_backlinks_table_raw(site_id: str, limit: int = 500) -> list[dict]:
    """The stored links themselves. Every value is a column; there is no derived text here.

    `firstSeen` / `rank` / `target` duplicate `first_seen` / `domain_rank` / `target_url`
    under the names the CSV export maps (`h.exportBacklinks` in app.js).
    """
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            rows = session.execute(
                select(Backlink)
                .where(Backlink.site_id.in_(site_ids))
                .order_by(Backlink.domain_rank.desc().nullslast())
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "domain": r.referring_domain,
                    "target_url": r.target_url,
                    "anchor": r.anchor or "—",
                    "status": r.status or "live",
                    "dofollow": bool(r.dofollow),
                    "domain_rank": r.domain_rank or 0,
                    "first_seen": r.first_seen.isoformat() if r.first_seen else None,
                    "last_seen": r.last_seen.isoformat() if r.last_seen else None,
                    "firstSeen": _fmt_date(r.first_seen),
                    "isNew": _is_recent(r.first_seen),
                    "rank": r.domain_rank or 0,
                    "target": r.target_url,
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_backlinks_table_raw error: {e}", exc_info=True)
        return []


def query_referring_domains_raw(site_id: str, links: list[dict] = None) -> list[dict]:
    """Referring domains rolled up from the real Backlink rows.

    `firstSeen` is the earliest real `first_seen` across that domain's links (empty when the
    connector never supplied one). `category` and `spam` have no column behind them, so they
    stay empty/None instead of carrying a stand-in value.
    """
    if links is None:
        links = query_backlinks_table_raw(site_id, limit=5000)
    by_domain = defaultdict(list)
    for l in links:
        by_domain[l.get("domain") or "—"].append(l)

    out = []
    for domain, rows in sorted(by_domain.items(), key=lambda kv: -len(kv[1])):
        ranks = [r.get("domain_rank") or 0 for r in rows]
        seen = sorted(r["first_seen"] for r in rows if r.get("first_seen"))
        first_seen_iso = seen[0] if seen else None
        first_seen_date = date.fromisoformat(first_seen_iso) if first_seen_iso else None
        out.append({
            "domain": domain,
            "flag": "🌐",
            "rank": round(sum(ranks) / len(ranks)) if ranks else 0,
            "backlinks": len(rows),
            "linksToUs": len(rows),
            "follow": any(r.get("dofollow") for r in rows),
            "firstSeen": _fmt_date(first_seen_date),
            "first_seen": first_seen_iso,
            "isNew": _is_recent(first_seen_date),
            "category": "",   # no category column on `backlinks`
            "spam": None,     # no spam score column on `backlinks`
        })
    return out


def query_dofollow_count_raw(site_id: str) -> int:
    """Dofollow links across the *whole* table (not the truncated page sample)."""
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            return session.execute(
                select(func.count(Backlink.id))
                .where(Backlink.site_id.in_(site_ids))
                .where(Backlink.dofollow == 1)
            ).scalar() or 0
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_dofollow_count_raw error: {e}", exc_info=True)
        return 0


def query_domain_dates_raw(site_id: str) -> list[dict]:
    """Per referring domain: earliest first_seen, latest last_seen, and whether every stored
    link from it is lost. Aggregated in Python from plain Date columns so the same code runs on
    SQLite and Postgres (no strftime/to_char)."""
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            rows = session.execute(
                select(Backlink.referring_domain, Backlink.first_seen,
                       Backlink.last_seen, Backlink.status)
                .where(Backlink.site_id.in_(site_ids))
            ).all()
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_domain_dates_raw error: {e}", exc_info=True)
        return []

    agg = {}
    for domain, first_seen, last_seen, status in rows:
        d = agg.setdefault(domain, {"domain": domain, "first_seen": None, "last_seen": None, "all_lost": True})
        if first_seen and (d["first_seen"] is None or first_seen < d["first_seen"]):
            d["first_seen"] = first_seen
        if last_seen and (d["last_seen"] is None or last_seen > d["last_seen"]):
            d["last_seen"] = last_seen
        if (status or "live") != "lost":
            d["all_lost"] = False
    return list(agg.values())


def build_months_from_dates(domain_dates: list[dict], window: int = 6) -> list[dict]:
    """New / lost referring domains per month, from real first_seen / last_seen dates.

    Returns [] when no row carries a date — an empty chart is correct there, an invented
    trajectory is not.
    """
    if not any(d.get("first_seen") or d.get("last_seen") for d in domain_dates):
        return []

    new_by_month, lost_by_month = defaultdict(int), defaultdict(int)
    for d in domain_dates:
        if d.get("first_seen"):
            new_by_month[d["first_seen"].strftime("%Y-%m")] += 1
        if d.get("all_lost") and d.get("last_seen"):
            lost_by_month[d["last_seen"].strftime("%Y-%m")] += 1

    cursor = date.today().replace(day=1)
    keys = []
    for _ in range(window):
        keys.append(cursor)
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    keys.reverse()

    return [{
        "label": k.strftime("%b '%y"),
        "nw": new_by_month.get(k.strftime("%Y-%m"), 0),
        "lost": lost_by_month.get(k.strftime("%Y-%m"), 0),
    } for k in keys]


def build_backlinks_response(site_id: str) -> dict:
    """Backlinks view. Listings come from the `backlinks` table, distributions from the stored
    DataForSEO snapshot; anything with no source behind it is empty, never filled in."""
    summary_raw = query_backlinks_summary_raw(site_id)
    links = query_backlinks_table_raw(site_id, limit=1000)
    ref_domains = query_referring_domains_raw(site_id, links=links)

    fetched_at, snap = _load_snapshot(site_id)
    snap_summary = snap.get("summary") or {}

    total = summary_raw["total"]
    kpis = {
        "total": total,
        "live": summary_raw["live"],
        "lost": summary_raw["lost"],
        "referring_domains": summary_raw["unique_domains"],
        "avg_rank": summary_raw["avg_dr"],
    }

    dofollow_pct = round(query_dofollow_count_raw(site_id) / total * 100) if total else 0

    # New / lost history: the snapshot's real DataForSEO history first, otherwise derived from
    # the first_seen / last_seen columns, otherwise nothing.
    domain_dates = query_domain_dates_raw(site_id)
    months = snap.get("months") or build_months_from_dates(domain_dates)

    # Referring domains first seen inside the current calendar month.
    this_month = date.today().replace(day=1)
    if snap_summary.get("newRdMonth") is not None:
        new_rd_month = snap_summary["newRdMonth"]
    elif any(d.get("first_seen") for d in domain_dates):
        new_rd_month = sum(1 for d in domain_dates if d.get("first_seen") and d["first_seen"] >= this_month)
    else:
        new_rd_month = None   # no first_seen data at all — unknown, not zero

    # Distributions. Each one describes the whole backlink profile, and the only whole-profile
    # source is the snapshot: the `links` sample is ordered by domain_rank, so a percentage
    # taken over it would be systematically wrong.
    types = snap.get("types") or []
    as_buckets = snap.get("asBuckets") or []
    anchors = snap.get("anchors") or []

    # Link Gap needs each competitor's referring domains; nothing syncs competitor backlinks,
    # so there is no row to build. The tracked competitor list itself is real.
    competitors = get_tracked_competitors(site_id) or []
    gap_domains = []

    if fetched_at is not None:
        last_updated = fetched_at.date().isoformat() if hasattr(fetched_at, "date") else str(fetched_at)[:10]
    else:
        last_seen_dates = [d["last_seen"] for d in domain_dates if d.get("last_seen")]
        last_updated = max(last_seen_dates).isoformat() if last_seen_dates else None

    return {
        "kpis": kpis,
        "links": links,
        "summary": {
            "authorityScore": summary_raw["avg_dr"],
            "asDelta": None,          # one snapshot row per site — no history to diff against
            "refDomains": summary_raw["unique_domains"],
            "backlinks": total,
            "dofollowPct": dofollow_pct,
            "broken": summary_raw["lost"],
            "spamScore": snap_summary.get("spamScore"),
            "newRdMonth": new_rd_month,
            "lastUpdated": last_updated,
        },
        "months": months,
        "types": types,
        "asBuckets": as_buckets,
        "refDomains": ref_domains,
        "anchors": anchors,
        "competitors": competitors,
        "gapDomains": gap_domains,
    }

"""Backlinks page data — raw calculators (shared by the old Django view and the new DRF API
view), extracted unmodified from apps.dashboard.views. See
docs/superpowers/specs/2026-07-12-phaseC1-backlinks-design.md for why the rich Backlink
Analytics fields (summary/months/types/asBuckets/refDomains/anchors/gapDomains) are NOT
built here — they need 5 DataForSEO sub-endpoint connectors this codebase doesn't have yet."""

from sqlalchemy import func, select

from pipeline.db.schema import Backlink
from pipeline.utils.db_connection import get_session
from pipeline.services.competitor_service import get_tracked_competitors


def query_backlinks_summary_raw(site_id: str) -> dict:
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    func.count(Backlink.id).label("total"),
                    func.count(Backlink.id).filter(Backlink.status == 'live').label("live"),
                    func.count(Backlink.id).filter(Backlink.status == 'lost').label("lost"),
                    func.count(func.distinct(Backlink.referring_domain)).label("unique_domains"),
                    func.avg(Backlink.domain_rank).label("avg_dr")
                ).where(Backlink.site_id == site_id)
            ).first()
            if not rows:
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


def query_backlinks_table_raw(site_id: str, limit: int = 200) -> list[dict]:
    try:
        with get_session() as session:
            rows = session.execute(
                select(Backlink)
                .where(Backlink.site_id == site_id)
                .order_by(Backlink.domain_rank.desc().nullslast())
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "domain": r.referring_domain,
                    "target_url": r.target_url,
                    "anchor": r.anchor or "—",
                    "status": r.status,
                    "dofollow": r.dofollow,
                    "domain_rank": r.domain_rank or 0,
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_backlinks_table_raw error: {e}", exc_info=True)
        return []


def query_referring_domains_raw(site_id: str) -> list[dict]:
    """Referring domains rolled up from the real Backlink rows."""
    from collections import defaultdict

    links = query_backlinks_table_raw(site_id, limit=5000)
    by_domain = defaultdict(list)
    for l in links:
        by_domain[l.get("domain") or "—"].append(l)

    out = []
    for domain, rows in sorted(by_domain.items(), key=lambda kv: -len(kv[1])):
        ranks = [r.get("domain_rank") or 0 for r in rows]
        out.append({
            "domain": domain,
            "flag": "",                                   # honest: no country data is stored
            "rank": round(sum(ranks) / len(ranks)) if ranks else 0,
            "backlinks": len(rows),
            "linksToUs": len(rows),
            "follow": any(r.get("dofollow") for r in rows),
            "firstSeen": "—",                             # honest: not exposed by the raw query
            "isNew": False,                               # honest: no new/lost history stored
            "category": "—",                              # honest: no category data is stored
            "spam": 0,                                    # honest: no spam score is stored
        })
    return out


def build_backlinks_response(site_id: str) -> dict:
    """Backlinks view, derived from the real `Backlink` rows.

    BUG HISTORY: `summary` used to be hardcoded {"state": "setup"}. The SPA gates the WHOLE
    Backlinks page on data.summary.state === 'setup', so the page could never render -- not
    even after a successful backlinks sync. `summary` is now derived from the real rows.

    Fields with no data source in the Backlink table (new/lost history, anchor rollups, link
    gap, spam scores) stay honestly empty -- never fabricated.
    """
    summary_raw = query_backlinks_summary_raw(site_id)
    links = query_backlinks_table_raw(site_id)
    ref_domains = query_referring_domains_raw(site_id)

    total = summary_raw["total"]
    kpis = {
        "total": total,
        "live": summary_raw["live"],
        "lost": summary_raw["lost"],
        "referring_domains": summary_raw["unique_domains"],
        "avg_rank": summary_raw["avg_dr"],
    }

    dofollow_n = sum(1 for l in links if l.get("dofollow"))
    dofollow_pct = round(dofollow_n / len(links) * 100) if links else 0

    return {
        "kpis": kpis,
        "links": links,
        "summary": {
            # Authority score: the average referring-domain rank we actually have.
            "authorityScore": summary_raw["avg_dr"],
            "asDelta": 0,                 # honest: no historical snapshot to diff against
            "refDomains": summary_raw["unique_domains"],
            "backlinks": total,
            "dofollowPct": dofollow_pct,
            "broken": summary_raw["lost"],
            "spamScore": 0,               # honest: no spam score is stored
            "newRdMonth": 0,              # honest: no new/lost history is stored
            "lastUpdated": "—",
        },
        "months": [],                     # honest: no backlink history table exists
        "types": [],                      # honest: link types aren't captured
        "asBuckets": [],
        "refDomains": ref_domains,        # real, rolled up from the Backlink rows
        "anchors": [],                    # honest: no anchor rollup endpoint/connector yet
        "competitors": get_tracked_competitors(site_id),
        "gapDomains": [],                 # honest: needs a domain-intersection connector
    }

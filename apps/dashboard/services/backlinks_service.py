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


def build_backlinks_response(site_id: str) -> dict:
    """HANDOFF_SPEC.md `backlinks` view shape. Only kpis/links/competitors are real — the
    rest need DataForSEO sub-endpoint connectors this codebase doesn't have yet, so they
    honestly report state:"setup" rather than fabricated numbers. See
    docs/superpowers/specs/2026-07-12-phaseC1-backlinks-design.md."""
    summary_raw = query_backlinks_summary_raw(site_id)
    links = query_backlinks_table_raw(site_id)

    kpis = {
        "total": summary_raw["total"],
        "live": summary_raw["live"],
        "lost": summary_raw["lost"],
        "referring_domains": summary_raw["unique_domains"],
        "avg_rank": summary_raw["avg_dr"],
    }

    return {
        "kpis": kpis,
        "links": links,
        "summary": {"state": "setup"},
        "months": [],
        "types": [],
        "asBuckets": [],
        "refDomains": [],
        "anchors": [],
        "competitors": get_tracked_competitors(site_id),
        "gapDomains": [],
    }

"""
pipeline/services/competitor_service.py — Resolve which competitor domains a site
tracks as columns in the Positioning grid (2026-06-15, additive).

Resolution rule:
  * If the site has an explicit override set (tracked_competitors rows), use it.
  * Otherwise auto-seed from the auto-discovered competitor_domains table
    (top-N by `intersections`).

The auto-discovery table (competitor_domains) and its connector are never modified
here — this module only reads it and manages the separate override table.
"""
from typing import Optional

from sqlalchemy import select, delete

from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger
from pipeline.db.schema import CompetitorDomain, TrackedCompetitor
from pipeline.db.writer import ensure_tables

logger = get_logger("competitor_service")

DEFAULT_COLUMN_COUNT = 5


def _bare(domain: str) -> str:
    """Normalize a domain to its bare form (no scheme, no trailing slash)."""
    if not domain:
        return ""
    return (
        domain.strip()
        .replace("https://", "")
        .replace("http://", "")
        .replace("sc-domain:", "")
        .rstrip("/")
        .lower()
    )


def get_tracked_competitors(site_id: str, limit: int = DEFAULT_COLUMN_COUNT) -> list[str]:
    """
    Return the bare competitor domains to show as grid columns for this site.

    Override set wins when present; otherwise auto-seed from competitor_domains.
    Returns an empty list when neither source has data (grid shows its empty state).
    """
    bare_site = _bare(site_id)
    with get_session() as session:
        ensure_tables(session, TrackedCompetitor)

        override = session.execute(
            select(TrackedCompetitor.competitor_domain)
            .where(TrackedCompetitor.site_id == site_id)
            .order_by(TrackedCompetitor.added_at.asc())
        ).scalars().all()
        if override:
            results = []
            for d in override:
                bare_d = _bare(d)
                if bare_d and bare_d != bare_site and bare_d not in results:
                    results.append(bare_d)
            return results

        discovered = session.execute(
            select(CompetitorDomain.competitor_domain)
            .where(CompetitorDomain.site_id == site_id)
            .order_by(CompetitorDomain.intersections.desc())
            .limit(limit * 2)
        ).scalars().all()
        results = []
        for d in discovered:
            bare_d = _bare(d)
            if bare_d and bare_d != bare_site and bare_d not in results:
                results.append(bare_d)
                if len(results) == limit:
                    break
        return results


def is_overridden(site_id: str) -> bool:
    """True when the site has an explicit (user-edited) competitor set."""
    with get_session() as session:
        ensure_tables(session, TrackedCompetitor)
        row = session.execute(
            select(TrackedCompetitor.id).where(TrackedCompetitor.site_id == site_id).limit(1)
        ).first()
        return row is not None


def set_tracked_competitors(site_id: str, domains: list[str]) -> int:
    """
    Replace the site's override competitor set with `domains` (deduped, normalized).

    Passing an empty list clears the override, so the grid reverts to auto-seed.
    Returns the number of domains stored.
    """
    cleaned: list[str] = []
    seen = set()
    for d in domains:
        bare = _bare(d)
        if bare and bare not in seen:
            seen.add(bare)
            cleaned.append(bare)

    with get_session() as session:
        ensure_tables(session, TrackedCompetitor)
        session.execute(
            delete(TrackedCompetitor).where(TrackedCompetitor.site_id == site_id)
        )
        if cleaned:
            session.execute(
                TrackedCompetitor.__table__.insert(),
                [{"site_id": site_id, "competitor_domain": d} for d in cleaned],
            )
    logger.info(f"[competitor_service] set {len(cleaned)} tracked competitors for {site_id!r}")
    return len(cleaned)


def get_discovered_competitors(site_id: str, limit: int = 25) -> list[str]:
    """All auto-discovered competitor domains (for populating the Settings picker)."""
    with get_session() as session:
        rows = session.execute(
            select(CompetitorDomain.competitor_domain)
            .where(CompetitorDomain.site_id == site_id)
            .order_by(CompetitorDomain.intersections.desc())
            .limit(limit)
        ).scalars().all()
        return [_bare(d) for d in rows]

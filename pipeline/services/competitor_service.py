"""
pipeline/services/competitor_service.py — Resolve which competitor domains a site
tracks as columns in the Positioning grid (2026-06-15, additive).

Resolution rule:
  * If the site has an explicit override set (tracked_competitors rows), use it.
  * Otherwise auto-seed from the auto-discovered competitor_domains table
    (top-N by `intersections`).

The auto-discovery table (competitor_domains) and its connector are never modified
here — this module only reads it and manages the separate override table.

THE OVERRIDE SET BELONGS TO A PROJECT, NOT A DOMAIN. Every function here takes `site_pk` and
every caller holding a project must pass it: one domain can be registered as several projects
(`add_site(allow_duplicate=True)`), so a call scoped by `site_id` alone reads — and, worse,
DELETES — every sibling project's list. `site_pk=None` means domain-wide and is still correct
for a caller with genuinely no project in hand (a maintenance command, an auto-seed audit); it
is not a shortcut for "I didn't have it handy". Same contract as saved_keyword_service.
"""
from typing import Optional

from sqlalchemy import select, delete

from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger
from pipeline.db.schema import (
    CompetitorDomain, TrackedCompetitor, UNOWNED_SITE_PK, ensure_tracked_competitor_project,
)
from pipeline.db.writer import ensure_tables

logger = get_logger("competitor_service")

DEFAULT_COLUMN_COUNT = 5


def _prepare(session) -> None:
    """Table exists and carries `site_pk`. Idempotent; issues nothing once reconciled."""
    ensure_tables(session, TrackedCompetitor)      # clean empty state pre-first-save
    ensure_tracked_competitor_project(session)     # self-provisions site_pk on an existing DB


def _scope(site_id: str, site_pk: Optional[int]) -> list:
    """WHERE clauses selecting one project's rows, or the whole domain when site_pk is None.

    `site_pk` alone when given, deliberately NOT `site_pk AND site_id` — the project id already
    implies the domain, while the reverse is not true because one site is stored under several
    `site_id` spellings (skills.md §3), and ANDing them hides rows filed under a spelling this
    project's own `site_url` doesn't happen to match. Mirrors
    `saved_keyword_service.project_scope`.
    """
    if site_pk:
        return [TrackedCompetitor.site_pk == site_pk]
    from pipeline.utils.site_ids import resolve_site_ids
    return [TrackedCompetitor.site_id.in_(resolve_site_ids(site_id))]


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


def get_tracked_competitors(site_id: str, limit: int = DEFAULT_COLUMN_COUNT,
                            site_pk: Optional[int] = None) -> list[str]:
    """
    Return the bare competitor domains to show as grid columns for THIS PROJECT.

    Override set wins when present; otherwise auto-seed from competitor_domains.
    Returns an empty list when neither source has data (grid shows its empty state).
    """
    bare_site = _bare(site_id)
    with get_session() as session:
        _prepare(session)

        override = session.execute(
            select(TrackedCompetitor.competitor_domain)
            .where(*_scope(site_id, site_pk))
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


def is_overridden(site_id: str, site_pk: Optional[int] = None) -> bool:
    """True when THIS PROJECT has an explicit (user-edited) competitor set."""
    with get_session() as session:
        _prepare(session)
        row = session.execute(
            select(TrackedCompetitor.id).where(*_scope(site_id, site_pk)).limit(1)
        ).first()
        return row is not None


def set_tracked_competitors(site_id: str, domains: list[str],
                            site_pk: Optional[int] = None) -> int:
    """
    Replace THIS PROJECT's override competitor set with `domains` (deduped, normalized).

    Passing an empty list clears the override, so the grid reverts to auto-seed.
    Returns the number of domains stored.

    The delete is scoped by `_scope`, not by `site_id`. It used to wipe every row on the domain,
    so a sibling project saving its own settings silently replaced this project's competitor
    list — the write half of report bug C3a.
    """
    cleaned: list[str] = []
    seen = set()
    for d in domains:
        bare = _bare(d)
        if bare and bare not in seen:
            seen.add(bare)
            cleaned.append(bare)

    with get_session() as session:
        _prepare(session)
        session.execute(
            delete(TrackedCompetitor).where(*_scope(site_id, site_pk))
        )
        if cleaned:
            session.execute(
                TrackedCompetitor.__table__.insert(),
                [{"site_id": site_id, "site_pk": site_pk or UNOWNED_SITE_PK,
                  "competitor_domain": d} for d in cleaned],
            )
        session.commit()
    logger.info("[competitor_service] set %d tracked competitors for %r (site_pk=%s)",
                len(cleaned), site_id, site_pk)
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

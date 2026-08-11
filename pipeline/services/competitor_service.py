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
    """A competitor entry reduced to the HOST it names.

    Delegates to `normalize_domain`, the one canonicaliser this codebase registers sites with
    (skills.md §3), so a competitor is spelled the same way a project is.

    The hand-rolled version this replaces stripped the scheme and a trailing slash but NOT the
    path, so pasting `https://premierstaff.com/event-staffing-agency-las-vegas` into the
    competitor box stored that entire string as a "competitor domain" — and the user's own
    landing pages turned up listed as their rivals in Share of Voice. A URL is a reasonable
    thing to paste; keeping the path was the bug.
    """
    if not domain:
        return ""
    from pipeline.utils.site_ids import normalize_domain
    return normalize_domain(str(domain))


def get_tracked_competitors(site_id: str, limit: int = DEFAULT_COLUMN_COUNT,
                            site_pk: Optional[int] = None,
                            include_discovered: bool = False) -> list[str]:
    """The competitor domains THIS PROJECT'S USER CHOSE. Nothing else, by default.

    This used to fall back to DataForSEO's auto-discovered `competitor_domains` whenever a
    project had chosen none — and that table is keyed by DOMAIN, so every sibling project on
    one domain got the same list, made of whatever ranks for the same keywords: youtube.com,
    facebook.com, indeed.com, linkedin.com, yelp.com. A user looking at Share of Voice saw
    "competitors" they had never heard of, next to an Edit Settings modal listing four
    completely different ones, and reasonably concluded the page was inventing data.

    Auto-discovery remains a legitimate *suggestion* source, reachable two ways:
    `include_discovered=True` here, or `get_discovered_competitors()`. It is not a stand-in for
    a choice the user has not made. A project with no competitors returns [], and every caller
    already has an empty state for it.

    NOTE, so nobody assumes otherwise: `get_discovered_competitors()` currently has NO caller.
    There is no "suggested competitors" picker in Settings, so a user with an empty competitor
    list has nothing in the UI helping them fill it — worth building, and worth not papering
    over by silently promoting suggestions into measurements, which is what this change ended.

    `site_pk` scopes to one project; without it the read widens across the domain, which is
    right only for a caller that genuinely has no project in hand.
    """
    bare_site = _bare(site_id)

    def _clean(domains, cap=None):
        out: list[str] = []
        for d in domains:
            bare_d = _bare(d)
            if bare_d and bare_d != bare_site and bare_d not in out:
                out.append(bare_d)
                if cap and len(out) == cap:
                    break
        return out

    with get_session() as session:
        _prepare(session)

        chosen = session.execute(
            select(TrackedCompetitor.competitor_domain)
            .where(*_scope(site_id, site_pk))
            .order_by(TrackedCompetitor.added_at.asc())
        ).scalars().all()
        if chosen or not include_discovered:
            return _clean(chosen)

        discovered = session.execute(
            select(CompetitorDomain.competitor_domain)
            .where(CompetitorDomain.site_id == site_id)
            .order_by(CompetitorDomain.intersections.desc())
            .limit(limit * 2)
        ).scalars().all()
        return _clean(discovered, cap=limit)


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

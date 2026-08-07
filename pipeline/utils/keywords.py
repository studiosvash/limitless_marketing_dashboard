"""
utils/keywords.py — single source of truth for loading a site's tracked keywords.

The tracked-keyword list is DATABASE-DRIVEN: it comes from the `saved_keywords` table, i.e.
exactly the keywords an admin bookmarked from the Keyword Explorer in the dashboard ("Track").
So the admin manages the tracking list dynamically from the UI -- no file to edit -- and the
paid per-keyword connectors (SERP position tracking, AI keyword volume) only ever spend money
on keywords the admin actually chose.

The legacy `keywords.txt` file is kept ONLY as a fallback, for backwards compatibility and for
callers with no site context. If the DB has tracked keywords for the site, the file is ignored.
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

KEYWORDS_FILE = str(Path(__file__).parent.parent.parent / "keywords.txt")  # optional fallback


def _load_from_file(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        return []

    seen = set()
    keywords = []
    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        if not line:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        keywords.append(line)
    return keywords


def _load_from_db(site_id: str, location: Optional[str] = None,
                  site_pk: Optional[int] = None) -> list[str]:
    """Keywords the admin explicitly tracks for THIS PROJECT (saved_keywords table).

    `site_pk` is the project's `sites.id`, and it is what makes the list per-project rather than
    per-domain. Position Tracking registers one domain as several projects
    (`add_site(allow_duplicate=True)`), and they all share `site_id` — so filtering on `site_id`
    alone hands a brand-new project every keyword its siblings already track. That is what made
    a freshly created project open with another project's keywords in its grid, in its Rankings
    Overview, and in Positioning's "Newly Added Keywords" card.

    `location` was the first discriminator tried (2026-08-06) and is kept ONLY as a fallback for
    a caller that has a project's location but not its id. It does not actually identify a
    project: two projects on one domain may track the same market, and the wizard defaults every
    project to "United States", so in the common case it separates nothing. Pass `site_pk`.

    Both `None` means domain-wide, which is still correct for a caller with genuinely no project
    in hand.
    """
    # Imported lazily: connectors import this module, and pulling in the DB layer at module
    # import time would risk a circular import.
    try:
        from sqlalchemy import select

        from pipeline.db.schema import SavedKeyword, ensure_saved_keyword_project
        from pipeline.utils.db_connection import get_session
        from pipeline.utils.site_ids import resolve_site_ids

        with get_session() as session:
            ensure_saved_keyword_project(session)   # site_pk may not exist yet on this database
            query = select(SavedKeyword.keyword)
            if site_pk:
                # `site_pk` alone: the project id already implies the domain, while the reverse
                # is not true — one site can be stored under several site_id spellings, and
                # ANDing them hides the rows filed under the ones this project's site_url does
                # not match. See saved_keyword_service._scope.
                query = query.where(SavedKeyword.site_pk == site_pk)
            else:
                query = query.where(SavedKeyword.site_id.in_(resolve_site_ids(site_id)))
                if location:
                    query = query.where(SavedKeyword.location == location)
            rows = list(session.execute(query).scalars().all())
    except Exception as e:
        logger.error(f"[keywords] DB lookup failed for {site_id!r}: {e}", exc_info=True)
        return []

    seen = set()
    keywords = []
    for kw in rows:
        kw = (kw or "").strip()
        if not kw:
            continue
        key = kw.lower()
        if key in seen:
            continue
        seen.add(key)
        keywords.append(kw)
    return keywords


def load_tracked_keywords(site_id: Optional[str] = None, path: str = KEYWORDS_FILE,
                          location: Optional[str] = None,
                          site_pk: Optional[int] = None) -> list[str]:
    """Tracked keywords for ONE PROJECT: the DB list the admin manages from the dashboard.

    `site_pk` scopes the list to a single project when several share a domain — see
    `_load_from_db`. Pass it from anything that has a project in hand; `location` is the weaker
    fallback for callers that only have that.

    THE FILE FALLBACK IS SKIPPED FOR A PROJECT-SCOPED CALL. `keywords.txt` is a legacy,
    domain-agnostic list; handing it to a brand-new project that has genuinely tracked nothing
    yet would refill the empty state this scoping exists to produce. An empty list is the
    honest answer there, and the UI already has a "no keywords tracked yet" state for it.
    """
    if site_id:
        db_keywords = _load_from_db(site_id, location, site_pk)
        if db_keywords:
            return db_keywords
        if site_pk or location:
            scope = f"project #{site_pk}" if site_pk else f"@ {location!r}"
            logger.info(
                f"[keywords] No tracked keywords for {site_id!r} {scope} — this project tracks "
                f"nothing yet. Add some from the Keyword Explorer."
            )
            return []
        logger.info(
            f"[keywords] No tracked keywords in DB for {site_id!r} — falling back to {path}. "
            f"Track keywords from the Keyword Explorer to manage this list from the dashboard."
        )
    return _load_from_file(path)


def keywords_needing_backfill(site_id: str, site_pk: Optional[int] = None,
                              location: Optional[str] = None) -> list[str]:
    """Tracked keywords that have never been measured — the subset an incremental sync needs.

    Scoped to ONE PROJECT by `site_pk`, and its measurements to that project's `location`. Both
    halves matter and for the same money: this is what "Track These New Keywords" narrows its
    sync to, so an unscoped call would spend DataForSEO credits re-measuring a sibling project's
    keywords, and a location-blind measurement check would skip a keyword this project has never
    had measured in ITS market because a sibling had it measured in another one.

    A keyword sent from the Keyword Explorer lands in `saved_keywords` immediately, but it has
    no SERP position, no search volume and no difficulty until a sync fetches them. Re-running
    the whole `positions` scope to pick those up re-queries EVERY tracked keyword against every
    competitor, which is slow and — because DataForSEO meters per query — expensive. This
    returns only the keywords with real work outstanding, so the caller can sync just those.

    "Outstanding" means any of:
      * no `keyword_rankings` row at all for the keyword (never looked up), or
      * every row has `search_volume` IS NULL (market data missing), or
      * every row has `rank_checked_at` IS NULL (no rank connector has ever looked).

    A keyword that has been measured and genuinely ranks nowhere is NOT returned. `rank_checked_at`
    is the whole reason that distinction is now possible: `dataforseo_serp` stamps it even when it
    writes `position: None` for a domain outside the top 30, and `gsc_keywords` stamps it because
    Search Console only returns a query row for a page it actually served. Both are real
    measurements, and re-buying them is exactly the waste this function exists to prevent.

    This used to infer the same thing from `position IS NOT NULL OR impressions > 0`, which could
    not tell a measured "not in the top 30" from a row `dataforseo_keywords` had merely priced —
    both are `position: NULL, impressions: 0`. So every genuinely-unranked keyword was re-queried
    on every incremental sync, forever, and paid for again each time.

    Returns [] on any failure — the caller then falls back to a normal full sync rather than
    silently syncing nothing.
    """
    try:
        from sqlalchemy import select
        from pipeline.db.schema import KeywordRanking
        from pipeline.utils.db_connection import get_session
        from pipeline.utils.site_ids import resolve_site_ids

        tracked = load_tracked_keywords(site_id, location=location, site_pk=site_pk)
        if not tracked:
            return []

        with get_session() as session:
            query = (
                select(KeywordRanking.keyword, KeywordRanking.search_volume,
                       KeywordRanking.rank_checked_at)
                .where(KeywordRanking.site_id.in_(resolve_site_ids(site_id)))
            )
            if location:
                query = query.where(KeywordRanking.location == location)
            rows = session.execute(query).all()

        # Matching is case-insensitive because GSC lower-cases queries while the Explorer
        # preserves what the user typed, and the same keyword must not look unmeasured purely
        # because of casing.
        has_volume = set()
        rank_checked = set()
        seen = set()
        for kw, vol, checked_at in rows:
            key = (kw or "").strip().lower()
            if not key:
                continue
            seen.add(key)
            if vol is not None:
                has_volume.add(key)
            if checked_at is not None:
                rank_checked.add(key)

        out = [
            k for k in tracked
            if (k or "").strip().lower() not in has_volume
            or (k or "").strip().lower() not in rank_checked
        ]
        logger.info(
            f"[keywords] {len(out)} of {len(tracked)} tracked keywords need backfill for "
            f"{site_id!r} ({len(seen)} have a ranking row, {len(has_volume)} have volume, "
            f"{len(rank_checked)} have been rank-checked)"
        )
        return out
    except Exception as exc:
        logger.error(f"[keywords] keywords_needing_backfill failed for {site_id!r}: {exc}", exc_info=True)
        return []

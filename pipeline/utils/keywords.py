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


def _load_from_db(site_id: str) -> list[str]:
    """Keywords the admin explicitly tracks for this site (saved_keywords table), plus any
    keywords currently in keyword_rankings (from GSC queries or past syncs)."""
    # Imported lazily: connectors import this module, and pulling in the DB layer at module
    # import time would risk a circular import.
    try:
        from sqlalchemy import select

        from pipeline.db.schema import SavedKeyword, KeywordRanking
        from pipeline.utils.db_connection import get_session

        with get_session() as session:
            saved_rows = session.execute(
                select(SavedKeyword.keyword).where(SavedKeyword.site_id == site_id)
            ).scalars().all()
            rows = list(saved_rows)
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


def load_tracked_keywords(site_id: Optional[str] = None, path: str = KEYWORDS_FILE) -> list[str]:
    """Tracked keywords for a site: the DB list the admin manages from the dashboard, falling
    back to the legacy keywords.txt file when the DB has none (or no site was given)."""
    if site_id:
        db_keywords = _load_from_db(site_id)
        if db_keywords:
            return db_keywords
        logger.info(
            f"[keywords] No tracked keywords in DB for {site_id!r} — falling back to {path}. "
            f"Track keywords from the Keyword Explorer to manage this list from the dashboard."
        )
    return _load_from_file(path)


def keywords_needing_backfill(site_id: str) -> list[str]:
    """Tracked keywords that have never been measured — the subset an incremental sync needs.

    A keyword sent from the Keyword Explorer lands in `saved_keywords` immediately, but it has
    no SERP position, no search volume and no difficulty until a sync fetches them. Re-running
    the whole `positions` scope to pick those up re-queries EVERY tracked keyword against every
    competitor, which is slow and — because DataForSEO meters per query — expensive. This
    returns only the keywords with real work outstanding, so the caller can sync just those.

    "Outstanding" means any of:
      * no `keyword_rankings` row at all for the keyword (never looked up), or
      * every row has `search_volume` IS NULL (position may exist, market data missing), or
      * every row has BOTH `position` IS NULL and `impressions` is 0/NULL (no evidence a rank
        connector ever actually checked it — see below).

    A keyword that has been measured and genuinely ranks nowhere is NOT returned: `dataforseo_serp`
    writes an explicit `position: None` row when it checks a keyword and the domain isn't in the
    top 30 (see `dataforseo_serp._normalize_task`), and `gsc_keywords` writes real impressions even
    on a 0-click day. Either signal proves a rank connector actually ran, so re-querying that
    keyword would be exactly the waste this exists to avoid — refreshing those is what the
    scheduled full sync is for. The ambiguity this guards against: `dataforseo_keywords` (volume
    only) can write a `position: None` row for a keyword that has NEVER been through a rank
    connector at all, and that row is indistinguishable from a genuine "checked, not ranking" row
    by `position` alone — a keyword tracked between two `positions` syncs landed exactly here,
    with real volume but a rank check that never happened, and the volume-only check let it slip
    through "Track These New Keywords" forever.

    Returns [] on any failure — the caller then falls back to a normal full sync rather than
    silently syncing nothing.
    """
    try:
        from sqlalchemy import select
        from pipeline.db.schema import KeywordRanking
        from pipeline.utils.db_connection import get_session

        tracked = load_tracked_keywords(site_id)
        if not tracked:
            return []

        variants = [site_id]
        if site_id.startswith("sc-domain:"):
            variants.append(site_id.replace("sc-domain:", "", 1))
        else:
            variants.append(f"sc-domain:{site_id}")

        with get_session() as session:
            rows = session.execute(
                select(KeywordRanking.keyword, KeywordRanking.search_volume,
                       KeywordRanking.position, KeywordRanking.impressions)
                .where(KeywordRanking.site_id.in_(variants))
            ).all()

        # Matching is case-insensitive because GSC lower-cases queries while the Explorer
        # preserves what the user typed, and the same keyword must not look unmeasured purely
        # because of casing.
        has_volume = set()
        rank_checked = set()
        seen = set()
        for kw, vol, pos, impressions in rows:
            key = (kw or "").strip().lower()
            if not key:
                continue
            seen.add(key)
            if vol is not None:
                has_volume.add(key)
            if pos is not None or (impressions or 0) > 0:
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

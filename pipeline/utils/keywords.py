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

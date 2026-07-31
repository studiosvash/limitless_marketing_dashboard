"""
pipeline/services/saved_keyword_service.py — the Keyword Explorer's saved research list.

A thin read/write layer over the `saved_keywords` table. This list is a research bookmark
store, completely separate from the keyword-tracking pipeline (keyword_rankings) — saved
keywords are never synced or position-tracked. Site-scoped, shared across the team.
"""
from typing import Optional

from sqlalchemy import select, delete

from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger
from pipeline.db.schema import SavedKeyword
from pipeline.db.writer import ensure_tables, upsert_saved_keywords

logger = get_logger("saved_keyword_service")

# Columns we persist from an Explorer row (anything else in the payload is ignored).
_FIELDS = ("keyword", "location", "search_volume", "keyword_difficulty",
           "cpc", "competition", "intent", "serp_features")


def list_saved_keywords(site_id: str) -> list[dict]:
    """Return the site's saved research keywords, newest first."""
    try:
        with get_session() as session:
            ensure_tables(session, SavedKeyword)  # idempotent; clean empty state pre-first-save
            rows = session.execute(
                select(SavedKeyword)
                .where(SavedKeyword.site_id == site_id)
                .order_by(SavedKeyword.saved_at.desc(), SavedKeyword.id.desc())
            ).scalars().all()
            return [
                {
                    "keyword": r.keyword,
                    "location": r.location,
                    "search_volume": r.search_volume,
                    "keyword_difficulty": r.keyword_difficulty,
                    "cpc": r.cpc,
                    "competition": r.competition,
                    "intent": r.intent,
                    "serp_features": r.serp_features,
                }
                for r in rows
            ]
    except Exception as exc:
        logger.error(f"[saved_keyword_service] list failed: {exc}", exc_info=True)
        return []


# Separators that mean "this was pasted from a list", never part of the keyword itself when
# they sit at either end. A comma INSIDE a phrase ("austin, tx event staff") is real and stays.
_LIST_SEPARATORS = " \t\r\n,;|"


def _clean_row(row: dict, location: Optional[str]) -> Optional[dict]:
    """Keep only persistable fields; require a keyword. Coerce numerics, default location.

    The keyword is stripped of list separators as well as whitespace. `.strip()` alone let a
    pasted comma-separated list through verbatim -- one project had all 16 tracked keywords
    stored as `"festival staffing,"` with the comma included, which is a different phrase: it
    went to DataForSEO inside the query and came back with no AI search volume, having been
    billed for the lookup anyway.
    """
    kw = (row.get("keyword") or "").strip(_LIST_SEPARATORS)
    if not kw:
        return None
    rec = {k: row.get(k) for k in _FIELDS}
    rec["keyword"] = kw
    rec["location"] = (row.get("location") or location or "United States").strip() or "United States"

    def _num(v, cast):
        try:
            return cast(v) if v not in (None, "", "—") else None
        except (TypeError, ValueError):
            return None

    rec["search_volume"] = _num(rec.get("search_volume"), int)
    rec["keyword_difficulty"] = _num(rec.get("keyword_difficulty"), float)
    rec["cpc"] = _num(rec.get("cpc"), float)
    return rec


def save_keywords(site_id: str, rows: list[dict], location: Optional[str] = None) -> int:
    """Upsert the given Explorer rows into the saved list. Returns count saved."""
    records = []
    for row in rows or []:
        rec = _clean_row(row, location)
        if rec:
            rec["site_id"] = site_id
            records.append(rec)
    if not records:
        return 0
    try:
        with get_session() as session:
            n = upsert_saved_keywords(session, records, site_id=site_id)
            session.commit()
            return n
    except Exception as exc:
        logger.error(f"[saved_keyword_service] save failed: {exc}", exc_info=True)
        return 0


def delete_saved_keyword(site_id: str, keyword: str, location: str) -> bool:
    """Remove one saved keyword (by keyword + location). Returns True if a row was deleted."""
    try:
        with get_session() as session:
            ensure_tables(session, SavedKeyword)
            result = session.execute(
                delete(SavedKeyword).where(
                    SavedKeyword.site_id == site_id,
                    SavedKeyword.keyword == keyword,
                    SavedKeyword.location == location,
                )
            )
            session.commit()
            return (result.rowcount or 0) > 0
    except Exception as exc:
        logger.error(f"[saved_keyword_service] delete failed: {exc}", exc_info=True)
        return False

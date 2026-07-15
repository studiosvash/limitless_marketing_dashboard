"""
pipeline/db/writer.py — All write operations (upsert helpers) for every analytics table.

Rules:
- Always upsert (on_conflict_do_update) — never blind INSERT.
- Never call these from Django views directly — only from connectors and pipeline tasks.
- sync_log and refresh_job writes are handled by Django (apps.sync.SyncLog), NOT here.

Every per-domain table carries a site_id column. Helpers below will inject
site_id into the records dict when the caller passes site_id but the records
themselves don't include it.
"""

from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from pipeline.db.schema import (
    Base,
    SEODaily, KeywordRanking, Page, AdMetricDaily,
    Backlink, TechnicalIssue, AISummary,
    CompetitorVisibility, CompetitorDomain,
    PageSpeed, IndexingStatus, SEOAggregate,
    Anomaly, ComparativeMetrics,
    CompetitorKeywordRanking, TrackedCompetitor, AIKeywordData,
    SavedKeyword, BacklinksSnapshot,
)
from pipeline.utils.logger import get_logger

logger = get_logger("db.writer")


# ─────────────────────────────────────────────
# Internal helper
# ─────────────────────────────────────────────

def _ensure_site_id(records: list[dict], site_id: Optional[str]) -> list[dict]:
    """If site_id is provided and not already in each record, inject it."""
    if not records or not site_id:
        return records
    for r in records:
        r.setdefault("site_id", site_id)
    return records


def ensure_tables(session: Session, *models) -> None:
    """Idempotently create the given table(s) if missing.

    The live analytics DB is created once by `init_db`; tables added later (e.g.
    the 2026-06-15 competitor/AI tables) won't exist until create_all runs again.
    create_all only builds MISSING tables, so this never touches existing data —
    it lets a new connector/view self-provision its table on first use.
    """
    bind = session.get_bind()
    Base.metadata.create_all(bind=bind, tables=[m.__table__ for m in models])


# ─────────────────────────────────────────────
# SEO Daily
# ─────────────────────────────────────────────

def upsert_seo_daily(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """
    Upsert SEO daily metrics. Unique on (date, site_id, country, device, landing_page).
    Returns number of records written.
    Batched to avoid SQLite 'too many SQL variables' limit (~999 params).
    """
    if not records:
        return 0

    _ensure_site_id(records, site_id)

    for r in records:
        r.setdefault("country", None)
        r.setdefault("device", None)
        r.setdefault("landing_page", None)

    BATCH_SIZE = 60
    _upsert_keys = ("date", "site_id", "country", "device", "landing_page")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total_written = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(SEODaily).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total_written += len(batch)

    logger.debug(f"[writer] seo_daily: upserted {total_written} rows")
    return total_written


# ─────────────────────────────────────────────
# Keyword Rankings
# ─────────────────────────────────────────────

def upsert_keyword_rankings(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert keyword rankings. Unique on (date, site_id, keyword)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    # site_id is mandatory under the new constraint — default to "" if caller forgot.
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("date", "site_id", "keyword")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(KeywordRanking).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                k: func.coalesce(stmt.excluded[k], getattr(KeywordRanking, k))
                for k in update_cols
            },
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────

def upsert_pages(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert page inventory. Unique on (site_id, url)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("site_id", "url")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(Page).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Ad Metrics
# ─────────────────────────────────────────────

def upsert_ad_metrics(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert ad metrics. Unique on (date, site_id, platform, campaign)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("date", "site_id", "platform", "campaign")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(AdMetricDaily).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Backlinks
# ─────────────────────────────────────────────

def upsert_backlinks(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert backlinks. Unique on (site_id, referring_domain, target_url)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("site_id", "referring_domain", "target_url")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(Backlink).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Competitor visibility
# ─────────────────────────────────────────────

def upsert_competitor_visibility(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert competitor visibility records. Unique on (date, site_id, competitor_domain)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("date", "site_id", "competitor_domain")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(CompetitorVisibility).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Competitor domains (DataForSEO Labs auto-discovered)
# ─────────────────────────────────────────────

def upsert_competitor_domains(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert auto-discovered competitor domains. Unique on (site_id, competitor_domain)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("site_id", "competitor_domain")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(CompetitorDomain).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Technical Issues
# ─────────────────────────────────────────────

def upsert_technical_issues(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert technical issues. Unique on (site_id, url, issue_type)."""
    if not records:
        return 0
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")
    BATCH_SIZE = 80
    _upsert_keys = ("site_id", "url", "issue_type")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(TechnicalIssue).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Page Speed
# ─────────────────────────────────────────────

def upsert_page_speed(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert PageSpeed Insights data. Unique on (site_id, url, strategy)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("site_id", "url", "strategy")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(PageSpeed).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Indexing Status
# ─────────────────────────────────────────────

def upsert_indexing_status(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert URL Inspection results. Unique on (site_id, url)."""
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("site_id", "url")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(IndexingStatus).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# AI Summary
# ─────────────────────────────────────────────

def upsert_ai_summary(session: Session, week_start: date, summary_text: str,
                      model: str = "", site_id: str = "") -> None:
    """Upsert AI summary for a given (week_start, site_id)."""
    stmt = sqlite_insert(AISummary).values(
        week_start=week_start,
        site_id=site_id or "",
        summary_text=summary_text,
        model_used=model,
        generated_at=datetime.now(timezone.utc),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["week_start", "site_id"],
        set_={
            "summary_text": stmt.excluded.summary_text,
            "generated_at": stmt.excluded.generated_at,
            "model_used": stmt.excluded.model_used,
        },
    )
    session.execute(stmt)


# ─────────────────────────────────────────────
# SEO Aggregates
# ─────────────────────────────────────────────

def upsert_seo_aggregate(session: Session, records: list[dict]) -> int:
    """Upsert pre-rolled SEO aggregates. Unique on (site_id, period_type, period_start)."""
    if not records:
        return 0
    update_cols = [k for k in records[0] if k not in ("site_id", "period_type", "period_start")]
    BATCH_SIZE = 60
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(SEOAggregate).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["site_id", "period_type", "period_start"],
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    return total


# ─────────────────────────────────────────────
# Anomalies
# ─────────────────────────────────────────────

def upsert_anomaly(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert detected metric anomalies. Unique on (date, site_id, metric_type)."""
    if not records:
        return 0
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")
    stmt = sqlite_insert(Anomaly).values(records)
    stmt = stmt.on_conflict_do_update(
        index_elements=["date", "site_id", "metric_type"],
        set_={k: stmt.excluded[k] for k in records[0] if k not in ("date", "site_id", "metric_type")},
    )
    session.execute(stmt)
    return len(records)


# ─────────────────────────────────────────────
# Comparative Metrics
# ─────────────────────────────────────────────

def upsert_comparative_metrics(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert week-over-week / month-over-month comparative metrics. Unique on (site_id, metric_type, week_start)."""
    if not records:
        return 0
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")
    stmt = sqlite_insert(ComparativeMetrics).values(records)
    stmt = stmt.on_conflict_do_update(
        index_elements=["site_id", "metric_type", "week_start"],
        set_={k: stmt.excluded[k] for k in records[0] if k not in ("site_id", "metric_type", "week_start")},
    )
    session.execute(stmt)
    return len(records)


# ─────────────────────────────────────────────
# Competitor keyword rankings (per-keyword competitor positions — 2026-06-15)
# ─────────────────────────────────────────────

def upsert_competitor_keyword_rankings(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert per-keyword competitor positions. Unique on (date, site_id, keyword, competitor_domain)."""
    if not records:
        return 0

    ensure_tables(session, CompetitorKeywordRanking)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 60
    _upsert_keys = ("date", "site_id", "keyword", "competitor_domain")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(CompetitorKeywordRanking).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] competitor_keyword_rankings: upserted {total} rows")
    return total


# ─────────────────────────────────────────────
# AI keyword data (DataForSEO AI Optimization — 2026-06-15)
# ─────────────────────────────────────────────

def upsert_ai_keyword_data(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert AI-search keyword data. Unique on (date, site_id, keyword)."""
    if not records:
        return 0

    ensure_tables(session, AIKeywordData)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    BATCH_SIZE = 80
    _upsert_keys = ("date", "site_id", "keyword")
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(AIKeywordData).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                k: func.coalesce(stmt.excluded[k], getattr(AIKeywordData, k))
                for k in update_cols
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] ai_keyword_data: upserted {total} rows")
    return total


# ─────────────────────────────────────────────
# Saved Keywords (Keyword Explorer research list)
# ─────────────────────────────────────────────

def upsert_saved_keywords(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert saved research keywords. Unique on (site_id, keyword, location).
    Re-saving the same keyword/location updates its metrics in place."""
    if not records:
        return 0

    ensure_tables(session, SavedKeyword)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")
        r.setdefault("location", "United States")

    BATCH_SIZE = 80
    _upsert_keys = ("site_id", "keyword", "location")
    update_cols = [k for k in records[0] if k not in _upsert_keys and k != "id"]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = sqlite_insert(SavedKeyword).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] saved_keywords: upserted {total} rows")
    return total


# ─────────────────────────────────────────────
# Backlinks page snapshot (one JSON payload per site; DB-first cache)
# ─────────────────────────────────────────────

def save_backlinks_snapshot(session: Session, site_id: str, payload_json: str) -> None:
    """Overwrite the stored Backlinks payload for a site (one row per site_id)."""
    ensure_tables(session, BacklinksSnapshot)
    stmt = sqlite_insert(BacklinksSnapshot).values(
        site_id=site_id or "", fetched_at=datetime.now(timezone.utc), payload=payload_json,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["site_id"],
        set_={"fetched_at": stmt.excluded.fetched_at, "payload": stmt.excluded.payload},
    )
    session.execute(stmt)
    logger.debug(f"[writer] backlinks_snapshot: saved for {site_id}")


def get_backlinks_snapshot(session: Session, site_id: str):
    """Return (fetched_at, payload_json) for a site, or None if never fetched."""
    ensure_tables(session, BacklinksSnapshot)
    row = session.get(BacklinksSnapshot, site_id or "")
    return (row.fetched_at, row.payload) if row else None

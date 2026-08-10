"""
pipeline/db/writer.py — All write operations (upsert helpers) for every analytics table.

Rules:
- Always upsert (on_conflict_do_update) — never blind INSERT.
- Take the `insert` construct and the batch size from pipeline.db.dialect, never
  from a hardcoded dialect import: the same writer runs against SQLite (dev/tests)
  and Postgres (prod), and the ON CONFLICT construct differs between them.
- Never call these from Django views directly — only from connectors and pipeline tasks.
- sync_log and refresh_job writes are handled by Django (apps.sync.SyncLog), NOT here.

Every per-domain table carries a site_id column. Helpers below will inject
site_id into the records dict when the caller passes site_id but the records
themselves don't include it.
"""

from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pipeline.db.dialect import max_batch_size, upsert_insert
from pipeline.db.schema import (
    Base,
    SEODaily, SEODailyTotal, GA4DailyTotal, KeywordRanking, Page, AdMetricDaily,
    Backlink, TechnicalIssue, AISummary,
    CompetitorVisibility, CompetitorDomain,
    PageSpeed, IndexingStatus, SEOAggregate,
    Anomaly, ComparativeMetrics,
    CompetitorKeywordRanking, TrackedCompetitor, AIKeywordData,
    LLMCitedPage, LLMMentionMetric,
    SavedKeyword, BacklinksSnapshot,
    AuditSnapshot, AdSearchTerm, GA4CampaignDaily, ConnectorCost,
    PageCrawlMeta, ensure_page_speed_columns, ensure_backlinks_columns,
    ensure_ranking_location_columns, ensure_ranking_location_keys, DEFAULT_LOCATION,
    ensure_saved_keyword_project, UNOWNED_SITE_PK,
)
from pipeline.utils.logger import get_logger

logger = get_logger("db.writer")


# ─────────────────────────────────────────────
# Internal helper
# ─────────────────────────────────────────────

def _canonical_site_map() -> dict:
    """Every known spelling of a site → its canonical `Site.site_url`.

    A site is reachable by at least three strings: its `site_url` (the key every page reads
    by), its `gsc_property` (`sc-domain:...`), and historically the URL-prefix form
    (`https://.../`). Connectors that stamped a non-canonical spelling created a full second
    copy of a site's history that no page read and any two-spelling query double-counted —
    123,396 seo_daily rows for one site, removed 2026-08-03. Mapping is rebuilt per write
    call (one small query against `sites`) rather than cached, so a site added mid-process
    is picked up.
    """
    from pipeline.db.schema import Site
    from pipeline.utils.db_connection import get_session
    mapping: dict[str, str] = {}
    with get_session() as s:
        rows = s.execute(select(Site.site_url, Site.gsc_property)).all()
    for site_url, gsc_property in rows:
        mapping[site_url] = site_url
        bare = site_url.replace("sc-domain:", "")
        for alias in (gsc_property, f"sc-domain:{bare}", bare,
                      f"https://{bare}/", f"https://{bare}", f"http://{bare}/"):
            if alias:
                mapping.setdefault(alias, site_url)
    return mapping


def _ensure_site_id(records: list[dict], site_id: Optional[str]) -> list[dict]:
    """Inject `site_id` where missing, then canonicalise EVERY record's spelling.

    Canonicalisation is unconditional — not just for the injected default — because the
    duplicated-history incident above was caused by records that already carried a site_id,
    just the wrong spelling of it. A spelling that matches no known site passes through
    unchanged: refusing to write would turn a missing Site row into silent data loss.
    """
    if not records:
        return records
    if site_id:
        for r in records:
            r.setdefault("site_id", site_id)
    try:
        mapping = _canonical_site_map()
    except Exception:
        logger.warning("[writer] could not build the canonical site map; writing site_id "
                       "as given", exc_info=True)
        return records
    for r in records:
        sid = r.get("site_id")
        if sid and sid in mapping and mapping[sid] != sid:
            r["site_id"] = mapping[sid]
    return records


def _dedupe_by_keys(records: list[dict], keys: tuple[str, ...]) -> list[dict]:
    """Collapse records sharing the same ON CONFLICT key tuple, keeping the LAST occurrence.

    MANDATORY before every multi-row `insert(...).values(batch).on_conflict_do_update(...)`,
    because the two dialects disagree about what a duplicate inside one statement means:

      * **Postgres** treats the whole multi-row INSERT as a single command and refuses to
        update the same row twice -- it raises
        `CardinalityViolation: ON CONFLICT DO UPDATE command cannot affect row a second time`.
      * **SQLite** applies rows one at a time, so the second duplicate simply UPDATEs the row
        the first one just inserted. No error, no warning.

    That asymmetry is a trap, not a nuisance: the entire test suite runs on SQLite
    (`config/settings/base.py` forces it when RUNNING_TESTS), so this class of bug **cannot**
    be caught by `manage.py test` and only appears in production. It cost a real outage --
    `upsert_backlinks` conflicts on (site_id, referring_domain, target_url) while the
    DataForSEO connector discards `url_from`, so every site-wide footer/nav link collapsed to
    the same key. Because `BaseConnector.sync` wraps the write in one `get_session()` that
    rolls back on any exception, a single duplicate discarded the whole 1000-row batch and the
    Backlinks page sat empty in its "setup" state. Postgres also raises the batch size from 80
    to 1000 (`dialect.max_batch_size`), so prod sends all rows as ONE statement -- maximising
    the chance that a duplicate lands inside it.

    "Last wins" matches `on_conflict_do_update` semantics: the final value for a key is what
    the row would have ended up with had the statement been applied row by row. Input order is
    otherwise preserved (the survivor keeps the first occurrence's position) so batching stays
    deterministic and diffable.

    A `None` in a key column is compared like any other value here. Neither Postgres nor
    SQLite treats NULL as conflicting in the unique index itself, so a record with a NULL
    key column would bypass the upsert and duplicate on every re-sync -- which is why
    upserts with nullable key columns run `_coerce_null_keys` first and store `""` instead.
    """
    if len(records) < 2:
        return records

    first_index: dict[tuple, int] = {}
    out: list[dict] = []
    for r in records:
        k = tuple(r.get(col) for col in keys)
        idx = first_index.get(k)
        if idx is None:
            first_index[k] = len(out)
            out.append(r)
        else:
            out[idx] = r  # last wins

    dropped = len(records) - len(out)
    if dropped:
        logger.info(
            f"[writer] Collapsed {dropped} duplicate row(s) on {keys} "
            f"({len(records)} in, {len(out)} out)"
        )
    return out


def _coerce_null_keys(records: list[dict], keys: tuple[str, ...]) -> None:
    """Replace None with "" in the given conflict-key columns, in place.

    NULL never equals NULL in a unique index (Postgres and SQLite alike), so a row with a
    NULL key column slips past ON CONFLICT and inserts a fresh duplicate on every re-sync.
    Storing the empty string instead keeps the upsert honest; readers only group/display
    these columns, they never filter on IS NULL.
    """
    for r in records:
        for col in keys:
            if r.get(col) is None:
                r[col] = ""


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

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 60)
    _upsert_keys = ("date", "site_id", "country", "device", "landing_page")
    _coerce_null_keys(records, ("country", "device", "landing_page"))
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total_written = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(SEODaily).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total_written += len(batch)

    logger.debug(f"[writer] seo_daily: upserted {total_written} rows")
    return total_written


def upsert_seo_daily_totals(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert the unfiltered per-day Search Console figures. Unique on (date, site_id).

    Always an upsert, never an insert-only: Google keeps adjusting a day's numbers for a
    couple of days after it first reports them, so a re-fetch of an already-stored date has
    to overwrite it. Storing the first observation and skipping later ones would freeze the
    dashboard on provisional figures that Search Console itself has since revised.
    """
    if not records:
        return 0

    _ensure_site_id(records, site_id)

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 6)
    _upsert_keys = ("date", "site_id")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total_written = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(SEODailyTotal).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total_written += len(batch)

    logger.debug(f"[writer] seo_daily_totals: upserted {total_written} rows")
    return total_written


def replace_keyword_lists(session: Session, site_id: str, lists: list[dict]) -> int:
    """Replace a site's research keyword lists wholesale. Returns entries written.

    Delete-then-insert rather than an upsert, deliberately: the SPA edits lists as whole
    objects (rename, remove keyword, delete list) and persists the complete new state, so
    the stored state must become exactly what was sent — an upsert would resurrect entries
    the user just removed. The delete and inserts share one transaction; a failed save
    leaves the previous lists intact.

    `lists`: [{"name": str, "keywords": [{"keyword", "search_volume", "keyword_difficulty",
    "cpc", "intent"}, ...]}, ...]. Keywords are deduplicated case-insensitively within a
    list; the same keyword MAY appear in several lists (that is what "lists" mean) — the
    portfolio KPIs deduplicate across them at read time instead.
    """
    from pipeline.db.schema import KeywordListEntry

    ensure_tables(session, KeywordListEntry)
    _canonical = _canonical_site_map().get(site_id, site_id)
    session.execute(
        KeywordListEntry.__table__.delete().where(KeywordListEntry.site_id == _canonical)
    )

    rows = []
    for lst in lists or []:
        name = (lst.get("name") or "").strip()
        if not name:
            continue
        seen: set[str] = set()
        for item in lst.get("keywords") or []:
            if isinstance(item, str):
                item = {"keyword": item}
            kw = (item.get("keyword") or item.get("kw") or "").strip()
            if not kw or kw.lower() in seen:
                continue
            seen.add(kw.lower())
            rows.append({
                "site_id": _canonical,
                "list_name": name,
                "keyword": kw,
                "search_volume": item.get("search_volume", item.get("volume")),
                "keyword_difficulty": item.get("keyword_difficulty", item.get("kd")),
                "cpc": item.get("cpc"),
                "intent": item.get("intent"),
            })

    if rows:
        BATCH = max_batch_size(session, 7)
        for i in range(0, len(rows), BATCH):
            session.execute(KeywordListEntry.__table__.insert().values(rows[i:i + BATCH]))
    logger.debug(f"[writer] keyword_list_entries: replaced with {len(rows)} rows for {site_id}")
    return len(rows)


def upsert_ga4_daily_totals(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert session-scoped GA4 daily figures. Unique on (date, site_id, country).

    An upsert for the same reason as seo_daily_totals: GA4 revises a recent day's numbers
    after first reporting them, so re-fetching an already-stored date must overwrite it.
    """
    if not records:
        return 0

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("country", "(not set)")

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 8)
    _upsert_keys = ("date", "site_id", "country")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total_written = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(GA4DailyTotal).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={k: stmt.excluded[k] for k in update_cols},
        )
        session.execute(stmt)
        total_written += len(batch)

    logger.debug(f"[writer] ga4_daily_totals: upserted {total_written} rows")
    return total_written


# ─────────────────────────────────────────────
# Keyword Rankings
# ─────────────────────────────────────────────

# Engines already reconciled for the `location` change this process. The reconcile is
# idempotent and cheap, but it runs an inspector over two tables and `upsert_keyword_rankings`
# is called once per batch of 80 rows — doing it every time would put a schema inspection in
# the middle of a 200k-row write. Keyed by engine so a process talking to two databases
# (the test suite creates one per case) reconciles each of them.
_RANKING_LOCATION_READY: set = set()


def _ensure_ranking_location(session: Session) -> None:
    """Make sure this database has the `location` column and its unique key. Once per engine."""
    bind = session.get_bind()
    key = id(bind)
    if key in _RANKING_LOCATION_READY:
        return
    ensure_ranking_location_columns(session)
    ensure_ranking_location_keys(session)
    _RANKING_LOCATION_READY.add(key)


# The columns a SERP rank capture OWNS. Pass these as `overwrite_columns` from a connector that
# actually inspected the SERP (`dataforseo_serp`), so that a measured ABSENCE can be recorded.
#
# `serp_features` is deliberately not here: `keyword_rankings` has no such column (it lives on
# `saved_keywords`). `overwrite_columns` ignores names the record set does not carry, so naming
# it would be harmless — but listing a column that does not exist in the one place a reader
# looks for the contract is how a fiction gets copied forward.
SERP_MEASUREMENT_COLUMNS = ("position", "url", "rank_checked_at")


def upsert_keyword_rankings(session: Session, records: list[dict], site_id: Optional[str] = None,
                            overwrite_columns: Optional[tuple] = None) -> int:
    """Upsert keyword rankings. Unique on (date, site_id, keyword, location).

    Every column is COALESCEd by default — `coalesce(excluded[k], stored[k])` — because THREE
    connectors write this one row and each must be unable to blank the others' work:
    `dataforseo_serp` owns the position, `dataforseo_keywords` owns volume/KD/CPC and knows
    nothing about ranks, `gsc_keywords` owns clicks/impressions. That default stays.

    `overwrite_columns` names the columns THIS caller owns, which are then set from the incoming
    record unconditionally. It exists because COALESCE made a measured DROP unrecordable:
    `dataforseo_serp` captures to depth 30 and writes `position: None` when the domain is not in
    it, which is a MEASUREMENT, not a gap. COALESCE discarded it and kept whatever rank the row
    already held — while stamping a fresh `rank_checked_at` on top, so a site that fell off page
    one on a date it had previously been recorded at #4 kept showing #4, marked freshly checked,
    permanently. `SERP_MEASUREMENT_COLUMNS` is the set for that caller.

    Names not present in the records are ignored, so a caller can pass one list for a batch that
    does not carry every column, and a caller that never sends `position` still cannot clear one.

    Defaults to None — today's behaviour exactly — so every existing call site is unaffected.
    """
    if not records:
        return 0

    # `location` was added to an already-shipped table and joined its unique key, so a database
    # created before that has neither — and both the INSERT's column list and its ON CONFLICT
    # target would fail. Same self-provisioning contract as ensure_page_speed_columns above.
    _ensure_ranking_location(session)

    _ensure_site_id(records, site_id)
    # site_id is mandatory under the new constraint — default to "" if caller forgot.
    for r in records:
        r.setdefault("site_id", "")
        # `location` is part of the key, so a NULL would bypass ON CONFLICT on Postgres and
        # duplicate the row on every sync. A writer that does not know its location is writing
        # the national SERP, which is what DEFAULT_LOCATION means.
        if not r.get("location"):
            r["location"] = DEFAULT_LOCATION

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("date", "site_id", "keyword", "location")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    overwrite = {c for c in (overwrite_columns or ()) if c in update_cols}
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(KeywordRanking).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                # An owned column takes the incoming value even when it is NULL: a measured
                # absence is a measurement. Everything else keeps COALESCE.
                k: (stmt.excluded[k] if k in overwrite
                    else func.coalesce(stmt.excluded[k], getattr(KeywordRanking, k)))
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

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "url")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(Page).values(batch)
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

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("date", "site_id", "platform", "campaign")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(AdMetricDaily).values(batch)
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

    # `select(Backlink)` / `insert(Backlink)` reference url_from/page_from_rank/spam_score,
    # which do not exist on a `backlinks` table created before those columns were added.
    ensure_backlinks_columns(session)

    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "referring_domain", "target_url")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(Backlink).values(batch)
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

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("date", "site_id", "competitor_domain")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(CompetitorVisibility).values(batch)
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

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "competitor_domain")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(CompetitorDomain).values(batch)
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
    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "url", "issue_type")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(TechnicalIssue).values(batch)
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

    # `tbt_ms` was added to an already-shipped table, so a database created before it has no
    # such column and both the INSERT and every later `select(PageSpeed)` would fail.
    ensure_page_speed_columns(session)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    insert = upsert_insert(session)
    # 60, not 80: page_speed is 15 columns wide now, and 80 rows would bind 1 200 parameters —
    # past SQLite's ~999 ceiling. 60 x 15 = 900.
    BATCH_SIZE = max_batch_size(session, 60)
    _upsert_keys = ("site_id", "url", "strategy")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(PageSpeed).values(batch)
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

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "url")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(IndexingStatus).values(batch)
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
    insert = upsert_insert(session)
    stmt = insert(AISummary).values(
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
    records = _dedupe_by_keys(records, ("site_id", "period_type", "period_start"))
    update_cols = [k for k in records[0] if k not in ("site_id", "period_type", "period_start")]
    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 60)
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(SEOAggregate).values(batch)
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
    records = _dedupe_by_keys(records, ("date", "site_id", "metric_type"))
    insert = upsert_insert(session)
    stmt = insert(Anomaly).values(records)
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
    records = _dedupe_by_keys(records, ("site_id", "metric_type", "week_start"))
    insert = upsert_insert(session)
    stmt = insert(ComparativeMetrics).values(records)
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
    """Upsert per-keyword competitor positions.
    Unique on (date, site_id, keyword, competitor_domain, location)."""
    if not records:
        return 0

    ensure_tables(session, CompetitorKeywordRanking)
    _ensure_ranking_location(session)   # see upsert_keyword_rankings
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")
        if not r.get("location"):
            r["location"] = DEFAULT_LOCATION

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 60)
    _upsert_keys = ("date", "site_id", "keyword", "competitor_domain", "location")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(CompetitorKeywordRanking).values(batch)
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

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("date", "site_id", "keyword")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(AIKeywordData).values(batch)
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
# LLM Mentions (DataForSEO AI Optimization)
# ─────────────────────────────────────────────

def upsert_llm_mention_metrics(session: Session, records: list[dict],
                               site_id: Optional[str] = None) -> int:
    """Upsert weekly LLM-mention aggregates. Unique on
    (site_id, week_start, subject_domain, platform)."""
    if not records:
        return 0

    ensure_tables(session, LLMMentionMetric)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "week_start", "subject_domain", "platform")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(LLMMentionMetric).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                k: func.coalesce(stmt.excluded[k], getattr(LLMMentionMetric, k))
                for k in update_cols
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] llm_mention_metrics: upserted {total} rows")
    return total


def upsert_llm_cited_pages(session: Session, records: list[dict],
                           site_id: Optional[str] = None) -> int:
    """Upsert the project's own cited URLs for a week. Unique on (site_id, week_start, url)."""
    if not records:
        return 0

    ensure_tables(session, LLMCitedPage)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "week_start", "url")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(LLMCitedPage).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                k: func.coalesce(stmt.excluded[k], getattr(LLMCitedPage, k))
                for k in update_cols
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] llm_cited_pages: upserted {total} rows")
    return total


# ─────────────────────────────────────────────
# Saved Keywords (Keyword Explorer research list)
# ─────────────────────────────────────────────

def upsert_saved_keywords(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert tracked keywords. Unique on (site_pk, site_id, keyword, location).

    `site_pk` is the OWNING PROJECT and leads the key — several projects share one `site_id`
    (see the SavedKeyword model), so without it a second project tracking a keyword its sibling
    already tracks would UPDATE the sibling's row instead of getting its own. Re-saving the same
    keyword for the same project updates its metrics in place, as before.
    """
    if not records:
        return 0

    ensure_tables(session, SavedKeyword)
    ensure_saved_keyword_project(session)   # self-provisions site_pk on a pre-existing database
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")
        r.setdefault("location", "United States")
        # Never NULL: it is a conflict-target column, and Postgres does not treat NULL = NULL as
        # a conflict, so a null here would bypass ON CONFLICT and duplicate on every save.
        if r.get("site_pk") is None:
            r["site_pk"] = UNOWNED_SITE_PK

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_pk", "site_id", "keyword", "location")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys and k != "id"]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(SavedKeyword).values(batch)
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
    insert = upsert_insert(session)
    stmt = insert(BacklinksSnapshot).values(
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


# ─────────────────────────────────────────────
# History & cost tables (2026-07)
# These back four screens that were built over data nothing ever stored:
# Site Audit Compare/Progress, Ads Search Terms, Ads Attribution, Settings cost.
# All four use ensure_tables() so they self-provision on an existing database
# without a migration, exactly like the 2026-06 competitor/AI tables did.
# ─────────────────────────────────────────────

def upsert_audit_snapshot(session: Session, record: dict) -> int:
    """Record one completed Site Audit crawl. Unique on (site_id, captured_at), so a second
    crawl on the same day updates rather than adding a misleading second trend point."""
    if not record:
        return 0
    ensure_tables(session, AuditSnapshot)
    insert = upsert_insert(session)
    stmt = insert(AuditSnapshot).values(record)
    stmt = stmt.on_conflict_do_update(
        index_elements=["site_id", "captured_at"],
        set_={
            "score": stmt.excluded.score,
            "errors": stmt.excluded.errors,
            "warnings": stmt.excluded.warnings,
            "notices": stmt.excluded.notices,
            "pages_crawled": stmt.excluded.pages_crawled,
            "by_check": stmt.excluded.by_check,
        },
    )
    session.execute(stmt)
    logger.debug(f"[writer] audit_snapshots: upserted {record.get('site_id')}")
    return 1


def upsert_ad_search_terms(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert Google Ads search-term rows. Unique on (date, site_id, term, campaign_id)."""
    if not records:
        return 0
    ensure_tables(session, AdSearchTerm)
    _ensure_site_id(records, site_id)
    _coerce_null_keys(records, ("campaign_id",))
    records = _dedupe_by_keys(records, ("date", "site_id", "term", "campaign_id"))
    insert = upsert_insert(session)
    total = 0
    batch_size = max_batch_size(session, 80)
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        stmt = insert(AdSearchTerm).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["date", "site_id", "term", "campaign_id"],
            set_={
                "matched_keyword": stmt.excluded.matched_keyword,
                "match_type": stmt.excluded.match_type,
                "campaign": stmt.excluded.campaign,
                "impressions": stmt.excluded.impressions,
                "clicks": stmt.excluded.clicks,
                "cost": stmt.excluded.cost,
                "conversions": stmt.excluded.conversions,
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] ad_search_terms: upserted {total} rows")
    return total


def upsert_ga4_campaign_daily(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert GA4 per-campaign key events / revenue. Unique on (date, site_id, campaign)."""
    if not records:
        return 0
    ensure_tables(session, GA4CampaignDaily)
    _ensure_site_id(records, site_id)
    records = _dedupe_by_keys(records, ("date", "site_id", "campaign"))
    insert = upsert_insert(session)
    total = 0
    batch_size = max_batch_size(session, 80)
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        stmt = insert(GA4CampaignDaily).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["date", "site_id", "campaign"],
            set_={
                "sessions": stmt.excluded.sessions,
                "key_events": stmt.excluded.key_events,
                "revenue": stmt.excluded.revenue,
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] ga4_campaign_daily: upserted {total} rows")
    return total


def upsert_page_crawl_meta(session: Session, records: list[dict], site_id: Optional[str] = None) -> int:
    """Upsert per-page OnPage link/word counts. Unique on (site_id, url).

    `func.coalesce(excluded.col, existing.col)` rather than a plain overwrite: OnPage omits a
    field it could not measure on a given crawl, and a re-crawl that returns NULL for
    `inbound_links_count` must not erase the number the previous crawl really measured. That is
    the same rule `upsert_keyword_rankings` applies for the same reason.

    `crawled_at` IS overwritten unconditionally — it is the freshness of the row, not a
    measurement, so the newest crawl always wins.
    """
    if not records:
        return 0
    # Self-provisions on an existing database, like the 2026-06 competitor/AI tables.
    ensure_tables(session, PageCrawlMeta)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    insert = upsert_insert(session)
    # 7 columns -> 80 rows binds 560 parameters, inside SQLite's ~999 ceiling.
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "url")
    records = _dedupe_by_keys(records, _upsert_keys)
    _always_overwrite = ("crawled_at",)
    update_cols = [k for k in records[0] if k not in _upsert_keys and k != "id"]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(PageCrawlMeta).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                k: (stmt.excluded[k] if k in _always_overwrite
                    else func.coalesce(stmt.excluded[k], getattr(PageCrawlMeta, k)))
                for k in update_cols
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] page_crawl_meta: upserted {total} rows")
    return total


def insert_connector_cost(session: Session, site_id: str, connector: str, cost: float,
                          units: Optional[int] = None, notes: Optional[str] = None) -> int:
    """Append one connector-run cost. Deliberately an INSERT, not an upsert: every run is a
    separate spend event, and collapsing them would make the 90-day total wrong. Never raises —
    a cost-logging failure must not fail the sync that produced the data."""
    try:
        ensure_tables(session, ConnectorCost)
        session.execute(
            ConnectorCost.__table__.insert(),
            [{
                "site_id": site_id or "",
                "connector": connector,
                "run_at": datetime.now(timezone.utc),
                "cost": float(cost or 0.0),
                "units": units,
                "currency": "USD",
                "notes": notes,
            }],
        )
        return 1
    except Exception as exc:
        logger.warning(f"[writer] connector_costs: could not record cost for {connector}: {exc}")
        return 0

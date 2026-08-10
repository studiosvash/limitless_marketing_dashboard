"""
pipeline/services/saved_keyword_service.py — the Keyword Explorer's tracked keyword list.

A thin read/write layer over the `saved_keywords` table: the keywords an admin explicitly sent
from the Keyword Explorer to a project. PROJECT-scoped, shared across the team.

EVERY FUNCTION HERE TAKES `site_pk`, AND EVERY CALLER THAT HAS A PROJECT MUST PASS IT. `site_id`
is the domain, and one domain can be registered as several independent projects
(`add_site(allow_duplicate=True)`), so a call scoped by `site_id` alone returns the union of
every sibling project's list — which is how a brand-new project came to open with 28 keywords
its user had never chosen. See the `site_pk` comment on the SavedKeyword model.

`site_pk=None` means domain-wide and is still correct for a caller with genuinely no project in
hand (a maintenance command, a cross-project audit). It is not a shortcut for "I didn't have it
handy".
"""
from typing import Optional

from sqlalchemy import select, delete

from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger
from pipeline.db.schema import SavedKeyword, UNOWNED_SITE_PK, ensure_saved_keyword_project
from pipeline.db.writer import ensure_tables, upsert_saved_keywords

logger = get_logger("saved_keyword_service")

# Columns we persist from an Explorer row (anything else in the payload is ignored).
_FIELDS = ("keyword", "location", "search_volume", "keyword_difficulty",
           "cpc", "competition", "intent", "serp_features")


def _prepare(session) -> None:
    """Table exists and carries `site_pk`. Idempotent; issues nothing once reconciled."""
    ensure_tables(session, SavedKeyword)      # clean empty state pre-first-save
    ensure_saved_keyword_project(session)     # self-provisions site_pk on an existing database


def project_scope(site_id: str, site_pk: Optional[int]) -> list:
    """WHERE clauses selecting one project's rows, or the whole domain when site_pk is None.

    `site_pk` alone when it is given, and deliberately NOT `site_pk AND site_id`. The project id
    already implies the domain — but the reverse is not true, because one site can be stored
    under several `site_id` spellings (`premierstaff.com`, `https://premierstaff.com/`, … —
    skills.md §3). ANDing them drops the rows filed under a spelling the project's own
    `site_url` doesn't happen to match: 16 of one live project's 44 tracked keywords were
    invisible to it that way, having been written before the domain was normalised.

    Without a project id, fall back to matching every spelling of the domain rather than the one
    exact string — same reason.
    """
    if site_pk:
        return [SavedKeyword.site_pk == site_pk]
    from pipeline.utils.site_ids import resolve_site_ids
    return [SavedKeyword.site_id.in_(resolve_site_ids(site_id))]


def list_saved_keywords(site_id: str, site_pk: Optional[int] = None) -> list[dict]:
    """Return THIS PROJECT's tracked keywords, newest first.

    Deduplicated on the keyword, case-insensitively, newest row winning. A project that had its
    tracking location edited can hold the same keyword under both the old and the new location
    (`location` is still part of the unique key) — that is one keyword the user tracked once,
    and showing it twice would be a rendering artefact of a schema detail.
    """
    try:
        with get_session() as session:
            _prepare(session)
            rows = session.execute(
                select(SavedKeyword)
                .where(*project_scope(site_id, site_pk))
                .order_by(SavedKeyword.saved_at.desc(), SavedKeyword.id.desc())
            ).scalars().all()
            out, seen = [], set()
            for r in rows:
                key = (r.keyword or "").strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                out.append({
                    "keyword": r.keyword,
                    "location": r.location,
                    "search_volume": r.search_volume,
                    "keyword_difficulty": r.keyword_difficulty,
                    "cpc": r.cpc,
                    "competition": r.competition,
                    "intent": r.intent,
                    "serp_features": r.serp_features,
                })
            return out
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


def save_keywords(site_id: str, rows: list[dict], location: Optional[str] = None,
                  site_pk: Optional[int] = None) -> int:
    """Upsert the given Explorer rows into THIS PROJECT's tracked list. Returns count saved."""
    records = []
    for row in rows or []:
        rec = _clean_row(row, location)
        if rec:
            rec["site_id"] = site_id
            rec["site_pk"] = site_pk or UNOWNED_SITE_PK
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


def reconcile_saved_keywords(site_id: str, rows: list[dict], location: Optional[str] = None,
                             site_pk: Optional[int] = None) -> dict:
    """Make this project's tracked list match `rows` by NAME. Returns {added, removed, kept}.

    Inserts the keywords that are missing, deletes the ones no longer present, and NEVER touches
    a surviving row. That last part is the whole point.

    The bulk-replace endpoint used to clear the list and rewrite it from the request body. The
    Edit Project modal has no metrics to send -- it fills every row with
    `{volume: 0, kd: null, cpc: null, intent: 'Informational'}` -- so every "Save Settings" press
    overwrote each keyword's real, paid-for search volume with a fabricated 0 and wiped its
    difficulty, CPC and intent. The 0 was worse than a null, because `_volume_coverage` counts
    only nulls: the response then reported full volume coverage over invented numbers.

    Identity is the cleaned, case-folded keyword, so a cosmetic edit ("Festival Staffing" for
    "festival staffing") is the same keyword and keeps its metrics rather than being deleted and
    reinserted blank. Metrics on an INCOMING row are still honoured for rows that are genuinely
    new -- the Keyword Explorer's send-to-project flow really does carry them.

    Idempotent: reconciling the same list twice reports {added: 0, removed: 0}.
    """
    incoming: dict[str, dict] = {}
    for row in rows or []:
        rec = _clean_row(row if isinstance(row, dict) else {"keyword": row}, location)
        if rec:
            incoming.setdefault(rec["keyword"].lower(), rec)

    existing = {(r["keyword"] or "").strip().lower(): r
                for r in list_saved_keywords(site_id, site_pk)}

    to_add = [incoming[k] for k in incoming.keys() - existing.keys()]
    to_remove = [existing[k]["keyword"] for k in existing.keys() - incoming.keys()]

    added = save_keywords(site_id, to_add, location, site_pk=site_pk) if to_add else 0
    removed = 0
    for kw in to_remove:
        if delete_saved_keyword(site_id, kw, location or "", site_pk=site_pk):
            removed += 1

    return {"added": added, "removed": removed,
            "kept": len(incoming.keys() & existing.keys())}


def delete_saved_keyword(site_id: str, keyword: str, location: str,
                         site_pk: Optional[int] = None) -> bool:
    """Untrack one keyword for one project. Returns True if a row was deleted.

    `location` is IGNORED when `site_pk` is given: it identifies nothing (see the model comment)
    and a project whose tracking location was edited still holds rows under the old one, so
    matching on it made those keywords undeletable from the UI. With a project in hand the
    keyword name is the whole identity, and every row of it for that project goes.
    """
    try:
        with get_session() as session:
            _prepare(session)
            stmt = delete(SavedKeyword).where(
                *project_scope(site_id, site_pk),
                SavedKeyword.keyword == keyword,
            )
            if not site_pk:
                stmt = stmt.where(SavedKeyword.location == location)
            result = session.execute(stmt)
            session.commit()
            return (result.rowcount or 0) > 0
    except Exception as exc:
        logger.error(f"[saved_keyword_service] delete failed: {exc}", exc_info=True)
        return False


def clear_saved_keywords(site_id: str, site_pk: Optional[int] = None) -> int:
    """Untrack everything for ONE PROJECT. Returns the number of rows removed.

    Exists because the bulk-replace endpoint used to issue its own
    `delete(SavedKeyword).where(site_id == ...)`, which wiped every sibling project's list on
    the domain as a side effect of one project saving its own — silently, since the response
    only reported the rows it then wrote back.

    Refuses to run without a `site_pk`: a domain-wide wipe is never what a caller with a project
    in hand means, and there is no UI that wants one.
    """
    if not site_pk:
        logger.error("[saved_keyword_service] clear refused: no site_pk given for %r", site_id)
        return 0
    try:
        with get_session() as session:
            _prepare(session)
            result = session.execute(
                delete(SavedKeyword).where(*project_scope(site_id, site_pk))
            )
            session.commit()
            return result.rowcount or 0
    except Exception as exc:
        logger.error(f"[saved_keyword_service] clear failed: {exc}", exc_info=True)
        return 0

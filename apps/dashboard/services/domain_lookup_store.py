"""Read and write one Domain Overview block to `domain_lookups`.

The one boundary where a block's payload is JSON-encoded. Everything above this file works in
dicts; everything below it stores Text.

WHY THIS EXISTS. The page kept its results in a 24-hour Django cache and nothing else, so
re-opening a URL the next morning bought it again. On the AI-questions endpoint that is a
$0.10 fixed fee per request before a single row is counted — measured, not assumed — which
makes "the same request twice" the most expensive habit this page can have. A stored lookup is
served forever until someone presses Refresh, and the age is returned alongside so the UI can
say "as of 4 Aug" instead of implying it is live.

Never raises. Losing persistence costs money, not correctness: every caller falls back to the
cache and then the network, which is exactly how the page behaved before this table existed.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from pipeline.db.schema import DomainLookup
from pipeline.db.writer import upsert_domain_lookup
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def _key(target: str, location: str = ""):
    """(domain, path, location) for a typed target. The path is what makes a page's questions
    a different row from its domain's."""
    from urllib.parse import urlsplit

    from pipeline.connectors.dataforseo_llm_questions import domain_of

    raw = str(target or "").strip()
    probe = raw if "://" in raw else "https://" + raw
    path = (urlsplit(probe).path or "").rstrip("/")
    return domain_of(raw), path, (location or "")


def load_block(target: str, block: str, location: str = "") -> Optional[dict]:
    """The stored payload for this block, or None when it has never been looked up.

    Adds `storedAt` (ISO) and `ageDays` so the caller can show how old the answer is and offer
    a Refresh, rather than serving a month-old lookup as though it were fresh.
    """
    domain, path, loc = _key(target, location)
    if not domain:
        return None
    try:
        with get_session() as session:
            from pipeline.db.schema import ensure_domain_lookups
            ensure_domain_lookups(session)
            row = session.execute(
                select(DomainLookup).where(
                    DomainLookup.domain == domain,
                    DomainLookup.path == path,
                    DomainLookup.location == loc,
                    DomainLookup.block == block,
                )
            ).scalars().first()
            if row is None:
                return None
            payload = json.loads(row.payload or "{}")
            fetched = row.fetched_at
    except Exception:
        logger.warning("[domain_lookup_store] could not read %s/%s", domain, block, exc_info=True)
        return None

    if not isinstance(payload, dict):
        return None

    stored_at = None
    age_days = None
    if fetched is not None:
        # `fetched_at` is naive UTC on SQLite and tz-aware on Postgres; compare like with like
        # rather than letting a TypeError decide the age.
        moment = fetched if fetched.tzinfo else fetched.replace(tzinfo=timezone.utc)
        stored_at = moment.isoformat()
        age_days = max(0, (datetime.now(timezone.utc) - moment).days)

    return {**payload, "storedAt": stored_at, "ageDays": age_days, "fromStore": True}


def stored_blocks(target: str, prefix: str = "") -> list[str]:
    """Block names actually held for this target's DOMAIN, newest first.

    Lets a caller ask "what do we already own?" instead of guessing names. The questions block
    is keyed by platform set (`questions:chat_gpt`, `questions:chat_gpt+google`) plus a legacy
    bare `questions` from before that existed, so a fixed list of guesses would miss whichever
    combination the user actually bought — and offer to sell it to them again.

    Never raises: an unreadable list means "nothing owned", which is the safe answer.
    """
    domain, _path, _loc = _key(target)
    if not domain:
        return []
    try:
        with get_session() as session:
            from pipeline.db.schema import ensure_domain_lookups
            ensure_domain_lookups(session)
            rows = session.execute(
                select(DomainLookup.block)
                .where(DomainLookup.domain == domain)
                .order_by(DomainLookup.fetched_at.desc())
            ).scalars().all()
    except Exception:
        logger.warning("[domain_lookup_store] could not list blocks for %s", domain, exc_info=True)
        return []
    return [b for b in rows if not prefix or (b or "").startswith(prefix)]


def recent_lookups(limit: int = 10) -> list[dict]:
    """The last N targets looked up, newest first — one entry per (domain, path, market).

    Read from `domain_lookups` rather than kept as its own list, because that table already
    records every lookup and a second copy could only ever disagree with it.

    This replaces a browser-only history that stored each entry's FULL payload in
    localStorage: the quota filled, `doHistSave` shed entries to recover, and a URL analysed
    a minute earlier had quietly vanished from Recent after a refresh. Storing the payload
    once in the database and the list here fixes both halves.

    Never raises: an unreadable history is an empty chip row, not a broken page.
    """
    try:
        with get_session() as session:
            from pipeline.db.schema import ensure_domain_lookups
            ensure_domain_lookups(session)
            rows = session.execute(
                select(DomainLookup.domain, DomainLookup.path, DomainLookup.location,
                       DomainLookup.fetched_at)
                .where(DomainLookup.block == "keywords")     # the block every Analyze writes
                .order_by(DomainLookup.fetched_at.desc())
                .limit(max(1, int(limit)))
            ).all()
    except Exception:
        logger.warning("[domain_lookup_store] could not read recent lookups", exc_info=True)
        return []

    out = []
    for domain, path, location, fetched in rows:
        moment = None
        if fetched is not None:
            moment = (fetched if fetched.tzinfo else fetched.replace(tzinfo=timezone.utc)).isoformat()
        out.append({
            "target": (domain or "") + (path or ""),
            "domain": domain or "",
            "location": location or "",
            "storedAt": moment,
        })
    return out


def save_block(target: str, block: str, payload: dict, location: str = "",
               cost: float = 0.0) -> bool:
    """Persist one block. Returns True when it landed; never raises."""
    domain, path, loc = _key(target, location)
    if not domain or not isinstance(payload, dict):
        return False
    # The age markers are computed on read from `fetched_at`; storing them would freeze the
    # moment of the first write into every later answer.
    body = {k: v for k, v in payload.items()
            if k not in ("storedAt", "ageDays", "fromStore", "cached")}
    try:
        with get_session() as session:
            upsert_domain_lookup(session, [{
                "domain": domain, "path": path, "location": loc, "block": block,
                "payload": json.dumps(body, default=str), "cost": cost,
            }])
            session.commit()
        return True
    except Exception:
        logger.warning("[domain_lookup_store] could not store %s/%s", domain, block, exc_info=True)
        return False

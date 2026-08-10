"""apps/dashboard/services/domain_overview_service.py — the Domain Overview lookup.

Domain Overview is one of the four sanctioned live-API endpoints: it calls DataForSEO
because a human pressed Analyze, not because a page rendered. Everything that decides
*whether* that call actually happens lives here — the 24-hour cache, the monthly spend
gate, and (for the backlink sections) a second, separately-cached opt-in fetch.

It used to live in `apps/api/views.py`, which made Domain Overview the only feature in the
codebase where a view constructed a connector. The view is now a passthrough like
`KeywordResearchView`, and this module is the one place that knows what a lookup costs.

Two independent caches, deliberately keyed differently:

  domain_overview_<target>_<location>      keywords + metrics (DataForSEO Labs)
  domain_overview_backlinks_<domain>       backlinks + anchors + spam (Backlinks API)

The Backlinks API has **no location concept at all** — a backlink profile is a property of
the domain, not of a market. Keying the backlink cache by location would buy the same data
twice and imply a market breakdown that does not exist. The UI says so out loud next to the
market dropdown.
"""
import logging
from typing import Optional
from urllib.parse import urlparse

from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 24  # 24 hours, for both caches

# --- approved live-lookup cost limits ---------------------------------------------------
# Each of these is a row count DataForSEO meters and bills per returned row, so they ARE the
# price of a press. They are deliberately smaller than the sync-path limits: the sync buys a
# project's whole profile once a week, this buys a readable sample of an arbitrary domain the
# moment a user asks about it.
KEYWORDS_LIMIT = 50            # Labs ranked_keywords (unchanged — the existing default)
BACKLINKS_LIMIT = 100          # backlinks/backlinks/live for a looked-up target
ANCHORS_LIMIT = 60             # backlinks/anchors/live (unchanged — matches refresh_backlinks)


def keywords_cache_key(target: str, location: str) -> str:
    """Unchanged from the original in-view key so a cache written before this refactor is
    still read after it."""
    return f"domain_overview_{target}_{location}"


def backlinks_cache_key(target: str) -> str:
    """Domain-only — see the module docstring. A path is kept because DataForSEO can answer
    for an exact page, but the market never appears."""
    return f"domain_overview_backlinks_{backlink_target(target)}"


def backlink_target(target: str) -> str:
    """Normalise a typed target for the Backlinks API.

    Mirrors the keywords connector's page-vs-domain handling
    (`dataforseo_domain_overview.py`): a bare host is queried as a domain, a host with a real
    path is queried as that exact page. The path is NOT lowercased — URL paths are
    case-sensitive and DataForSEO matches them exactly.
    """
    raw = (target or "").strip()
    if not raw:
        return ""
    raw = raw.replace("sc-domain:", "")
    if not raw.lower().startswith(("http://", "https://")):
        parsed = urlparse("https://" + raw)
    else:
        parsed = urlparse(raw)

    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    path = parsed.path
    if path and path != "/":
        return domain + path
    return domain


# ---------------------------------------------------------------------------------------
# Keywords + metrics (the default Analyze press)
# ---------------------------------------------------------------------------------------
def fetch_keywords_block(target: str, location: str, site_id: str = "",
                         allow_fetch: bool = True) -> Optional[dict]:
    """The cached Labs `ranked_keywords/live` result for this target+market.

    `allow_fetch=False` returns the cache or None and NEVER spends — that is what the PDF
    report uses so generating a report can't silently buy a lookup.
    """
    key = keywords_cache_key(target, location)
    cached = cache.get(key)
    if cached is not None:
        return cached
    if not allow_fetch:
        return None

    # The spend gate. Refuse BEFORE constructing the connector, so a refusal cannot be
    # confused with a call that went out and failed.
    from pipeline.connectors.dataforseo_cost import ensure_budget
    refusal = ensure_budget()
    if refusal is not None:
        return refusal

    from pipeline.connectors.dataforseo_domain_overview import DataForSEODomainOverviewConnector
    connector = DataForSEODomainOverviewConnector()
    result = connector.get_domain_overview(target, location, limit=KEYWORDS_LIMIT, site_id=site_id)
    if result.get("status") == "ok":
        cache.set(key, result, CACHE_TTL)
    return result


def apply_tracked_flags(result: dict, site_id: str = "", site_pk: Optional[int] = None) -> dict:
    """Join the returned keywords against this project's SavedKeyword rows.

    Applied AFTER the cache read and never stored in it: the DataForSEO payload is identical
    for every project, but which of those keywords you already track is not. Baking it into
    the cached blob would show project A's tracking state to project B. Without a project the
    flag is simply absent — the UI then shows Track on every row, which is harmless because
    save_keywords upserts.
    """
    if not site_id or result.get("status") != "ok" or not result.get("keywords"):
        return result
    try:
        from pipeline.services.saved_keyword_service import list_saved_keywords
        tracked = {(k.get("keyword") or "").strip().lower()
                   for k in list_saved_keywords(site_id, site_pk=site_pk)}
        return {**result, "keywords": [
            {**row, "tracked": (row.get("keyword") or "").strip().lower() in tracked}
            for row in result["keywords"]
        ]}
    except Exception as exc:
        # A tracking-state lookup must never break the research result itself.
        logger.warning(f"domain-overview tracked-flag lookup failed: {exc}")
        return result


def run_domain_overview(target: str, location: str = "United States", site_id: str = "",
                        site_pk: Optional[int] = None) -> dict:
    """POST /api/domain-overview handler."""
    target = (target or "").strip()
    if not target:
        return {"status": "error", "error": "Target URL is required."}
    location = location or "United States"

    result = fetch_keywords_block(target, location, site_id=site_id) or {}
    result = apply_tracked_flags(result, site_id=site_id, site_pk=site_pk)
    return result

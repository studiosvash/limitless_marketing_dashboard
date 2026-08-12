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

# The store is what makes a domain cost money once rather than once a day; the cache in front
# of it only saves a DB round-trip inside a session.
from apps.dashboard.services.domain_lookup_store import (
    load_block, recent_lookups, save_block, stored_blocks,
)

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
# llm_mentions/search/live. MEASURED on a real account rather than assumed, because the shape
# of this endpoint's pricing decides the whole design:
#
#     limit 10, 1 platform -> $0.1100        limit 25, 1 platform -> $0.1250
#
# so the cost is a $0.10 FIXED FEE PER REQUEST plus ~$0.001 per returned row. Two consequences,
# both counter-intuitive:
#
#   * Shrinking the limit saves almost nothing — 10 rows cost $0.11, 100 rows cost $0.20. The
#     request is the expense, not the data. So we ask for a useful number and keep it.
#   * Halving the number of REQUESTS halves the bill. Hence one platform by default: ChatGPT,
#     which is where this product's users actually see themselves recommended. Google AI
#     Overviews doubles the price for a second opinion, so it is opt-in, not standard.
#
# For scale: the Analyze press costs $0.015 and the backlink block ~$0.03, so this tab is by
# far the most expensive thing on the page — which is why it has its own button and a 24h
# domain-wide cache.
QUESTIONS_LIMIT = 100
# The default when the caller names none. Each platform is a separate request carrying its own
# $0.10 base fee, so the user picks: ChatGPT, Google AI Overviews, or both. On a live account
# ChatGPT alone returned 62 questions and the pair returned 162, so "both" is worth its price
# often enough to be offered rather than decided here.
QUESTIONS_PLATFORMS = ("chat_gpt",)
QUESTIONS_PLATFORM_CHOICES = ("chat_gpt", "google")
# What the questions block was stored under before the platform selector existed. Renaming a
# storage key orphans every row already written with the old one — those lookups were paid
# for, so they are still read rather than silently re-bought.
LEGACY_QUESTIONS_BLOCK = "questions"


def keywords_cache_key(target: str, location: str) -> str:
    """Unchanged from the original in-view key so a cache written before this refactor is
    still read after it."""
    return f"domain_overview_{target}_{location}"


def backlinks_cache_key(target: str) -> str:
    """Domain-only — see the module docstring. A path is kept because DataForSEO can answer
    for an exact page, but the market never appears."""
    return f"domain_overview_backlinks_{backlink_target(target)}"


def questions_cache_key(target: str, platforms=None) -> str:
    """DOMAIN-ONLY, and that is the whole cost story for this tab.

    The request can only ever ask for a domain — DataForSEO rejects a path in its `domain`
    field — so one call already contains the answer for EVERY page on that domain, and the
    page filter is applied when reading. Keying this on the full URL instead would buy the
    same domain again for each page a user checked: ten blog posts on one competitor would be
    ten calls at $0.10 base apiece instead of one.

    No market in the key: the request is per location, but this tab does not offer a market
    picker, so every lookup uses the same one.
    """
    from pipeline.connectors.dataforseo_llm_questions import domain_of
    return f"domain_overview_questions_{domain_of(target)}_{'+'.join(platforms or QUESTIONS_PLATFORMS)}"


def _domain_only(target: str) -> str:
    """The bare domain — the key both the request and the store use for this block."""
    from pipeline.connectors.dataforseo_llm_questions import domain_of
    return domain_of(target)


def normalise_platforms(platforms) -> tuple:
    """The platforms to ask, from whatever the client sent. Unknown names are dropped.

    Order is fixed rather than the caller's, so the same pair always produces the same cache
    key however the checkboxes were ticked.
    """
    wanted = {str(p).strip().lower() for p in (platforms or [])}
    chosen = tuple(p for p in QUESTIONS_PLATFORM_CHOICES if p in wanted)
    return chosen or QUESTIONS_PLATFORMS


def fetch_questions_block(target: str, site_id: str = "", allow_fetch: bool = True,
                          refresh: bool = False, platforms=None) -> dict:
    """The AI Questions tab: which questions does this URL turn up in?

    ONE billed call per platform (chat_gpt, google) against llm_mentions/search/live, and only
    when the user presses "Find questions".

    A path in `target` costs nothing extra: DataForSEO rejects a path in its `domain` field
    (40501), so the request always carries the bare domain and the page filter is applied to
    the rows here. One press therefore answers for the exact page AND leaves the whole
    domain's answer in cache.

    Cached 24h like the other blocks, so `allow_fetch=False` — the PDF path — reads what the
    user already bought and can never spend on its own.
    """
    raw = str(target or "").strip()
    if not raw:
        return {"state": "setup", "rows": [], "total": 0,
                "note": "Enter a domain or URL first."}

    chosen = normalise_platforms(platforms)
    key = questions_cache_key(raw, chosen)
    # The stored block is keyed by platform set too: asking ChatGPT alone and asking both are
    # different answers, and serving one for the other would under-report without saying so.
    store_block = "questions:" + "+".join(chosen)
    if not refresh:
        cached = cache.get(key)
        if cached is not None:
            # Both the cache and the store hold the WHOLE domain; the page filter is applied on
            # the way out, so a second page on a domain already looked up costs nothing.
            return {**_narrow_to_page(cached, raw), "cached": True}
        stored = load_block(_domain_only(raw), store_block)
        if stored is None and chosen == QUESTIONS_PLATFORMS:
            # Blocks written before the platform selector existed are stored under the bare
            # name. Renaming the key orphaned them: a domain whose questions had been bought
            # showed "Not looked up yet" and offered to buy them again. Only the DEFAULT set
            # falls back, because that is what those rows were fetched with.
            stored = load_block(_domain_only(raw), LEGACY_QUESTIONS_BLOCK)
        if stored is not None:
            cache.set(key, stored, CACHE_TTL)
            return _narrow_to_page(stored, raw)
    if not allow_fetch:
        return {"state": "not_loaded", "rows": [], "total": 0,
                "note": "AI questions not loaded for this report — press “Find questions” on "
                        "the Domain Overview page first. Generating this report never buys them."}

    from pipeline.connectors.dataforseo_cost import ensure_budget
    refusal = ensure_budget()
    if refusal is not None:
        return {"state": "budget", "rows": [], "total": 0, "note": refusal["error"],
                "budgetExceeded": True}

    from pipeline.connectors.dataforseo_llm_questions import fetch_llm_questions
    # Fetched WITHOUT the page filter on purpose: the call is per domain either way, so
    # storing the whole domain makes every other page on it free for 24h. `page_url=""`
    # overrides the connector's own "a path means filter" default.
    result = fetch_llm_questions(raw, page_url="", platforms=chosen,
                                 limit=QUESTIONS_LIMIT, site_id=site_id)

    if result.get("status") != "ok":
        # setup / error — reported as-is, never as an empty "no questions found", which would
        # claim a measurement that was not taken.
        return {"state": result.get("status") or "error", "rows": [], "total": 0,
                "note": result.get("error") or "DataForSEO did not answer."}

    rows = result["rows"]
    block = {
        "state": "ok" if rows else "empty",
        "rows": rows,
        "total": len(rows),
        "domain": result.get("domain"),
        "platforms": result.get("platforms") or [],
        "partial": result.get("partial"),
        "cost": result.get("cost", 0.0),
    }
    cache.set(key, block, CACHE_TTL)
    # Keyed on the domain alone, like the request and the cache — one stored answer serves
    # every page on it, for good. An empty answer is deliberately NOT kept: see the same
    # reasoning in fetch_keywords_block. A domain DataForSEO has not indexed yet is a
    # temporary fact, and freezing it would make the next press pointless.
    if rows:
        save_block(_domain_only(raw), store_block, block, cost=block.get("cost", 0.0))
    return _narrow_to_page(block, raw)


def _narrow_to_page(block: dict, target: str) -> dict:
    """Apply the page filter to a whole-domain block, and count what survives.

    Cited and seen are counted separately because they are different findings: cited means the
    engine QUOTED the page in its answer, seen means it retrieved the page and quoted somebody
    else. A single "mentioned" number would hide the second, which is the one worth acting on.
    """
    from pipeline.connectors.dataforseo_llm_questions import url_matches
    from urllib.parse import urlsplit

    raw = str(target or "").strip()
    probe = raw if "://" in raw else "https://" + raw
    has_path = bool(urlsplit(probe).path.strip("/"))

    all_rows = block.get("rows") or []
    rows = [r for r in all_rows if url_matches(r.get("our_url", ""), raw)] if has_path else all_rows

    if not (block.get("state") in ("ok", "empty")):
        return block           # setup / budget / error blocks pass through untouched

    return {
        **block,
        "rows": rows,
        "total": len(rows),
        "citedCount": sum(1 for r in rows if r.get("cited")),
        "seenCount": sum(1 for r in rows if not r.get("cited")),
        "state": "ok" if rows else "empty",
        "page": raw if has_path else None,
        # Stated so a page with no questions does not read as "this domain has none".
        "domainTotal": len(all_rows),
        "note": "" if rows else (
            "This exact page is not referenced in any AI answer DataForSEO has on record — "
            f"though {len(all_rows)} question(s) reference the domain."
            if has_path and all_rows else
            "DataForSEO has no AI answers on record that reference this URL."),
    }


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
                         allow_fetch: bool = True, refresh: bool = False) -> Optional[dict]:
    """The Labs `ranked_keywords/live` result for this target+market.

    READ ORDER: stored row -> 24h cache -> network. The store is what makes a domain cost
    money ONCE rather than once a day; the cache still sits in front of it to save the DB
    round-trip inside a session. `refresh=True` is the user pressing Refresh and is the only
    thing that skips both.

    `allow_fetch=False` returns whatever is already held and NEVER spends — that is what the
    PDF report uses, so generating a report of a domain looked up last month is complete and
    free.
    """
    key = keywords_cache_key(target, location)
    if not refresh:
        cached = cache.get(key)
        if cached is not None:
            return cached
        stored = load_block(target, "keywords", location=location)
        if stored is not None:
            cache.set(key, stored, CACHE_TTL)
            return stored
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
        # Stored as well as cached — the cache expires in a day, the answer does not — but ONLY
        # when there is an answer. A stored "we found nothing" is the one result that must
        # never be sticky: it costs nothing to re-derive and it is the answer most likely to be
        # wrong. It cost a real bug once already — a page target missing its trailing slash
        # returned nothing, that nothing was persisted, and the fix for the slash could not
        # reach the network past it, so the page kept reporting "0 keywords" after being fixed.
        if result.get("keywords"):
            save_block(target, "keywords", result, location=location,
                       cost=float(result.get("cost") or 0.0))
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


# ---------------------------------------------------------------------------------------
# Backlinks + anchors + spam score (opt-in: a deliberate SECOND button press)
# ---------------------------------------------------------------------------------------

def spam_band(score) -> str:
    """green <= 30 · amber 31-60 · red > 60 · unknown when DataForSEO returned no score.

    "unknown" is its own band, not green. A backlink DataForSEO has not scored has not been
    found clean; colouring it green would assert a measurement nobody took.
    """
    if score is None:
        return "unknown"
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "unknown"
    if value <= 30:
        return "low"
    if value <= 60:
        return "medium"
    return "high"


def _empty_backlinks_block(state: str, note: str, **extra) -> dict:
    block = {
        "state": state,
        "note": note,
        "cached": False,
        "target": "",
        "links": [],
        "anchors": [],
        "spam": {"targetScore": None, "highSpamLinks": 0, "scoredLinks": 0, "unknownLinks": 0},
        "summary": {},
        "limit": BACKLINKS_LIMIT,
        "anchorsLimit": ANCHORS_LIMIT,
        # The Backlinks API has no location parameter. Stated in the payload so the UI can
        # say it beside a market dropdown that governs the keyword sections only.
        "locationApplies": False,
    }
    block.update(extra)
    return block


def _shape_links(records: list) -> list:
    rows = []
    for r in records:
        score = r.get("spam_score")
        rows.append({
            "urlFrom": r.get("url_from") or "",
            "referringDomain": r.get("referring_domain") or "",
            "targetUrl": r.get("target_url") or "",
            "anchor": r.get("anchor") or "",
            "dofollow": bool(r.get("dofollow")),
            "domainRank": r.get("domain_rank"),
            "pageRank": r.get("page_from_rank"),
            # Kept as returned -- None means "not scored", which is a different fact from 0.
            "spamScore": score,
            "spamBand": spam_band(score),
            "firstSeen": r.get("first_seen").isoformat() if hasattr(r.get("first_seen"), "isoformat") else (r.get("first_seen") or ""),
            "status": r.get("status") or "",
        })
    return rows


def fetch_backlinks_block(target: str, site_id: str = "", allow_fetch: bool = True,
                          refresh: bool = False) -> dict:
    """The Domain Overview backlink sections: link sample, anchor breakdown, spam score.

    THREE billed DataForSEO calls, and only when the user presses "Load backlinks":
      backlinks/summary/live      -- profile totals + the TARGET-LEVEL spam score
      backlinks/backlinks/live    -- BACKLINKS_LIMIT (100) rows, highest-authority first
      backlinks/anchors/live      -- ANCHORS_LIMIT (60) anchor rows

    The spam data costs nothing extra: `backlink_spam_score` rides along on every row of the
    backlinks call and `backlinks_spam_score` on the summary. Both were already being paid
    for on the Backlinks page and simply never read.

    Cached 24h under a DOMAIN-ONLY key. `allow_fetch=False` returns the cache or a
    "not_loaded" block and can never spend -- that is what the PDF report uses.
    """
    normalised = backlink_target(target)
    if not normalised:
        return _empty_backlinks_block("setup", "Enter a domain or URL first.")

    key = backlinks_cache_key(target)
    if not refresh:
        cached = cache.get(key)
        if cached is not None:
            return {**cached, "cached": True}
        stored = load_block(backlink_target(target), "backlinks")
        if stored is not None:
            cache.set(key, stored, CACHE_TTL)
            return stored
    if not allow_fetch:
        return _empty_backlinks_block(
            "not_loaded",
            "Backlinks not loaded for this report — press “Load backlinks” on the Domain "
            "Overview page first. Generating this report never buys them.",
            target=normalised)

    from pipeline.connectors.dataforseo_cost import ensure_budget
    refusal = ensure_budget()
    if refusal is not None:
        return _empty_backlinks_block("budget", refusal["error"], target=normalised,
                                      budgetExceeded=True)

    # The backlinks connector RAISES on missing credentials in its constructor (unlike the
    # domain-overview connector, which returns an error dict). Unwrapped, that is a 500 on a
    # deployment that simply has not configured DataForSEO yet.
    try:
        from pipeline.connectors.dataforseo_backlinks import DataForSEOBacklinksConnector
        connector = DataForSEOBacklinksConnector()
    except Exception as exc:
        logger.warning(f"domain-overview backlinks unavailable: {exc}")
        return _empty_backlinks_block(
            "setup",
            "DataForSEO credentials are not configured — add them in Settings to load "
            "backlinks.", target=normalised)

    from pipeline.services.backlinks_service import fetch_anchors, summary_for

    summary, links, anchors = {}, [], []
    try:
        summary = summary_for(normalised, site_id=site_id)
    except Exception as exc:
        logger.warning(f"domain-overview backlinks summary failed: {exc}")
    try:
        # No _write_records: there is no project to write to. An arbitrary looked-up domain
        # is not this workspace's site, and filing its backlinks into `backlinks` would put
        # a competitor's profile under a site_id every page reads.
        links = _shape_links(connector.fetch(site_id=normalised, limit=BACKLINKS_LIMIT,
                                             dofollow_only=False) or [])
    except Exception as exc:
        logger.warning(f"domain-overview backlinks fetch failed: {exc}")
        return _empty_backlinks_block(
            "error", f"DataForSEO could not return backlinks for this target: {exc}",
            target=normalised)
    try:
        anchors = fetch_anchors(normalised, limit=ANCHORS_LIMIT, site_id=site_id)
    except Exception as exc:
        logger.warning(f"domain-overview anchors failed: {exc}")

    scored = [r for r in links if r["spamScore"] is not None]
    block = _empty_backlinks_block(
        "ok" if links else "empty",
        "" if links else "DataForSEO has no indexed backlinks for this target.",
        target=normalised,
    )
    block.update({
        "links": links,
        "anchors": anchors,
        "summary": summary,
        "spam": {
            # Profile-wide, straight from summary/live. None when the call failed --
            # not 0, which would read as "measured, and clean".
            "targetScore": summary.get("spamScore"),
            # Counted over the sampled links only; the UI says so next to the number.
            "highSpamLinks": sum(1 for r in scored if r["spamBand"] == "high"),
            "mediumSpamLinks": sum(1 for r in scored if r["spamBand"] == "medium"),
            "scoredLinks": len(scored),
            "unknownLinks": len(links) - len(scored),
        },
    })
    if links:
        cache.set(key, block, CACHE_TTL)
        save_block(backlink_target(target), "backlinks", block,
                   cost=float(block.get("cost") or 0.0))
    return block


def run_domain_overview(target: str, location: str = "United States", site_id: str = "",
                        site_pk: Optional[int] = None,
                        include: Optional[list] = None, refresh: bool = False,
                        platforms: Optional[list] = None) -> dict:
    """POST /api/domain-overview handler.

    `include` is the opt-in list for sections that cost extra. The default Analyze press
    buys exactly what it always bought -- one Labs call -- so nobody's price changed when
    the backlink sections were added; `{"include": ["backlinks"]}` is a second, deliberate
    press behind its own button.
    """
    target = (target or "").strip()
    if not target:
        return {"status": "error", "error": "Target URL is required."}
    location = location or "United States"
    wanted = {str(i).strip().lower() for i in (include or [])}

    result = fetch_keywords_block(target, location, site_id=site_id, refresh=refresh) or {}
    result = apply_tracked_flags(result, site_id=site_id, site_pk=site_pk)

    if "backlinks" in wanted:
        result = {**result, "backlinks": fetch_backlinks_block(target, site_id=site_id,
                                                               refresh=refresh)}
    elif not refresh:
        # Not asked for, but already OWNED — hand it back free. Without this a hard refresh
        # showed "Load backlinks" for a target whose backlinks were sitting in the store, and
        # the only way to see them again was to buy them again. `allow_fetch=False` guarantees
        # this branch can never reach the network.
        owned = fetch_backlinks_block(target, site_id=site_id, allow_fetch=False)
        if owned.get("state") == "ok":
            result = {**result, "backlinks": owned}
    # Same contract as backlinks: its own button, its own cache, never bought by the default
    # Analyze press.
    if "questions" in wanted:
        result = {**result, "questions": fetch_questions_block(target, site_id=site_id,
                                                               refresh=refresh,
                                                               platforms=platforms)}
    elif not refresh:
        # Same rule, but the platform set is asked of the STORE rather than guessed: the
        # questions block is keyed by which engines were bought, so a fixed list of guesses
        # misses whichever combination the user actually paid for — and then offers to sell it
        # to them again. Newest stored block wins.
        for block in stored_blocks(target, prefix="questions"):
            suffix = block.split(":", 1)[1] if ":" in block else ""
            choice = tuple(suffix.split("+")) if suffix else QUESTIONS_PLATFORMS
            owned = fetch_questions_block(target, site_id=site_id, allow_fetch=False,
                                          platforms=choice)
            if owned.get("state") in ("ok", "empty") and owned.get("domainTotal") is not None:
                result = {**result, "questions": owned}
                break

    # The Recent chips, from the database rather than the browser. localStorage held each
    # entry's whole payload, so the quota filled and entries were shed — a URL analysed a
    # minute earlier could be missing after a refresh.
    result = {**result, "recent": recent_lookups()}
    return result

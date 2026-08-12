"""AI Visibility block — assembled from stored DataForSEO LLM Mentions snapshots.

Reads `llm_mention_metrics` and `llm_cited_pages`, never an external API: the connector
`pipeline/connectors/dataforseo_llm_mentions.py` is the only thing that calls DataForSEO.

Everything here comes from a real stored row. Where a number cannot honestly be produced --
no snapshot yet, no competitors configured, no prior week to compare against -- the caller
gets an explicit state or `None`, never a zero dressed up as a measurement.
"""
import json
import logging

from sqlalchemy import select

from pipeline.db.schema import LLMCitedPage, LLMMentionMetric
from pipeline.db.writer import ensure_tables
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import canonical_domain, normalize_domain, resolve_site_ids

logger = logging.getLogger(__name__)

# The only two platforms DataForSEO's LLM Mentions API covers. Claude, Gemini and Perplexity
# are NOT available from it at any price -- they appear only on the Prompts tab, which is fed
# by this deployment's own LLM API keys. Keep this list separate from ai_service's
# MENTION_PLATFORMS/llmPlatforms for exactly that reason.
MENTION_PLATFORMS = [
    {"id": "google", "name": "AI Overviews", "color": "#4285f4"},
    {"id": "chat_gpt", "name": "ChatGPT", "color": "#10a37f"},
]


def _empty_block() -> dict:
    """A fresh block every call — never a shared module-level dict.

    A shallow copy would hand every caller the SAME nested `sov`/`rows`/`topPages`/`topDomains`
    objects, so a single mutation anywhere would poison every subsequent setup-state response
    in the process.
    """
    return {
        "sov": {"you": 0, "delta": None, "rows": []},
        "mentions": 0,
        "impressions": 0,
        "cited_pages": 0,
        "topPages": [],
        "coCitedPages": [],
        "topDomains": [],
        "mentionPlatforms": [dict(p) for p in MENTION_PLATFORMS],
        "state": "setup",
    }


def _bare_host(domain: str) -> str:
    """`www.` stripped, for comparing two hosts. Mirrors the connector's helper of the name."""
    d = (domain or "").lower()
    return d[4:] if d.startswith("www.") else d


def page_is_ours(url: str, own_domain: str) -> bool:
    """Is this cited URL on the project's own site?

    Host-wise with a dot boundary, so `blog.<us>.com` is ours and `notus.com` never is —
    substring containment answers a different question and has bitten this codebase before
    (skills.md §9, `"linkedin" in "lnkd.in"`). `www.` is stripped on both sides because the
    two hosts are one site here (§3).
    """
    own = _bare_host(own_domain)
    host = _bare_host(canonical_domain(url))
    if not own or not host:
        return False
    return host == own or host.endswith("." + own)


def query_mention_metrics_raw(site_id: str, weeks: int = 2) -> list[dict]:
    """The most recent `weeks` weekly snapshots, newest first. [] on any failure."""
    site_ids = resolve_site_ids(site_id)
    if not site_ids:
        return []
    try:
        with get_session() as session:
            ensure_tables(session, LLMMentionMetric)
            recent = session.execute(
                select(LLMMentionMetric.week_start)
                .where(LLMMentionMetric.site_id.in_(site_ids))
                .distinct().order_by(LLMMentionMetric.week_start.desc()).limit(weeks)
            ).scalars().all()
            if not recent:
                return []
            rows = session.execute(
                select(LLMMentionMetric)
                .where(LLMMentionMetric.site_id.in_(site_ids),
                       LLMMentionMetric.week_start.in_(recent))
            ).scalars().all()
            return [{
                "week_start": r.week_start, "subject_domain": r.subject_domain,
                "subject_type": r.subject_type, "platform": r.platform,
                "mentions": r.mentions or 0, "ai_search_volume": r.ai_search_volume or 0,
            } for r in rows]
    except Exception as exc:
        logger.error(f"query_mention_metrics_raw error: {exc}", exc_info=True)
        return []


def query_cited_pages_raw(site_id: str, week_start) -> list[dict]:
    """Stored cited URLs for one week, most-mentioned first. [] on any failure.

    Both kinds of row: the project's own pages and the co-cited pages from other domains that
    arrived in the same paid response. `build_visibility_block` is what separates them —
    callers wanting one or the other should read `topPages` / `coCitedPages` from there rather
    than re-deriving ownership here.
    """
    site_ids = resolve_site_ids(site_id)
    if not site_ids:
        return []
    try:
        with get_session() as session:
            ensure_tables(session, LLMCitedPage)
            rows = session.execute(
                select(LLMCitedPage)
                .where(LLMCitedPage.site_id.in_(site_ids),
                       LLMCitedPage.week_start == week_start)
                .order_by(LLMCitedPage.mentions.desc())
            ).scalars().all()
    except Exception as exc:
        logger.error(f"query_cited_pages_raw error: {exc}", exc_info=True)
        return []

    out = []
    for r in rows:
        try:
            platforms = json.loads(r.platforms) if r.platforms else []
        except (ValueError, TypeError):
            platforms = []
        out.append({
            "url": r.url, "mentions": r.mentions or 0,
            "impressions": r.ai_search_volume or 0,
            "platforms": platforms if isinstance(platforms, list) else [],
            # The host, so the co-cited list can say WHOSE page it is without the SPA parsing
            # URLs. Computed here because `canonical_domain` is the one canonicaliser (§3).
            "domain": canonical_domain(r.url),
        })
    return out


DISCOVERED_PLATFORM = "all"


def _totals_by_domain(rows: list[dict], week) -> dict:
    """{domain: {"type", "mentions", "volume"}} for one week.

    Two passes on purpose. The type is decided first, because `you`/`competitor` must win over
    a stray `discovered` row for the same domain -- otherwise a project could be listed as its
    own rival. Only then are rows summed, and only the rows belonging to that type: a tracked
    subject's total is the sum of its real platform rows, a discovered domain's total is its
    single `all` sentinel row. Summing both would inflate the share-of-voice numerator.
    """
    week_rows = [r for r in rows if r["week_start"] == week]

    types: dict = {}
    for r in week_rows:
        domain = r["subject_domain"]
        if r["subject_type"] in ("you", "competitor"):
            types[domain] = r["subject_type"]
        else:
            types.setdefault(domain, "discovered")

    # Seeded with every domain at zero so a competitor with no mentions still appears --
    # absence is information on this page, not a reason to drop the row.
    agg = {d: {"type": t, "mentions": 0, "volume": 0} for d, t in types.items()}
    for r in week_rows:
        domain = r["subject_domain"]
        is_sentinel = r["platform"] == DISCOVERED_PLATFORM
        if (types[domain] == "discovered") != is_sentinel:
            continue
        agg[domain]["mentions"] += r["mentions"]
        agg[domain]["volume"] += r["ai_search_volume"]
    return agg


def _sov_percentages(agg: dict) -> dict:
    """{domain: whole-number share} across tracked subjects only, forced to total 100.

    The denominator is the sum of tracked subjects, so the rows add up to 100 the way the
    page presents them. The API's own deduplicated `total` is deliberately not used -- it
    counts a response once even when it mentions two subjects, so shares built from it would
    not sum to 100.
    """
    tracked = {d: v for d, v in agg.items() if v["type"] in ("you", "competitor")}
    total = sum(v["mentions"] for v in tracked.values())
    if not total:
        return {d: 0 for d in tracked}

    raw = {d: v["mentions"] / total * 100 for d, v in tracked.items()}
    out = {d: int(p) for d, p in raw.items()}
    # Hand the rounding remainder to the largest fractional parts so the column totals 100
    # instead of 99 -- a share list that does not add up reads as a bug.
    remainder = 100 - sum(out.values())
    for d, _ in sorted(raw.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True):
        if remainder <= 0:
            break
        out[d] += 1
        remainder -= 1
    return out


def build_visibility_block(site_id: str) -> dict:
    """`sov`, KPI values, `topPages`, `topDomains` and `mentionPlatforms` for the AI page."""
    rows = query_mention_metrics_raw(site_id, weeks=2)
    if not rows:
        return _empty_block()

    weeks = sorted({r["week_start"] for r in rows}, reverse=True)
    this_week = weeks[0]
    agg = _totals_by_domain(rows, this_week)

    shares = _sov_percentages(agg)
    sov_rows = [{
        "domain": d,
        "sov": shares[d],
        "mentions": agg[d]["mentions"],
        "isYou": agg[d]["type"] == "you",
    } for d in shares]
    sov_rows.sort(key=lambda r: (-r["mentions"], r["domain"]))

    you_row = next((r for r in sov_rows if r["isYou"]), None)
    you_share = you_row["sov"] if you_row else 0

    # A delta needs a real prior measurement. Without one it stays None and the SPA shows
    # "no comparison yet" -- printing +0 would claim last week was measured when it was not.
    delta = None
    if len(weeks) > 1 and you_row is not None:
        prev_agg = _totals_by_domain(rows, weeks[1])
        prev_you_domain = next((d for d, v in prev_agg.items() if v["type"] == "you"), None)
        # Compare like with like. A different subject last week is not a change in OUR share,
        # so the honest answer is "no comparison" rather than a misleading number.
        if prev_you_domain == you_row["domain"]:
            prev_shares = _sov_percentages(prev_agg)
            delta = you_share - prev_shares[prev_you_domain]

    competitors = [d for d, v in agg.items() if v["type"] == "competitor"]
    state = "ok" if competitors else "no_competitors"

    top_domains_total = sum(v["mentions"] for v in agg.values()) or 1
    top_domains = sorted(agg.items(), key=lambda kv: -kv[1]["mentions"])[:10]
    top_domains_out = [{
        "domain": d,
        "share": round(v["mentions"] / top_domains_total * 100, 1),
        "mentions": v["mentions"],
        "isYou": v["type"] == "you",
        "isComp": v["type"] == "competitor",
    } for d, v in top_domains]

    # Ours vs. co-cited, decided here rather than stored (see LLMCitedPage's docstring).
    # `normalize_domain` is the "which site is this?" question — the right one, because it is
    # what `sites.site_url` was registered as. The measured `you` subject is the fallback for a
    # site_id that normalises to nothing.
    own_domain = normalize_domain(site_id) or (you_row["domain"] if you_row else "")
    all_pages = query_cited_pages_raw(site_id, this_week)
    pages = [p for p in all_pages if page_is_ours(p["url"], own_domain)]
    # Pages on OTHER domains that AI cited in the same answers. They cost nothing extra (they
    # arrive in the same top_pages response) and they answer "who else is being cited on the
    # questions that cite us?" — the "Cited Pages" tab shows them beside ours.
    co_cited = [p for p in all_pages if not page_is_ours(p["url"], own_domain)]

    return {
        "sov": {"you": you_share, "delta": delta, "rows": sov_rows},
        "mentions": agg.get(you_row["domain"], {}).get("mentions", 0) if you_row else 0,
        "impressions": agg.get(you_row["domain"], {}).get("volume", 0) if you_row else 0,
        # Deliberately OURS only: the KPI is labelled "of your URLs used as sources".
        "cited_pages": len(pages),
        "topPages": pages,
        "coCitedPages": co_cited,
        "topDomains": top_domains_out,
        "mentionPlatforms": [dict(p) for p in MENTION_PLATFORMS],
        "state": state,
    }

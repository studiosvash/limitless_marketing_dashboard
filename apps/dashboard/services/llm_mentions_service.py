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
from pipeline.utils.site_ids import resolve_site_ids

logger = logging.getLogger(__name__)

# The only two platforms DataForSEO's LLM Mentions API covers. Claude, Gemini and Perplexity
# are NOT available from it at any price -- they appear only on the Prompts tab, which is fed
# by this deployment's own LLM API keys. Keep this list separate from ai_service's
# MENTION_PLATFORMS/llmPlatforms for exactly that reason.
MENTION_PLATFORMS = [
    {"id": "google", "name": "AI Overviews", "color": "#4285f4"},
    {"id": "chat_gpt", "name": "ChatGPT", "color": "#10a37f"},
]

_EMPTY = {
    "sov": {"you": 0, "delta": None, "rows": []},
    "mentions": 0,
    "impressions": 0,
    "cited_pages": 0,
    "topPages": [],
    "topDomains": [],
    "mentionPlatforms": MENTION_PLATFORMS,
    "state": "setup",
}


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
    """Stored cited URLs for one week, most-mentioned first. [] on any failure."""
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
        })
    return out


def _totals_by_domain(rows: list[dict], week) -> dict:
    """{domain: {"type", "mentions", "volume"}} for one week, platforms summed."""
    agg: dict = {}
    for r in rows:
        if r["week_start"] != week:
            continue
        d = agg.setdefault(r["subject_domain"],
                           {"type": r["subject_type"], "mentions": 0, "volume": 0})
        d["mentions"] += r["mentions"]
        d["volume"] += r["ai_search_volume"]
        # 'you' and 'competitor' must win over a stray 'discovered' row for the same domain.
        if r["subject_type"] in ("you", "competitor"):
            d["type"] = r["subject_type"]
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
        return dict(_EMPTY)

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
    if len(weeks) > 1:
        prev_agg = _totals_by_domain(rows, weeks[1])
        prev_shares = _sov_percentages(prev_agg)
        prev_you_domain = next((d for d, v in prev_agg.items() if v["type"] == "you"), None)
        if prev_you_domain is not None:
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

    pages = query_cited_pages_raw(site_id, this_week)

    return {
        "sov": {"you": you_share, "delta": delta, "rows": sov_rows},
        "mentions": agg.get(you_row["domain"], {}).get("mentions", 0) if you_row else 0,
        "impressions": agg.get(you_row["domain"], {}).get("volume", 0) if you_row else 0,
        "cited_pages": len(pages),
        "topPages": pages,
        "topDomains": top_domains_out,
        "mentionPlatforms": MENTION_PLATFORMS,
        "state": state,
    }

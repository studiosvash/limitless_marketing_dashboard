"""AI Optimization page (Phase D) — real reshape of AIKeywordData plus first-party
targets/lists/prompts persistence (Django ORM), plus honest empty/zero placeholders for
everything requiring the LLM Mentions/Responses/scraper infrastructure that doesn't exist
anywhere in this codebase. See docs/superpowers/specs/2026-07-13-phaseD-ai-optimization-design.md."""
import json
import logging

from sqlalchemy import func, select

from apps.dashboard.models import AITarget, AIPromptList, AIPrompt
from pipeline.db.schema import AIKeywordData
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

# Final-review finding: the SPA reads pl2.name (not .label) off both mentionPlatforms and
# llmPlatforms, and treats llmPlatforms as the SAME {id,name,color} object shape as
# mentionPlatforms (pl2.id/.name/.color all dereferenced against it) -- not a bare id string.
MENTION_PLATFORMS = [
    {"id": "chatgpt", "name": "ChatGPT", "color": "#10a37f"},
    {"id": "claude", "name": "Claude", "color": "#d97757"},
    {"id": "gemini", "name": "Gemini", "color": "#4285f4"},
    {"id": "perplexity", "name": "Perplexity", "color": "#20808d"},
]


def query_ai_keywords_raw(site_id: str) -> list[dict]:
    """Real reshape of AIKeywordData for the latest captured snapshot date -- same
    "latest date per site" query pattern as the old MVP's apps/dashboard/views.py
    _get_ai_keywords (reused deliberately, not reinvented: AIKeywordData rows are captured
    as one full snapshot per sync date, so "latest date" is the correct notion of current
    state, not a per-keyword max-date dedup). mentions/gap are ALWAYS 0/False -- no LLM
    Mentions data exists to derive them from; never fabricate a signal."""
    try:
        with get_session() as session:
            latest = session.execute(
                select(func.max(AIKeywordData.date)).where(AIKeywordData.site_id == site_id)
            ).scalar()
            if latest is None:
                return []
            rows = session.execute(
                select(AIKeywordData)
                .where(AIKeywordData.site_id == site_id, AIKeywordData.date == latest)
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_ai_keywords_raw error: {e}", exc_info=True)
        return []

    out = []
    for r in rows:
        ai_vol = r.ai_search_volume or 0
        g_vol = r.search_volume or 0
        try:
            monthly = json.loads(r.trend) if r.trend else []
        except (ValueError, TypeError):
            monthly = []
        # trend is stored as a list of {year, month, ai_search_volume} objects (see
        # pipeline/connectors/dataforseo_ai_keywords.py::_normalize), not a flat list of
        # numbers -- flatten + sort chronologically before handing it to the SPA's sparkline,
        # which expects trend[11] to be the most recent month.
        ordered = sorted(monthly, key=lambda m: (m.get("year") or 0, m.get("month") or 0))
        trend = [int(m["ai_search_volume"]) if m.get("ai_search_volume") is not None else 0 for m in ordered]
        if len(trend) < 12:
            # Pad at the START with zeros so the most-recent real month stays last (index 11).
            trend = [0] * (12 - len(trend)) + trend
        out.append({
            "kw": r.keyword,
            "aiVolume": ai_vol,
            "gVolume": g_vol,
            # None (not a fabricated 0%) when there's no Google-volume denominator to compare
            # against -- the connector doesn't fetch search_volume yet, so g_vol==0 means "no
            # signal," not "0% AI share." A flat 0% would misleadingly read as "no AI interest."
            "ratio": round(ai_vol / g_vol * 100) if g_vol else None,
            "intent": r.intent or "",
            "trend": trend[-12:],
            "mentions": 0,   # honest -- no LLM Mentions data exists
            "gap": False,    # honest -- no LLM Mentions data exists
        })
    return out


def _target_dict(t: "AITarget | None") -> dict:
    if t is None:
        return {"brand": "", "aliases": [], "competitors": []}
    return {"brand": t.brand, "aliases": t.aliases, "competitors": t.competitors}


def build_ai_response(site_id: str) -> dict:
    """API-shaped AI Optimization response. Real: targets/lists/prompts/setupDone (first-party
    ORM data), aiKeywords (real AIKeywordData reshape). Honest empty/zero: everything requiring
    LLM Mentions/Responses/scraper infra that doesn't exist -- sov/trend/topPages/topDomains/
    prompts[].results/suggestions/history/budget/costs/next_run."""
    target = AITarget.objects.filter(site_url=site_id).first()
    lists = list(AIPromptList.objects.filter(site_url=site_id).values("id", "name"))
    prompts_qs = AIPrompt.objects.filter(site_url=site_id).select_related(None)
    prompts = [
        {
            "id": p.id,
            "text": p.text,
            "listId": p.list_id,
            # The SPA reads pr.cfg.models/.cadence/.country/.city (a nested object), not a
            # flat pr.models -- without this, pr.cfg.models.length crashes unconditionally
            # once any prompt exists (found tracing the SPA's render code independently,
            # not caught by any test since 0 real prompts existed when Tasks 1-3 were
            # reviewed). "weekly" is a real system-wide constant (the only cadence this
            # feature is designed for -- see the wizard's own "weekly schedule" copy), not
            # fabricated per-prompt data; country/city/webSearch are honestly empty/false
            # since no per-prompt geo-targeting or web-search toggle is persisted yet.
            "cfg": {
                "models": p.tracked_models,
                "cadence": "weekly",
                "country": "",
                "city": "",
                "webSearch": False,
            },
            "results": {},  # keyed by platform id once real LLM Responses data exists
            "lastRun": None,
        }
        for p in prompts_qs
    ]

    return {
        "setupDone": bool(target and target.setup_done),
        "targets": _target_dict(target),
        "budget": {"cap": 0, "spent": 0, "weekly_est": 0},
        "costs": {"model": None, "inspect": None},
        "next_run": None,
        "mentionPlatforms": MENTION_PLATFORMS,
        # Same {id,name,color} object shape as mentionPlatforms -- the SPA uses llmPlatforms
        # (aliased "llm") for the Prompts table's model-column headers/dots/coverage counts
        # via pl2.name/.id/.color, not a bare id string.
        "llmPlatforms": MENTION_PLATFORMS,
        "sov": {"you": 0, "delta": 0, "rows": []},
        "kpis": {"mentions": 0, "impressions": 0, "cited_pages": 0, "prompt_coverage": {"cited": 0, "total": len(prompts)}},
        "trend": [],
        "topPages": [],
        "topDomains": [],
        "lists": lists,
        "prompts": prompts,
        "suggestions": [],
        "aiKeywords": query_ai_keywords_raw(site_id),
        "history": [],
    }

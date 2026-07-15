"""Keyword Explorer + Prompt Explorer JSON services (new SPA).

Keyword Explorer restores the old MVP's `keyword_explorer_search` feature (which the new
dashboard called via POST /api/research but which was never built -- it 404'd). It wraps the
same real connector the old MVP used (DataForSEOKeywordsConnector.lookup_keywords), so it works
exactly as well as the old version did: it returns real keyword metrics when DataForSEO
credentials are live, and an honest empty result (never fabricated rows) when they aren't.

This is an on-demand user action (like Refresh), so the live API call here is consistent with
the database-first contract -- it's not a page render.
"""
import logging

from sqlalchemy import func, select

from pipeline.db.schema import KeywordRanking
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

# The old MVP's Keyword Explorer restricted to a known location set; keep the same guardrail.
EXPLORER_LOCATIONS = {
    "United States", "United Kingdom", "Canada", "Australia", "India",
    "Germany", "France", "Spain", "Italy", "Netherlands",
}


def _tracked_keywords(site_id: str) -> set[str]:
    """Lowercased set of keywords this site already tracks (real GSC KeywordRanking rows), so
    Explorer rows can honestly show a 'Tracked' badge."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(func.distinct(KeywordRanking.keyword)).where(KeywordRanking.site_id == site_id)
            ).scalars().all()
        return {(k or "").lower() for k in rows}
    except Exception as e:
        logger.error(f"_tracked_keywords error: {e}", exc_info=True)
        return set()


def _to_spa_row(old_row: dict, tracked: set[str]) -> dict:
    """Map the old connector's row shape to exactly what the SPA's research table reads
    (kw/match/volume/kd/cpc/intent/tracked/monthly/serpFeatures)."""
    kw = old_row.get("keyword") or ""
    serp = old_row.get("serp_features") or ""
    return {
        "kw": kw,
        # The old connector does an exact lookup of the entered keywords -- no algorithmic
        # expansion -- so every row is honestly 'exact'. The SPA's phrase/broad/questions/
        # related tabs stay empty until the DataForSEO Labs expansion connectors are built
        # (explicitly future work, same status as the other blocked DataForSEO surfaces).
        "match": "exact",
        "volume": old_row.get("search_volume") or 0,
        "kd": old_row.get("keyword_difficulty") or 0,
        "cpc": old_row.get("cpc") or 0,
        "intent": old_row.get("intent") or "Informational",
        "serpFeatures": [s.strip() for s in serp.split(",") if s.strip()],
        "monthly": [],  # per-month trend not returned by this lookup; SPA sparkline handles []
        "tracked": kw.lower() in tracked,
    }


def run_keyword_research(site_id: str, keywords: list[str], location: str) -> dict:
    """POST /api/research handler. Returns {rows, cost, location} -- honest empty rows (never
    fabricated) when DataForSEO is unavailable, so the SPA shows an empty result rather than a
    500/404."""
    location = (location or "United States").strip() or "United States"
    if location not in EXPLORER_LOCATIONS:
        location = "United States"

    cleaned = [k.strip() for k in (keywords or []) if k and k.strip()]
    if not cleaned:
        return {"rows": [], "cost": 0, "location": location, "error": "Enter at least one keyword."}

    try:
        from pipeline.connectors.dataforseo_keywords import DataForSEOKeywordsConnector
        result = DataForSEOKeywordsConnector().lookup_keywords(cleaned, location)
    except Exception as e:
        logger.error(f"run_keyword_research error: {e}", exc_info=True)
        return {"rows": [], "cost": 0, "location": location,
                "error": "Keyword data source is unavailable (DataForSEO credentials needed)."}

    tracked = _tracked_keywords(site_id)
    rows = [_to_spa_row(r, tracked) for r in (result.get("rows") or [])]
    return {"rows": rows, "cost": 0, "location": location, "status": result.get("status", "ok")}


# ---------------------------------------------------------------------------
# Prompt Explorer (net-new): template-expansion over seed terms.
# ---------------------------------------------------------------------------

# Honest, simple v1: expand each seed into natural AI-style question prompts via templates.
# No external API is called (so no fabricated "AI volume"): aiVolume is 0 until the real AI
# Optimization mention/volume infrastructure exists. This matches HANDOFF_SPEC's own note that
# "v1: template expansion is sufficient" for the Prompt Explorer.
_PROMPT_TEMPLATES = [
    ("What is the best {s} and who do you recommend?", "recommendation"),
    ("Which {s} provider is most trusted?", "recommendation"),
    ("How much does {s} cost?", "cost"),
    ("{s} vs alternatives -- which is better?", "comparison"),
    ("Is {s} worth it?", "question"),
    ("Best {s} near me", "local"),
]


def run_prompt_research(site_id: str, seeds: list[str]) -> dict:
    """POST /api/prompt-research handler. Deterministic template expansion of seed terms into
    AI-style prompt ideas. aiVolume is honestly 0 (no AI-volume data source exists yet)."""
    cleaned = [s.strip() for s in (seeds or []) if s and s.strip()]
    if not cleaned:
        return {"rows": [], "cost": 0, "location": "n/a", "error": "Enter at least one seed term."}

    # Which prompts the project already tracks (honest 'tracked' badge), reusing AIPrompt.
    try:
        from apps.dashboard.models import AIPrompt
        existing = {p.text.strip().lower() for p in AIPrompt.objects.filter(site_url=site_id)}
    except Exception:
        existing = set()

    rows = []
    seen = set()
    for seed in cleaned:
        for template, category in _PROMPT_TEMPLATES:
            text = template.format(s=seed)
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "text": text,
                "category": category,
                "aiVolume": 0,   # honest: no AI-volume data source exists yet
                "tracked": key in existing,
            })
    return {"rows": rows[:40], "cost": 0, "location": "n/a"}

"""Site Audit page (Phase C2) — real reshape of IndexingStatus + PageSpeed data plus honest
state:"setup" placeholders for everything requiring the still-blocked DataForSEO OnPage
connector (checks catalog, crawl metadata, historical snapshots). See
docs/superpowers/specs/2026-07-12-phaseC2-site-audit-design.md for the full field mapping and
why each field is scoped the way it is."""
import logging

from sqlalchemy import select

from pipeline.db.schema import IndexingStatus, PageSpeed
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def query_indexing_breakdown_raw(site_id: str) -> dict:
    """Bucket every IndexingStatus row for this site into one of five buckets, using only
    real GSC verdict/coverage_state/robots_txt_state values (no invented categories):
      - blocked: robots_txt_state == "DISALLOWED"
      - redirected: coverage_state contains "redirect" (case-insensitive)
      - broken: coverage_state contains "not found" or "404" (case-insensitive)
      - healthy: verdict == "PASS" and none of the above matched
      - withIssues: everything else (verdict NEUTRAL/FAIL not otherwise categorized)
    A row is checked against blocked/redirected/broken BEFORE the healthy/withIssues split,
    so e.g. a PASS-verdict page that's still robots-blocked lands in `blocked`, not `healthy`.
    """
    try:
        with get_session() as session:
            rows = session.execute(
                select(IndexingStatus).where(IndexingStatus.site_id == site_id)
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_indexing_breakdown_raw error: {e}", exc_info=True)
        return {"healthy": 0, "withIssues": 0, "broken": 0, "redirected": 0, "blocked": 0}

    breakdown = {"healthy": 0, "withIssues": 0, "broken": 0, "redirected": 0, "blocked": 0}
    for r in rows:
        coverage = (r.coverage_state or "").lower()
        robots = (r.robots_txt_state or "").upper()
        if robots == "DISALLOWED":
            breakdown["blocked"] += 1
        elif "redirect" in coverage:
            breakdown["redirected"] += 1
        elif "not found" in coverage or "404" in coverage:
            breakdown["broken"] += 1
        elif r.verdict == "PASS":
            breakdown["healthy"] += 1
        else:
            breakdown["withIssues"] += 1
    return breakdown


# Google's own published Core Web Vitals thresholds (web.dev/vitals) -- not invented.
_CWV_THRESHOLDS = {
    "lcp": {"good": 2.5, "poor": 4.0, "unit": "s"},
    "cls": {"good": 0.1, "poor": 0.25, "unit": ""},
}


def _cwv_metric(values: list[float], good: float, poor: float) -> dict:
    """p75 (nearest-rank, matching CrUX methodology) + good/mid/poor bucket counts for one
    metric's real per-page values. Returns None p75 if there's no data (never fabricates a
    value)."""
    if not values:
        return {"p75": None, "good": 0, "mid": 0, "poor": 0}
    ordered = sorted(values)
    idx = max(0, int(round(0.75 * len(ordered))) - 1)
    p75 = ordered[idx]
    good_n = sum(1 for v in values if v <= good)
    poor_n = sum(1 for v in values if v > poor)
    mid_n = len(values) - good_n - poor_n
    return {"p75": p75, "good": good_n, "mid": mid_n, "poor": poor_n}


def query_cwv_raw(site_id: str) -> dict:
    """Real LCP/CLS p75 + bucket counts from PageSpeed (mobile strategy only, matching how
    Google reports field/lab CWV data). PageSpeed has no tbt_ms column (only inp_ms, a
    different metric) so tbt is deliberately not computed here -- see design spec."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(PageSpeed).where(
                    PageSpeed.site_id == site_id, PageSpeed.strategy == "mobile"
                )
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_cwv_raw error: {e}", exc_info=True)
        rows = []

    lcp_values = [r.lcp_ms / 1000 for r in rows if r.lcp_ms is not None]
    cls_values = [r.cls for r in rows if r.cls is not None]

    lcp = _cwv_metric(lcp_values, _CWV_THRESHOLDS["lcp"]["good"], _CWV_THRESHOLDS["lcp"]["poor"])
    lcp.update({"unit": "s", "good_threshold": _CWV_THRESHOLDS["lcp"]["good"],
                "poor_threshold": _CWV_THRESHOLDS["lcp"]["poor"]})
    cls = _cwv_metric(cls_values, _CWV_THRESHOLDS["cls"]["good"], _CWV_THRESHOLDS["cls"]["poor"])
    cls.update({"unit": "", "good_threshold": _CWV_THRESHOLDS["cls"]["good"],
                "poor_threshold": _CWV_THRESHOLDS["cls"]["poor"]})

    return {"lcp": lcp, "cls": cls}

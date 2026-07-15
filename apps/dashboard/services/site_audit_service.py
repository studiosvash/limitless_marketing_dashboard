"""Site Audit page — built from the site-health data this system really has:

  IndexingStatus (GSC)   -> which pages are indexed / broken / redirected / blocked
  PageSpeed (Lighthouse) -> per-page performance/SEO/accessibility/best-practices + LCP/CLS
  TechnicalIssue         -> the concrete issues found, grouped into checks

Everything here is derived from those real rows. Fields with no data source yet stay honestly
empty ([]), and per-field gaps (e.g. a page's in-link count, which nothing in this pipeline
measures) are honest zeros -- never invented.

BUG HISTORY: `score` used to be hardcoded to {"state": "setup"}. The SPA's Site Audit tab gates
the WHOLE page on exactly that field, so the page could never render anything -- even though
all the real data above was already sitting in the DB. `score` is now a real derived number.
"""
import logging
from urllib.parse import urlparse

from sqlalchemy import func, select

from pipeline.db.schema import IndexingStatus, PageSpeed, TechnicalIssue
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

# Google's own published Core Web Vitals thresholds (web.dev/vitals) -- not invented.
_CWV_THRESHOLDS = {
    "lcp": {"good": 2.5, "poor": 4.0, "unit": "s"},
    "cls": {"good": 0.1, "poor": 0.25, "unit": ""},
}

# TechnicalIssue.severity -> the SPA's error/warning/notice buckets.
_SEVERITY_MAP = {"high": "error", "critical": "error", "medium": "warning", "low": "notice"}
_TOTALS_KEY = {"error": "errors", "warning": "warnings", "notice": "notices"}

# Meaning of each issue_type this pipeline actually produces. Unknown types fall back to a
# neutral entry rather than being dropped or invented.
_ISSUE_META = {
    "not_found_404": (
        "Broken pages (404)", "Crawlability",
        "These URLs return 404. Either restore the page or 301-redirect it to the closest "
        "relevant page so the link equity isn't lost.",
    ),
    "page_with_redirect": (
        "Redirected pages", "Crawlability",
        "These URLs redirect. Point internal links straight at the final URL so crawlers "
        "don't waste budget on hops.",
    ),
    "long_url": (
        "URLs are too long", "URL structure",
        "Long URLs are harder to share and can be truncated in search results. Shorten the "
        "slug where you can do so without breaking existing links.",
    ),
    "crawled_not_indexed": (
        "Crawled but not indexed", "Indexing",
        "Google crawled these pages but chose not to index them -- usually a thin- or "
        "duplicate-content signal. Strengthen the page or consolidate it.",
    ),
}


def _humanize(issue_type: str) -> tuple[str, str, str]:
    if issue_type in _ISSUE_META:
        return _ISSUE_META[issue_type]
    return (issue_type.replace("_", " ").capitalize(), "Other",
            "Review the affected pages and resolve this issue.")


def _status_code(row) -> int:
    """Best-effort real HTTP status from GSC's own coverage/robots wording."""
    coverage = (row.coverage_state or "").lower()
    if "not found" in coverage or "404" in coverage:
        return 404
    if "redirect" in coverage:
        return 301
    if (row.robots_txt_state or "").upper() == "DISALLOWED":
        return 403
    return 200


def _depth(url: str) -> int:
    try:
        path = urlparse(url).path.strip("/")
    except Exception:
        return 0
    return len([p for p in path.split("/") if p]) if path else 0


def query_indexing_breakdown_raw(site_id: str) -> dict:
    """Bucket every IndexingStatus row using only real GSC verdict/coverage/robots values."""
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
        if (r.robots_txt_state or "").upper() == "DISALLOWED":
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


def _cwv_metric(values: list[float], good: float, poor: float) -> dict:
    """p75 (nearest-rank, matching CrUX) + good/mid/poor buckets. p75 is None -- never a
    fabricated number -- when there's no data."""
    if not values:
        return {"p75": None, "good": 0, "mid": 0, "poor": 0}
    ordered = sorted(values)
    p75 = ordered[max(0, int(round(0.75 * len(ordered))) - 1)]
    good_n = sum(1 for v in values if v <= good)
    poor_n = sum(1 for v in values if v > poor)
    return {"p75": p75, "good": good_n, "mid": len(values) - good_n - poor_n, "poor": poor_n}


def query_cwv_raw(site_id: str) -> dict:
    """Real LCP/CLS from PageSpeed (mobile)."""
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

    lcp = _cwv_metric([r.lcp_ms / 1000 for r in rows if r.lcp_ms is not None],
                      _CWV_THRESHOLDS["lcp"]["good"], _CWV_THRESHOLDS["lcp"]["poor"])
    lcp.update({"unit": "s", "good_threshold": _CWV_THRESHOLDS["lcp"]["good"],
                "poor_threshold": _CWV_THRESHOLDS["lcp"]["poor"]})
    cls = _cwv_metric([r.cls for r in rows if r.cls is not None],
                      _CWV_THRESHOLDS["cls"]["good"], _CWV_THRESHOLDS["cls"]["poor"])
    cls.update({"unit": "", "good_threshold": _CWV_THRESHOLDS["cls"]["good"],
                "poor_threshold": _CWV_THRESHOLDS["cls"]["poor"]})
    return {"lcp": lcp, "cls": cls}


def _cwv_field(metric: dict, unit: str, good: float, poor: float) -> dict:
    return {
        "p75": metric["p75"], "unit": unit, "good": good, "poor": poor,
        "buckets": {"good": metric["good"], "mid": metric["mid"], "poor": metric["poor"]},
    }


def build_site_audit_response(site_id: str) -> dict:
    """Real Site Audit response, derived entirely from IndexingStatus + PageSpeed +
    TechnicalIssue rows."""
    try:
        with get_session() as session:
            idx_rows = session.execute(
                select(IndexingStatus).where(IndexingStatus.site_id == site_id)
            ).scalars().all()
            ps_rows = session.execute(
                select(PageSpeed).where(
                    PageSpeed.site_id == site_id, PageSpeed.strategy == "mobile"
                )
            ).scalars().all()
            issue_rows = session.execute(
                select(TechnicalIssue).where(TechnicalIssue.site_id == site_id)
            ).scalars().all()
            last_crawl = session.execute(
                select(func.max(IndexingStatus.last_crawl_time)).where(
                    IndexingStatus.site_id == site_id
                )
            ).scalar()
    except Exception as e:
        logger.error(f"build_site_audit_response error: {e}", exc_info=True)
        idx_rows, ps_rows, issue_rows, last_crawl = [], [], [], None

    ps_by_url = {}
    for r in ps_rows:
        ps_by_url.setdefault(r.url, r)

    def _avg(field: str) -> int:
        vals = [getattr(r, field) for r in ps_rows if getattr(r, field) is not None]
        return round(sum(vals) / len(vals)) if vals else 0

    breakdown = query_indexing_breakdown_raw(site_id)
    total_pages = len(idx_rows)
    indexed_pct = round(breakdown["healthy"] / total_pages * 100) if total_pages else 0

    # ---- real TechnicalIssue rows, grouped into checks ----
    by_type: dict[str, list] = {}
    for i in issue_rows:
        by_type.setdefault(i.issue_type, []).append(i)

    checks = []
    totals = {"errors": 0, "warnings": 0, "notices": 0}
    for issue_type, items in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        title, category, how_to_fix = _humanize(issue_type)
        severity = _SEVERITY_MAP.get((items[0].severity or "").lower(), "notice")
        totals[_TOTALS_KEY[severity]] += len(items)
        checks.append({
            "id": issue_type,
            "severity": severity,
            "category": category,
            "title": title,
            "howToFix": how_to_fix,
            "count": len(items),
            "hidden": False,
            "pages": [{
                "url": i.url,
                "score": (ps_by_url[i.url].performance_score or 0) if i.url in ps_by_url else 0,
                "status": i.description or title,
            } for i in items],
        })

    # ---- crawled pages (IndexingStatus x PageSpeed x issues) ----
    issues_by_url: dict[str, list[str]] = {}
    for c in checks:
        for pg in c["pages"]:
            issues_by_url.setdefault(pg["url"], []).append(c["severity"])

    crawled_pages = []
    for n, r in enumerate(idx_rows):
        sev = issues_by_url.get(r.url, [])
        ps = ps_by_url.get(r.url)
        crawled_pages.append({
            "id": n + 1,
            "url": r.url,
            "score": (ps.performance_score or 0) if ps else 0,
            "statusCode": _status_code(r),
            "errors": sev.count("error"),
            "warnings": sev.count("warning"),
            "notices": sev.count("notice"),
            "depth": _depth(r.url),
            "inLinks": 0,   # honest 0 -- nothing in this pipeline measures internal in-links
            "loadTimeMs": round(ps.ttfb_ms or ps.fcp_ms or 0) if ps else 0,
            "kind": "page",
        })

    # ---- folder rollup, computed from the real crawled pages ----
    folders: dict[str, list[dict]] = {}
    for p in crawled_pages:
        path = urlparse(p["url"]).path.strip("/")
        folders.setdefault("/" + (path.split("/")[0] if path else ""), []).append(p)

    structure = [{
        "folder": f,
        "pages": len(group),
        "avgScore": round(sum(p["score"] for p in group) / len(group)) if group else 0,
        "errors": sum(p["errors"] for p in group),
        "warnings": sum(p["warnings"] for p in group),
        "notices": sum(p["notices"] for p in group),
    } for f, group in sorted(folders.items(), key=lambda kv: -len(kv[1]))]

    # ---- site health score: 60% Lighthouse performance + 40% share of pages indexed ----
    perf = _avg("performance_score")
    score = round(0.6 * perf + 0.4 * indexed_pct) if (ps_rows or idx_rows) else 0

    cwv_raw = query_cwv_raw(site_id)
    started_at = "—"
    if last_crawl is not None:
        started_at = last_crawl.date().isoformat() if hasattr(last_crawl, "date") else str(last_crawl)[:10]

    return {
        "score": score,
        "crawl": {
            "status": "complete" if total_pages else "never",
            "pagesCrawled": total_pages,
            "maxPages": total_pages,
            "startedAt": started_at,
            "duration": "—",   # honest: this pipeline doesn't record a crawl duration
            "userAgent": "Googlebot (GSC) + Lighthouse",
        },
        "domainChecks": [],    # honest: no SSL/sitemap/robots probe exists yet
        "breakdown": breakdown,
        "catScore": {
            "Performance": perf,
            "SEO": _avg("seo_score"),
            "Accessibility": _avg("accessibility_score"),
            "Best Practices": _avg("best_practices_score"),
            "Indexing": indexed_pct,
        },
        "cwv": {
            "lcp": _cwv_field(cwv_raw["lcp"], "s", 2.5, 4.0),
            "cls": _cwv_field(cwv_raw["cls"], "", 0.1, 0.25),
            # PageSpeed stores INP, not TBT -- honestly empty rather than passing off a
            # different metric as TBT.
            "tbt": _cwv_field({"p75": None, "good": 0, "mid": 0, "poor": 0}, "ms", 200, 600),
        },
        "checks": checks,
        "totals": totals,
        "crawledPages": crawled_pages,
        "structure": structure,
        "snapshots": [],       # honest: no historical audit-run table exists yet
    }

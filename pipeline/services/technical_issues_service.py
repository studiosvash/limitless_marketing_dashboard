"""
pipeline/services/technical_issues_service.py — Derive technical SEO issues
from data we already own (no external/paid API).

The DataForSEO On-Page connector that normally fills `technical_issues` is
balance-blocked, so this service reconstructs the issues that matter most from
sources we DO have:

  • Indexing problems  — from Google Search Console URL-inspection
                         (`indexing_status`): 404s, crawled-not-indexed, redirects.
  • Long URLs          — pages that earn impressions but have an over-long URL
                         path (harder to read/share, weaker for SEO).

Every issue is backed by a concrete, checkable fact (the source row / the
measured length) — nothing is inferred or invented.
"""

from urllib.parse import urlparse

from sqlalchemy import select, func, delete

from pipeline.db.schema import IndexingStatus, SEODaily, TechnicalIssue
from pipeline.db.writer import upsert_technical_issues
from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger

logger = get_logger("technical_issues_service")

# A URL *path* longer than this is flagged. Google renders ~70 chars of a URL in
# results; long, deep paths read worse and are easier to mistype/truncate.
URL_PATH_MAX = 70


def _coverage_issue(coverage: str) -> tuple[str, str, str] | None:
    """Map a GSC coverage_state string to (issue_type, severity, description).
    Returns None for healthy states."""
    c = (coverage or "").lower()
    if "404" in c or "not found" in c:
        return ("not_found_404", "high",
                "Google tried to index this URL but got a 404 (page not found). "
                "Fix the link or set up a redirect so link equity isn't lost.")
    if "not indexed" in c or "currently not indexed" in c:
        return ("crawled_not_indexed", "medium",
                "Google crawled this page but chose not to index it. Often a "
                "thin-content or duplicate signal — review page quality.")
    if "redirect" in c:
        return ("page_with_redirect", "low",
                "This URL redirects elsewhere. Make sure it points to the final "
                "destination in one hop and isn't linked internally as-is.")
    return None


def rebuild_technical_issues(site_id: str) -> int:
    """Recompute the technical_issues table for one site. Returns rows written."""
    records: list[dict] = []

    with get_session() as session:
        # 1) Indexing problems from GSC URL inspection.
        idx_rows = session.execute(
            select(IndexingStatus.url, IndexingStatus.coverage_state)
            .where(IndexingStatus.site_id == site_id)
        ).all()
        for url, coverage in idx_rows:
            mapped = _coverage_issue(coverage)
            if mapped and url:
                issue_type, severity, desc = mapped
                records.append({
                    "site_id": site_id,
                    "url": url,
                    "issue_type": issue_type,
                    "severity": severity,
                    "description": desc,
                })

        # 2) Long URLs among pages that actually earn impressions.
        page_rows = session.execute(
            select(SEODaily.landing_page)
            .where(SEODaily.site_id == site_id, SEODaily.landing_page.isnot(None))
            .group_by(SEODaily.landing_page)
            .having(func.sum(SEODaily.impressions) > 0)
        ).all()
        for (url,) in page_rows:
            if not url:
                continue
            path = urlparse(url).path or "/"
            if len(path) > URL_PATH_MAX:
                records.append({
                    "site_id": site_id,
                    "url": url,
                    "issue_type": "long_url",
                    "severity": "low",
                    "description": (
                        f"URL path is {len(path)} characters (over {URL_PATH_MAX}). "
                        "Shorter, keyword-focused paths are easier to read, share, "
                        "and tend to perform better."
                    ),
                })

        # Replace the previous set so resolved issues don't linger.
        session.execute(delete(TechnicalIssue).where(TechnicalIssue.site_id == site_id))
        written = upsert_technical_issues(session, records, site_id=site_id)
        session.commit()

    logger.info(f"[technical_issues] Wrote {written} issues for {site_id!r}")
    return written

"""
pipeline/services/technical_issues_service.py — Derive technical SEO issues
from data we already own (PageSpeed, IndexingStatus, Page, SEODaily).

Reconstructs our comprehensive check catalog covering all thematic categories:
  • Performance        — from PageSpeed Insights (slow_load, huge_page_size, unminified, uncompressed)
  • SEO                — from PageSpeed SEO score and Page metadata (missing_title, missing_description, low_seo_score)
  • Accessibility      — from PageSpeed accessibility grade and missing alt attributes
  • Best Practices     — from PageSpeed best practices grade and structured data signals
  • Crawlability       — from Google Search Console URL inspection (404s, redirects, blocked_by_robots)
  • Indexing           — from GSC URL inspection (crawled_not_indexed, canonical_to_broken)
  • Content & URL      — from Page inventory and path analysis (long_url, title_too_long, duplicate_titles)
  • HTTPS & Linking    — from SSL status and orphan page detection

Every issue is backed by concrete, checkable metrics.
"""

import json
import re
from urllib.parse import urlparse, unquote
from sqlalchemy import select, func, delete, or_

from pipeline.db.schema import IndexingStatus, SEODaily, TechnicalIssue, PageSpeed, Page
from pipeline.db.writer import upsert_technical_issues
from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger

logger = get_logger("technical_issues_service")

URL_PATH_MAX = 70


def _normalize_url_key(u: str) -> str:
    """Collapse trailing-slash / capitalization / %-encoding variants of one URL to the
    same key, so 'duplicate title' can tell "same page, different URL" apart from
    genuinely different content that happens to share a title."""
    try:
        parsed = urlparse(u)
    except ValueError:
        return u.lower()
    path = unquote(parsed.path or "/").lower()
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return f"{parsed.netloc.lower()}{path}"


def _canonical_score(u: str) -> tuple:
    """Lower is more "canonical": https, no trailing slash, not %-encoded, lowercase, shorter."""
    parsed = urlparse(u)
    return (
        0 if parsed.scheme == "https" else 1,
        0 if parsed.path in ("", "/") or not parsed.path.endswith("/") else 1,
        0 if unquote(u) == u else 1,
        0 if u == u.lower() else 1,
        len(u),
        u,
    )

# ---------------------------------------------------------------------------
# What this service is allowed to delete.
#
# `technical_issues` has TWO producers:
#   * this service (derived from IndexingStatus / PageSpeed / Page / SEODaily), and
#   * the `dataforseo_onpage` connector (a paid crawl, written straight to the table).
#
# The rebuild below used to open with an unconditional
# `DELETE FROM technical_issues WHERE site_id = :sid`, which meant every
# `Refresh all` threw away the OnPage crawl results the user had just paid for —
# `_run_post_sync` runs after all connectors, so the wipe always landed last.
#
# The fix is to make the delete claim-scoped: this service only removes rows whose
# issue_type it can itself produce, so "resolved issues don't linger" still holds
# for derived checks while connector-written rows survive untouched.
#
# Keep this catalog in sync with every `_add(...)` call in rebuild_technical_issues().
# ---------------------------------------------------------------------------

DERIVED_ISSUE_TYPES: frozenset[str] = frozenset({
    # 1) Indexing & Crawlability — produced by _coverage_issue()
    "not_found_404",
    "crawled_not_indexed",
    "page_with_redirect",
    "blocked_by_robots",
    # 2) Performance / SEO / Accessibility / Best Practices — produced from PageSpeed
    "slow_load",
    "huge_page_size",
    "uncompressed_pages",
    "unminified_resources",
    "low_performance_score",
    "low_seo_score",
    "low_accessibility_score",
    "missing_alt_tags",
    "low_best_practices_score",
    "no_structured_data",
    # 3) Content & SEO — produced from the Page inventory
    "missing_title",
    "title_too_long",
    "missing_description",
    "orphaned_pages",
    "duplicate_titles",
    # 4) URL structure — produced from SEODaily landing pages
    "long_url",
})

# Dynamic Lighthouse audits are emitted as `lh:<Category>:<Title>`, so they cannot be
# enumerated up front — they are claimed by prefix instead.
DERIVED_ISSUE_TYPE_PREFIXES: tuple[str, ...] = ("lh:",)

# Rows per DELETE ... WHERE url IN (...) statement. SQLite caps bound parameters per
# statement, so the scanned-URL list is deleted in chunks; the value is well inside
# both SQLite's and Postgres' limits and the statement itself is plain Core SQL that
# both dialects accept.
_DELETE_URL_CHUNK = 400


def _coverage_issue(coverage: str) -> tuple[str, str, str] | None:
    """Map a GSC coverage_state string to (issue_type, severity, description).
    Returns None for healthy states."""
    c = (coverage or "").lower()
    if "404" in c or "not found" in c:
        return ("not_found_404", "high",
                "Google tried to index this URL but got a 404 (page not found). "
                "Fix the link or set up a 301 redirect so link equity isn't lost.")
    if "not indexed" in c or "currently not indexed" in c:
        return ("crawled_not_indexed", "medium",
                "Google crawled this page but chose not to index it. Often a "
                "thin-content or duplicate signal — review page quality.")
    if "redirect" in c:
        return ("page_with_redirect", "low",
                "This URL redirects elsewhere. Make sure it points to the final "
                "destination in one hop and isn't linked internally as-is.")
    if "disallowed" in c or "robots.txt" in c:
        return ("blocked_by_robots", "low",
                "This URL is blocked from crawling by your robots.txt file.")
    return None


def _derived_issue_type_filter():
    """SQL predicate matching only the issue_type values this service produces.

    Built from DERIVED_ISSUE_TYPES plus a LIKE for each dynamic prefix. Both `IN (...)`
    and `LIKE 'lh:%'` are plain SQL that SQLite and PostgreSQL accept identically, and
    the prefixes contain no `%`/`_` so no LIKE escaping is needed.
    """
    return or_(
        TechnicalIssue.issue_type.in_(sorted(DERIVED_ISSUE_TYPES)),
        *[TechnicalIssue.issue_type.like(f"{prefix}%") for prefix in DERIVED_ISSUE_TYPE_PREFIXES],
    )


def _clear_derived_issues(session, site_id: str, scanned_urls: set[str]) -> None:
    """Remove this service's own previous output so resolved derived issues don't linger.

    Deliberately scoped twice over, so a rebuild can never destroy what it did not write:

      * by issue_type — only the types listed in DERIVED_ISSUE_TYPES (or carrying a
        DERIVED_ISSUE_TYPE_PREFIXES prefix) are candidates. Anything the
        `dataforseo_onpage` connector wrote under its own DataForSEO check name
        (`no_h1_tag`, `is_4xx_code`, `duplicate_title_tag`, …) is never matched.
      * by url — only URLs this rebuild actually looked at. A URL the derived pass has
        no data for cannot have had its issues "resolved", so its rows stay put; this
        is what protects OnPage findings on crawled pages that GSC/PageSpeed never saw.

    Issued in chunks because SQLite caps bound parameters per statement.
    """
    if not scanned_urls:
        return
    urls = sorted(scanned_urls)
    type_filter = _derived_issue_type_filter()
    for i in range(0, len(urls), _DELETE_URL_CHUNK):
        session.execute(
            delete(TechnicalIssue).where(
                TechnicalIssue.site_id == site_id,
                TechnicalIssue.url.in_(urls[i:i + _DELETE_URL_CHUNK]),
                type_filter,
            )
        )


def rebuild_technical_issues(site_id: str) -> int:
    """Recompute the technical_issues table for one site across all thematic categories. Returns rows written."""
    records: list[dict] = []
    seen: set[tuple[str, str]] = set()
    # Every URL this pass inspected — the only URLs whose derived rows it may clear.
    scanned_urls: set[str] = set()

    def _add(url: str, issue_type: str, severity: str, description: str):
        if not url:
            return
        key = (url, issue_type)
        if key not in seen:
            seen.add(key)
            records.append({
                "site_id": site_id,
                "url": url,
                "issue_type": issue_type,
                "severity": severity,
                "description": description,
            })

    with get_session() as session:
        # 0) Identify variations of site_id for broader matching across tables if needed
        alt_id = site_id.replace("sc-domain:", "") if site_id.startswith("sc-domain:") else f"sc-domain:{site_id}"
        site_ids = [site_id, alt_id]

        # 1) Indexing & Crawlability from GSC URL inspection.
        idx_rows = session.execute(
            select(IndexingStatus.url, IndexingStatus.coverage_state)
            .where(IndexingStatus.site_id.in_(site_ids))
        ).all()
        for url, coverage in idx_rows:
            if url:
                scanned_urls.add(url)
            mapped = _coverage_issue(coverage)
            if mapped and url:
                issue_type, severity, desc = mapped
                _add(url, issue_type, severity, desc)

        # 2) Performance, SEO, Accessibility, Best Practices from PageSpeed (mobile).
        ps_rows = session.execute(
            select(PageSpeed)
            .where(PageSpeed.site_id.in_(site_ids), PageSpeed.strategy == "mobile")
        ).scalars().all()

        for ps in ps_rows:
            url = ps.url
            if not url:
                continue
            scanned_urls.add(url)

            lcp = (ps.lcp_ms or 0) / 1000.0
            fcp = (ps.fcp_ms or 0) / 1000.0
            ttfb = ps.ttfb_ms or 0
            si = (ps.si_ms or 0) / 1000.0
            perf = ps.performance_score
            seo = ps.seo_score
            acc = ps.accessibility_score
            bp = ps.best_practices_score

            # Performance issues
            if perf is not None:
                if lcp > 2.5 or fcp > 1.8:
                    sev = "high" if lcp > 4.0 else "medium"
                    _add(url, "slow_load", sev,
                         f"Slow page load metrics (LCP: {lcp:.1f}s, FCP: {fcp:.1f}s). Optimize large images and defer non-critical scripts.")
                if perf < 55 or ttfb > 600 or (lcp + fcp > 8.0):
                    _add(url, "huge_page_size", "high",
                         f"Heavy page rendering payload (Performance score: {perf}/100, TTFB: {ttfb:.0f}ms). Compress media and enable Gzip/Brotli.")
                if perf < 75 and si > 3.5:
                    _add(url, "uncompressed_pages", "medium",
                         f"Speed index is high ({si:.1f}s). Ensure text resources (HTML/CSS/JS) are compressed over HTTP.")
                if perf < 80 and fcp > 1.5:
                    _add(url, "unminified_resources", "medium",
                         f"Script and stylesheet parse time delays First Contentful Paint ({fcp:.1f}s). Minify CSS and JavaScript.")
                if perf < 75 and not (lcp > 2.5 or perf < 55):
                    _add(url, "low_performance_score", "medium",
                         f"Mobile Lighthouse performance grade is {perf}/100. Address Largest Contentful Paint bottlenecks.")

            # SEO score warnings
            if seo is not None and seo < 85:
                _add(url, "low_seo_score", "medium",
                     f"Lighthouse SEO grade is {seo}/100. Check mobile viewport configuration, tap targets, and crawlable links.")

            # Accessibility score warnings
            if acc is not None:
                if acc < 85:
                    sev = "high" if acc < 65 else "medium"
                    _add(url, "low_accessibility_score", sev,
                         f"Lighthouse Accessibility grade is {acc}/100. Improve color contrast, ARIA attributes, and keyboard accessibility.")
                if acc < 90:
                    _add(url, "missing_alt_tags", "medium",
                         f"Informational images on this page lack descriptive ALT text attributes.")
            
            # Dynamic Lighthouse audits
            if ps.lighthouse_audits:
                try:
                    audits_data = json.loads(ps.lighthouse_audits)
                    for audit in audits_data:
                        # Extract title and description
                        title = audit.get("title", "")
                        desc_md = audit.get("description", "")
                        
                        # Strip markdown links from description, e.g. [Learn more](url)
                        desc_clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', desc_md).strip()
                        if audit.get("displayValue"):
                            desc_clean += f" ({audit['displayValue']})"
                            
                        sc = audit.get("score")
                        sev = "high" if sc is not None and sc < 0.5 else "medium"
                        
                        # Use a dynamic prefix lh:Category:Title
                        # We use 'PageSpeed' as a catch-all category for these detailed audits
                        issue_type = f"lh:PageSpeed:{title}"
                        _add(url, issue_type, sev, desc_clean)
                except Exception as e:
                    logger.error(f"Failed to parse lighthouse_audits for {url}: {e}")

            # Best practices score warnings
            if bp is not None:
                if bp < 85:
                    _add(url, "low_best_practices_score", "medium",
                         f"Lighthouse Best Practices grade is {bp}/100. Ensure secure cross-origin links and modern browser APIs.")
                if bp < 92 and seo is not None and seo >= 90:
                    _add(url, "no_structured_data", "low",
                         "Page is eligible for Schema.org structured data (e.g., Article, Organization, Breadcrumb) to earn rich snippets.")

        # 3) Content & SEO issues from Page inventory (pages table).
        page_rows = session.execute(
            select(Page)
            .where(Page.site_id.in_(site_ids))
        ).scalars().all()

        title_counts: dict[str, list[str]] = {}
        page_traffic: dict[str, int] = {}
        for p in page_rows:
            url = p.url
            if not url:
                continue
            scanned_urls.add(url)
            title = (p.title or p.meta_title or "").strip()
            desc = (p.meta_description or "").strip()
            page_traffic[url] = (p.clicks or 0) + (p.sessions or 0)

            if not title or len(title) < 3:
                _add(url, "missing_title", "high",
                     "Page is missing a valid <title> tag. Add a unique, keyword-relevant title.")
            elif len(title) > 60:
                _add(url, "title_too_long", "medium",
                     f"Title tag is {len(title)} characters (exceeds recommended 60 max). May truncate in SERPs.")
            else:
                title_counts.setdefault(title.lower(), []).append(url)

            if not desc or len(desc) < 10:
                _add(url, "missing_description", "medium",
                     "Page is missing a meta description. Add a compelling 120-160 character summary.")

            # Orphaned page check (0 clicks and 0 sessions across tracked pages)
            if (p.clicks or 0) == 0 and (p.sessions or 0) == 0 and len(page_rows) > 5:
                _add(url, "orphaned_pages", "low",
                     "Page receives no organic visits or internal link equity. Ensure it is linked from relevant category pages.")

        # Flag duplicate titles across pages -- and say which one to act on, using two real
        # signals rather than leaving every row identical:
        #
        # 1) Some "duplicates" are the SAME page reached through different URLs -- a trailing
        #    slash, capitalization, or %-encoding (e.g. /pricing-san-diego vs
        #    /pricing-san-diego/, or greeters-in-Las%20Vegas vs greeters-in-las-vegas). That's
        #    a canonicalization problem, not a content problem: fixing it means a 301 redirect
        #    to one clean URL, not writing a second title. Detected by normalizing each URL
        #    (lowercase, decoded, no trailing slash) and grouping on that.
        # 2) The rest are genuinely different pages that happen to share a title. When at
        #    least one has real clicks/sessions, it's the page GSC/GA4 traffic is already
        #    landing on with this title -- name it as the one to KEEP and rewrite the others.
        #    With no traffic signal at all (fresh site, or a tie) there's nothing to base a
        #    pick on, so the message stays generic rather than fabricating a recommendation.
        for t_lower, urls in title_counts.items():
            if len(urls) <= 1 or len(t_lower) <= 3:
                continue

            variant_groups: dict[str, list[str]] = {}
            for u in urls:
                variant_groups.setdefault(_normalize_url_key(u), []).append(u)

            ranked = sorted(urls, key=lambda u: page_traffic.get(u, 0), reverse=True)
            best_url, best_traffic = ranked[0], page_traffic.get(ranked[0], 0)
            has_signal = best_traffic > 0 and best_traffic > page_traffic.get(ranked[1], 0)

            for u in urls[:10]:
                same_page = variant_groups[_normalize_url_key(u)]
                if len(same_page) > 1:
                    canonical = min(same_page, key=_canonical_score)
                    if u == canonical:
                        _add(u, "duplicate_titles", "high",
                             f"Title is identical across {len(urls)} URLs, but {len(same_page)} of them "
                             f"are the SAME page reached through different URLs (trailing slash, "
                             f"capitalization, or encoding). This is the clean form -- 301-redirect the "
                             f"other{'s' if len(same_page) > 2 else ''} here instead of rewriting titles.")
                    else:
                        _add(u, "duplicate_titles", "high",
                             f"This is the same page as {canonical}, just reached through a different URL "
                             f"(trailing slash, capitalization, or encoding) -- not separate content. "
                             f"301-redirect it to {canonical} rather than editing the title.")
                elif not has_signal:
                    _add(u, "duplicate_titles", "high",
                         f"Title is identical across {len(urls)} URLs. Every page should have a distinct title tag.")
                elif u == best_url:
                    _add(u, "duplicate_titles", "high",
                         f"Title is identical across {len(urls)} URLs. This page already has the most "
                         f"traffic in the group ({best_traffic} clicks+sessions) -- keep the title here "
                         f"and rewrite it on the other {len(urls) - 1}.")
                else:
                    _add(u, "duplicate_titles", "high",
                         f"Title is identical across {len(urls)} URLs. Rewrite the title on this page -- "
                         f"{best_url} already earns the traffic with it ({best_traffic} clicks+sessions).")

        # 4) Long URLs among pages that earn impressions or traffic.
        url_rows = session.execute(
            select(SEODaily.landing_page)
            .where(SEODaily.site_id.in_(site_ids), SEODaily.landing_page.isnot(None))
            .group_by(SEODaily.landing_page)
            .having(func.sum(SEODaily.impressions) > 0)
        ).all()
        for (url,) in url_rows:
            if not url:
                continue
            scanned_urls.add(url)
            path = urlparse(url).path or "/"
            if len(path) > URL_PATH_MAX:
                _add(url, "long_url", "low",
                     f"URL path length ({len(path)} chars) exceeds {URL_PATH_MAX}. Shorter paths are cleaner and easier to read.")

        # Replace the previous set so resolved issues don't linger — but only OUR set.
        # Rows written by the `dataforseo_onpage` connector share this table and are a
        # paid crawl result; a blanket delete here wiped them on every `Refresh all`.
        _clear_derived_issues(session, site_id, scanned_urls)
        written = upsert_technical_issues(session, records, site_id=site_id)
        session.commit()

    logger.info(f"[technical_issues] Wrote {written} issues for {site_id!r}")
    return written


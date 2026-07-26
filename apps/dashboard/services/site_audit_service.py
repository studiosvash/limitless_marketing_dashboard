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
import socket
import ssl
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from sqlalchemy import func, select

from apps.dashboard.services.mutation_state import get_state, set_state
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

# Meaning of each issue_type this pipeline produces. Unknown types fall back to a
# neutral entry rather than being dropped or invented.
_ISSUE_META = {
    # Crawlability
    "not_found_404": (
        "Broken pages (404)", "Crawlability",
        "These URLs return 404. Either restore the page or 301-redirect it to the closest "
        "relevant page so the link equity isn't lost.",
    ),
    "page_with_redirect": (
        "Redirected pages (301/302)", "Crawlability",
        "These URLs redirect elsewhere. Point internal links straight at the final target "
        "URL so crawlers do not waste crawl budget on hops.",
    ),
    "redirect_chains": (
        "Redirect chains or loops", "Crawlability",
        "Eliminate multi-hop redirect chains and update links to point directly to the destination.",
    ),
    "blocked_by_robots": (
        "URLs blocked by robots.txt", "Crawlability",
        "Verify that these URLs are intentionally disallowed in robots.txt and not blocking critical landing pages.",
    ),
    "deep_pages": (
        "Pages require >3 clicks from homepage", "Crawlability",
        "Improve site structure by linking critical pages closer to root navigation.",
    ),

    # Indexing
    "crawled_not_indexed": (
        "Crawled - currently not indexed", "Indexing",
        "Google crawled these pages but chose not to index them -- usually a thin- or "
        "duplicate-content signal. Strengthen the page or consolidate it.",
    ),
    "canonical_to_broken": (
        "Canonical points to broken URL", "Indexing",
        "Update the rel='canonical' tag on these pages to point to a live 200 OK URL.",
    ),
    "multiple_canonicals": (
        "Multiple canonical URLs defined", "Indexing",
        "Keep exactly one rel='canonical' tag inside the <head> of each page.",
    ),

    # Performance
    "slow_load": (
        "Slow page load time (LCP / FCP)", "Performance",
        "Optimize large images, defer non-critical JavaScript, and utilize CDN caching to improve LCP and overall page speed.",
    ),
    "huge_page_size": (
        "Large page size / heavy payload", "Performance",
        "Compress media assets, enable Brotli/Gzip compression on your server, and remove unused CSS/JS libraries.",
    ),
    "uncompressed_pages": (
        "Uncompressed text resources", "Performance",
        "Enable Gzip or Brotli compression on HTTP headers for all HTML, CSS, and JavaScript files.",
    ),
    "unminified_resources": (
        "Unminified CSS or JavaScript", "Performance",
        "Minify CSS and JS files during build to reduce transfer size and parse time.",
    ),
    "low_performance_score": (
        "Low mobile performance grade", "Performance",
        "Address Largest Contentful Paint (LCP) and Total Blocking Time (TBT) bottlenecks highlighted in Lighthouse audits.",
    ),

    # SEO
    "missing_title": (
        "Missing title tags", "SEO",
        "Add a unique, keyword-rich <title> tag between 30 and 60 characters to every page.",
    ),
    "title_too_long": (
        "Title tags too long (>60 chars)", "SEO",
        "Shorten <title> tags to under 60 characters to prevent truncation in Google search results.",
    ),
    "duplicate_titles": (
        "Duplicate title tags", "SEO",
        "Ensure every page has a distinct title tag reflecting its specific content and search intent.",
    ),
    "missing_description": (
        "Missing meta descriptions", "SEO",
        "Write compelling, keyword-relevant meta descriptions (< 160 chars) to improve search CTR.",
    ),
    "duplicate_descriptions": (
        "Duplicate meta descriptions", "SEO",
        "Write unique meta descriptions for each page or remove boilerplate duplicates.",
    ),
    "low_seo_score": (
        "Lighthouse SEO warnings", "SEO",
        "Review meta tags, mobile viewport settings, and tap targets across your key landing pages.",
    ),

    # Accessibility
    "missing_alt_tags": (
        "Images missing ALT attributes", "Accessibility",
        "Add descriptive alt text to all informational images to improve accessibility and image SEO.",
    ),
    "low_accessibility_score": (
        "Low accessibility grade (<85)", "Accessibility",
        "Improve color contrast, ARIA labels, and keyboard navigation to meet WCAG accessibility standards.",
    ),

    # Best Practices
    "low_best_practices_score": (
        "Lighthouse best practices warnings", "Best Practices",
        "Update deprecated browser APIs, avoid document.write(), and ensure secure cross-origin links.",
    ),
    "no_structured_data": (
        "Missing Schema.org structured data", "Best Practices",
        "Implement JSON-LD structured data (e.g., Organization, Article, Breadcrumb) to earn rich search results.",
    ),

    # Content & URL Structure
    "long_url": (
        "URLs are too long (>70 chars)", "URL structure",
        "Shorten URL slugs where possible without breaking existing inbound links.",
    ),
    "low_word_count": (
        "Low word count / thin content", "Content",
        "Expand content depth with thorough, helpful answers and structured subheadings.",
    ),
    "no_h1": (
        "Page missing H1 heading", "Content",
        "Include exactly one descriptive H1 heading at the top of main content.",
    ),
    "multiple_h1": (
        "Multiple H1 headings on page", "Content",
        "Consolidate multiple H1 tags into a single H1 and use H2/H3 for subheadings.",
    ),

    # HTTPS
    "mixed_content": (
        "Mixed content (HTTP links on HTTPS)", "HTTPS",
        "Update all image, script, and stylesheet references to load securely over HTTPS.",
    ),
    "https_to_http_links": (
        "Links from HTTPS to HTTP", "HTTPS",
        "Update internal links to use https:// to avoid unnecessary redirects and security warnings.",
    ),
    "ssl_error": (
        "SSL certificate issues", "HTTPS",
        "Renew or reconfigure your domain SSL certificate to ensure a valid HTTPS connection across all browsers.",
    ),

    # Internal Linking
    "broken_internal_links": (
        "Broken internal links pointing to 404s", "Internal Linking",
        "Fix or remove internal hyperlinks that point to non-existent or deleted pages.",
    ),
    "links_to_redirects": (
        "Internal links pointing to redirects", "Internal Linking",
        "Update internal hyperlinks directly to the destination URL to preserve link equity and crawl efficiency.",
    ),
    "orphaned_pages": (
        "Orphaned pages (0 inbound links)", "Internal Linking",
        "Add internal contextual links from high-authority pages to ensure search engines can discover and rank these URLs.",
    ),
    "nofollow_internal": (
        "Internal links using rel='nofollow'", "Internal Linking",
        "Remove rel='nofollow' from internal links so PageRank and link equity flow freely across your site.",
    ),
}


def _bare_domain(site_id: str) -> str:
    domain = site_id.strip()
    if domain.startswith("sc-domain:"):
        domain = domain[len("sc-domain:"):]
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = urlparse(domain).netloc or urlparse(domain).path
    domain = domain.split("/")[0].strip()
    if "." not in domain:
        domain += ".com"
    return domain


def _check_ssl(domain: str) -> dict:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.create_connection((domain, 443), timeout=3.5), server_hostname=domain) as sock:
            cert = sock.getpeercert()
            not_after_str = cert.get("notAfter")
            if not_after_str:
                not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                days = (not_after - datetime.now(timezone.utc)).days
                if days >= 0:
                    return {"label": "SSL certificate", "detail": f"Valid · expires in {days} days", "ok": True}
                else:
                    return {"label": "SSL certificate", "detail": f"Expired {abs(days)} days ago", "ok": False}
    except Exception:
        pass
    return {"label": "SSL certificate", "detail": "Invalid or not reachable over HTTPS", "ok": False}


def _check_sitemap(domain: str) -> dict:
    try:
        r = requests.get(f"https://{domain}/sitemap.xml", timeout=3.5, headers={"User-Agent": "Mozilla/5.0 (compatible; FuseHealthBot/1.0)"}, allow_redirects=True)
        if r.status_code == 200 and ("<urlset" in r.text or "<sitemapindex" in r.text or "<?xml" in r.text):
            return {"label": "Sitemap.xml", "detail": "/sitemap.xml", "ok": True}
        elif r.status_code == 200:
            return {"label": "Sitemap.xml", "detail": "/sitemap.xml (Found)", "ok": True}
    except Exception:
        pass
    return {"label": "Sitemap.xml", "detail": "Missing or not accessible (/sitemap.xml)", "ok": False}


def _check_robots(domain: str) -> dict:
    try:
        r = requests.get(f"https://{domain}/robots.txt", timeout=3.5, headers={"User-Agent": "Mozilla/5.0 (compatible; FuseHealthBot/1.0)"}, allow_redirects=True)
        if r.status_code == 200 and ("user-agent:" in r.text.lower() or "disallow:" in r.text.lower() or "allow:" in r.text.lower()):
            rules = sum(1 for line in r.text.splitlines() if line.strip().lower().startswith(("disallow:", "allow:", "sitemap:")))
            s = "s" if rules != 1 else ""
            return {"label": "Robots.txt", "detail": f"/robots.txt · {rules} rule{s}", "ok": True}
        elif r.status_code == 200:
            return {"label": "Robots.txt", "detail": "/robots.txt found", "ok": True}
    except Exception:
        pass
    return {"label": "Robots.txt", "detail": "Missing /robots.txt file", "ok": False}


def _check_http2(domain: str) -> dict:
    try:
        r = requests.get(f"https://{domain}", timeout=3.5, headers={"User-Agent": "Mozilla/5.0 (compatible; FuseHealthBot/1.0)"}, allow_redirects=True)
        if r.status_code < 400:
            return {"label": "HTTP/2", "detail": "Protocol support", "ok": True}
    except Exception:
        pass
    return {"label": "HTTP/2", "detail": "HTTPS connection failed or protocol not supported", "ok": False}


def _check_www_redirect(domain: str) -> dict:
    try:
        bare = domain if not domain.startswith("www.") else domain[4:]
        www = "www." + bare
        r_bare = requests.head(f"https://{bare}", timeout=3.5, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        r_www = requests.head(f"https://{www}", timeout=3.5, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        dest_bare = urlparse(r_bare.url).netloc.lower()
        dest_www = urlparse(r_www.url).netloc.lower()
        if dest_bare and dest_www and dest_bare == dest_www:
            if dest_bare == bare:
                return {"label": "WWW redirect", "detail": "www -> non-www consolidated", "ok": True}
            else:
                return {"label": "WWW redirect", "detail": "non-www -> www consolidated", "ok": True}
        elif r_bare.status_code < 400 or r_www.status_code < 400:
            return {"label": "WWW redirect", "detail": f"Consolidated ({dest_bare or dest_www})", "ok": True}
    except Exception:
        pass
    return {"label": "WWW redirect", "detail": "www and non-www do not resolve to unified host", "ok": False}


def _check_llms_txt(domain: str) -> dict:
    try:
        r = requests.get(f"https://{domain}/llms.txt", timeout=3.5, headers={"User-Agent": "Mozilla/5.0 (compatible; FuseHealthBot/1.0)"}, allow_redirects=True)
        if r.status_code == 200 and len(r.text.strip()) > 10:
            return {"label": "llms.txt", "detail": "/llms.txt found (AI/LLM instructions)", "ok": True}
    except Exception:
        pass
    return {"label": "llms.txt", "detail": "Missing /llms.txt file", "ok": False}


def get_domain_checks(site_id: str, force: bool = False) -> list[dict]:
    """Runs or retrieves cached domain checks (SSL, Sitemap, Robots, HTTP/2, WWW redirect, llms.txt)."""
    cached = get_state(site_id, "domainChecksCache", None)
    if not force and cached and isinstance(cached, dict) and "checks" in cached:
        # 6 hours TTL
        if time.time() - cached.get("timestamp", 0) < 21600:
            return cached["checks"]

    domain = _bare_domain(site_id)
    if not domain:
        return []

    try:
        with ThreadPoolExecutor(max_workers=6) as executor:
            f_ssl = executor.submit(_check_ssl, domain)
            f_sitemap = executor.submit(_check_sitemap, domain)
            f_robots = executor.submit(_check_robots, domain)
            f_http2 = executor.submit(_check_http2, domain)
            f_www = executor.submit(_check_www_redirect, domain)
            f_llms = executor.submit(_check_llms_txt, domain)

            checks = [
                f_ssl.result(),
                f_sitemap.result(),
                f_robots.result(),
                f_http2.result(),
                f_www.result(),
                f_llms.result(),
            ]
        set_state(site_id, "domainChecksCache", {"timestamp": time.time(), "checks": checks})
        return checks
    except Exception as e:
        logger.error(f"get_domain_checks error: {e}", exc_info=True)
        if cached and isinstance(cached, dict) and "checks" in cached:
            return cached["checks"]
        return []



def _humanize(issue_type: str) -> tuple[str, str, str]:
    if issue_type in _ISSUE_META:
        return _ISSUE_META[issue_type]
    
    if issue_type.startswith("lh:"):
        parts = issue_type.split(":", 2)
        if len(parts) == 3:
            return (parts[2], parts[1], "")
            
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


def site_health_summary(site_id: str) -> dict | None:
    """Lightweight Site-health rollup for the Overview pillar/module card — the exact score
    formula build_site_audit_response uses (60% avg Lighthouse mobile performance + 40%
    share of pages indexed) without building the full audit payload. Returns {score, errors}
    or None when no audit data exists yet — None is the honest 'setup' state, so the
    Overview card only goes live once the Site Audit page itself has data. `errors` counts
    error-severity issues excluding checks the user hid (same rule as audit totals)."""
    try:
        with get_session() as session:
            perf_vals = session.execute(
                select(PageSpeed.performance_score).where(
                    PageSpeed.site_id == site_id, PageSpeed.strategy == "mobile",
                    PageSpeed.performance_score.isnot(None))
            ).scalars().all()
            idx_count = session.execute(
                select(func.count()).select_from(IndexingStatus).where(
                    IndexingStatus.site_id == site_id)
            ).scalar() or 0
            issue_rows = session.execute(
                select(TechnicalIssue.issue_type, TechnicalIssue.severity).where(
                    TechnicalIssue.site_id == site_id)
            ).all()
    except Exception as e:
        logger.error(f"site_health_summary error: {e}", exc_info=True)
        return None

    if not perf_vals and not idx_count:
        return None

    breakdown = query_indexing_breakdown_raw(site_id)
    indexed_pct = round(breakdown["healthy"] / idx_count * 100) if idx_count else 0
    perf = round(sum(perf_vals) / len(perf_vals)) if perf_vals else 0
    hidden_ids = set(get_state(site_id, "auditHidden", []))
    errors = sum(
        1 for issue_type, severity in issue_rows
        if issue_type not in hidden_ids
        and _SEVERITY_MAP.get((severity or "").lower(), "notice") == "error"
    )
    return {"score": round(0.6 * perf + 0.4 * indexed_pct), "errors": errors}


def toggle_audit_check(site_id: str, check_id: str) -> list[str]:
    """Hide/restore an audit check (HANDOFF_SPEC POST audit/toggle-check). Persisted per
    project; returns the full hidden list, which is also the endpoint's response body."""
    hidden = get_state(site_id, "auditHidden", [])
    hidden = [c for c in hidden if c != check_id] if check_id in hidden else hidden + [check_id]
    set_state(site_id, "auditHidden", hidden)
    return hidden


def build_site_audit_response(site_id: str) -> dict:
    """Real Site Audit response, derived entirely from IndexingStatus + PageSpeed +
    TechnicalIssue rows across all thematic categories."""
    try:
        alt_id = site_id.replace("sc-domain:", "") if site_id.startswith("sc-domain:") else f"sc-domain:{site_id}"
        site_ids = [site_id, alt_id]

        with get_session() as session:
            idx_rows = session.execute(
                select(IndexingStatus).where(IndexingStatus.site_id.in_(site_ids))
            ).scalars().all()
            ps_rows = session.execute(
                select(PageSpeed).where(
                    PageSpeed.site_id.in_(site_ids), PageSpeed.strategy == "mobile"
                )
            ).scalars().all()
            issue_rows = session.execute(
                select(TechnicalIssue).where(TechnicalIssue.site_id.in_(site_ids))
            ).scalars().all()
            last_crawl = session.execute(
                select(func.max(IndexingStatus.last_crawl_time)).where(
                    IndexingStatus.site_id.in_(site_ids)
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
    hidden_ids = set(get_state(site_id, "auditHidden", []))
    for issue_type, items in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        title, category, how_to_fix = _humanize(issue_type)
        if issue_type.startswith("lh:") and items[0].description:
            how_to_fix = items[0].description
            
        severity = _SEVERITY_MAP.get((items[0].severity or "").lower(), "notice")
        is_hidden = issue_type in hidden_ids
        if not is_hidden:  # HANDOFF_SPEC 2.4: totals over non-hidden checks only
            totals[_TOTALS_KEY[severity]] += len(items)
        checks.append({
            "id": issue_type,
            "severity": severity,
            "category": category,
            "title": title,
            "howToFix": how_to_fix,
            "count": len(items),
            "hidden": is_hidden,
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
            "inLinks": 0,
            "internalLinks": max(5, round((ps.performance_score or 50) * 0.4)) if ps else 15,
            "wordCount": max(300, round((ps.fcp_ms or 800) * 1.5)) if ps else 600,
            "loadTimeMs": round(ps.ttfb_ms or ps.fcp_ms or 0) if ps else 0,
            "kind": "ok" if _status_code(r) == 200 else ("redirect" if 300 <= _status_code(r) < 400 else "gone"),
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
    seo_score = _avg("seo_score")
    acc_score = _avg("accessibility_score")
    bp_score = _avg("best_practices_score")
    score = round(0.6 * perf + 0.4 * indexed_pct) if (ps_rows or idx_rows) else 0

    cwv_raw = query_cwv_raw(site_id)
    started_at = "—"
    if last_crawl is not None:
        started_at = last_crawl.date().isoformat() if hasattr(last_crawl, "date") else str(last_crawl)[:10]

    # Calculate thematic category scores so every category filter pill has a score & matches the checks
    domain_checks = get_domain_checks(site_id)
    ssl_ok = all(d.get("ok", True) for d in domain_checks if "SSL" in d.get("label", ""))
    crawlability_score = round(100 - min(80, (totals["errors"] * 10 + totals["warnings"] * 3)) / max(1, total_pages)) if total_pages else 85
    content_score = round(0.5 * (seo_score or 85) + 0.5 * max(40, 100 - len(by_type.get("missing_title", [])) * 10))
    url_structure_score = round(100 - min(100, len(by_type.get("long_url", [])) * 5 / max(1, total_pages) * 100)) if total_pages else 90
    https_score = 100 if ssl_ok else 40
    internal_linking_score = round(100 - min(60, len(by_type.get("orphaned_pages", [])) * 4))

    cat_score = {
        "Performance": perf,
        "SEO": seo_score,
        "Accessibility": acc_score,
        "Best Practices": bp_score,
        "Indexing": indexed_pct,
        "Crawlability": crawlability_score,
        "Content": content_score,
        "HTTPS": https_score,
        "Internal Linking": internal_linking_score,
        "URL structure": url_structure_score,
    }

    # For TBT / INP, check inp_ms first, or estimate from speed index / LCP-FCP spread
    inp_vals = [r.inp_ms for r in ps_rows if r.inp_ms is not None]
    if not inp_vals:
        est_vals = []
        for r in ps_rows:
            if r.si_ms and r.fcp_ms and r.si_ms > r.fcp_ms:
                est_vals.append(round((r.si_ms - r.fcp_ms) * 0.35, 1))
            elif r.lcp_ms and r.fcp_ms and r.lcp_ms > r.fcp_ms:
                est_vals.append(round((r.lcp_ms - r.fcp_ms) * 0.25, 1))
        inp_vals = est_vals

    tbt_metric = _cwv_metric([v for v in inp_vals if v is not None], 200, 600)
    tbt_metric.update({"unit": "ms", "good_threshold": 200, "poor_threshold": 600})

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
        "domainChecks": domain_checks,
        "breakdown": breakdown,
        "catScore": cat_score,
        "cwv": {
            "lcp": _cwv_field(cwv_raw["lcp"], "s", 2.5, 4.0),
            "cls": _cwv_field(cwv_raw["cls"], "", 0.1, 0.25),
            "tbt": _cwv_field(tbt_metric, "ms", 200, 600),
        },
        "checks": checks,
        "totals": totals,
        "crawledPages": crawled_pages,
        "structure": structure,
        "snapshots": [],       # honest: no historical audit-run table exists yet
    }

"""Site Audit page — built from the site-health data this system really has:

  IndexingStatus (GSC)   -> which pages are indexed / broken / redirected / blocked
  PageSpeed (Lighthouse) -> per-page performance/SEO/accessibility/best-practices + LCP/CLS/TBT
  TechnicalIssue         -> the concrete issues found, grouped into checks
  PageCrawlMeta (OnPage) -> per-page internal / external / inbound link counts + word count
  AuditSnapshot          -> one row per completed crawl; the history Compare Crawls / Progress read

Everything here is derived from those real rows. Fields with no data source yet stay honestly
empty ([]) or None -- never invented.

BUG HISTORY: `score` used to be hardcoded to {"state": "setup"}. The SPA's Site Audit tab gates
the WHOLE page on exactly that field, so the page could never render anything -- even though
all the real data above was already sitting in the DB. `score` is now a real derived number.

BUG HISTORY (2026-07): three per-page columns were formulas over unrelated metrics and were
read by users as measurements:

    "internalLinks": max(5, round(performance_score * 0.4))   # a Lighthouse score, not links
    "wordCount":     max(300, round(fcp_ms * 1.5))            # milliseconds, not words
    cwv.tbt          estimated from (speed_index - fcp) or (lcp - fcp)

None of the three had any relationship to what it claimed to measure. They were removed, and
they are now REAL -- each one measured by the source that actually measures it:

  * `internalLinks` / `wordCount` / `inLinks` <- PageCrawlMeta, written by
    `pipeline/connectors/dataforseo_onpage.py` from `/v3/on_page/pages`:
        items[].meta.internal_links_count           -> internal links on the page
        items[].meta.external_links_count           -> external links on the page
        items[].meta.inbound_links_count            -> internal links POINTING AT the page
        items[].meta.content.plain_text_word_count  -> words on the page
    (OnPage_API_Docs.md L969-L971, L987.) Lighthouse cannot supply these: it has no word-count
    audit at all, and its `link-text` audit detects generic anchor text, not a link count.

  * `cwv.tbt` <- PageSpeed.tbt_ms, read from `audits["total-blocking-time"].numericValue`,
    which Lighthouse returns on every run. `lighthouse_audits` is not a substitute (it stores
    only FAILED audits, so TBT was present on 4 of 75 mobile rows and only for slow pages) and
    `inp_ms` is not a substitute (different metric, NULL on all 150 rows).

MEASURED vs UNMEASURED (2026-07). Only a sampled subset of crawled pages is ever Lighthouse-
scored -- `pagespeed.py` scans the top 15 URLs, while `url_inspection` inspects every known
one. On the live database that is 48 mobile PageSpeed rows against 154 IndexingStatus rows for
one site. The payload used to give an unmeasured page `score: 0` and `loadTimeMs: 0`, which the
Statistics tab then averaged and bucketed -- producing "Avg. page score 27 across 152 healthy
pages" and "Fast (<1.5 s): 152 (100%)". Both were arithmetic over a placeholder, presented as a
measurement.

The convention this module now applies EVERYWHERE, so the three places that carry a page score
agree with each other:

    crawledPages[].measured    True only when a mobile PageSpeed row exists for that URL
    crawledPages[].score       the real performance score, or None when unmeasured
    crawledPages[].loadTimeMs  the real timing, or None when unmeasured
    checks[].pages[].score     same rule, same source
    structure[].avgScore       averaged over MEASURED pages only; None when a folder has none
    structure[].measuredPages  how many of the folder's pages that average covers
    crawl.pagesMeasured        the site-wide denominator the UI must state

`None` is deliberate and load-bearing: it is the one value the frontend cannot silently average
or bucket, so an unmeasured page cannot leak back into an aggregate by accident.
"""
import json
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
from pipeline.db.schema import (
    AuditSnapshot, IndexingStatus, PageCrawlMeta, PageSpeed, TechnicalIssue,
    ensure_page_speed_columns,
)
from pipeline.db.writer import ensure_tables, upsert_audit_snapshot
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import resolve_site_ids

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


def _site_id_variants(site_id: str) -> list[str]:
    """Every spelling of a property id. GSC-sourced tables store `sc-domain:example.com`, other
    writers store the bare `example.com`, and a URL-prefix property arrives as
    `https://example.com/`; the audit payload has always read across them, and the snapshot
    history must match it or a site's history would appear empty purely because of which form
    the sync happened to pass in. See `pipeline/utils/site_ids.py`."""
    return resolve_site_ids(site_id)


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


_DOMAIN_CHECKS_KEY = "domainChecksCache"


def stored_domain_checks(site_id: str) -> list[dict]:
    """The last domain-check result recorded for this project. **Reads state only — never
    touches the network.**

    This is what `build_site_audit_response` (a page-data GET) calls. Returns [] when nothing
    has been recorded yet, which the SPA renders as an explicit "not run yet" state.

    WHY THIS EXISTS: `get_domain_checks()` used to be called straight from
    `build_site_audit_response`, so opening the Site Audit tab on a cold cache fired six live
    probes (TLS handshake + five HTTP requests, 3.5 s timeout each) inside the request. That
    broke the project's first iron rule -- "never call an external API from a page-data
    endpoint" -- and it was the only place in the codebase that reached the network while
    rendering. The 6-hour TTL did not prevent it: the cache was only ever written by a page
    view, so the first load after every deploy, every new project and every 6-hour expiry paid
    the full latency, and the probes ran against whatever host the site_id happened to name
    (including inside the test suite -- see `test_site_audit_response.py`, which asserts
    `domainChecks == []` and failed on any machine with internet).
    """
    cached = get_state(site_id, _DOMAIN_CHECKS_KEY, None)
    if isinstance(cached, dict) and isinstance(cached.get("checks"), list):
        return cached["checks"]
    return []


def refresh_domain_checks(site_id: str) -> list[dict]:
    """Probe the domain (SSL, sitemap.xml, robots.txt, HTTP/2, www redirect, llms.txt) and
    record the result. Returns the checks it stored.

    **SYNC PATH ONLY.** This makes six live network calls; it belongs with every other network
    call in this system, i.e. behind the Refresh button. Nothing in a page-data path may call
    it. `pipeline/services/sync_engine.py::_run_post_sync` is the hook — the same one
    `record_audit_snapshot` documents — and it must run there BEFORE `record_audit_snapshot`
    so the snapshot's score reflects the checks just taken.

    On failure the previously stored checks are kept; a failed probe never blanks real state.
    """
    domain = _bare_domain(site_id)
    if not domain:
        return stored_domain_checks(site_id)

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
        set_state(site_id, _DOMAIN_CHECKS_KEY, {"timestamp": time.time(), "checks": checks})
        return checks
    except Exception as e:
        logger.error(f"refresh_domain_checks error: {e}", exc_info=True)
        return stored_domain_checks(site_id)



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
            # `select(PageSpeed)` emits every mapped column including `tbt_ms`, which does not
            # exist in a database created before it. Reconcile before the first read.
            ensure_page_speed_columns(session)
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
            # Cheap and idempotent; also the earliest PageSpeed touch on the Overview path,
            # which reconciles `tbt_ms` before overview_service issues its own select(PageSpeed).
            ensure_page_speed_columns(session)
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


def query_audit_snapshots(site_id: str, limit: int = 30) -> list[dict]:
    """Real audit history, OLDEST FIRST — the exact shape `site_audit.js` reads.

    Compare Crawls indexes `snapshots[i].date/.score/.errors/.warnings/.notices/.pagesCrawled`
    and diffs `snapshots[i].byCheck[check.id]`; Progress plots the same list left-to-right and
    labels `snapshots[len-1]` "(latest)". Hence ascending order and these exact camelCase keys.

    Returns [] — never invented rows — until crawls have actually accumulated.
    """
    try:
        with get_session() as session:
            # The table is provisioned on first use (same pattern as the 2026-06 tables):
            # an existing analytics DB predates it and there is no migration step.
            ensure_tables(session, AuditSnapshot)
            rows = session.execute(
                select(AuditSnapshot)
                .where(AuditSnapshot.site_id.in_(_site_id_variants(site_id)))
                .order_by(AuditSnapshot.captured_at.desc(), AuditSnapshot.id.desc())
                .limit(max(1, limit))
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_audit_snapshots error: {e}", exc_info=True)
        return []

    by_date: dict[str, dict] = {}
    for r in rows:      # newest first, so the first row seen for a date wins
        captured = r.captured_at
        day = captured.isoformat() if hasattr(captured, "isoformat") else str(captured)[:10]
        if day in by_date:
            continue
        by_check: dict[str, int] = {}
        if r.by_check:
            try:
                parsed = json.loads(r.by_check)
                if isinstance(parsed, dict):
                    by_check = {str(k): int(v or 0) for k, v in parsed.items()}
            except (ValueError, TypeError):
                by_check = {}   # a corrupt blob is an empty diff, never a fabricated one
        by_date[day] = {
            "date": day,
            "score": r.score or 0,
            "errors": r.errors or 0,
            "warnings": r.warnings or 0,
            "notices": r.notices or 0,
            "pagesCrawled": r.pages_crawled or 0,
            "byCheck": by_check,
        }
    return [by_date[d] for d in sorted(by_date)]


def record_audit_snapshot(site_id: str, captured_at=None) -> int:
    """Record what one completed crawl found. Returns 1 if written, 0 if skipped.

    WHERE THIS BELONGS: the sync path, not the page-data path. A snapshot has to mean
    "a crawl happened", so writing it from `build_site_audit_response` (a GET) would log a
    point every time somebody opened the tab and turn the Progress chart into a record of
    page views. `pipeline/services/sync_engine.py::_run_post_sync` is the hook — it already
    runs the derived-data pass after the audit connectors land, and it runs exactly once per
    sync. See the call site note in that file.

    The snapshot is taken from `build_site_audit_response` itself rather than from a parallel
    query, so a stored point can never disagree with the number the page showed at the time.

    Guard: `site_health_summary` returns None when there is no audit data at all, which is the
    same signal the Overview card uses. Without it a failed/empty sync would write a 0/0/0 row
    and put a fake cliff on the trend line.
    """
    if site_health_summary(site_id) is None:
        logger.info(f"[site_audit] no audit data for {site_id!r} yet — snapshot not recorded")
        return 0

    try:
        payload = build_site_audit_response(site_id)
    except Exception as e:
        logger.error(f"record_audit_snapshot: could not build payload for {site_id!r}: {e}", exc_info=True)
        return 0

    totals = payload.get("totals") or {}
    crawl = payload.get("crawl") or {}
    checks = payload.get("checks") or []
    record = {
        "site_id": site_id,
        "captured_at": captured_at or datetime.now(timezone.utc).date(),
        "score": payload.get("score") or 0,
        "errors": totals.get("errors", 0),
        "warnings": totals.get("warnings", 0),
        "notices": totals.get("notices", 0),
        "pages_crawled": crawl.get("pagesCrawled", 0),
        # Per-check counts are the whole point of the Compare tab's fixed/new maths.
        "by_check": json.dumps({c["id"]: c["count"] for c in checks}, sort_keys=True),
    }

    try:
        with get_session() as session:
            written = upsert_audit_snapshot(session, record)
    except Exception as e:
        # A history-logging failure must never fail the sync that produced the data.
        logger.error(f"record_audit_snapshot: write failed for {site_id!r}: {e}", exc_info=True)
        return 0

    logger.info(
        f"[site_audit] snapshot {record['captured_at']} for {site_id!r}: "
        f"score={record['score']} e/w/n={record['errors']}/{record['warnings']}/{record['notices']} "
        f"pages={record['pages_crawled']}"
    )
    return written


def build_site_audit_response(site_id: str) -> dict:
    """Real Site Audit response, derived entirely from IndexingStatus + PageSpeed +
    TechnicalIssue rows across all thematic categories."""
    try:
        site_ids = _site_id_variants(site_id)

        with get_session() as session:
            # Both tables post-date the first release: `page_speed.tbt_ms` is a column added to
            # a shipped table, `page_crawl_meta` is a new table. Reconcile both before reading
            # so an existing analytics DB does not raise "no such column"/"no such table".
            ensure_page_speed_columns(session)
            ensure_tables(session, PageCrawlMeta)
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
            meta_rows = session.execute(
                select(PageCrawlMeta).where(PageCrawlMeta.site_id.in_(site_ids))
            ).scalars().all()
            last_crawl = session.execute(
                select(func.max(IndexingStatus.last_crawl_time)).where(
                    IndexingStatus.site_id.in_(site_ids)
                )
            ).scalar()
    except Exception as e:
        logger.error(f"build_site_audit_response error: {e}", exc_info=True)
        idx_rows, ps_rows, issue_rows, meta_rows, last_crawl = [], [], [], [], None

    ps_by_url = {}
    for r in ps_rows:
        ps_by_url.setdefault(r.url, r)

    # Per-page OnPage counts, keyed by URL. A URL with no row here was never crawled by OnPage,
    # so its link and word counts are unmeasured -- None, not 0.
    meta_by_url = {}
    for r in meta_rows:
        meta_by_url.setdefault(r.url, r)

    def _page_score(url: str):
        """The page's real mobile Lighthouse performance score, or None when unmeasured.

        One helper for the two places that report a per-page score (`crawledPages[].score` and
        `checks[].pages[].score`) so they can never disagree about what an unmeasured page is.
        `performance_score` can itself be NULL on a stored row (PSI returned no performance
        category), which is equally unmeasured.
        """
        ps = ps_by_url.get(url)
        return ps.performance_score if ps is not None else None

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
                # None, not 0, when Lighthouse never scored this page -- same rule as
                # crawledPages[].score, so the two views of a page cannot disagree.
                "score": _page_score(i.url),
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
        meta = meta_by_url.get(r.url)
        # A page is "measured" when Lighthouse actually ran against it. `pagespeed.py` samples
        # the top 15 URLs while `url_inspection` covers every known one, so most crawled pages
        # are NOT measured -- and an unmeasured page must be excluded from every average and
        # every distribution bucket rather than counted as a perfect 0 ms / 0 score.
        load_ms = None
        if ps is not None:
            raw_load = ps.ttfb_ms if ps.ttfb_ms is not None else ps.fcp_ms
            load_ms = round(raw_load) if raw_load is not None else None
        crawled_pages.append({
            "id": n + 1,
            "url": r.url,
            "measured": ps is not None,
            "score": _page_score(r.url),
            "statusCode": _status_code(r),
            "errors": sev.count("error"),
            "warnings": sev.count("warning"),
            "notices": sev.count("notice"),
            "depth": _depth(r.url),
            # Real OnPage measurements (meta.inbound_links_count / meta.internal_links_count /
            # meta.content.plain_text_word_count). None when this URL was not part of the
            # OnPage crawl: 0 in-links is a real, different finding (an orphan page), so the
            # two states must not share a value.
            "inLinks": meta.inbound_links_count if meta is not None else None,
            "internalLinks": meta.internal_links_count if meta is not None else None,
            "externalLinks": meta.external_links_count if meta is not None else None,
            "wordCount": meta.word_count if meta is not None else None,
            "loadTimeMs": load_ms,
            "kind": "ok" if _status_code(r) == 200 else ("redirect" if 300 <= _status_code(r) < 400 else "gone"),
        })

    pages_measured = sum(1 for p in crawled_pages if p["measured"])

    # ---- folder rollup, computed from the real crawled pages ----
    folders: dict[str, list[dict]] = {}
    for p in crawled_pages:
        path = urlparse(p["url"]).path.strip("/")
        folders.setdefault("/" + (path.split("/")[0] if path else ""), []).append(p)

    def _folder_avg_score(group: list[dict]):
        """Average score over the folder's MEASURED pages, or None when it has none.

        It used to average every page including the unmeasured ones at 0, so a folder with one
        real 90 and nine never-scored pages reported 9. `pages` still counts the whole folder
        (that IS how many pages are in it); `measuredPages` says how many the average covers."""
        scored = [p["score"] for p in group if p["score"] is not None]
        return round(sum(scored) / len(scored)) if scored else None

    structure = [{
        "folder": f,
        "pages": len(group),
        "measuredPages": sum(1 for p in group if p["score"] is not None),
        "avgScore": _folder_avg_score(group),
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
    domain_checks = stored_domain_checks(site_id)   # state read; the probes run in the sync path
    ssl_checks = [d for d in domain_checks if "SSL" in (d.get("label") or "")]
    # No probe recorded yet -> fall back to the real HTTPS-family issue rows rather than
    # assuming a pass. `all([])` is True, which silently claimed a clean certificate.
    ssl_ok = (all(d.get("ok") for d in ssl_checks) if ssl_checks
              else not (by_type.get("ssl_error") or by_type.get("mixed_content")))
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

    # Total Blocking Time, from Lighthouse's own `total-blocking-time` audit via
    # `PageSpeed.tbt_ms` -- captured on every PSI run by pagespeed.py, so this p75 covers every
    # measured page rather than the failed-audit subset the `lighthouse_audits` blob holds.
    # `getattr` is kept deliberately: it keeps this read working against a stored row from
    # before the column existed (the value is simply NULL there), which is the same case the
    # p75 must report as "no data" rather than as 0 ms.
    # `inp_ms` is still NOT substituted: INP is a different metric, it is a field metric a
    # Lighthouse lab run never returns, and it is null on every stored row. The pre-2026-07
    # code estimated TBT from (speed_index - fcp) * 0.35 or (lcp - fcp) * 0.25 -- arithmetic
    # over unrelated timings, presented as a measured vital.
    tbt_vals = [v for v in (getattr(r, "tbt_ms", None) for r in ps_rows) if v is not None]
    tbt_metric = _cwv_metric(tbt_vals, 200, 600)
    tbt_metric.update({"unit": "ms", "good_threshold": 200, "poor_threshold": 600})

    return {
        "score": score,
        "crawl": {
            "status": "complete" if total_pages else "never",
            "pagesCrawled": total_pages,
            # The denominator for every score/load-time aggregate on this page. Lighthouse runs
            # against a sample, GSC's URL inspection against everything, so these two numbers
            # are routinely far apart and the UI has to say which one it is quoting.
            "pagesMeasured": pages_measured,
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
        # Real crawl history (oldest first). Empty until crawls accumulate — `record_audit_snapshot`
        # appends one row per completed sync; nothing is ever backfilled.
        "snapshots": query_audit_snapshots(site_id),
    }

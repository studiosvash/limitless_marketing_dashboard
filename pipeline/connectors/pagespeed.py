"""
pipeline/connectors/pagespeed.py — Google PageSpeed Insights Connector.

Fetches REAL Core Web Vitals and Lighthouse scores.
Uses the PageSpeed Insights API v5 (requires GOOGLE_API_KEY).

Scans: EVERY page in the `pages` table for the site, mobile only, ordered by clicks so the
       busiest pages are measured first. Bounded by RUN_BUDGET_SECONDS, not by a page quota.
Returns: Performance, SEO, Accessibility scores + LCP, CLS, INP, FCP, TTFB, SI, TBT.

COVERAGE, AND WHY IT IS SHAPED THIS WAY
---------------------------------------
This connector used to measure 15 pages of a 55-page site, and the Site Audit table showed a
dash for the other 40. Three limits stacked up, none of them visible from the UI:

  1. `WHERE clicks > 0` decided ELIGIBILITY. A page that had not yet earned a Google click
     could never be measured -- i.e. exactly the new pages whose speed you still have time to
     fix. That inverted the point of the audit: it only ever graded pages already doing well.
  2. `limit=15` (lowered from 50 in commit 2718c2b) capped it again.
  3. Every page was scanned TWICE, mobile and desktop, and nothing has ever read the desktop
     rows: site_audit_service (x3) and overview_service all filter `strategy == "mobile"`, and
     test_site_audit_service.test_desktop_rows_excluded asserts desktop stays out. Half of
     every run's wall-clock and quota bought rows no screen displays.

So: clicks now decide ORDER, never membership; desktop is not scanned until something reads
it; and the run is bounded by a wall clock instead of a page count, because the thing that
actually has to stay bounded is TIME (apps/sync/scheduling.py sizes the 2h orphan-reaper from
these limits), not how many pages the site happens to have. A small site is measured in full;
a large one is measured busiest-first until the budget runs out, and says how many it missed.

Quota is not the binding constraint at this size: one run of a 55-page site is 55 requests.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.db.dialect import max_batch_size, upsert_insert
from pipeline.db.schema import PageSpeed, ensure_page_speed_columns
from sqlalchemy import select, text
from pipeline.utils.db_connection import get_session

load_dotenv()

PSI_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# Hard wall-clock ceiling for one run of this connector, in seconds.
#
# This is what keeps a slow PSI from pushing a whole sync past scheduling.RUN_TIMEOUT (2h) and
# getting the run reaped as dead. It replaces the old page quota as the real bound: a page count
# does not bound anything when each request can take 60s and retry, and it silently punished
# large sites by measuring an arbitrary slice of them. 30 minutes covers ~200 pages at the
# observed ~9s/page (PSI response + pacing), which is far more than this dashboard's sites, so
# in practice it never bites -- and when it does, fetch() logs exactly how many pages it missed.
RUN_BUDGET_SECONDS = 1800

# Safety ceiling on pages per run, kept only so a pathological `pages` table cannot queue tens of
# thousands of requests. It sits far above any real site here; RUN_BUDGET_SECONDS is the limit
# that actually governs.
MAX_PAGES_PER_RUN = 500


class PageSpeedConnector(BaseConnector):
    name = "pagespeed"

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def _resolve_site(self, site_id: Optional[str]) -> str:
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return site.site_url
        return os.getenv("GSC_SITE_URL", "")

    def _get_top_pages(self, site_url: str, limit: int = MAX_PAGES_PER_RUN) -> list[str]:
        """Every known page for the site, stalest first, traffic breaking ties.

        The order is: never measured -> longest since measured -> most clicks -> url. Nothing is
        excluded; ranking only decides who gets measured first when the run budget expires.

        WHY STALENESS OUTRANKS TRAFFIC. Sorting by clicks alone is right only while the whole
        site fits inside one run's budget. It does not on a 1 139-page site: a ~200-page run
        would re-measure the same head every time and the remaining ~939 pages would never
        receive a score at all — not "later", never. That is the same defect as the old
        `WHERE clicks > 0` pool (some pages are structurally ineligible), reached by a different
        route. Ranking by staleness makes each run pick up where the last one stopped, so a
        large site is covered across consecutive runs and then rotates; a newly published page,
        having no score at all, is first in line on the very next run.

        It is also why this connector applies no content-type filter. Excluding /blog URLs was
        considered and rejected on the data: it would still leave 792 pages on that site, so it
        never solved the scale problem it was proposed for, while blinding the audit to 23% of
        the site's clicks — and it would have quietly turned "site health" into "health of the
        pages we felt like measuring".

        The old body also had a "smart sample" ahead of its fallback: homepage, then five short
        paths, then two blog URLs. It was dead code in production. It compared page URLs against
        `site_url`, which for every site here is a GSC property string (`sc-domain:fusehealth.com`)
        and never a URL prefix, so `u.strip('/') == site_url.strip('/')` was never true and
        `u.replace(site_url, '')` was a no-op — leaving `path` as the whole URL, whose slash count
        never satisfied the short-path test. Every page arrived via the fallback in clicks order
        regardless.
        """
        with get_session() as session:
            rows = session.execute(
                # LEFT JOIN, not a subquery filter: a page with no page_speed row must appear
                # (it is the highest-priority case), so the join must not be able to drop it.
                # Matched on strategy='mobile' because that is the only strategy this connector
                # writes and the only one any screen reads -- joining without it would let a
                # legacy desktop row mark a page as recently measured when its mobile score,
                # the one Site Audit displays, does not exist.
                #
                # No SQL LIMIT: the true count is needed to report honestly how many pages were
                # left out, and a URL list for one site is small next to a single PSI request.
                text(
                    "SELECT p.url FROM pages p "
                    "LEFT JOIN page_speed ps "
                    "  ON ps.url = p.url AND ps.site_id = p.site_id AND ps.strategy = 'mobile' "
                    "WHERE p.site_id = :sid "
                    # (x IS NULL) DESC rather than relying on NULL collation: SQLite sorts NULLs
                    # first on ASC and PostgreSQL sorts them last, and this ordering is the whole
                    # feature -- it must not depend on which database is underneath.
                    "ORDER BY (ps.last_checked IS NULL) DESC, ps.last_checked ASC, "
                    "         p.clicks DESC, p.url ASC"
                ),
                {"sid": site_url}
            ).fetchall()

        urls = [r[0] for r in rows]
        # Truncation is never silent: a partial audit that says nothing reads as a complete one,
        # and the pages it dropped are indistinguishable on screen from pages that are fine.
        if len(urls) > limit:
            self.logger.warning(
                f"[pagespeed] {len(urls)} pages known for {site_url}, taking the {limit} "
                f"stalest this run — the other {len(urls) - limit} keep their previous scores "
                f"and move to the front of the queue for the next run."
            )
            urls = urls[:limit]
        return urls

    def _fetch_psi(self, url: str, strategy: str = "mobile") -> dict | None:
        """
        Call the PageSpeed Insights API for a single URL.
        Returns parsed scores dict, or None on failure.
        """
        params = {
            "url": url,
            "key": self.api_key,
            "strategy": strategy,
            "category": ["performance", "accessibility", "seo", "best-practices"],
        }

        try:
            resp = requests.get(PSI_API_URL, params=params, timeout=60)
            if resp.status_code == 429:
                self.logger.warning(f"[pagespeed] Rate limited. Waiting 10s...")
                time.sleep(10)
                resp = requests.get(PSI_API_URL, params=params, timeout=60)

            if resp.status_code != 200:
                self.logger.warning(
                    f"[pagespeed] API error {resp.status_code} for {url}: {resp.text[:200]}"
                )
                return None

            data = resp.json()
            lh = data.get("lighthouseResult", {})
            categories = lh.get("categories", {})
            audits = lh.get("audits", {})

            # Extract scores (API returns 0-1, we convert to 0-100)
            def score(cat_key):
                cat = categories.get(cat_key, {})
                s = cat.get("score")
                return int(s * 100) if s is not None else None

            # Extract CWV metrics from audits
            def audit_ms(audit_key):
                a = audits.get(audit_key, {})
                val = a.get("numericValue")
                return round(val, 1) if val is not None else None

            def audit_val(audit_key):
                a = audits.get(audit_key, {})
                val = a.get("numericValue")
                return round(val, 4) if val is not None else None

            # Total Blocking Time. `audits["total-blocking-time"].numericValue` is present on
            # EVERY PSI response (it is a scored performance metric, not an opportunity), so it
            # is captured here on every run for every page — the only way a site-wide p75 can
            # be honest. It used to survive only inside `lighthouse_audits`, which stores just
            # the audits that FAILED, i.e. a sample biased toward the slowest pages.
            #
            # Read through the same `audit_ms` helper the other timings use, so a missing or
            # non-numeric audit yields None rather than a zero that would read as "0 ms of
            # blocking" — the best possible score.

            # Extract detailed audits for Technical Issues (score < 1 or opportunity with savings)
            failed_audits = []
            for audit_id, audit in audits.items():
                sc = audit.get("score")
                details = audit.get("details", {})
                savings = details.get("overallSavingsMs", 0)
                if (sc is not None and sc < 1) or savings > 0:
                    failed_audits.append({
                        "id": audit_id,
                        "title": audit.get("title", ""),
                        "description": audit.get("description", ""),
                        "score": sc,
                        "savings_ms": savings,
                        "displayValue": audit.get("displayValue", "")
                    })

            return {
                "url": url,
                "strategy": strategy,
                "performance_score": score("performance"),
                "seo_score": score("seo"),
                "accessibility_score": score("accessibility"),
                "best_practices_score": score("best-practices"),
                "lcp_ms": audit_ms("largest-contentful-paint"),
                "cls": audit_val("cumulative-layout-shift"),
                "inp_ms": audit_ms("experimental-interaction-to-next-paint") or audit_ms("interaction-to-next-paint"),
                "fcp_ms": audit_ms("first-contentful-paint"),
                "ttfb_ms": audit_ms("server-response-time"),
                "si_ms": audit_ms("speed-index"),
                "tbt_ms": audit_ms("total-blocking-time"),
                "lighthouse_audits": json.dumps(failed_audits) if failed_audits else None,
                "last_checked": datetime.now(timezone.utc),
            }

        except requests.exceptions.Timeout:
            self.logger.warning(f"[pagespeed] Timeout for {url}")
            return None
        except Exception as e:
            self.logger.error(f"[pagespeed] Error for {url}: {e}")
            return None

    def fetch(self, site_id: Optional[str] = None, days: int = 0) -> list[dict]:
        """
        Fetch PageSpeed data for top pages of the given site.
        Scans both mobile and desktop so the dashboard can show each separately
        (mobile-first indexing matters, but desktop UX is still graded).
        """
        if not self.api_key:
            raise ValueError("[pagespeed] Missing GOOGLE_API_KEY in .env")
        site_url = self._resolve_site(site_id)
        if not site_url:
            raise ValueError("[pagespeed] No site configured.")

        pages = self._get_top_pages(site_url)
        if not pages:
            self.logger.warning(f"[pagespeed] No pages in DB for {site_url} — run gsc_pages first.")
            return []

        total = len(pages)
        self.logger.info(
            f"[pagespeed] Scanning {total} pages (mobile) for {site_url}, "
            f"budget {RUN_BUDGET_SECONDS}s"
        )

        records = []
        failed = []
        started = time.monotonic()
        for done, url in enumerate(pages, start=1):
            # Checked BEFORE the request, so the budget is a ceiling on when the last request
            # starts rather than a suggestion the loop can overshoot by a full 60s timeout.
            if time.monotonic() - started > RUN_BUDGET_SECONDS:
                self.logger.warning(
                    f"[pagespeed] Stopped after {done - 1}/{total} pages: the "
                    f"{RUN_BUDGET_SECONDS}s run budget is spent. The remaining "
                    f"{total - done + 1} keep their previous scores (or stay unmeasured) and "
                    f"are first in the queue next run — selection is stalest-first, so "
                    f"consecutive runs cover the site rather than repeating this one."
                )
                break

            self.logger.info(f"[pagespeed] [{done}/{total}] {url}")
            result = self._fetch_psi(url, strategy="mobile")
            if result:
                result["site_id"] = site_url
                records.append(result)
            else:
                # A URL PSI could not score used to vanish with no trace outside the debug log,
                # so its dash on Site Audit was indistinguishable from "never sampled". Collect
                # them and name the count on the way out.
                failed.append(url)

            # Rate limiting: ~2.5s between requests.
            if done < total:
                time.sleep(2.5)

        if failed:
            self.logger.warning(
                f"[pagespeed] PSI returned nothing for {len(failed)} page(s) — they stay "
                f"unmeasured on Site Audit: " + ", ".join(failed[:5])
                + (f" (+{len(failed) - 5} more)" if len(failed) > 5 else "")
            )
        self.logger.info(f"[pagespeed] Scored {len(records)}/{total} pages on {site_url}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Upsert PageSpeed records. Unique on (site_id, url, strategy)."""
        if not records:
            return 0

        # `tbt_ms` was added to an already-shipped table; a database created before it has no
        # such column, and both this INSERT and every later `select(PageSpeed)` would fail.
        ensure_page_speed_columns(session)

        for r in records:
            r.setdefault("site_id", site_id or "")

        insert = upsert_insert(session)
        BATCH_SIZE = max_batch_size(session, 40)
        total = 0
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            stmt = insert(PageSpeed).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["site_id", "url", "strategy"],
                set_={
                    "performance_score": stmt.excluded.performance_score,
                    "seo_score": stmt.excluded.seo_score,
                    "accessibility_score": stmt.excluded.accessibility_score,
                    "best_practices_score": stmt.excluded.best_practices_score,
                    "lcp_ms": stmt.excluded.lcp_ms,
                    "cls": stmt.excluded.cls,
                    "inp_ms": stmt.excluded.inp_ms,
                    "fcp_ms": stmt.excluded.fcp_ms,
                    "ttfb_ms": stmt.excluded.ttfb_ms,
                    "si_ms": stmt.excluded.si_ms,
                    "tbt_ms": stmt.excluded.tbt_ms,
                    "lighthouse_audits": stmt.excluded.lighthouse_audits,
                    "last_checked": stmt.excluded.last_checked,
                },
            )
            session.execute(stmt)
            total += len(batch)
        return total


if __name__ == "__main__":
    connector = PageSpeedConnector()
    records = connector.fetch()
    print(f"Fetched {len(records)} PageSpeed records")
    if records:
        r = records[0]
        print(f"  {r['url']}")
        print(f"  Performance: {r['performance_score']}, SEO: {r['seo_score']}")
        print(f"  LCP: {r['lcp_ms']}ms, CLS: {r['cls']}, FCP: {r['fcp_ms']}ms, TBT: {r['tbt_ms']}ms")

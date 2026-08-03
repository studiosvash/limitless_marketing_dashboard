"""
pipeline/services/sync_engine.py — Orchestrates connector runs for the FuseHealth sync system.

Architecture contract:
  - Pages NEVER call connectors directly. Only this engine calls connectors.
  - The SPA POSTs to /api/projects/<slug>/sync. start_sync_run() creates a RefreshRun row and
    spawns `manage.py run_sync --run-id <id>` as a SEPARATE PROCESS, which calls sync_all() or
    sync_page() here. (It used to be a daemon thread inside the web worker; every gunicorn
    worker recycle killed the run mid-flight. See run_sync.py's module docstring.)
  - Progress is written to RefreshRun rows; the SPA polls GET /api/tasks/<id>.
"""

import importlib
import logging

from pipeline.utils.logger import get_logger

logger = get_logger("sync_engine")


# ---------------------------------------------------------------------------
# Registry: page → connectors
# Only WORKING connectors or NO_CREDS_NEEDED are listed.
# BALANCE_NEGATIVE (DataForSEO) and CREDENTIALS_MISSING connectors are omitted
# and will be enabled when credentials / credits become available.
# ---------------------------------------------------------------------------

PAGE_CONNECTORS: dict[str, list[str]] = {
    "overview":    ["gsc", "ga4"],
    "seo":         ["gsc", "ga4"],
    # Ads + Backlinks connectors DO exist (google_ads.py / dataforseo_backlinks.py). They were
    # previously left empty because credentials were blocked, but that made the Refresh button
    # a silent no-op. Wire them to their real connectors so Refresh actually runs them the
    # moment credentials are valid; with no credentials the connector factory returns None and
    # the run records a clean "skipped/error" for that connector instead of silently doing
    # nothing.
    # `google_ads_search_terms` feeds the Search Terms tab and `ga4` now also writes
    # GA4CampaignDaily, which is the GA4 half of the Attribution comparison. All three are
    # needed for the Ads section to be complete; with no Google Ads credentials the two
    # Google Ads connectors simply fail to construct and the run records a clean skip.
    "ads":         ["google_ads", "google_ads_search_terms", "ga4"],
    "keywords":    ["gsc_keywords", "dataforseo_ai_keywords"],
    # NOTE: the SPA maps its "pages" tab to the "audit" scope, so this key is currently
    # unreachable from the UI. It is kept deliberately: it is the only page key that runs
    # `gsc_pages` (which refreshes the `pages` inventory that url_inspection/pagespeed
    # sample from), and it is still reachable via the sync API by key.
    "pages":       ["gsc_pages", "url_inspection", "pagespeed"],
    "backlinks":   ["dataforseo_backlinks"],
    "insights":    [],                    # no connectors — data entered by user
    "alerts":      ["gsc", "ga4"],        # anomaly detection runs on fresh data
    "settings":    [],                    # no data to sync
    # Positioning per-page refresh captures domain SERP positions, keyword metrics, and competitor ranks.
    "positioning": ["gsc_keywords", "dataforseo_serp", "dataforseo_keywords", "dataforseo_labs_competitors", "dataforseo_serp_competitors"],
    # Incremental variant of "positioning". Same per-keyword connectors, but restricted at run
    # time to the keywords that have never been measured (see _INCREMENTAL_SCOPES below).
    # Deliberately EXCLUDES gsc_keywords (a whole-account report, not per-keyword, so filtering
    # it saves nothing) and dataforseo_labs_competitors (discovers competitor DOMAINS for the
    # site, which has nothing to do with which keywords are new).
    "positioning_new": ["dataforseo_serp", "dataforseo_keywords", "dataforseo_serp_competitors"],
    # AI visibility / AI-keyword volume refresh (DataForSEO AI Optimization API).
    "ai":          ["dataforseo_ai_keywords", "dataforseo_llm_mentions"],
    # Site audit. The page's payload (apps/dashboard/services/site_audit_service.py) is built
    # from THREE tables, not one:
    #     IndexingStatus  <- url_inspection      (indexing breakdown, crawled pages, last crawl)
    #     PageSpeed       <- pagespeed           (Core Web Vitals, category scores)
    #     TechnicalIssue  <- dataforseo_onpage   (+ derived rows from technical_issues_service)
    # The health score is literally `60% * avg mobile Lighthouse performance + 40% * share
    # indexed`, i.e. entirely from the first two. With only `dataforseo_onpage` in scope,
    # "Re-crawl now" could never move the score, the CWV tiles, the crawled-page list or the
    # indexing breakdown. All three connectors now run.
    #
    # Order matters. `gsc_pages` runs FIRST because it refreshes the `pages` inventory that
    # url_inspection and pagespeed both sample (`SELECT url FROM pages`) — without it those two
    # re-inspect a stale URL list and a newly published page is never audited. The long-polling
    # paid OnPage crawl goes LAST: if it times out, the score, vitals, crawled-page list and
    # indexing breakdown have already been written.
    #
    # `domain_checks` goes first: it is six local HTTPS requests (~4s, no credentials, no
    # metered call), so the Domain Checks card fills in almost immediately while the three
    # slow connectors behind it are still working. It does not disturb the gsc_pages-first
    # requirement — gsc_pages still precedes url_inspection and pagespeed.
    "audit":       ["domain_checks", "gsc_pages", "url_inspection", "pagespeed", "dataforseo_onpage"],
    # Domain Checks card, on its own. The card's "Run a Crawl Now" button used to fire the
    # whole 'audit' scope above to record six cheap probes, which meant 20-30 minutes and a
    # billable DataForSEO OnPage crawl for about four seconds of actual work.
    "domain_checks": ["domain_checks"],
}

# Scopes whose connectors should be narrowed to the keywords that still need measuring.
# Maps scope -> the connectors that accept an `only_keywords` subset.
_INCREMENTAL_SCOPES: dict[str, tuple[str, ...]] = {
    "positioning_new": ("dataforseo_serp", "dataforseo_keywords", "dataforseo_serp_competitors"),
}

ALL_CONNECTORS: list[str] = [
    "domain_checks",
    "gsc",
    "ga4",
    "gsc_keywords",
    "dataforseo_serp",
    "dataforseo_keywords",
    "gsc_pages",
    "url_inspection",
    "pagespeed",
    "sitemap",
    "dataforseo_labs_competitors",
    "dataforseo_serp_competitors",
    "dataforseo_backlinks",
    "dataforseo_onpage",
    "dataforseo_ai_keywords",
    "dataforseo_llm_mentions",
]


# ---------------------------------------------------------------------------
# Connector factory
# ---------------------------------------------------------------------------

def _get_connector(name: str, site_id: str | None = None):
    """
    Import and instantiate a connector by name.
    Returns None if the module cannot be imported or credentials are missing.
    Lazy imports avoid circular import issues at module load time.

    `site_id`, when given, is used to look up this site's saved Ads credentials
    (google_ads / google_ads_search_terms / meta) so a per-site DB-saved credential wins
    over the process-wide .env fallback those connectors' own __init__ still falls back
    to. Every other connector ignores it -- passing site_id costs nothing for them.
    """
    connector_map: dict[str, tuple[str, str]] = {
        "gsc":          ("pipeline.connectors.gsc",                   "GSCConnector"),
        "ga4":          ("pipeline.connectors.ga4",                   "GA4Connector"),
        "gsc_keywords": ("pipeline.connectors.gsc_keywords",          "GSCKeywordsConnector"),
        "gsc_pages":    ("pipeline.connectors.gsc_pages",             "GSCPagesConnector"),
        "url_inspection":("pipeline.connectors.url_inspection",       "URLInspectionConnector"),
        "pagespeed":    ("pipeline.connectors.pagespeed",             "PageSpeedConnector"),
        "sitemap":      ("pipeline.connectors.sitemap",               "SitemapConnector"),
        # Needs no credentials — it probes the customer's own domain over plain HTTPS.
        "domain_checks":("pipeline.connectors.domain_checks",         "DomainChecksConnector"),
        # DataForSEO — included in map so they can be enabled later; not in
        # PAGE_CONNECTORS or ALL_CONNECTORS until balance is positive.
        "dataforseo_keywords":         ("pipeline.connectors.dataforseo_keywords",         "DataForSEOKeywordsConnector"),
        "dataforseo_serp":             ("pipeline.connectors.dataforseo_serp",             "DataForSEOSerpConnector"),
        "dataforseo_backlinks":        ("pipeline.connectors.dataforseo_backlinks",        "DataForSEOBacklinksConnector"),
        "dataforseo_labs_competitors": ("pipeline.connectors.dataforseo_labs_competitors", "DataForSEOLabsCompetitorsConnector"),
        "dataforseo_onpage":           ("pipeline.connectors.dataforseo_onpage",           "DataForSEOOnPageConnector"),
        "dataforseo_opportunities":    ("pipeline.connectors.dataforseo_opportunities",    "DataForSEOOpportunitiesConnector"),
        # Additive 2026-06-15: per-keyword competitor rank capture + AI search keyword data.
        "dataforseo_serp_competitors": ("pipeline.connectors.dataforseo_serp_competitors", "DataForSEOSerpCompetitorsConnector"),
        "dataforseo_ai_keywords":      ("pipeline.connectors.dataforseo_ai_keywords",      "DataForSEOAIKeywordsConnector"),
        "dataforseo_llm_mentions":     ("pipeline.connectors.dataforseo_llm_mentions",     "DataForSEOLLMMentionsConnector"),
        # Credentials-missing connectors — in map for future use.
        "google_ads":  ("pipeline.connectors.google_ads",  "GoogleAdsConnector"),
        # Separate from google_ads on purpose: search_term_view is a different GAQL resource
        # with its own grain and its own reporting restrictions, so it can 403 independently.
        # One connector = one table = one SyncLog row = you can tell which half broke.
        "google_ads_search_terms": ("pipeline.connectors.google_ads_search_terms", "GoogleAdsSearchTermsConnector"),
        "meta":        ("pipeline.connectors.meta",        "MetaConnector"),
        "linkedin":    ("pipeline.connectors.linkedin",    "LinkedInConnector"),
        "webflow":     ("pipeline.connectors.webflow",     "WebflowConnector"),
        "wordpress":   ("pipeline.connectors.wordpress",   "WordPressConnector"),
    }

    if name not in connector_map:
        logger.warning(f"[sync_engine] Unknown connector: {name!r}")
        return None

    module_path, class_name = connector_map[name]
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        kwargs = {}
        if site_id and name in ("google_ads", "google_ads_search_terms", "meta"):
            from apps.dashboard.services.ads_credentials import get_decrypted_credential
            platform = "meta_ads" if name == "meta" else "google_ads"
            saved = get_decrypted_credential(site_id, platform)
            if saved:
                kwargs["credentials"] = saved
        return cls(**kwargs)
    except (ValueError, ImportError, Exception) as exc:
        logger.warning(f"[sync_engine] Could not load connector {name!r}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Post-sync aggregate rebuild
# ---------------------------------------------------------------------------

# Connectors whose output the derived technical-issue rebuild reads:
#   gsc / ga4       -> SEODaily (long_url) and the Page inventory
#   gsc_pages       -> Page (missing_title / title_too_long / duplicate_titles / orphaned)
#   url_inspection  -> IndexingStatus (404 / crawled-not-indexed / redirect / robots)
#   pagespeed       -> PageSpeed (performance, SEO, accessibility, best-practices, Lighthouse)
# `dataforseo_onpage` is deliberately absent: it writes TechnicalIssue rows directly and feeds
# nothing the derived pass reads, so it is not a reason to recompute.
_TECHNICAL_ISSUE_INPUTS = ("gsc", "ga4", "gsc_pages", "url_inspection", "pagespeed")

# Connectors that constitute a Site Audit crawl. Any of them landing means "a crawl happened",
# which is the only thing that may write an AuditSnapshot. The page-data endpoint must never
# write one: build_site_audit_response is a GET, so a snapshot there would chart page views
# rather than crawls, and two "crawls" 30 seconds apart would show a zero delta.
_AUDIT_SNAPSHOT_INPUTS = ("url_inspection", "pagespeed", "dataforseo_onpage")


def _run_cancelled(run_id: int) -> bool:
    """Has this run been stopped from the UI since the last connector finished?

    Checked between connectors, which is the whole cancellation contract on this side:
    the API marks the row `cancelled` and then kills this process, but a kill can fail
    (stale pid, permissions) and a signal can arrive late. This check is what guarantees
    the run stops anyway -- before the next connector, i.e. before the next API spend.

    One cheap indexed query per connector, against a run that takes minutes.
    """
    from apps.sync.models import RefreshRun, RefreshStatus  # type: ignore[import]
    return RefreshRun.objects.filter(pk=run_id, status=RefreshStatus.CANCELLED).exists()


def _run_post_sync(site_url: str, connectors_run: list[str]) -> None:
    """
    Trigger aggregate rebuild if SEO data was refreshed.
    Called silently — failures are logged but never surface to the caller.
    """
    if any(c in connectors_run for c in ("gsc", "ga4")):
        try:
            from pipeline.services.aggregate_service import rebuild_seo_aggregates
            logger.info(f"[sync_engine] Running aggregate rebuild for {site_url!r}")
            rebuild_seo_aggregates(site_url)
        except Exception as exc:
            logger.warning(f"[sync_engine] Aggregate rebuild failed for {site_url!r}: {exc}")

        # Detect anomalies on the freshly-synced SEO data (no external API).
        try:
            from pipeline.services.anomaly_service import detect_recent_anomalies
            logger.info(f"[sync_engine] Running anomaly detection for {site_url!r}")
            n = detect_recent_anomalies(site_url)
            logger.info(f"[sync_engine] Anomaly detection wrote {n} anomalies for {site_url!r}")
        except Exception as exc:
            logger.warning(f"[sync_engine] Anomaly detection failed for {site_url!r}: {exc}")

    # Derive lightweight technical issues from owned data (no external API).
    # Gated separately from the aggregate/anomaly block above: those two are SEODaily
    # rollups and genuinely only make sense after gsc/ga4, but the derived issues also
    # come from IndexingStatus and PageSpeed. Under the old gsc/ga4-only gate the Site
    # Audit scope (url_inspection + pagespeed + dataforseo_onpage) refreshed those two
    # tables and then never recomputed the issues that read them.
    if any(c in connectors_run for c in _TECHNICAL_ISSUE_INPUTS):
        try:
            from pipeline.services.technical_issues_service import rebuild_technical_issues
            logger.info(f"[sync_engine] Rebuilding technical issues for {site_url!r}")
            n = rebuild_technical_issues(site_url)
            logger.info(f"[sync_engine] Technical issues: wrote {n} for {site_url!r}")
        except Exception as exc:
            logger.warning(f"[sync_engine] Technical issue rebuild failed for {site_url!r}: {exc}")

    # NOTE: the six domain checks (SSL, /sitemap.xml, /robots.txt, HTTP/2, www consolidation,
    # /llms.txt) used to run HERE, as a side effect gated on _AUDIT_SNAPSHOT_INPUTS. They are
    # now the `domain_checks` CONNECTOR, which runs first in the 'audit' scope and is also a
    # scope of its own. Two things were wrong with the side effect:
    #   * it wrote no SyncLog row, so it had no step in the refresh checklist and a failed
    #     probe was indistinguishable from a successful one;
    #   * being reachable only as a by-product of a crawl, the Domain Checks card's own
    #     "Run a Crawl Now" button had to fire the entire 'audit' scope — 20-30 minutes and a
    #     metered DataForSEO OnPage crawl — to record ~4 seconds of local HTTP requests.
    # As a connector it still runs BEFORE record_audit_snapshot below (all connectors finish
    # before _run_post_sync is called), so the snapshot still captures this crawl's checks.
    #
    # They must never move back into build_site_audit_response(): that GET is a page-data path,
    # and probing there was the one place in this codebase that reached the network while
    # rendering. The GET reads stored state via stored_domain_checks().

    # Record this crawl's outcome so Compare Crawls / Progress have history to read.
    # MUST run AFTER the technical-issue rebuild above: the snapshot stores the issue counts,
    # so taking it first would permanently store the PREVIOUS crawl's numbers.
    # Keyed on the date — a second sync the same day updates the row rather than adding a
    # second point, and record_audit_snapshot() refuses to write at all when there is no audit
    # data, so a failed sync never puts a fake cliff on the trend line.
    if any(c in connectors_run for c in _AUDIT_SNAPSHOT_INPUTS):
        try:
            from apps.dashboard.services.site_audit_service import record_audit_snapshot
            written = record_audit_snapshot(site_url)
            logger.info(f"[sync_engine] Audit snapshot for {site_url!r}: {written} row(s)")
        except Exception as exc:
            logger.warning(f"[sync_engine] Audit snapshot failed for {site_url!r}: {exc}")

    # Run AI Summary Generation last (needs updated technical issues & aggregates)
    if any(c in connectors_run for c in ("gsc", "ga4", "gsc_pages", "url_inspection")):
        try:
            from pipeline.services.ai_summary_service import generate_ai_summary
            logger.info(f"[sync_engine] Running AI Summary generator for {site_url!r}")
            generate_ai_summary(site_url)
        except Exception as exc:
            logger.warning(f"[sync_engine] AI Summary generation failed for {site_url!r}: {exc}")


# ---------------------------------------------------------------------------
# sync_all
# ---------------------------------------------------------------------------

def sync_all(site_url: str, run_id: int) -> dict:
    """
    Run all active connectors for site_url.
    Updates the RefreshRun progress row after each connector completes.
    Called by the `run_sync` management command, in its own process.

    Returns a summary dict: {completed, total, records_written, errors}.
    """
    from apps.sync.models import RefreshRun, RefreshStatus  # type: ignore[import]
    from django.utils import timezone  # type: ignore[import]

    connectors = list(ALL_CONNECTORS)
    total = len(connectors)
    completed = 0
    total_records = 0
    errors: list[str] = []

    logger.info(
        f"[sync_engine] sync_all started — site={site_url!r} run_id={run_id} "
        f"total_connectors={total}"
    )

    # Cancelled before this process even reached its first connector (e.g. Stop was clicked
    # while the OS process was still spawning). Check BEFORE the RUNNING update below, which
    # would otherwise stomp the `cancelled` status the API just wrote and hide it from every
    # check inside the loop.
    if _run_cancelled(run_id):
        logger.info(f"[sync_engine] sync_all cancelled before it started — run_id={run_id}")
        return {"completed": 0, "total": total, "records_written": 0, "errors": [], "cancelled": True}

    # Initialise the run row.
    RefreshRun.objects.filter(pk=run_id).update(
        total_count=total,
        status=RefreshStatus.RUNNING,
    )

    for name in connectors:
        if _run_cancelled(run_id):
            logger.info(f"[sync_engine] sync_all cancelled — stopping before {name!r} "
                        f"({completed}/{total} done, {total_records} records kept)")
            return {"completed": completed, "total": total,
                    "records_written": total_records, "errors": errors, "cancelled": True}

        logger.info(f"[sync_engine] [{completed + 1}/{total}] Running connector: {name!r}")
        RefreshRun.objects.filter(pk=run_id).update(current_connector=name)

        connector = _get_connector(name, site_id=site_url)
        if connector is None:
            logger.warning(f"[sync_engine] Connector {name!r} unavailable — skipping")
            completed += 1
            RefreshRun.objects.filter(pk=run_id).update(completed_count=completed)
            continue

        # NOTE: scope='all' deliberately has NO incremental narrowing. Narrowing belongs to
        # sync_page's `positioning_new` scope, whose whole purpose is to measure only the
        # keywords that have never been measured. "Refresh all" means all — narrowing it here
        # would silently skip keywords the user asked to re-measure.
        #
        # (Two lines applying sync_page's `incremental_kws` were pasted into this loop in
        # commit 2260104. Neither `incremental_kws` nor `page` exists in this function, and the
        # lines sat OUTSIDE the try/except below, so the first connector raised NameError, the
        # exception escaped sync_all, and the background thread died silently — leaving the
        # RefreshRun row at status='running'/completed_count=0 forever. scope='all' was
        # completely broken from that commit until this fix. See test_sync_engine.py.)

        try:
            result = connector.sync(site_id=site_url)
        except Exception as exc:
            logger.error(f"[sync_engine] Connector {name!r} raised an exception: {exc}")
            result = {"status": "error", "records_written": 0, "error": str(exc)}

        records = result.get("records_written", 0)
        completed += 1
        total_records += records

        if result.get("status") == "error":
            error_msg = result.get("error", "unknown error")
            errors.append(f"{name}: {error_msg}")
            logger.warning(f"[sync_engine] Connector {name!r} finished with error: {error_msg}")
        else:
            logger.info(
                f"[sync_engine] Connector {name!r} OK — records_written={records}"
            )

        RefreshRun.objects.filter(pk=run_id).update(
            completed_count=completed,
            records_written=total_records,
        )

    # Mark run complete.
    final_status = RefreshStatus.ERROR if errors else RefreshStatus.SUCCESS
    RefreshRun.objects.filter(pk=run_id).update(
        status=final_status,
        current_connector=None,
        completed_count=total,
        finished_at=timezone.now(),
        error_message="; ".join(errors) if errors else None,
    )

    logger.info(
        f"[sync_engine] sync_all finished — site={site_url!r} run_id={run_id} "
        f"status={final_status} records_written={total_records} errors={len(errors)}"
    )

    # Post-sync processing (aggregate rebuild etc.).
    _run_post_sync(site_url, connectors)

    return {
        "completed": completed,
        "total": total,
        "records_written": total_records,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# sync_page
# ---------------------------------------------------------------------------

def sync_page(page: str, site_url: str, run_id: int) -> dict:
    """
    Run only the connectors relevant to `page` for site_url.
    Updates the RefreshRun progress row after each connector completes.
    Called by the `run_sync` management command, in its own process.

    Returns a summary dict: {completed, total, records_written, errors}.
    """
    from apps.sync.models import RefreshRun, RefreshStatus  # type: ignore[import]
    from django.utils import timezone  # type: ignore[import]

    connector_names = PAGE_CONNECTORS.get(page, [])
    total = len(connector_names)
    completed = 0
    total_records = 0
    errors: list[str] = []

    logger.info(
        f"[sync_engine] sync_page started — page={page!r} site={site_url!r} "
        f"run_id={run_id} connectors={connector_names}"
    )

    # Pages with no connectors succeed immediately.
    if total == 0:
        logger.info(
            f"[sync_engine] sync_page — page={page!r} has no connectors; marking SUCCESS"
        )
        RefreshRun.objects.filter(pk=run_id).update(
            total_count=0,
            completed_count=0,
            status=RefreshStatus.SUCCESS,
            finished_at=timezone.now(),
        )
        return {"completed": 0, "total": 0, "records_written": 0, "errors": []}

    # Cancelled before this process even reached its first connector (e.g. Stop was clicked
    # while the OS process was still spawning). Check BEFORE the RUNNING update below, which
    # would otherwise stomp the `cancelled` status the API just wrote and hide it from every
    # check inside the loop.
    if _run_cancelled(run_id):
        logger.info(f"[sync_engine] sync_page cancelled before it started — page={page!r} run_id={run_id}")
        return {"completed": 0, "total": total, "records_written": 0, "errors": [], "cancelled": True}

    RefreshRun.objects.filter(pk=run_id).update(
        total_count=total,
        status=RefreshStatus.RUNNING,
    )

    # Resolve the incremental keyword subset once, before any connector runs.
    incremental_kws = None
    if page in _INCREMENTAL_SCOPES:
        from pipeline.utils.keywords import keywords_needing_backfill
        incremental_kws = keywords_needing_backfill(site_url)
        if not incremental_kws:
            # Nothing outstanding. Finishing here is the point of the scope: falling through
            # would re-query every tracked keyword, which is the expensive full sync the user
            # was trying to avoid.
            logger.info(f"[sync_engine] {page!r}: no keywords need backfill for {site_url!r} — nothing to do")
            RefreshRun.objects.filter(pk=run_id).update(
                status=RefreshStatus.SUCCESS, completed_count=total, total_count=total,
                finished_at=timezone.now(), records_written=0,
            )
            return {"completed": total, "total": total, "records_written": 0, "errors": [],
                    "note": "no keywords needed backfill"}
        logger.info(f"[sync_engine] {page!r}: narrowing to {len(incremental_kws)} keyword(s) needing backfill")

    for name in connector_names:
        if _run_cancelled(run_id):
            logger.info(f"[sync_engine] sync_page cancelled — stopping before {name!r} "
                        f"({completed}/{total} done, {total_records} records kept)")
            return {"completed": completed, "total": total,
                    "records_written": total_records, "errors": errors, "cancelled": True}

        logger.info(f"[sync_engine] [{completed + 1}/{total}] Running connector: {name!r}")
        RefreshRun.objects.filter(pk=run_id).update(current_connector=name)

        connector = _get_connector(name, site_id=site_url)
        if connector is None:
            logger.warning(f"[sync_engine] Connector {name!r} unavailable — skipping")
            completed += 1
            RefreshRun.objects.filter(pk=run_id).update(completed_count=completed)
            continue

        # Narrow this run to the keywords that actually need measuring, for scopes that ask
        # for it. `incremental_kws` is resolved ONCE above, before any connector runs; if it
        # came back empty the scope returned early rather than silently running the full list,
        # because "nothing new" and "everything" must not be the same outcome. Consumers read
        # it with getattr(self, "only_keywords", None) — see dataforseo_serp.fetch().
        if incremental_kws is not None and name in _INCREMENTAL_SCOPES.get(page, ()):
            connector.only_keywords = incremental_kws

        try:
            result = connector.sync(site_id=site_url)
        except Exception as exc:
            logger.error(f"[sync_engine] Connector {name!r} raised an exception: {exc}")
            result = {"status": "error", "records_written": 0, "error": str(exc)}

        records = result.get("records_written", 0)
        completed += 1
        total_records += records

        if result.get("status") == "error":
            error_msg = result.get("error", "unknown error")
            errors.append(f"{name}: {error_msg}")
            logger.warning(f"[sync_engine] Connector {name!r} finished with error: {error_msg}")
        else:
            logger.info(
                f"[sync_engine] Connector {name!r} OK — records_written={records}"
            )

        RefreshRun.objects.filter(pk=run_id).update(
            completed_count=completed,
            records_written=total_records,
        )

    # Mark run complete.
    final_status = RefreshStatus.ERROR if errors else RefreshStatus.SUCCESS
    RefreshRun.objects.filter(pk=run_id).update(
        status=final_status,
        current_connector=None,
        completed_count=total,
        finished_at=timezone.now(),
        error_message="; ".join(errors) if errors else None,
    )

    logger.info(
        f"[sync_engine] sync_page finished — page={page!r} site={site_url!r} "
        f"run_id={run_id} status={final_status} records_written={total_records} "
        f"errors={len(errors)}"
    )

    # Post-sync processing (aggregate rebuild etc.).
    _run_post_sync(site_url, connector_names)

    return {
        "completed": completed,
        "total": total,
        "records_written": total_records,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Public helpers (used by views)
# ---------------------------------------------------------------------------

def get_connector_names_for_page(page: str) -> list[str]:
    """Return the list of connector names active for a given page key."""
    return list(PAGE_CONNECTORS.get(page, []))


def get_all_connector_names() -> list[str]:
    """Return the full list of connector names used in sync_all."""
    return list(ALL_CONNECTORS)
